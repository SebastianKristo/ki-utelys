"""Tallene man justerer: tersklene og kravet til mørketid."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, NUMBERS


async def async_setup_entry(hass, entry, add):
    add([KiTall(entry, *n) for n in NUMBERS])


class KiTall(NumberEntity, RestoreEntity):
    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_mode = "box"

    def __init__(self, entry, slug, navn, lav, hoy, steg, enhet, standard, ikon):
        self._entry = entry
        self._attr_name = navn
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_native_min_value = lav
        self._attr_native_max_value = hoy
        self._attr_native_step = steg
        self._attr_native_unit_of_measurement = enhet
        self._attr_icon = ikon
        self._verdi = standard
        self.entity_id = f"number.{slug}"

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        sist = await self.async_get_last_state()
        if sist is not None:
            try:
                self._verdi = float(sist.state)
            except (TypeError, ValueError):
                pass

    @property
    def native_value(self) -> float:
        return self._verdi

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._entry.entry_id)},
                "name": "KI Utelys", "manufacturer": "KI"}

    async def async_set_native_value(self, value: float) -> None:
        self._verdi = value
        self.async_write_ha_state()
