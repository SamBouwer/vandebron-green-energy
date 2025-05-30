from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .coordinator import VandebronDataUpdateCoordinator
import logging

DOMAIN = "vandebron_green_energy"
_LOGGER = logging.getLogger(__name__)  # ✅ Proper logging setup

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Vandebron Green Energy from a config entry."""
    
    _LOGGER.debug("Setting up Vandebron Green Energy")  # ✅ Use _LOGGER instead of hass.logger

    # ✅ Pass day_offset to the coordinator
    try:
        day_offset = entry.data.get("day_offset", 1) # ✅ Retrieve user-configured day_offset from entry
        coordinator = VandebronDataUpdateCoordinator(hass, day_offset)
        await coordinator.async_config_entry_first_refresh()
        await coordinator.async_request_refresh()
        hass.data[DOMAIN] = coordinator
        # ✅ Force a manual refresh right after setup

        hass.data[DOMAIN] = coordinator
    
        # ✅ Forward entry setup for sensors
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
        return True
        
    except Exception as e:
        _LOGGER.error(f"Error setting up Vandebron Green Energy: {e}")
        return False
    
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload integration entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
