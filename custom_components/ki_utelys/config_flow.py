"""Oppsett i brukerflaten."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_LYS, CONF_MINST_MORKE, CONF_MORGEN_AV, CONF_MORGEN_PAA,
    CONF_SENEST_PAA, CONF_SKY_JUSTERING, CONF_TERSKEL_AV, CONF_TERSKEL_PAA,
    CONF_TIDLIGST_AV, CONF_VAER, DOMAIN, STANDARD,
)


def _skjema(data: dict | None = None) -> vol.Schema:
    d = data or {}

    def v(nokkel):
        return d.get(nokkel, STANDARD.get(nokkel))

    return vol.Schema({
        vol.Required(CONF_LYS, default=d.get(CONF_LYS, [])): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=["light", "switch", "input_boolean"], multiple=True)),
        vol.Optional(CONF_VAER, default=d.get(CONF_VAER, "")): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="weather")),
        vol.Optional(CONF_TERSKEL_PAA, default=v(CONF_TERSKEL_PAA)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=-12, max=6, step=0.5, unit_of_measurement="°")),
        vol.Optional(CONF_TERSKEL_AV, default=v(CONF_TERSKEL_AV)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=-12, max=6, step=0.5, unit_of_measurement="°")),
        vol.Optional(CONF_MINST_MORKE, default=v(CONF_MINST_MORKE)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=0, max=10, step=0.5, unit_of_measurement="t")),
        vol.Optional(CONF_SENEST_PAA, default=v(CONF_SENEST_PAA)):
            selector.TimeSelector(),
        vol.Optional(CONF_TIDLIGST_AV, default=v(CONF_TIDLIGST_AV)):
            selector.TimeSelector(),
        vol.Optional(CONF_MORGEN_PAA, default=v(CONF_MORGEN_PAA)):
            selector.TimeSelector(),
        vol.Optional(CONF_MORGEN_AV, default=v(CONF_MORGEN_AV)):
            selector.TimeSelector(),
        vol.Optional(CONF_SKY_JUSTERING, default=v(CONF_SKY_JUSTERING)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=0, max=4, step=0.5, unit_of_measurement="°")),
    })


class KiUtelysFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="KI Utelys", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_skjema())

    @staticmethod
    def async_get_options_flow(entry):
        return KiUtelysOptions(entry)


class KiUtelysOptions(config_entries.OptionsFlow):
    def __init__(self, entry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data = {**self.entry.data, **self.entry.options}
        return self.async_show_form(step_id="init", data_schema=_skjema(data))
