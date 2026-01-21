"""
Sentinel-K Telegram Notifier
Sends real-time alerts to Telegram channel/group
"""
import httpx
import os
import logging
from typing import Optional
from datetime import datetime

import sys
sys.path.append('..')
from models.incident import Incident, ConfidenceLevel

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Sends alerts to Telegram via Bot API

    Setup:
    1. Create bot with @BotFather on Telegram
    2. Get bot token
    3. Create channel/group and add bot as admin
    4. Get chat_id (use @userinfobot or API)
    """

    API_BASE = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

    def _get_emoji(self, incident_type: str) -> str:
        """Get emoji for incident type"""
        emojis = {
            "fire": "🔥",
            "flood": "🌊",
            "explosion": "💥",
            "shooting": "🔫",
            "traffic": "🚗",
            "power_outage": "⚡",
            "heatwave": "🌡️",
            "protest": "📢",
            "unknown": "⚠️",
        }
        return emojis.get(incident_type, "⚠️")

    def _get_level_indicator(self, level: ConfidenceLevel) -> str:
        """Get visual indicator for confidence level"""
        indicators = {
            ConfidenceLevel.HIGH: "🔴 HIGH",
            ConfidenceLevel.MEDIUM: "🟡 MEDIUM",
            ConfidenceLevel.LOW: "🟢 LOW",
        }
        return indicators.get(level, "⚪ UNKNOWN")

    def format_alert(self, incident: Incident) -> str:
        """Format incident as Telegram message"""
        emoji = self._get_emoji(incident.incident_type.value)
        level = self._get_level_indicator(incident.confidence_level)

        message = f"""
{emoji} *SENTINEL-K ALERT* {emoji}

*Type:* {incident.incident_type.value.upper()}
*Location:* {incident.location or 'Unknown'}
*Confidence:* {level} ({incident.confidence_score:.0%})
*Sources:* {incident.source_count} corroborating

*Time:* {incident.created_at.strftime('%H:%M PKT')}

━━━━━━━━━━━━━━━━━━━━━━
⚠️ *VERIFY FIRST*
This is automated early warning.
Confirm before taking action.

Emergency: Police 15 | Rescue 1122 | Edhi 115
━━━━━━━━━━━━━━━━━━━━━━
"""
        return message

    def send_alert(self, incident: Incident) -> bool:
        """Send alert to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured, skipping notification")
            return False

        # Only send for MEDIUM or HIGH confidence
        if incident.confidence_level == ConfidenceLevel.LOW:
            logger.debug("Skipping LOW confidence alert for Telegram")
            return False

        message = self.format_alert(incident)

        try:
            url = self.API_BASE.format(token=self.bot_token)
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }

            response = httpx.post(url, json=payload, timeout=30)
            response.raise_for_status()

            logger.info(f"Telegram alert sent for incident {incident.id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def send_heartbeat(self, active_alerts: int = 0, weather_temp: float = None) -> bool:
        """Send 5-minute heartbeat status to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured, skipping heartbeat")
            return False

        now = datetime.now()
        time_str = now.strftime('%H:%M PKT')

        # Build status line
        if active_alerts > 0:
            status = f"⚠️ {active_alerts} active alert(s)"
        else:
            status = "✅ All clear"

        # Weather info
        weather_line = ""
        if weather_temp is not None:
            weather_line = f"\n🌡️ {weather_temp:.1f}°C"

        message = f"""
🛡️ *SENTINEL-K STATUS*
{time_str}

{status} - Monitoring Karachi{weather_line}

📡 RSS | 🌤️ Weather | 📱 Social
━━━━━━━━━━━━━━━━━━━━━━
"""

        try:
            url = self.API_BASE.format(token=self.bot_token)
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_notification": True,  # Silent heartbeat
            }
            response = httpx.post(url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info("Telegram heartbeat sent")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False

    def send_daily_summary(self, incidents: list, weather: dict) -> bool:
        """Send daily summary to Telegram"""
        if not self.bot_token or not self.chat_id:
            return False

        high_count = len([i for i in incidents if i.confidence_level == ConfidenceLevel.HIGH])
        medium_count = len([i for i in incidents if i.confidence_level == ConfidenceLevel.MEDIUM])

        temp = weather.get('temperature_c', 'N/A')

        message = f"""
📊 *SENTINEL-K DAILY SUMMARY*
{datetime.now().strftime('%Y-%m-%d')}

*Incidents Today:*
🔴 High Confidence: {high_count}
🟡 Medium Confidence: {medium_count}

*Current Conditions:*
🌡️ Temperature: {temp}°C

━━━━━━━━━━━━━━━━━━━━━━
Stay safe, Karachi!
"""

        try:
            url = self.API_BASE.format(token=self.bot_token)
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }
            response = httpx.post(url, json=payload, timeout=30)
            return response.status_code == 200
        except:
            return False


# Test
if __name__ == "__main__":
    from models.incident import Incident, IncidentType
    from models.source import Source, SourceType

    # Create test incident
    test_incident = Incident(
        incident_type=IncidentType.FIRE,
        location="saddar",
    )
    test_incident.sources = [
        Source(type=SourceType.NEWS, content="Fire in Saddar", timestamp=datetime.now(), verified=True),
        Source(type=SourceType.SOCIAL, content="Aag lagi hai", timestamp=datetime.now(), verified=False),
    ]

    notifier = TelegramNotifier()
    print("Formatted message:")
    print(notifier.format_alert(test_incident))
