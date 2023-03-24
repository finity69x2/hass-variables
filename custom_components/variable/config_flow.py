from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_ICON, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    CONF_ATTRIBUTES,
    CONF_ENTITY_PLATFORM,
    CONF_FORCE_UPDATE,
    CONF_RESTORE,
    CONF_VALUE,
    CONF_VARIABLE_ID,
    DEFAULT_BINARY_SENSOR_VALUE,
    DEFAULT_FORCE_UPDATE,
    DEFAULT_ICON,
    DEFAULT_RESTORE,
    DOMAIN,
    PLATFORMS,
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

ADD_BINARY_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VARIABLE_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ICON, default=DEFAULT_ICON): selector.IconSelector(
            selector.IconSelectorConfig()
        ),
        vol.Optional(
            CONF_VALUE, default=DEFAULT_BINARY_SENSOR_VALUE
        ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
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
            menu_options=["add_" + p for p in PLATFORMS],
        )

    async def async_step_add_sensor(self, user_input=None, errors=None):
        if user_input is not None:

            try:
                user_input.update({CONF_ENTITY_PLATFORM: Platform.SENSOR})
                info = await validate_sensor_input(self.hass, user_input)
                _LOGGER.debug("[New Sensor Variable] info: " + str(info))
                _LOGGER.debug("[New Sensor Variable] user_input: " + str(user_input))
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

    async def async_step_add_binary_sensor(self, user_input=None, errors=None):
        if user_input is not None:

            try:
                user_input.update({CONF_ENTITY_PLATFORM: Platform.BINARY_SENSOR})
                info = await validate_sensor_input(self.hass, user_input)
                _LOGGER.debug("[New Binary Sensor Variable] info: " + str(info))
                _LOGGER.debug(
                    "[New Binary Sensor Variable] user_input: " + str(user_input)
                )
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception as err:
                _LOGGER.exception(
                    "[config_flow async_step_add_binary_sensor] Unexpected exception:"
                    + str(err)
                )
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="add_binary_sensor",
            data_schema=ADD_BINARY_SENSOR_SCHEMA,
            errors=errors,
            description_placeholders={
                "component_config_url": COMPONENT_CONFIG_URL,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ):
        """Get the options flow."""
        return VariableOptionsFlowHandler(config_entry)


class VariableOptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""

        _LOGGER.debug("Starting Options")
        # errors = {}

        _LOGGER.debug("[Options] initial config: " + str(self.config_entry.data))
        _LOGGER.debug("[Options] initial options: " + str(self.config_entry.options))

        if self.config_entry.data.get(CONF_ENTITY_PLATFORM) in PLATFORMS and (
            new_func := getattr(
                self,
                "async_step_"
                + self.config_entry.data.get(CONF_ENTITY_PLATFORM)
                + "_options",
                False,
            )
        ):
            return await new_func()

    async def async_step_sensor_options(
        self, user_input=None, errors=None
    ) -> FlowResult:

        _LOGGER.debug("Starting Sensor Options")
        if user_input is not None:
            _LOGGER.debug("[Sensor Options] user_input: " + str(user_input))

            for m in dict(self.config_entry.data).keys():
                user_input.setdefault(m, self.config_entry.data[m])
            _LOGGER.debug("[Sensor Options] updated user_input: " + str(user_input))
            self.config_entry.options = {}
            _LOGGER.debug(
                "[Sensor Options] cleared config_entry.options: "
                + str(self.config_entry.options)
            )
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data=user_input)

        SENSOR_OPTIONS_SCHEMA = vol.Schema(
            {
                vol.Optional(
                    CONF_VALUE, default=self.config_entry.data.get(CONF_VALUE)
                ): cv.string,
                vol.Optional(
                    CONF_ATTRIBUTES, default=self.config_entry.data.get(CONF_ATTRIBUTES)
                ): selector.ObjectSelector(selector.ObjectSelectorConfig()),
                vol.Optional(
                    CONF_RESTORE,
                    default=self.config_entry.data.get(CONF_RESTORE, DEFAULT_RESTORE),
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Optional(
                    CONF_FORCE_UPDATE,
                    default=self.config_entry.data.get(
                        CONF_FORCE_UPDATE, DEFAULT_FORCE_UPDATE
                    ),
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            }
        )

        return self.async_show_form(
            step_id="sensor_options",
            data_schema=SENSOR_OPTIONS_SCHEMA,
            description_placeholders={
                "component_config_url": COMPONENT_CONFIG_URL,
                "sensor_name": self.config_entry.data.get(
                    CONF_NAME, self.config_entry.data.get(CONF_VARIABLE_ID)
                ),
            },
        )

    async def async_step_binary_sensor_options(
        self, user_input=None, errors=None
    ) -> FlowResult:

        if user_input is not None:
            _LOGGER.debug("[Binary Sensor Options] user_input: " + str(user_input))
            return self.async_create_entry(title="", data=user_input)

        BINARY_SENSOR_OPTIONS_SCHEMA = vol.Schema(
            {
                vol.Optional(
                    CONF_VALUE,
                    default=self.config_entry.data.get(
                        CONF_VALUE, DEFAULT_BINARY_SENSOR_VALUE
                    ),
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Optional(
                    CONF_ATTRIBUTES, default=self.config_entry.data.get(CONF_ATTRIBUTES)
                ): selector.ObjectSelector(selector.ObjectSelectorConfig()),
                vol.Optional(
                    CONF_RESTORE,
                    default=self.config_entry.data.get(CONF_RESTORE, DEFAULT_RESTORE),
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Optional(
                    CONF_FORCE_UPDATE,
                    default=self.config_entry.data.get(
                        CONF_FORCE_UPDATE, DEFAULT_FORCE_UPDATE
                    ),
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            }
        )

        return self.async_show_form(
            step_id="binary_sensor_options",
            data_schema=BINARY_SENSOR_OPTIONS_SCHEMA,
            description_placeholders={
                "component_config_url": COMPONENT_CONFIG_URL,
                "sensor_name": self.config_entry.data.get(
                    CONF_NAME, self.config_entry.data.get(CONF_VARIABLE_ID)
                ),
            },
        )
