"""Hele integrasjonen i en HA-testinstans: lyset som sto på fra før blir slukket."""
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ki_utelys.const import DOMAIN, CONF_LYS

OSLO = ZoneInfo("Europe/Oslo")
pytestmark = pytest.mark.asyncio


async def _oppsett(hass, naa):
    """Setter opp med klokka frosset på `naa`, så første tikk ved oppstart er forutsigbart."""
    hass.config.latitude = 59.91
    hass.config.longitude = 10.75
    kall = []

    async def tjeneste(call):
        kall.append((call.service, call.data["entity_id"]))
        hass.states.async_set(call.data["entity_id"], "on" if call.service == "turn_on" else "off")
    hass.services.async_register("light", "turn_on", tjeneste)
    hass.services.async_register("light", "turn_off", tjeneste)
    hass.states.async_set("light.ute", "on")                       # sto på fra før
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 20.0})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_LYS: ["light.ute"]}, options={})
    entry.add_to_hass(hass)
    with patch("homeassistant.util.dt.now", return_value=naa):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, kall


async def test_lys_som_sto_paa_fra_for_slukkes_til_slutt(hass):
    formiddag = datetime(2026, 10, 7, 11, 0, tzinfo=OSLO)
    entry, kall = await _oppsett(hass, formiddag)
    ul = hass.data[DOMAIN][entry.entry_id]
    with patch("homeassistant.util.dt.now", return_value=formiddag):
        await ul._tikk(formiddag)
    assert kall == [], "manuelt tent lys skal få stå den første tiden"
    assert ul.lysstatus["light.ute"]["manuell_siden"] and not ul.lysstatus["light.ute"]["vaart"]
    # 13 timer senere (midt på natta sier reglene fortsatt «av» uten at det er vårt? nei – kveld = på)
    # så vi tester grensen på dagtid neste dag i stedet: slå av sola-høyden lav om kvelden
    kveld = datetime(2026, 10, 7, 20, 0, tzinfo=OSLO)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -8.0})
    with patch("homeassistant.util.dt.now", return_value=kveld):
        await ul._tikk(kveld)
    assert kall == [] and ul.lysstatus["light.ute"]["vaart"], "om kvelden overtas lyset"
    morgen = datetime(2026, 10, 8, 10, 0, tzinfo=OSLO)
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 15.0})
    with patch("homeassistant.util.dt.now", return_value=morgen):
        await ul._tikk(morgen)
    assert kall == [("turn_off", "light.ute")], "og slukkes om morgenen"
    assert hass.states.get("light.ute").state == "off"


async def test_manuelt_lys_slukkes_etter_tolv_timer(hass):
    t0 = datetime(2026, 10, 7, 9, 30, tzinfo=OSLO)
    entry, kall = await _oppsett(hass, t0)
    ul = hass.data[DOMAIN][entry.entry_id]
    with patch("homeassistant.util.dt.now", return_value=t0):
        await ul._tikk(t0)
    assert kall == []
    # tretten timer senere er det kveld, og da overtas det — så sett tiden en vinterdag med sol oppe lenge? Nei:
    # bruk en senere dag med samme solhøyde (dagtid) og manuell_siden skrudd tilbake
    ul.lysstatus["light.ute"]["manuell_siden"] = (t0 - timedelta(hours=13)).isoformat(timespec="seconds")
    with patch("homeassistant.util.dt.now", return_value=t0):
        await ul._tikk(t0)
    assert kall == [("turn_off", "light.ute")]
