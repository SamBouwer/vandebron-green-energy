import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, API_URL_BASE  # ✅ Import API base URL

_LOGGER = logging.getLogger(__name__)

# ✅ Define Amsterdam timezone for proper DST handling
AMSTERDAM_TZ = ZoneInfo("Europe/Amsterdam")

class VandebronDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Vandebron Green Energy data."""
    
    def __init__(self, hass, day_offset):
        """Initialize the data coordinator."""
        self.hass = hass
        self.day_offset = day_offset  # ✅ Store number of days to retrieve
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
            
            for day in range(self.day_offset):  # ✅ Loop from today up to 'day_offset'
                # ✅ Use Amsterdam timezone for proper DST handling
                target_date = datetime.now(AMSTERDAM_TZ) + timedelta(days=day)
                
                greenest_window_response = await self.api.get_greenest_window(target_date)
                if greenest_window_response:
                    greenest_windows.append(greenest_window_response)
                
                forecast_response = await self.api.get_forecast(target_date)
                if forecast_response:
                    forecast_data.append(forecast_response["data"])
            
            _LOGGER.debug(f"Fetched greenest windows from Vandebron for {self.day_offset} days: {greenest_windows}")
            _LOGGER.debug(f"Fetched green energy forecast from Vandebron for {self.day_offset} days: {forecast_data}")
            
            return {"greenest_windows": greenest_windows, "forecast_data": forecast_data}
            
        except Exception as e:
            _LOGGER.error(f"Error fetching data from Vandebron: {e}")
            raise UpdateFailed(f"Failed to update Vandebron data: {e}")

class VandebronAPI:
    """Handles API communication with Vandebron."""
    
    async def get_greenest_window(self, target_date):
        """Retrieve greenest window for a specific date."""
        try:
            params = {
                "window_size": "3H",
                "forecast_date": target_date.strftime("%Y-%m-%d")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL_BASE}/api/v1/window", params=params) as response:
                    if response.status != 200:
                        _LOGGER.error(f"Error fetching greenest window from Vandebron for {target_date}: HTTP {response.status}")
                        return None
                    
                    return await response.json()
                    
        except Exception as e:
            _LOGGER.error(f"API request failed: {e}")
            return None
    
    async def get_forecast(self, target_date):
        """Retrieve green energy forecast for a specific date."""
        try:
            params = {"forecast_date": target_date.strftime("%Y-%m-%d")}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL_BASE}/api/v1/forecast", params=params) as response:
                    if response.status != 200:
                        _LOGGER.error(f"Error fetching green energy forecast from Vandebron for {target_date}: HTTP {response.status}")
                        return None
                    
                    return await response.json()
                    
        except Exception as e:
            _LOGGER.error(f"API request failed: {e}")
            return None
