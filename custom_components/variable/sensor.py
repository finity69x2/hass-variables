import asyncio
from datetime import timedelta
import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_ICON,
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    SERVICE_RELOAD,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify
import voluptuous as vol

from .const import (
    ATTR_ATTRIBUTES,
    ATTR_REPLACE_ATTRIBUTES,
    ATTR_VALUE,
    ATTR_VARIABLE,
    CONF_ATTRIBUTES,
    CONF_FORCE_UPDATE,
    CONF_RESTORE,
    CONF_VALUE,
    CONF_VARIABLE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

try:
    use_issue_reg = True
    from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
except Exception as e:
    _LOGGER.debug(
        "Unknown Exception trying to import issue_registry. Is HA version <2022.9?: "
        + str(e)
    )
    use_issue_reg = False

THROTTLE_INTERVAL = timedelta(seconds=600)
SCAN_INTERVAL = timedelta(seconds=30)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

SERVICE_SET_VARIABLE = "set_variable"


SERVICE_SET_VARIABLE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VARIABLE): cv.string,
        vol.Optional(ATTR_VALUE): cv.match_all,
        vol.Optional(ATTR_ATTRIBUTES): dict,
        vol.Optional(ATTR_REPLACE_ATTRIBUTES): cv.boolean,
    }
)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_VARIABLE_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ICON): cv.string,
        vol.Optional(CONF_VALUE): cv.match_all,
        vol.Optional(CONF_ATTRIBUTES): dict,
        vol.Optional(CONF_RESTORE): cv.boolean,
        vol.Optional(CONF_FORCE_UPDATE): cv.boolean,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType = None,
) -> None:
    """Set up Variable sensor from YAML."""

    @callback
    def schedule_import(_):
        """Schedule delayed import after HA is fully started."""
        _LOGGER.debug("[YAML Import] Awaiting HA Startup before importing")
        async_call_later(hass, 10, do_import)

    @callback
    def do_import(_):
        """Process YAML import."""
        _LOGGER.debug("[YAML Import] HA Started, proceeding")
        if validate_import():
            _LOGGER.warning(
                "[YAML Import] New YAML sensor, importing: "
                + str(import_config.get(CONF_NAME))
            )

            if use_issue_reg and import_config is not None:
                async_create_issue(
                    hass,
                    DOMAIN,
                    "deprecated_yaml",
                    is_fixable=False,
                    severity=IssueSeverity.WARNING,
                    translation_key="deprecated_yaml",
                )

            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data=import_config,
                )
            )
        # else:
        #    _LOGGER.debug("[YAML Import] Failed validation, not importing")

    @callback
    def validate_import():

        _LOGGER.debug("Starting YAML validate_import")
        return True

    import_config = dict(config)
    _LOGGER.debug("[YAML Import] initial import_config: " + str(import_config))

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, schedule_import)


# async def async_setup(hass: HomeAssistant, config: ConfigType):
#    """Set up the Variable integration component."""
#    _LOGGER.debug("Starting async_setup")
#    hass.data.setdefault(DOMAIN, {})
#    hass.data[DOMAIN] = {}
#    component = EntityComponent(_LOGGER, DOMAIN, hass)
#    # _LOGGER.debug("[async_setup] config: " + str(config))
#
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
#
#    async def async_set_variable_service(call):
#        """Handle calls to the set_variable service."""
#
#        _LOGGER.debug("Starting async_set_variable_service")
#        _LOGGER.debug("call: " + str(call))
#
#        entity_id = ENTITY_ID_FORMAT.format(call.data.get(CONF_VARIABLE_ID))
#        entity = component.get_entity(entity_id)
#
#        if entity:
#            await entity.async_set_variable(
#                call.data.get(ATTR_VALUE),
#                call.data.get(ATTR_ATTRIBUTES),
#                call.data.get(ATTR_REPLACE_ATTRIBUTES, False),
#            )
#        else:
#            _LOGGER.warning("Failed to set unknown variable: %s", entity_id)
#
#    hass.services.async_register(
#        DOMAIN,
#        SERVICE_SET_VARIABLE,
#        async_set_variable_service,
#        schema=SERVICE_SET_VARIABLE_SCHEMA,
#    )
#
#    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:

    """Setup the variable entities with a config_entry (config_flow)."""

    _LOGGER.debug("Starting async_setup_entry")

    config = hass.data.get(DOMAIN).get(config_entry.entry_id)
    unique_id = config_entry.entry_id
    name = config.get(CONF_NAME)
    _LOGGER.debug(
        "[async_setup_entry] config_entry type: " + str(config_entry.__class__.__mro__)
    )
    _LOGGER.debug("[async_setup_entry] config_entry: " + str(config_entry.as_dict()))
    _LOGGER.debug("[async_setup_entry] config: " + str(config))
    _LOGGER.debug("[async_setup_entry] unique_id: " + str(unique_id))

    async_add_entities(
        [Variable(hass, config, config_entry, name, unique_id)], update_before_add=True
    )

    return True


