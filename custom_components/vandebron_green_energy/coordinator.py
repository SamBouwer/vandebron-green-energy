import logging
import aiohttp
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, API_URL_BASE, WINDOW_SIZE_HOURS, MAX_DAY_OFFSET  # ✅ Import API settings

_LOGGER = logging.getLogger(__name__)

AMSTERDAM_TZ = ZoneInfo("Europe/Amsterdam")

class VandebronDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Vandebron Green Energy data."""

    def __init__(self, hass, day_offset):
        """Initialize the data coordinator."""
        self.hass = hass
        self.day_offset = min(day_offset, MAX_DAY_OFFSET)  # ✅ Clamp older entries that were configured with up to 7 days
        self.api = VandebronAPI()  # ✅ Initialize API handler

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),  # ✅ Refresh data every 15 minutes
        )

    async def _async_update_data(self):
        """Fetch data from Vandebron API for multiple days."""
        try:
            greenest_windows = []  # ✅ Store greenest window data for requested days
            forecast_data = []

            today = datetime.now(AMSTERDAM_TZ).date()  # ✅ API interprets dates in Amsterdam local time

            for day in range(self.day_offset):  # ✅ Loop from today up to 'day_offset'

                target_date = today + timedelta(days=day)  # ✅ Calculate correct date

                # ✅ Keep a None placeholder on failure so list index always matches the day offset
                greenest_windows.append(await self.api.get_greenest_window(target_date))

                forecast_response = await self.api.get_forecast(target_date)  # ✅ Fetch forecast for specific day
                forecast_data.append(forecast_response["data"] if forecast_response else None)

            _LOGGER.debug(f"Fetched greenest windows from Vandebron for {self.day_offset} days: {greenest_windows}")  # ✅ Debug full dataset
            _LOGGER.debug(f"Fetched green energy forecast from Vandebron for {self.day_offset} days: {forecast_data}")  # ✅ Debug full dataset

            return {"greenest_windows": greenest_windows, "forecast_data": forecast_data}  # ✅ Return full forecast range

        except Exception as e:
            _LOGGER.error(f"Error fetching data from Vandebron: {e}")
            raise UpdateFailed(f"Failed to update Vandebron data: {e}")

class VandebronAPI:
    """Handles API communication with Vandebron."""

    async def get_greenest_window(self, target_date):
        """Retrieve greenest window for a specific date."""
        params = {"windowSizeHours": WINDOW_SIZE_HOURS}
        return await self._get(f"/v1/window/{target_date.isoformat()}", params, "greenest window", target_date)

    async def get_forecast(self, target_date):
        """Retrieve green energy forecast for a specific date."""
        return await self._get(f"/v1/forecast/{target_date.isoformat()}", None, "green energy forecast", target_date)

    async def _get(self, path, params, description, target_date):
        """Perform a GET request and return the parsed JSON, or None on failure."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL_BASE}{path}", params=params) as response:  # ✅ Use imported API URL
                    if response.status != 200:
                        error = await self._read_error(response)
                        _LOGGER.error(f"Error fetching {description} from Vandebron for {target_date}: HTTP {response.status} {error}")
                        return None
                    return await response.json()  # ✅ Parse JSON response

        except Exception as e:
            _LOGGER.error(f"API request failed: {e}")
            return None

    @staticmethod
    async def _read_error(response):
        """Extract errorType and message from an API error response, if present."""
        try:
            body = await response.json()
            return f"{body.get('errorType')}: {body.get('message')}"
        except Exception:
            return ""
