"""Navet: leser solhøyde, spør reglene, og slår lysene av og på."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import regler, sol
from .const import (
    CONF_LYS,
    CONF_MINST_MORKE,
    CONF_MORGEN_AV,
    CONF_MORGEN_PAA,
    CONF_SENEST_PAA,
    CONF_SKY_JUSTERING,
    CONF_TERSKEL_AV,
    CONF_TERSKEL_PAA,
    CONF_TIDLIGST_AV,
    CONF_VAER,
    DOMAIN,
    STANDARD,
)

_LOGGER = logging.getLogger(__name__)

# Hvert minutt. Solhøyden endrer seg med rundt 0,13° i minuttet ved våre breddegrader,
# så tettere sjekk ville ikke gitt et eneste tidligere lysskifte.
INTERVALL = timedelta(minutes=1)


class Utelys:
    """Én instans per sted. Eier bryterne, tallene og selve avgjørelsen."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.minne: dict = {}
        self._av = None
        # Hva vi sist gjorde, og hvorfor. Vises på statussensoren.
        self.siste: regler.Svar | None = None
        self.vi_slo_paa = False

    # -- oppsett ------------------------------------------------------------
    async def async_start(self) -> None:
        self._av = async_track_time_interval(self.hass, self._tikk, INTERVALL)
        await self._tikk(dt_util.now())

    async def async_stop(self) -> None:
        if self._av:
            self._av()
            self._av = None

    # -- hjelpere -----------------------------------------------------------
    def cfg(self, nokkel, standard=None):
        """Verdi fra oppsettet, med standard fra const som reserve."""
        data = {**self.entry.data, **self.entry.options}
        return data.get(nokkel, STANDARD.get(nokkel, standard))

    def st(self, eid: str):
        s = self.hass.states.get(eid) if eid else None
        if not s or s.state in ("unknown", "unavailable", ""):
            return None
        return s

    def tall(self, eid: str, standard: float) -> float:
        """Les et number.* fra vår egen integrasjon, ellers standarden."""
        s = self.st(eid)
        if not s:
            return standard
        try:
            return float(s.state)
        except (TypeError, ValueError):
            return standard

    def bryter_paa(self, slug: str, standard: bool = True) -> bool:
        s = self.st(f"switch.{slug}")
        if not s:
            return standard
        return s.state == "on"

    @property
    def breddegrad(self) -> float:
        """Fra Home Assistants egen posisjon.

        Det er med vilje at dette ikke er en innstilling: står HA på riktig sted, er
        breddegraden riktig. En ekstra innstilling ville bare vært et sted å skrive feil.
        """
        return float(self.hass.config.latitude or 59.9)

    def solhoyde(self) -> float | None:
        """Solhøyden nå, fra sun-integrasjonen."""
        s = self.hass.states.get("sun.sun")
        if not s:
            return None
        h = s.attributes.get("elevation")
        try:
            return float(h)
        except (TypeError, ValueError):
            return None

    def skydekke(self) -> float | None:
        """Skydekke i prosent fra værentiteten, om den er satt opp."""
        eid = self.cfg(CONF_VAER)
        s = self.st(eid) if eid else None
        if not s:
            return None
        v = s.attributes.get("cloud_coverage")
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    # -- selve avgjørelsen --------------------------------------------------
    def vurder(self, naa=None) -> regler.Svar | None:
        naa = naa or dt_util.now()
        hoyde = self.solhoyde()
        if hoyde is None:
            return None

        lys = self.cfg(CONF_LYS) or []
        if isinstance(lys, str):
            lys = [lys]
        star_paa = any((self.st(e) or type("x", (), {"state": "off"})).state == "on"
                       for e in lys)

        t_paa = self.tall("number.ki_utelys_terskel_paa", self.cfg(CONF_TERSKEL_PAA))
        t_av = self.tall("number.ki_utelys_terskel_av", self.cfg(CONF_TERSKEL_AV))
        minst = self.tall("number.ki_utelys_minst_morke", self.cfg(CONF_MINST_MORKE))

        # Sommersperren regnes på kveldens dato. Etter midnatt hører natta til i går,
        # så vi ser bakover — ellers ville sperren slått inn midt i en natt som var
        # godkjent da den startet.
        dag = naa.date() if naa.hour >= 12 else (naa - timedelta(days=1)).date()
        morkt = sol.blir_morkt(dag, self.breddegrad, t_paa, minst)

        return regler.bor_lyse(
            naa=naa,
            hoyde=hoyde,
            star_paa=star_paa,
            morkt_i_natt=morkt,
            terskel_paa=t_paa,
            terskel_av=t_av,
            senest_paa=self.cfg(CONF_SENEST_PAA),
            tidligst_av=self.cfg(CONF_TIDLIGST_AV),
            morgen_paa=self.cfg(CONF_MORGEN_PAA),
            morgen_av=self.cfg(CONF_MORGEN_AV),
            kveld_aktiv=self.bryter_paa("ki_utelys_kveld"),
            morgen_aktiv=self.bryter_paa("ki_utelys_morgen"),
            skydekke=self.skydekke(),
            sky_justering=float(self.cfg(CONF_SKY_JUSTERING) or 0),
        )

    async def _tikk(self, naa) -> None:
        if not self.bryter_paa("ki_utelys_auto"):
            self.siste = regler.Svar(False, "Automatikken er av")
            return

        svar = self.vurder(naa)
        if svar is None:
            self.siste = regler.Svar(False, "Finner ikke solhøyden")
            return
        self.siste = svar

        lys = self.cfg(CONF_LYS) or []
        if isinstance(lys, str):
            lys = [lys]
        if not lys:
            return

        for eid in lys:
            s = self.st(eid)
            if not s:
                continue
            er_paa = s.state == "on"
            if svar.paa and not er_paa:
                await self._sett(eid, True)
                self.vi_slo_paa = True
            elif not svar.paa and er_paa:
                # Vi slår bare av det VI slo på. Har noen tent lyset manuelt, står det
                # — den som trykket vet best hvorfor.
                if self.vi_slo_paa:
                    await self._sett(eid, False)
        if not svar.paa:
            self.vi_slo_paa = False

    async def _sett(self, eid: str, paa: bool) -> None:
        domene = eid.split(".")[0]
        if domene not in ("light", "switch", "input_boolean"):
            _LOGGER.warning("ki_utelys: kan ikke styre %s", eid)
            return
        await self.hass.services.async_call(
            domene, "turn_on" if paa else "turn_off", {"entity_id": eid}, blocking=False
        )

    # -- til sensorene ------------------------------------------------------
    def neste_tider(self):
        """Når slår lyset seg på og av neste gang?

        Vises som sensorer, så man ser at automatikken lever i stedet for å lure.
        """
        naa = dt_util.now()
        t_paa = self.tall("number.ki_utelys_terskel_paa", self.cfg(CONF_TERSKEL_PAA))
        t_av = self.tall("number.ki_utelys_terskel_av", self.cfg(CONF_TERSKEL_AV))
        return (
            sol.naar_krysser(naa, self.breddegrad, t_paa, synkende=True),
            sol.naar_krysser(naa, self.breddegrad, t_av, synkende=False),
        )
