from homeassistant.components.binary_sensor import BinarySensorEntity
from .coordinator import VandebronDataUpdateCoordinator
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

_LOGGER = logging.getLogger(__name__)

AMSTERDAM_TZ = ZoneInfo("Europe/Amsterdam")

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor entities."""
    coordinator = hass.data["vandebron_green_energy"]

    entities = [
        VandebronGreenWindowBinarySensor(coordinator),
    ]

    async_add_entities(entities)

def parse_amsterdam_time(datetime_str):
    """Parse datetime string and ensure it's in Amsterdam timezone.

    Handles both formats:
    - ISO format with timezone: "2024-03-15T14:30:00+01:00"
    - ISO format without timezone: "2024-03-15T14:30:00"
    """
    try:
        dt = datetime.fromisoformat(datetime_str)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=AMSTERDAM_TZ)
        else:
            dt = dt.astimezone(AMSTERDAM_TZ)

        return dt
    except Exception as e:
        _LOGGER.error(f"Error parsing datetime '{datetime_str}': {e}")
        return None

class VandebronGreenWindowBinarySensor(BinarySensorEntity):
    """Binary sensor that indicates if a green window is currently active."""

    def __init__(self, coordinator):
        """Initialize the binary sensor with coordinator updates."""
        self.coordinator = coordinator
        self._attr_name = "Vandebron Green Window Active"
        self._attr_should_poll = False
        self._attr_unique_id = "vandebron_green_window_active"
        self.coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def is_on(self):
        """Return True if we are currently in a green window."""
        greenest_windows = self.coordinator.data.get("greenest_windows", [])

        if not greenest_windows:
            return False

        window_start = parse_amsterdam_time(greenest_windows[0]["windowStartAms"])
        window_end = parse_amsterdam_time(greenest_windows[0]["windowEndAms"])

        if not window_start or not window_end:
            return False

        now = datetime.now(AMSTERDAM_TZ)

        is_active = window_start <= now < window_end

        _LOGGER.debug(f"Green window check: now={now}, start={window_start}, end={window_end}, active={is_active}")

        return is_active

    @property
    def extra_state_attributes(self):
        """Return additional attributes about the current window."""
        greenest_windows = self.coordinator.data.get("greenest_windows", [])

        if not greenest_windows:
            return {}

        window_start = parse_amsterdam_time(greenest_windows[0]["windowStartAms"])
        window_end = parse_amsterdam_time(greenest_windows[0]["windowEndAms"])
        green_percentage = greenest_windows[0].get("greenPercentage")

        attributes = {}

        if window_start:
            attributes["window_start"] = window_start.strftime("%H:%M")

        if window_end:
            attributes["window_end"] = window_end.strftime("%H:%M")

        if green_percentage is not None:
            attributes["green_percentage"] = round(green_percentage)

        return attributes