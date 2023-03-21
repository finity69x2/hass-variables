"""Variable implementation for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    ATTR_ATTRIBUTES,
    ATTR_ENTITY,
    ATTR_REPLACE_ATTRIBUTES,
    ATTR_VALUE,
    ATTR_VARIABLE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS: list[str] = [Platform.SENSOR]

ENTITY_ID_FORMAT = Platform.SENSOR + ".{}"

SERVICE_SET_VARIABLE_LEGACY = "set_variable"
SERVICE_SET_ENTITY_LEGACY = "set_entity"

SERVICE_SET_VARIABLE_LEGACY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VARIABLE): cv.string,
        vol.Optional(ATTR_VALUE): cv.match_all,
        vol.Optional(ATTR_ATTRIBUTES): dict,
        vol.Optional(ATTR_REPLACE_ATTRIBUTES): cv.boolean,
    }
)

SERVICE_SET_ENTITY_LEGACY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY): cv.string,
        vol.Optional(ATTR_VALUE): cv.match_all,
        vol.Optional(ATTR_ATTRIBUTES): dict,
        vol.Optional(ATTR_REPLACE_ATTRIBUTES): cv.boolean,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Variable services."""
    _LOGGER.debug("Starting async_setup")
    # _LOGGER.debug("[async_setup] config: " + str(config))

    async def async_set_variable_legacy_service(call):
        """Handle calls to the set_variable service."""

        _LOGGER.debug("Starting async_set_variable_legacy_service")
        _LOGGER.debug("call: " + str(call))

        entity_id = ENTITY_ID_FORMAT.format("variable_" + call.data.get(ATTR_VARIABLE))
        entity_registry = er.async_get(hass)
        entity = entity_registry.get_entity(entity_id)

        if entity:
            await entity.async_set_variable(
                call.data.get(ATTR_VALUE),
                call.data.get(ATTR_ATTRIBUTES),
                call.data.get(ATTR_REPLACE_ATTRIBUTES, False),
            )
        else:
            _LOGGER.warning("Failed to set unknown variable: %s", entity_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_VARIABLE_LEGACY,
        async_set_variable_legacy_service,
        schema=SERVICE_SET_VARIABLE_LEGACY_SCHEMA,
    )

    async def async_set_entity_legacy_service(call):
        """Handle calls to the set_entity service."""

        _LOGGER.debug("Starting async_set_entity_legacy_service")
        _LOGGER.debug("call: " + str(call))

        entity_id: str = call.data.get(ATTR_ENTITY)
        entity_registry = er.async_get(hass)
        entity = entity_registry.get_entity(entity_id)

        if entity:
            await entity.async_set_variable(
                call.data.get(ATTR_VALUE),
                call.data.get(ATTR_ATTRIBUTES),
                call.data.get(ATTR_REPLACE_ATTRIBUTES, False),
            )
        else:
            _LOGGER.warning("Failed to set unknown variable: %s", entity_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ENTITY_LEGACY,
        async_set_entity_legacy_service,
        schema=SERVICE_SET_ENTITY_LEGACY_SCHEMA,
    )

    return True


#    async def _handle_reload(service):
#        """Handle reload service call."""
#        _LOGGER.info("Service %s.reload called: reloading integration", DOMAIN)
#
#        current_entries = hass.config_entries.async_entries(DOMAIN)
#
#        reload_tasks = [
#            hass.config_entries.async_reload(entry.entry_id)
#            for entry in current_entries
#        ]
#
#        await asyncio.gather(*reload_tasks)
#
#    hass.helpers.service.async_register_admin_service(
#        DOMAIN,
#        SERVICE_RELOAD,
#        _handle_reload,
#    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    _LOGGER.debug("[init async_setup_entry] entry: " + str(entry.data))
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # This creates each HA object for each platform your device requires.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    _LOGGER.info("Unloading: " + str(entry.data))
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
