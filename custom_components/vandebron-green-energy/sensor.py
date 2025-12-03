from homeassistant.components.sensor import SensorEntity
from .coordinator import VandebronDataUpdateCoordinator
from datetime import datetime, timezone
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities dynamically."""
    coordinator = hass.data["vandebron_green_energy"]
    
    sensor_types = ["windowStartAms", "windowEndAms", "greenPercentage"]
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

        if not greenest_windows or len(greenest_windows) <= self.day:
            return None  # ✅ Handle missing data gracefully

        value = greenest_windows[self.day].get(self.sensor_type, "Unknown")
        
        # ✅ Convert greenPercentage to whole number
        if self.sensor_type == "greenPercentage" and value != "Unknown":
            return round(value)
        
        return value

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
        
        if not forecast_data:
            return None  # ✅ Return None if forecast data is missing
        
        return forecast_data[0][0]["datetimeAms"]  # ✅ Show latest forecasted percentage

    @property
    def extra_state_attributes(self):
        """Return all forecast data with formatted timestamps."""
        forecast_data = self.coordinator.data.get("forecast_data", [])
        
        timestamps = []
        solar_percentages = []
        wind_percentages = []
        green_percentages = []

        for day in forecast_data:
            for timepoint in day:
                _LOGGER.debug(f"Entry in forecast_data: {timepoint}")
                timestamps.append(timepoint["datetimeAms"])
                # ✅ Round percentages to whole numbers
                solar_percentages.append(round(timepoint["solarPercentage"]))
                wind_percentages.append(round(timepoint["windPercentage"]))
                green_percentages.append(round(timepoint["greenPercentage"]))

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
        greenest_windows = self.coordinator.data.get("greenest_windows", [])

        if not greenest_windows:
            return None  # ✅ Avoid errors if no data is available
        
        window_start = datetime.strptime(greenest_windows[0]["windowStartAms"],"%Y-%m-%dT%H:%M+01:00")
        _LOGGER.debug(f"Retrieving Vandebron greenest_windows from Coordinator for start: {window_start}")

        now = datetime.now()
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
        greenest_windows = self.coordinator.data.get("greenest_windows", [])

        if not greenest_windows:
            return None  # ✅ Avoid errors if no data is available
        
        window_start = datetime.strptime(greenest_windows[0]["windowStartAms"],"%Y-%m-%dT%H:%M+01:00").replace(tzinfo=timezone.utc)


        return window_start.strftime("%H:%M")  # ✅ Format as HH:MM

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
        greenest_windows = self.coordinator.data.get("greenest_windows", [])

        if not greenest_windows:
            return None  # ✅ Avoid errors if no data is available
        
        window_end = datetime.strptime(greenest_windows[0]["windowEndAms"],"%Y-%m-%dT%H:%M+01:00").replace(tzinfo=timezone.utc)

        if not window_end:
            return None  # ✅ Prevent errors if no data is available

        return window_end.strftime("%H:%M")  # ✅ Format as HH:MM
