from homeassistant.components.sensor import SensorEntity
from .coordinator import VandebronDataUpdateCoordinator, AMSTERDAM_TZ
from datetime import datetime, timezone
import logging

_LOGGER = logging.getLogger(__name__)

# ✅ Sensor keys are kept from the old API so entity IDs stay stable; map them to the new API fields
WINDOW_FIELDS = {
    "windowStartAms": "windowStartDateTime",
    "windowEndAms": "windowEndDateTime",
    "greenPercentage": "greenPercentage",
}

def parse_utc(value):
    """Parse an API UTC timestamp (e.g. 2026-04-26T08:15:00Z) into an Amsterdam-local datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(AMSTERDAM_TZ)

def first_window(coordinator):
    """Return today's greenest window, or None if unavailable."""
    greenest_windows = coordinator.data.get("greenest_windows", [])
    return greenest_windows[0] if greenest_windows else None

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities dynamically."""
    coordinator = hass.data["vandebron_green_energy"]

    sensor_types = list(WINDOW_FIELDS)
    days_offset = range(coordinator.day_offset)

    entities = [VandebronGreenestWindowSensor(coordinator, sensor_type, day)
        for sensor_type in sensor_types
        for day in days_offset
    ]

    for entity in entities:
        _LOGGER.debug(f"Registering sensor for vandebron: {entity._attr_name}")

    # ✅ Add new formatted time sensors
    entities.extend([
        VandebronWindowStartTimeSensor(coordinator),
        VandebronWindowEndTimeSensor(coordinator),
        VandebronForecastSensor(coordinator),
        VandebronTimeUntilNextWindowSensor(coordinator),
    ])

    async_add_entities(entities)

class VandebronGreenestWindowSensor(SensorEntity):
    def __init__(self, coordinator, sensor_type, day):
        """Initialize individual sensor per datapoint and day."""
        self.coordinator = coordinator
        self.sensor_type = sensor_type
        self.day = day  # ✅ Store the day we are retrieving
        self._attr_name = f"Vandebron {sensor_type} Day {day}"
        self._attr_should_poll = False
        self._attr_unique_id = f"vandebron_{sensor_type}_{day}"
        self.coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def state(self):
        """Retrieve the specific datapoint for the given day."""
        greenest_windows = self.coordinator.data.get("greenest_windows", [])

        if len(greenest_windows) <= self.day or not greenest_windows[self.day]:
            return None  # ✅ Handle missing data gracefully

        value = greenest_windows[self.day].get(WINDOW_FIELDS[self.sensor_type])  # ✅ Extract datapoint per day

        if value is None:
            return None

        if self.sensor_type == "greenPercentage":
            return round(value, 2)

        return parse_utc(value).isoformat(timespec="minutes")  # ✅ Same Amsterdam-local format as the old API

class VandebronForecastSensor(SensorEntity):
    def __init__(self, coordinator):
        """Initialize the sensor with coordinator updates."""
        self.coordinator = coordinator
        self._attr_name = "Vandebron Forecast"
        self._attr_should_poll = False  # ✅ Disable polling; rely on coordinator
        self._attr_unique_id = f"vandebron_forecast"  # ✅ Add unique ID
        self.coordinator.async_add_listener(self.async_write_ha_state)  # ✅ Ensure entity updates when data refreshes

    @property
    def state(self):
        """Return the most recent forecasted green percentage."""
        forecast_data = self.coordinator.data.get("forecast_data", [])

        _LOGGER.debug(f"Retrieving Vandebron forecast_data from Coordinator: {forecast_data}")

        if not forecast_data or not forecast_data[0]:
            return None  # ✅ Return None if forecast data is missing

        return forecast_data[0][0]["forecastDateTime"]  # ✅ Show latest forecasted percentage

    @property
    def extra_state_attributes(self):
        """Return all forecast data with formatted timestamps."""
        forecast_data = self.coordinator.data.get("forecast_data", [])

        timestamps = []
        solar_percentages = []
        wind_percentages = []
        green_percentages = []

        for day in forecast_data:
            for timepoint in day or []:  # ✅ Skip days the API returned no data for
                _LOGGER.debug(f"Entry in forecast_data: {timepoint}")
                timestamps.append(timepoint["forecastDateTime"])
                solar_percentages.append(timepoint["solarPercentage"])
                wind_percentages.append(timepoint["windPercentage"])
                green_percentages.append(timepoint["greenPercentage"])

        return {
            "timestamps": timestamps,
            "solar_percentages": solar_percentages,
            "wind_percentages": wind_percentages,
            "green_percentages": green_percentages
        }

    async def async_update(self):
        """Manually trigger a data refresh if needed."""
        await self.coordinator.async_request_refresh()

class VandebronTimeUntilNextWindowSensor(SensorEntity):
    """Sensor that returns minutes left until the start of the next greenest window."""

    def __init__(self, coordinator):
        """Initialize the sensor with coordinator updates."""
        self.coordinator = coordinator
        self._attr_name = "Minutes Until Next Green Window"
        self._attr_should_poll = False  # ✅ Coordinator-driven updates
        self._attr_unique_id = "vandebron_minutesuntilnextwindow"  # ✅ Add unique ID
        self.coordinator.async_add_listener(self.async_write_ha_state)  # ✅ Update when data refreshes

    @property
    def state(self):
        """Return the number of minutes until today's next green window."""
        window = first_window(self.coordinator)

        if not window:
            return None  # ✅ Avoid errors if no data is available

        window_start = parse_utc(window["windowStartDateTime"])
        _LOGGER.debug(f"Retrieving Vandebron greenest_windows from Coordinator for start: {window_start}")

        now = datetime.now(timezone.utc)
        delta = window_start - now

        _LOGGER.debug(f"Retrieving Vandebron greenest_windows from Coordinator for delta: {delta}")

        return max(0, int(delta.total_seconds() // 60))  # ✅ Return minutes left (non-negative)

    async def async_update(self):
        """Manually trigger a data refresh if needed."""
        await self.coordinator.async_request_refresh()

class VandebronWindowStartTimeSensor(SensorEntity):
    """Sensor that returns the start time of the next green window in HH:MM format."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Vandebron Green Window Start Time"
        self._attr_should_poll = False
        self._attr_unique_id = "vandebron_green_window_start_time"
        self.coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def state(self):
        """Return the window start time formatted as HH:MM."""
        window = first_window(self.coordinator)

        if not window:
            return None  # ✅ Avoid errors if no data is available

        window_start = parse_utc(window["windowStartDateTime"])

        return window_start.strftime("%H:%M")  # ✅ Format as HH:MM (Amsterdam time)

class VandebronWindowEndTimeSensor(SensorEntity):
    """Sensor that returns the end time of the next green window in HH:MM format."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Vandebron Green Window End Time"
        self._attr_should_poll = False
        self._attr_unique_id = "vandebron_green_window_end_time"
        self.coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def state(self):
        """Return the window end time formatted as HH:MM."""
        window = first_window(self.coordinator)

        if not window:
            return None  # ✅ Avoid errors if no data is available

        window_end = parse_utc(window["windowEndDateTime"])

        return window_end.strftime("%H:%M")  # ✅ Format as HH:MM (Amsterdam time)
