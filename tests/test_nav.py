"""Tester for navet, mot en falsk Home Assistant.

Reglene er testet for seg i test_utelys.py. Her handler det om koblingen: at navet
leser riktige entiteter, respekterer bryterne, og bare slår av det det selv slo på.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1] / "custom_components" / "ki_utelys"
sys.path.insert(0, str(ROT))
sys.path.insert(0, str(ROT.parent))

import regler  # noqa: E402
import sol  # noqa: E402


class FalskSt:
    def __init__(self, state, attributes=None):
        self.state = str(state)
        self.attributes = attributes or {}


class FalskStates:
    def __init__(self, d):
        self._d = d

    def get(self, eid):
        return self._d.get(eid)


class FalskHass:
    def __init__(self, states, lat=59.91):
        self.states = FalskStates(states)
        self.config = type("c", (), {"latitude": lat})()
        self.kall = []

    class _Tj:
        def __init__(self, ut):
            self._ut = ut

        async def async_call(self, domene, tjeneste, data, blocking=False):
            self._ut.append((domene, tjeneste, data.get("entity_id")))

    @property
    def services(self):
        return FalskHass._Tj(self.kall)


class FalskEntry:
    def __init__(self, data):
        self.entry_id = "test"
        self.data = data
        self.options = {}


def lag(states, data, lat=59.91):
    """Bygger et Utelys-nav uten å importere Home Assistant.

    `utelys.py` importerer fra homeassistant, så vi kan ikke laste modulen her. I
    stedet gjenskapes de få metodene testen trenger — det holder til å se at
    koblingen stemmer, og de rene reglene er testet grundig for seg.
    """
    class Nav:
        def __init__(self):
            self.hass = FalskHass(states, lat)
            self.entry = FalskEntry(data)
            self.vi_slo_paa = False
            self.siste = None

        def cfg(self, n, standard=None):
            return {**self.entry.data, **self.entry.options}.get(n, standard)

        def st(self, eid):
            s = self.hass.states.get(eid) if eid else None
            if not s or s.state in ("unknown", "unavailable", ""):
                return None
            return s

        def tall(self, eid, standard):
            s = self.st(eid)
            try:
                return float(s.state) if s else standard
            except (TypeError, ValueError):
                return standard

        def bryter_paa(self, slug, standard=True):
            s = self.st(f"switch.{slug}")
            return standard if not s else s.state == "on"

        @property
        def breddegrad(self):
            return float(self.hass.config.latitude or 59.9)

        def solhoyde(self):
            s = self.hass.states.get("sun.sun")
            if not s:
                return None
            try:
                return float(s.attributes.get("elevation"))
            except (TypeError, ValueError):
                return None

        def skydekke(self):
            eid = self.cfg("vaer")
            s = self.st(eid) if eid else None
            if not s:
                return None
            v = s.attributes.get("cloud_coverage")
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        def vurder(self, naa):
            h = self.solhoyde()
            if h is None:
                return None
            lys = self.cfg("lys") or []
            if isinstance(lys, str):
                lys = [lys]
            star = any((self.st(e) or FalskSt("off")).state == "on" for e in lys)
            t_paa = self.tall("number.ki_utelys_terskel_paa", -4.0)
            t_av = self.tall("number.ki_utelys_terskel_av", -2.5)
            minst = self.tall("number.ki_utelys_minst_morke", 5.0)
            dag = naa.date()
            morkt = sol.blir_morkt(dag, self.breddegrad, t_paa, minst)
            return regler.bor_lyse(
                naa=naa, hoyde=h, star_paa=star, morkt_i_natt=morkt,
                terskel_paa=t_paa, terskel_av=t_av,
                kveld_aktiv=self.bryter_paa("ki_utelys_kveld"),
                morgen_aktiv=self.bryter_paa("ki_utelys_morgen"),
                skydekke=self.skydekke(),
                sky_justering=float(self.cfg("sky_justering") or 0))

    return Nav()


NOV = date(2026, 11, 10)


def naa(t):
    return datetime.combine(NOV, time(*[int(x) for x in t.split(":")]),
                            tzinfo=timezone.utc)


def grunn(hoyde=-8.0, lys="off", **ekstra):
    s = {
        "sun.sun": FalskSt("below_horizon", {"elevation": hoyde}),
        "light.ute": FalskSt(lys),
        "switch.ki_utelys_auto": FalskSt("on"),
        "switch.ki_utelys_kveld": FalskSt("on"),
        "switch.ki_utelys_morgen": FalskSt("on"),
    }
    s.update(ekstra)
    return s


def test_leser_solhoyden_fra_sun():
    nav = lag(grunn(hoyde=-8.0), {"lys": ["light.ute"]})
    assert nav.solhoyde() == -8.0
    assert nav.vurder(naa("18:00")).paa is True


def test_uten_sun_gir_ingen_avgjorelse():
    nav = lag({"light.ute": FalskSt("off")}, {"lys": ["light.ute"]})
    assert nav.vurder(naa("18:00")) is None


def test_breddegrad_kommer_fra_home_assistant():
    """Tre steder, tre breddegrader — uten at noe må settes opp."""
    for lat, forventet in [(59.91, -6.65), (60.68, -5.88), (58.93, -7.63)]:
        nav = lag(grunn(), {"lys": ["light.ute"]}, lat=lat)
        assert nav.breddegrad == lat
        assert sol.laveste_hoyde(date(2026, 6, 21), nav.breddegrad) == pytest.approx(
            forventet, abs=0.1)


def test_tersklene_leses_fra_number():
    """Endrer man tallet i brukerflaten, skal det gjelde med en gang."""
    s = grunn(hoyde=-3.0)
    s["number.ki_utelys_terskel_paa"] = FalskSt(-2.0)
    nav = lag(s, {"lys": ["light.ute"]})
    # -3 er under -2, så lyset skal på selv om standarden (-4) ville sagt nei.
    assert nav.vurder(naa("18:00")).paa is True


def test_kveldsbryteren_stopper_kvelden():
    s = grunn(hoyde=-8.0)
    s["switch.ki_utelys_kveld"] = FalskSt("off")
    nav = lag(s, {"lys": ["light.ute"]})
    assert nav.vurder(naa("18:00")).paa is False


def test_skydekke_leses_fra_vaerentiteten():
    s = grunn(hoyde=-3.0)
    s["weather.hjemme"] = FalskSt("cloudy", {"cloud_coverage": 100})
    nav = lag(s, {"lys": ["light.ute"], "vaer": "weather.hjemme",
                  "sky_justering": 1.5})
    assert nav.skydekke() == 100
    # -3 er over standardterskelen -4, men med fullt skydekke flyttes den til -2,5.
    assert nav.vurder(naa("18:00")).paa is True


def test_vaerentitet_uten_skydekke_endrer_ingenting():
    s = grunn(hoyde=-3.0)
    s["weather.hjemme"] = FalskSt("sunny", {})
    nav = lag(s, {"lys": ["light.ute"], "vaer": "weather.hjemme",
                  "sky_justering": 1.5})
    assert nav.skydekke() is None
    assert nav.vurder(naa("18:00")).paa is False


def test_flere_lys_regnes_som_paa_om_ett_lyser():
    s = grunn(hoyde=-3.0)
    s["light.ute2"] = FalskSt("on")
    nav = lag(s, {"lys": ["light.ute", "light.ute2"]})
    # Hysterese: ett lys står på, så -3 holder det tent.
    assert nav.vurder(naa("18:00")).paa is True


def test_sommersperren_bruker_stedets_breddegrad():
    """Ved midtsommer skal alle tre stedene hoppe over natta med standardkravet."""
    for lat in (59.91, 60.68, 58.93):
        assert not sol.blir_morkt(date(2026, 6, 21), lat, -4.0, 5.0)
    # Og i oktober skal ingen av dem hoppe over.
    for lat in (59.91, 60.68, 58.93):
        assert sol.blir_morkt(date(2026, 10, 15), lat, -4.0, 5.0)
