"""
Sentinel-K Enhanced Main Orchestrator
Urban Emergency Intelligence System for Karachi

Enhanced version with:
- Telegram notifications
- Web dashboard
- SQLite database
- Scheduled reports

Run with: python src/main_enhanced.py
"""
import os
import sys
import time
import json
import logging
import threading
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from watchers.rss_watcher import RSSWatcher
from watchers.weather_watcher import WeatherWatcher
from watchers.social_watcher import SocialWatcher
from engines.correlation_engine import CorrelationEngine
from models.incident import Incident, ConfidenceLevel

# Enhanced imports
from notifiers.telegram_bot import TelegramNotifier
from notifiers.discord_bot import DiscordNotifier
from storage.database import IncidentDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("sentinel-k")


class SentinelKEnhanced:
    """
    Enhanced Sentinel-K with notifications, database, and web dashboard
    """

    # Poll intervals (seconds)
    RSS_INTERVAL = 300       # 5 minutes
    WEATHER_INTERVAL = 900   # 15 minutes
    SOCIAL_INTERVAL = 300    # 5 minutes
    HEARTBEAT_INTERVAL = 300 # 5 minutes (Telegram heartbeat)

    STARTUP_BANNER = """
================================================================
              SENTINEL-K ENHANCED
        Karachi Urban Intelligence Officer

  Features:
  * Multi-source correlation      * Telegram alerts
  * Web dashboard                 * SQLite history
  * Roman Urdu detection          * Confidence scoring

  WARNING: NOT AN EMERGENCY DISPATCHER
  For emergencies: Police 15 | Rescue 1122 | Edhi 115
================================================================
"""

    def __init__(self, vault_path: str = "Sentinel_Vault"):
        self.vault_path = vault_path
        self._setup_vault()

        # Initialize watchers
        self.rss_watcher = RSSWatcher()
        self.weather_watcher = WeatherWatcher()
        self.social_watcher = SocialWatcher()

        # Initialize engines
        self.correlation_engine = CorrelationEngine(vault_path)
        self.correlation_engine.clear_all_incidents()  # Clear old cached data on startup

        # Initialize enhancements
        self.telegram = TelegramNotifier()
        self.discord = DiscordNotifier()
        self.database = IncidentDatabase(os.path.join(vault_path, "sentinel_k.db"))

        # Track last poll times
        self.last_rss_poll = 0
        self.last_weather_poll = 0
        self.last_social_poll = 0
        self.last_heartbeat = 0

        # Web dashboard thread
        self.dashboard_thread = None

        logger.info("Sentinel-K Enhanced initialized")

        # Initialize dashboard data with weather on startup
        self._initialize_dashboard()

    def _initialize_dashboard(self):
        """Create initial dashboard data file with weather"""
        try:
            weather = self.weather_watcher.get_current_conditions()
            dashboard_data = {
                "active_alerts": 0,
                "monitoring": 0,
                "logged": 0,
                "incidents": [],
                "weather": weather,
                "stats": {"accuracy": {}, "by_location": {}},
                "updated": datetime.now().isoformat()
            }
            dashboard_path = os.path.join(self.vault_path, "config", "dashboard_data.json")
            os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
            with open(dashboard_path, "w") as f:
                json.dump(dashboard_data, f, indent=2)
            logger.info(f"Dashboard initialized with weather: {weather.get('temperature_c', 'N/A')}C")
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")

    def _setup_vault(self):
        """Create Sentinel_Vault directory structure"""
        dirs = ["incidents", "logs", "audit", "config"]
        for dir_name in dirs:
            path = os.path.join(self.vault_path, dir_name)
            os.makedirs(path, exist_ok=True)

    def _should_poll(self, last_poll: float, interval: int) -> bool:
        return (time.time() - last_poll) >= interval

    def poll_all_sources(self):
        """Poll all data sources"""
        all_sources = []
        now = time.time()

        if self._should_poll(self.last_rss_poll, self.RSS_INTERVAL):
            logger.info("📰 Polling RSS feeds...")
            sources = self.rss_watcher.poll_all()
            all_sources.extend(sources)
            self.last_rss_poll = now

        if self._should_poll(self.last_weather_poll, self.WEATHER_INTERVAL):
            logger.info("🌤️ Polling weather data...")
            sources = self.weather_watcher.poll()
            all_sources.extend(sources)
            self.last_weather_poll = now

        if self._should_poll(self.last_social_poll, self.SOCIAL_INTERVAL):
            logger.info("📱 Polling social media...")
            sources = self.social_watcher.poll()
            all_sources.extend(sources)
            self.last_social_poll = now

        return all_sources

    def process_cycle(self):
        """Run one processing cycle"""
        sources = self.poll_all_sources()

        if sources:
            logger.info(f"🔄 Processing {len(sources)} sources...")

            # Correlate and detect incidents
            alertable = self.correlation_engine.process_and_alert(sources)

            # Handle alerts
            for incident in alertable:
                self._handle_alert(incident)

            # Update dashboard
            self._update_dashboard()
        else:
            logger.debug("No new sources to process")

        # Send heartbeat every 5 minutes
        self._send_heartbeat_if_due()

    def _send_heartbeat_if_due(self):
        """Send heartbeat every 5 minutes (Discord + Telegram)"""
        now = time.time()
        if self._should_poll(self.last_heartbeat, self.HEARTBEAT_INTERVAL):
            try:
                # Get current stats
                active_alerts = len(self.correlation_engine.get_active_incidents())
                weather = self.weather_watcher.get_current_conditions()
                temp = weather.get('temperature_c')

                # Send heartbeat (Discord primary, Telegram backup)
                self.discord.send_heartbeat(
                    active_alerts=active_alerts,
                    weather_temp=temp
                )
                self.telegram.send_heartbeat(
                    active_alerts=active_alerts,
                    weather_temp=temp
                )
                self.last_heartbeat = now
                logger.info("💓 Heartbeat sent (Discord + Telegram)")
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")

    def _handle_alert(self, incident: Incident):
        """Handle an alertable incident with all notification channels"""
        level = incident.confidence_level

        # Log to database
        self.database.save_incident(incident)

        # Console output
        if level == ConfidenceLevel.HIGH:
            logger.warning(f"HIGH ALERT: {incident.incident_type.value} at {incident.location}")
        elif level == ConfidenceLevel.MEDIUM:
            logger.warning(f"MEDIUM ALERT: {incident.incident_type.value} at {incident.location}")

        # Send notifications (Discord primary, Telegram backup)
        self.discord.send_alert(incident)
        self.telegram.send_alert(incident)

        # Write to file for external integrations
        self._write_alert_file(incident)

        # Print alert to console
        print(incident.generate_alert())

    def _write_alert_file(self, incident: Incident):
        """Write alert to file"""
        alert_path = os.path.join(self.vault_path, "logs", "latest_alert.json")
        with open(alert_path, "w") as f:
            json.dump(incident.to_dict(), f, indent=2)

    def _update_dashboard(self):
        """Update dashboard data file"""
        dashboard_data = self.correlation_engine.generate_dashboard_data()
        dashboard_data["weather"] = self.weather_watcher.get_current_conditions()

        # Add database stats
        dashboard_data["stats"] = {
            "accuracy": self.database.get_accuracy_stats(days=7),
            "by_location": self.database.get_location_stats(days=7),
        }

        dashboard_path = os.path.join(self.vault_path, "config", "dashboard_data.json")
        with open(dashboard_path, "w") as f:
            json.dump(dashboard_data, f, indent=2)

        # Also update Obsidian file
        self._update_obsidian(dashboard_data)

    def _update_obsidian(self, data: dict):
        """Update Obsidian mission-control.md file"""
        obsidian_path = "obsidian/mission-control.md"
        if not os.path.exists("obsidian"):
            os.makedirs("obsidian", exist_ok=True)

        incidents = data.get("incidents", [])
        weather = data.get("weather", {})
        now = datetime.now()

        # Build incident table
        incident_rows = ""
        if incidents:
            for inc in incidents[:10]:
                incident_rows += f"| {inc.get('time', '--')} | {inc.get('type', 'unknown')} | {inc.get('location', '--')} | {inc.get('level', 'LOW')} | {inc.get('sources', 1)} | Active |\n"
        else:
            incident_rows = "| -- | -- | -- | -- | -- | No active incidents |\n"

        content = f"""# SENTINEL-K MISSION CONTROL

> **Last Update**: {now.strftime('%Y-%m-%d %H:%M:%S')} PKT
> **System Status**: ONLINE

---

## KPI STRIP

| Active Alerts | Temperature | Humidity | Wind | System |
|:-------------:|:-----------:|:--------:|:----:|:------:|
| {len(incidents)} | {weather.get('temperature_c', '--')}°C | {weather.get('humidity_percent', '--')}% | {weather.get('wind_kmh', '--')} km/h | ONLINE |

---

## LIVE INCIDENT FEED

| Time | Type | Location | Level | Sources | Status |
|------|------|----------|-------|---------|--------|
{incident_rows}
> *Auto-updates when Sentinel-K is running*

---

## DATA SOURCES

| Source | Status | Last Poll |
|--------|--------|-----------|
| RSS Feeds | ✅ Active | {now.strftime('%H:%M')} |
| Weather API | ✅ Active | {now.strftime('%H:%M')} |
| Social/Brave | ✅ Active | {now.strftime('%H:%M')} |
| Discord | ✅ Active | Heartbeat every 5 min |

---

## EMERGENCY CONTACTS

| Service | Number |
|---------|--------|
| Police | 15 |
| Rescue 1122 | 1122 |
| Edhi | 115 |
| Chhipa | 1021 |

---

*Sentinel-K v1.0 | Auto-generated at {now.strftime('%H:%M:%S')}*
"""
        try:
            with open(obsidian_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to update Obsidian: {e}")

    def start_web_dashboard(self, port: int = 8000):
        """Start web dashboard in background thread"""
        def run_dashboard():
            from dashboard.web_server import run_server
            run_server(port=port)

        self.dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        self.dashboard_thread.start()
        logger.info(f"🌐 Web dashboard started at http://localhost:{port}")

    def run(self, single_cycle: bool = False, with_dashboard: bool = True):
        """Main run loop"""
        print(self.STARTUP_BANNER)
        logger.info("Starting Sentinel-K Enhanced...")

        # Start web dashboard
        if with_dashboard:
            self.start_web_dashboard()
            time.sleep(2)  # Let dashboard start

        # Force initial poll
        self.last_rss_poll = 0
        self.last_weather_poll = 0
        self.last_social_poll = 0

        try:
            while True:
                cycle_start = time.time()

                try:
                    self.process_cycle()
                except Exception as e:
                    logger.error(f"Error in cycle: {e}", exc_info=True)

                if single_cycle:
                    break

                # Wait before next cycle
                elapsed = time.time() - cycle_start
                sleep_time = max(60 - elapsed, 10)
                logger.debug(f"💤 Sleeping {sleep_time:.0f}s...")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
            self._shutdown()

    def _shutdown(self):
        """Clean shutdown"""
        logger.info("Sentinel-K shutting down...")
        self._update_dashboard()

        # Send daily summary if configured
        try:
            summary = self.database.generate_daily_summary()
            weather = self.weather_watcher.get_current_conditions()
            incidents = self.correlation_engine.get_active_incidents()
            self.telegram.send_daily_summary(incidents, weather)
        except:
            pass

        logger.info("Shutdown complete.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sentinel-K Enhanced")
    parser.add_argument("--vault", default="Sentinel_Vault", help="Vault path")
    parser.add_argument("--single", action="store_true", help="Single cycle only")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable web dashboard")
    parser.add_argument("--debug", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    sentinel = SentinelKEnhanced(vault_path=args.vault)
    sentinel.run(
        single_cycle=args.single,
        with_dashboard=not args.no_dashboard
    )


if __name__ == "__main__":
    main()
