"""
Sentinel-K Weather Watcher
Monitors OpenWeatherMap for Karachi weather conditions
Per Constitution Section V.3
"""
import httpx
import os
from datetime import datetime
from typing import List, Optional
import logging

import sys
sys.path.append('..')
from models.source import Source, SourceType
from models.incident import IncidentType

logger = logging.getLogger(__name__)


class WeatherWatcher:
    """
    Polls OpenWeatherMap API for Karachi weather data
    Generates alerts for heatwaves, heavy rain, and extreme conditions
    """

    # Karachi OpenWeatherMap City ID
    KARACHI_CITY_ID = 1174872

    # API endpoint
    API_BASE = "https://api.openweathermap.org/data/2.5/weather"

    # Alert thresholds per Constitution Section V.3
    THRESHOLDS = {
        "heatwave_high": 42,      # > 42°C = HIGH alert
        "heatwave_medium": 38,    # > 38°C = MEDIUM alert
        "rain_heavy": 10,         # > 10mm/hour = HIGH alert
        "rain_moderate": 5,       # > 5mm/hour = MEDIUM alert
        "wind_high": 50,          # > 50 km/h = MEDIUM alert
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            logger.warning("No OpenWeatherMap API key configured. Weather monitoring disabled.")

    def _kelvin_to_celsius(self, kelvin: float) -> float:
        """Convert Kelvin to Celsius"""
        return kelvin - 273.15

    def _mps_to_kmh(self, mps: float) -> float:
        """Convert meters/second to km/hour"""
        return mps * 3.6

    def fetch_weather(self) -> Optional[dict]:
        """Fetch current weather data for Karachi"""
        if not self.api_key:
            return None

        try:
            url = f"{self.API_BASE}?id={self.KARACHI_CITY_ID}&appid={self.api_key}"
            response = httpx.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Weather API error: {e}")
            return None

    def analyze_conditions(self, weather_data: dict) -> List[Source]:
        """Analyze weather data and generate alert sources if thresholds exceeded"""
        sources = []
        now = datetime.now()

        if not weather_data:
            return sources

        main = weather_data.get("main", {})
        wind = weather_data.get("wind", {})
        rain = weather_data.get("rain", {})

        # Temperature analysis
        temp_kelvin = main.get("temp", 0)
        temp_celsius = self._kelvin_to_celsius(temp_kelvin)

        if temp_celsius > self.THRESHOLDS["heatwave_high"]:
            source = Source(
                type=SourceType.WEATHER,
                content=f"HEATWAVE ALERT: Temperature {temp_celsius:.1f}°C exceeds 42°C threshold",
                timestamp=now,
                location="karachi_general",
                verified=True,
            )
            sources.append(source)
            logger.warning(f"[WEATHER] HEATWAVE: {temp_celsius:.1f}°C")

        elif temp_celsius > self.THRESHOLDS["heatwave_medium"]:
            source = Source(
                type=SourceType.WEATHER,
                content=f"Heat Advisory: Temperature {temp_celsius:.1f}°C (approaching extreme)",
                timestamp=now,
                location="karachi_general",
                verified=True,
            )
            sources.append(source)
            logger.info(f"[WEATHER] Heat advisory: {temp_celsius:.1f}°C")

        # Rain analysis (mm in last hour)
        rain_1h = rain.get("1h", 0)

        if rain_1h > self.THRESHOLDS["rain_heavy"]:
            source = Source(
                type=SourceType.WEATHER,
                content=f"HEAVY RAIN ALERT: {rain_1h}mm in last hour - flood risk elevated",
                timestamp=now,
                location="karachi_general",
                verified=True,
            )
            sources.append(source)
            logger.warning(f"[WEATHER] HEAVY RAIN: {rain_1h}mm/hour")

        elif rain_1h > self.THRESHOLDS["rain_moderate"]:
            source = Source(
                type=SourceType.WEATHER,
                content=f"Rain Alert: {rain_1h}mm in last hour - monitor for flooding",
                timestamp=now,
                location="karachi_general",
                verified=True,
            )
            sources.append(source)
            logger.info(f"[WEATHER] Moderate rain: {rain_1h}mm/hour")

        # Wind analysis
        wind_speed_mps = wind.get("speed", 0)
        wind_speed_kmh = self._mps_to_kmh(wind_speed_mps)

        if wind_speed_kmh > self.THRESHOLDS["wind_high"]:
            source = Source(
                type=SourceType.WEATHER,
                content=f"High Wind Alert: {wind_speed_kmh:.1f} km/h winds",
                timestamp=now,
                location="karachi_general",
                verified=True,
            )
            sources.append(source)
            logger.warning(f"[WEATHER] HIGH WIND: {wind_speed_kmh:.1f} km/h")

        return sources

    def poll(self) -> List[Source]:
        """Poll weather API and analyze conditions"""
        logger.info("Starting weather poll...")
        weather_data = self.fetch_weather()
        sources = self.analyze_conditions(weather_data)

        if weather_data:
            main = weather_data.get("main", {})
            temp = self._kelvin_to_celsius(main.get("temp", 0))
            humidity = main.get("humidity", 0)
            logger.info(f"Weather poll complete. Temp: {temp:.1f}°C, Humidity: {humidity}%")

        return sources

    def get_current_conditions(self) -> dict:
        """Get formatted current conditions for dashboard"""
        weather_data = self.fetch_weather()
        if not weather_data:
            return {"status": "unavailable"}

        main = weather_data.get("main", {})
        wind = weather_data.get("wind", {})
        rain = weather_data.get("rain", {})

        return {
            "temperature_c": round(self._kelvin_to_celsius(main.get("temp", 0)), 1),
            "humidity_percent": main.get("humidity", 0),
            "wind_kmh": round(self._mps_to_kmh(wind.get("speed", 0)), 1),
            "rain_1h_mm": rain.get("1h", 0),
            "description": weather_data.get("weather", [{}])[0].get("description", ""),
            "updated": datetime.now().isoformat(),
        }


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watcher = WeatherWatcher()
    print("Current conditions:", watcher.get_current_conditions())
    sources = watcher.poll()
    for source in sources:
        print(f"- [{source.type.value}] {source.content}")
