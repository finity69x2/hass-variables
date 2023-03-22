from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    CONF_ATTRIBUTES,
    CONF_FORCE_UPDATE,
    CONF_RESTORE,
    CONF_VALUE,
    CONF_VARIABLE_ID,
    DEFAULT_FORCE_UPDATE,
    DEFAULT_ICON,
    DEFAULT_RESTORE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

COMPONENT_CONFIG_URL = "https://github.com/Wibias/hass-variables"

# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations

ADD_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VARIABLE_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ICON, default=DEFAULT_ICON): selector.IconSelector(
            selector.IconSelectorConfig()
        ),
        vol.Optional(CONF_VALUE): cv.string,
        vol.Optional(CONF_ATTRIBUTES): selector.ObjectSelector(
            selector.ObjectSelectorConfig()
        ),
        vol.Optional(CONF_RESTORE, default=DEFAULT_RESTORE): selector.BooleanSelector(
            selector.BooleanSelectorConfig()
        ),
        vol.Optional(
            CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE
        ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
    }
)


async def validate_sensor_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input"""

    _LOGGER.debug("[config_flow validate_sensor_input] data: " + str(data))
    if data.get(CONF_NAME):
        return {"title": data.get(CONF_NAME)}
    else:
        return {"title": data.get(CONF_VARIABLE_ID)}


class VariableConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    # Connection classes in homeassistant/config_entries.py are now deprecated

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""

        return self.async_show_menu(
            step_id="user",
            menu_options=["add_sensor", "add_binary_sensor"],
        )

    async def async_step_add_sensor(self, user_input=None, errors=None):
        if user_input is not None:

            try:
                info = await validate_sensor_input(self.hass, user_input)
                _LOGGER.debug("[New Variable] info: " + str(info))
                _LOGGER.debug("[New Variable] user_input: " + str(user_input))
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception as err:
                _LOGGER.exception(
                    "[config_flow async_step_add_sensor] Unexpected exception:"
                    + str(err)
                )
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="add_sensor",
            data_schema=ADD_SENSOR_SCHEMA,
            errors=errors,
            description_placeholders={
                "component_config_url": COMPONENT_CONFIG_URL,
            },
        )
