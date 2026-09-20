"""Sensorene: status med begrunnelse, og når lyset skifter neste gang."""
from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import sol
from .const import DOMAIN
from .utelys import INTERVALL


async def async_setup_entry(hass, entry, add):
    ul = hass.data[DOMAIN][entry.entry_id]
    add([KiStatus(entry, ul), KiNeste(entry, ul, True), KiNeste(entry, ul, False)])


class _Base(SensorEntity):
    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, entry, ul):
        self._entry = entry
        self._ul = ul
        self._av = None

    async def async_added_to_hass(self):
        self._av = async_track_time_interval(
            self.hass, lambda _: self.async_write_ha_state(), INTERVALL)

    async def async_will_remove_from_hass(self):
        if self._av:
            self._av()

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._entry.entry_id)},
                "name": "KI Utelys", "manufacturer": "KI"}


class KiStatus(_Base):
    _attr_icon = "mdi:lightbulb-auto"

    def __init__(self, entry, ul):
        super().__init__(entry, ul)
        self._attr_name = "KI Utelys Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self.entity_id = "sensor.ki_utelys_status"

    @property
    def native_value(self):
        s = self._ul.siste
        if not s:
            return "ukjent"
        return "på" if s.paa else "av"

    @property
    def extra_state_attributes(self):
        """Begrunnelsen er poenget her.

        «Av» alene sier ingenting om hvorfor. «Av — lys sommernatt, hopper over» sier
        at automatikken lever og har tatt et valg.
        """
        s = self._ul.siste
        naa = dt_util.now()
        dag = naa.date() if naa.hour >= 12 else date.fromordinal(naa.toordinal() - 1)
        bredde = self._ul.breddegrad
        t_paa = self._ul.tall("number.ki_utelys_terskel_paa", -4.0)
        return {
            "grunn": s.grunn if s else "",
            "terskel_naa": round(s.terskel, 2) if s and s.terskel is not None else None,
            "solhoyde": self._ul.solhoyde(),
            "skydekke": self._ul.skydekke(),
            "morketid_i_natt": round(sol.timer_under(dag, bredde, t_paa), 2),
            "laveste_solhoyde_i_natt": round(sol.laveste_hoyde(dag, bredde), 2),
            "breddegrad": round(bredde, 3),
        }


class KiNeste(_Base):
    def __init__(self, entry, ul, paa: bool):
        super().__init__(entry, ul)
        self._paa = paa
        navn = "På" if paa else "Av"
        self._attr_name = f"KI Utelys Neste {navn}"
        self._attr_unique_id = f"{entry.entry_id}_neste_{'paa' if paa else 'av'}"
        self._attr_icon = ("mdi:weather-sunset-down" if paa
                           else "mdi:weather-sunset-up")
        self.entity_id = f"sensor.ki_utelys_neste_{'paa' if paa else 'av'}"
        self._attr_device_class = "timestamp"

    @property
    def native_value(self):
        paa, av = self._ul.neste_tider()
        return paa if self._paa else av
