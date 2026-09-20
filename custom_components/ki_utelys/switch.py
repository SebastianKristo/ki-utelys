"""Bryterne: automatikk, morgen og kveld."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, SWITCHES


async def async_setup_entry(hass, entry, add):
    add([KiBryter(entry, *s) for s in SWITCHES])


class KiBryter(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, entry, slug, navn, standard, ikon):
        self._entry = entry
        self._slug = slug
        self._attr_name = navn
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_icon = ikon
        self._standard = standard
        self._paa = standard
        self.entity_id = f"switch.{slug}"

    async def async_added_to_hass(self):
        """Husk stillingen over omstart.

        Uten dette ville en omstart midt på natta satt bryterne tilbake til standard,
        og lyset kunne slått seg på i en periode du hadde skrudd av med vilje.
        """
        await super().async_added_to_hass()
        sist = await self.async_get_last_state()
        if sist is not None and sist.state in ("on", "off"):
            self._paa = sist.state == "on"

    @property
    def is_on(self) -> bool:
        return self._paa

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._entry.entry_id)},
                "name": "KI Utelys", "manufacturer": "KI"}

    async def async_turn_on(self, **kw):
        self._paa = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kw):
        self._paa = False
        self.async_write_ha_state()
