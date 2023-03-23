# import asyncio
# from datetime import timedelta
import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA, RestoreSensor
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (  # SERVICE_RELOAD,
    CONF_ICON,
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify
import voluptuous as vol

from .const import (
    ATTR_ATTRIBUTES,
    ATTR_REPLACE_ATTRIBUTES,
    ATTR_VALUE,
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

PLATFORM = Platform.SENSOR
ENTITY_ID_FORMAT = PLATFORM + ".{}"

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

SERVICE_UPDATE_VARIABLE = "update"

SERVICE_UPDATE_VARIABLE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_VALUE): cv.match_all,
        vol.Optional(ATTR_ATTRIBUTES): dict,
        vol.Optional(ATTR_REPLACE_ATTRIBUTES): cv.boolean,
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:

    """Setup the variable entities with a config_entry (config_flow)."""

    _LOGGER.debug("Starting async_setup_entry")
    config_entry.options = {}
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_UPDATE_VARIABLE,
        {
            vol.Optional(ATTR_VALUE): cv.string,
            vol.Optional(ATTR_ATTRIBUTES): dict,
            vol.Optional(ATTR_REPLACE_ATTRIBUTES): cv.boolean,
        },
        "async_update_variable",
    )

    config = hass.data.get(DOMAIN).get(config_entry.entry_id)
    unique_id = config_entry.entry_id
    _LOGGER.debug("[async_setup_entry] config_entry: " + str(config_entry.as_dict()))
    _LOGGER.debug("[async_setup_entry] config: " + str(config))
    _LOGGER.debug("[async_setup_entry] unique_id: " + str(unique_id))

    async_add_entities([Variable(hass, config, unique_id)])

    return True


class Variable(RestoreSensor):
    """Representation of a variable."""

    def __init__(
        self,
        hass,
        config,
        unique_id,
    ):
        """Initialize a variable."""
        _LOGGER.debug("[init] config: " + str(config))
        self._hass = hass
        self._attr_has_entity_name = True
        self._variable_id = slugify(config.get(CONF_VARIABLE_ID).lower())
        self._attr_unique_id = unique_id
        if config.get(CONF_NAME):
            self._attr_name = config.get(CONF_NAME)
        else:
            self._attr_name = config.get(CONF_VARIABLE_ID)
        self._attr_icon = config.get(CONF_ICON)
        self._attr_native_value = config.get(CONF_VALUE)
        self._attr_extra_state_attributes = config.get(CONF_ATTRIBUTES)
        self._restore = config.get(CONF_RESTORE)
        self._force_update = config.get(CONF_FORCE_UPDATE)
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, self._variable_id, hass=self._hass
        )
        _LOGGER.debug("[init] name: " + str(self._attr_name))
        _LOGGER.debug("[init] variable_id: " + str(self._variable_id))
        _LOGGER.debug("[init] entity_id: " + str(self.entity_id))
        _LOGGER.debug("[init] unique_id: " + str(self._attr_unique_id))
        _LOGGER.debug("[init] icon: " + str(self._attr_icon))
        _LOGGER.debug("[init] value: " + str(self._attr_native_value))
        _LOGGER.debug("[init] attributes: " + str(self._attr_extra_state_attributes))
        _LOGGER.debug("[init] restore: " + str(self._restore))
        _LOGGER.debug("[init] force_update: " + str(self._force_update))

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if self._restore is True:
            # If variable state have been saved.
            _LOGGER.debug("Restoring")
            sensor = await self.async_get_last_sensor_data()
            if sensor:
                _LOGGER.debug("Restored sensor: " + str(sensor.as_dict()))
                self._attr_native_value = sensor.native_value
            state = await self.async_get_last_state()
            if state:
                _LOGGER.debug("Restored state: " + str(state.as_dict()))
                self._attr_extra_state_attributes = state.attributes
                self._state = state.state

    @property
    def should_poll(self):
        """If entity should be polled."""
        return False

    @property
    def force_update(self) -> bool:
        """Force update status of the entity."""
        return self._force_update

    async def async_update_variable(
        self,
        value=None,
        attributes=None,
        replace_attributes=False,
    ) -> None:
        """Update variable."""

        _LOGGER.debug("Starting async_update_variable")
        updated_attributes = None
        updated_value = None

        if not replace_attributes and self._attr_extra_state_attributes is not None:
            updated_attributes = dict(self._attr_extra_state_attributes)

        if attributes is not None:
            if updated_attributes is not None:
                updated_attributes.update(attributes)
            else:
                updated_attributes = attributes

        if value is not None:
            updated_value = value

        self._attr_extra_state_attributes = updated_attributes

        if updated_value is not None:
            self._attr_native_value = updated_value

        await self.async_update_ha_state()