class Variable(SensorEntity, RestoreEntity):
    """Representation of a variable."""

    def __init__(
        self,
        hass,
        config,
        unique_id,
    ):
        """Initialize a variable."""
        _LOGGER.debug("[init] config: " + str(config))
        self._variable_id = config.get(CONF_VARIABLE_ID)
        # self.entity_id = ENTITY_ID_FORMAT.format(self._variable_id)
        # self._config_entry = config_entry
        self._hass = hass
        self._attr_unique_id = unique_id
        # self.config_entry_id = unique_id
        self._attr_name = config.get(CONF_NAME)
        self._attr_icon = config.get(CONF_ICON)
        self._attr_state = config.get(CONF_VALUE)
        # self._attr_native_value = None  # Represents the state in SensorEntity

        self._attr_extra_state_attributes = config.get(CONF_ATTRIBUTES)
        self._restore = config.get(CONF_RESTORE)
        self._force_update = config.get(CONF_FORCE_UPDATE)
        _LOGGER.debug("[init] self type: " + str(self.__class__.__mro__))
        _LOGGER.debug("[init] self: " + str(self))
        _LOGGER.debug("[init] name: " + str(self._attr_name))
        _LOGGER.debug("[init] variable_id: " + str(self._variable_id))
        _LOGGER.debug("[init] entity_id: " + str(self.entity_id))
        _LOGGER.debug("[init] unique_id: " + str(self._attr_unique_id))
        _LOGGER.debug("[init] icon: " + str(self._attr_icon))
        _LOGGER.debug("[init] value: " + str(self._attr_state))
        _LOGGER.debug("[init] attributes: " + str(self._attr_extra_state_attributes))
        _LOGGER.debug("[init] restore: " + str(self._restore))
        _LOGGER.debug("[init] force_update: " + str(self._force_update))

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if self._restore is True:
            # If variable state have been saved.
            _LOGGER.debug("Restoring")
            state = await self.async_get_last_state()
            _LOGGER.debug("Restored state: " + str(state))
            if state:
                # restore state
                self._attr_value = state.state
                # restore value
                self._attr_extra_state_attributes = state.attributes

    @property
    def should_poll(self):
        """If entity should be polled."""
        return False

    # @property
    # def state(self):
    #    """Return the state of the component."""
    #    return self._value

    # @property
    # def state_attributes(self):
    #    """Return the attributes of the variable."""
    #    return self._attributes

    @property
    def force_update(self) -> bool:
        """Force update status of the entity."""
        return self._force_update

    async def async_set_variable(
        self,
        value,
        attributes,
        replace_attributes,
    ):
        """Update variable."""
        updated_attributes = None
        updated_value = None

        if not replace_attributes and self._attributes is not None:
            updated_attributes = dict(self._attributes)

        if attributes is not None:
            if updated_attributes is not None:
                updated_attributes.update(attributes)
            else:
                updated_attributes = attributes

        if value is not None:
            updated_value = value

        self._attr_extra_state_attributes = updated_attributes

        if updated_value is not None:
            self._attr_state = updated_value

        await self.async_update_ha_state()
