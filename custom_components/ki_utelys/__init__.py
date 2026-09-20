"""KI Utelys – utelys som en fotocelle, tilpasset norske sommernetter."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .utelys import Utelys

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.NUMBER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ul = Utelys(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ul
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Startes ETTER at plattformene er lastet: bryterne og tallene må finnes før
    # første vurdering, ellers leses standardverdier i stedet for dine.
    await ul.async_start()
    entry.async_on_unload(entry.add_update_listener(_oppdater))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ul = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if ul:
        await ul.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _oppdater(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
