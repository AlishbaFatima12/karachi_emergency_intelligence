"""
Sentinel-K Main Orchestrator
Urban Emergency Intelligence System for Karachi

Entry point for continuous monitoring loop.
Run with: python src/main.py
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from watchers.rss_watcher import RSSWatcher
from watchers.weather_watcher import WeatherWatcher
from watchers.social_watcher import SocialWatcher
from engines.correlation_engine import CorrelationEngine
from models.incident import Incident, ConfidenceLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("sentinel-k")


class SentinelK:
    """
    Sentinel-K: The Karachi Urban Intelligence Officer

    Main orchestrator that coordinates:
    - Data watchers (RSS, Weather, Social)
    - Correlation engine
    - Alert generation
    - Dashboard updates
    """

    # Poll intervals (seconds)
    RSS_INTERVAL = 300       # 5 minutes
    WEATHER_INTERVAL = 900   # 15 minutes
    SOCIAL_INTERVAL = 300    # 5 minutes

    # Disclaimer per Constitution
    STARTUP_BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                        SENTINEL-K                                 ║
║            Karachi Urban Intelligence Officer                     ║
║                                                                   ║
║  24/7 Autonomous Monitoring | Multi-Source Correlation            ║
║                                                                   ║
║  ⚠️  VERIFY FIRST: This is an early warning system.               ║
║  NOT AN EMERGENCY DISPATCHER. For emergencies call:               ║
║  Police: 15 | Rescue: 1122 | Edhi: 115                           ║
╚══════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, vault_path: str = "Sentinel_Vault"):
        self.vault_path = vault_path
        self._setup_vault()

        # Initialize watchers
        self.rss_watcher = RSSWatcher()
        self.weather_watcher = WeatherWatcher()
        self.social_watcher = SocialWatcher()

        # Initialize correlation engine
        self.correlation_engine = CorrelationEngine(vault_path)

        # Track last poll times
        self.last_rss_poll = 0
        self.last_weather_poll = 0
        self.last_social_poll = 0

        logger.info("Sentinel-K initialized")

    def _setup_vault(self):
        """Create Sentinel_Vault directory structure"""
        dirs = [
            "incidents",
            "logs",
            "audit",
            "config",
        ]
        for dir_name in dirs:
            path = os.path.join(self.vault_path, dir_name)
            os.makedirs(path, exist_ok=True)

    def _should_poll(self, last_poll: float, interval: int) -> bool:
        """Check if enough time has passed for next poll"""
        return (time.time() - last_poll) >= interval

    def poll_all_sources(self):
        """Poll all data sources based on their intervals"""
        all_sources = []
        now = time.time()

        # RSS feeds (every 5 minutes)
        if self._should_poll(self.last_rss_poll, self.RSS_INTERVAL):
            logger.info("Polling RSS feeds...")
            sources = self.rss_watcher.poll_all()
            all_sources.extend(sources)
            self.last_rss_poll = now

        # Weather API (every 15 minutes)
        if self._should_poll(self.last_weather_poll, self.WEATHER_INTERVAL):
            logger.info("Polling weather data...")
            sources = self.weather_watcher.poll()
            all_sources.extend(sources)
            self.last_weather_poll = now

        # Social media (every 5 minutes)
        if self._should_poll(self.last_social_poll, self.SOCIAL_INTERVAL):
            logger.info("Polling social media...")
            sources = self.social_watcher.poll()
            all_sources.extend(sources)
            self.last_social_poll = now

        return all_sources

    def process_cycle(self):
        """Run one processing cycle"""
        # Collect sources
        sources = self.poll_all_sources()

        if sources:
            logger.info(f"Processing {len(sources)} sources...")

            # Correlate and detect incidents
            alertable = self.correlation_engine.process_and_alert(sources)

            # Handle alerts
            for incident in alertable:
                self._handle_alert(incident)

            # Update dashboard
            self._update_dashboard()
        else:
            logger.debug("No new sources to process")

    def _handle_alert(self, incident: Incident):
        """Handle an alertable incident"""
        level = incident.confidence_level

        if level == ConfidenceLevel.HIGH:
            logger.warning(f"🔴 HIGH ALERT: {incident.incident_type.value} at {incident.location}")
            self._write_alert_file(incident)
        elif level == ConfidenceLevel.MEDIUM:
            logger.warning(f"🟡 MEDIUM ALERT: {incident.incident_type.value} at {incident.location}")
            self._write_alert_file(incident)

        # Generate alert text
        alert_text = incident.generate_alert()
        print(alert_text)

    def _write_alert_file(self, incident: Incident):
        """Write alert to file for notification systems"""
        alert_path = os.path.join(self.vault_path, "logs", "latest_alert.json")
        with open(alert_path, "w") as f:
            json.dump(incident.to_dict(), f, indent=2)

    def _update_dashboard(self):
        """Update Obsidian dashboard data"""
        dashboard_data = self.correlation_engine.generate_dashboard_data()

        # Add weather data
        weather_conditions = self.weather_watcher.get_current_conditions()
        dashboard_data["weather"] = weather_conditions

        # Write dashboard data
        dashboard_path = os.path.join(self.vault_path, "config", "dashboard_data.json")
        with open(dashboard_path, "w") as f:
            json.dump(dashboard_data, f, indent=2)

    def run(self, single_cycle: bool = False):
        """
        Main run loop

        Args:
            single_cycle: If True, run only one cycle (for testing)
        """
        print(self.STARTUP_BANNER)
        logger.info("Starting Sentinel-K monitoring loop...")

        # Force initial poll of all sources
        self.last_rss_poll = 0
        self.last_weather_poll = 0
        self.last_social_poll = 0

        try:
            while True:
                cycle_start = time.time()

                try:
                    self.process_cycle()
                except Exception as e:
                    logger.error(f"Error in processing cycle: {e}", exc_info=True)

                if single_cycle:
                    break

                # Wait before next cycle (check every 60 seconds)
                elapsed = time.time() - cycle_start
                sleep_time = max(60 - elapsed, 10)
                logger.debug(f"Sleeping {sleep_time:.0f}s until next cycle")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Shutdown requested. Exiting gracefully...")
            self._shutdown()

    def _shutdown(self):
        """Clean shutdown"""
        logger.info("Sentinel-K shutting down...")
        # Save current state
        self._update_dashboard()
        logger.info("Shutdown complete.")


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Sentinel-K Urban Intelligence System")
    parser.add_argument(
        "--vault",
        default="Sentinel_Vault",
        help="Path to Sentinel_Vault directory"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run single cycle only (for testing)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    sentinel = SentinelK(vault_path=args.vault)
    sentinel.run(single_cycle=args.single)


if __name__ == "__main__":
    main()
