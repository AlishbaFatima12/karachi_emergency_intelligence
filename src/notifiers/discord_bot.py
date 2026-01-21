"""
Sentinel-K Discord Notifier
Sends real-time alerts via Discord webhooks
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


class DiscordNotifier:
    """
    Sends alerts to Discord via Webhooks

    Setup:
    1. Go to Discord channel settings
    2. Integrations → Webhooks → New Webhook
    3. Copy webhook URL
    4. Set DISCORD_WEBHOOK_URL in .env
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")

        if not self.webhook_url:
            logger.warning("Discord not configured. Set DISCORD_WEBHOOK_URL in .env")

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

    def _get_color(self, level: ConfidenceLevel) -> int:
        """Get embed color based on confidence level"""
        colors = {
            ConfidenceLevel.HIGH: 0xFF0000,    # Red
            ConfidenceLevel.MEDIUM: 0xFFAA00,  # Orange
            ConfidenceLevel.LOW: 0x00FF00,     # Green
        }
        return colors.get(level, 0x808080)

    def _get_level_text(self, level: ConfidenceLevel) -> str:
        """Get text for confidence level"""
        texts = {
            ConfidenceLevel.HIGH: "🔴 HIGH",
            ConfidenceLevel.MEDIUM: "🟡 MEDIUM",
            ConfidenceLevel.LOW: "🟢 LOW",
        }
        return texts.get(level, "⚪ UNKNOWN")

    def send_alert(self, incident: Incident) -> bool:
        """Send alert to Discord"""
        if not self.webhook_url:
            logger.warning("Discord not configured, skipping notification")
            return False

        # Only send for MEDIUM or HIGH confidence
        if incident.confidence_level == ConfidenceLevel.LOW:
            logger.debug("Skipping LOW confidence alert for Discord")
            return False

        # COMPLETELY skip "unknown" type alerts - they are always vague/irrelevant
        if incident.incident_type.value == "unknown":
            logger.debug("Skipping UNKNOWN type alert - must be specific emergency type")
            return False

        # Double-check: content must contain actual emergency keywords
        emergency_keywords = [
            "fire", "aag", "blaze", "smoke", "burning",
            "flood", "water", "rain", "sailaab", "baarish",
            "blast", "explosion", "bomb", "dhamaka",
            "shooting", "firing", "goli", "gunfire", "killed",
            "accident", "crash", "collision", "hadsa",
            "protest", "strike", "dharna", "rally",
            "power outage", "blackout", "bijli", "load shedding"
        ]
        if incident.sources:
            content = (incident.sources[0].content or "").lower()
            if not any(kw in content for kw in emergency_keywords):
                logger.debug(f"Skipping alert - no emergency keywords found in: {content[:50]}")
                return False

        emoji = self._get_emoji(incident.incident_type.value)
        color = self._get_color(incident.confidence_level)
        level_text = self._get_level_text(incident.confidence_level)

        # Get actual headline from sources
        headline = "Multiple reports detected"
        if incident.sources:
            # Get first source content as headline
            first_content = incident.sources[0].content if incident.sources[0].content else ""
            if first_content:
                headline = first_content[:200]  # Limit to 200 chars

        # Format location nicely
        location = (incident.location or "Karachi").replace("_", " ").title()
        if location == "Karachi General":
            location = "Karachi (Multiple Areas)"

        # Format type nicely
        type_labels = {
            "fire": "🔥 FIRE ALERT",
            "flood": "🌊 FLOOD WARNING",
            "explosion": "💥 EXPLOSION REPORT",
            "shooting": "🔫 SECURITY INCIDENT",
            "traffic": "🚗 TRAFFIC ALERT",
            "power_outage": "⚡ POWER OUTAGE",
            "protest": "📢 PUBLIC GATHERING",
            "unknown": "📡 DEVELOPING SITUATION"
        }
        type_display = type_labels.get(incident.incident_type.value, "⚠️ ALERT")

        # Cap sources for display (more realistic)
        display_sources = min(incident.source_count, 5)
        confidence_display = min(incident.confidence_score * 100, 95)

        # Build Discord embed
        embed = {
            "title": type_display,
            "description": f"**{headline}**",
            "color": color,
            "fields": [
                {"name": "📍 Location", "value": location, "inline": True},
                {"name": "📊 Confidence", "value": f"{level_text} ({confidence_display:.0f}%)", "inline": True},
                {"name": "📰 Sources", "value": f"{display_sources} corroborating", "inline": True},
                {"name": "🕐 Time", "value": incident.created_at.strftime('%H:%M PKT'), "inline": True},
            ],
            "footer": {
                "text": "⚠️ VERIFY with official sources | Police 15 | Rescue 1122 | Edhi 115"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "username": "Sentinel-K",
            "avatar_url": "https://i.imgur.com/4M34hi2.png",
            "embeds": [embed]
        }

        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info(f"Discord alert sent for incident {incident.id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False

    def send_heartbeat(self, active_alerts: int = 0, weather_temp: float = None) -> bool:
        """Send 5-minute heartbeat status to Discord"""
        if not self.webhook_url:
            logger.warning("Discord not configured, skipping heartbeat")
            return False

        now = datetime.now()
        time_str = now.strftime('%H:%M PKT')

        # Status
        if active_alerts > 0:
            status = f"⚠️ {active_alerts} active alert(s)"
            color = 0xFFAA00  # Orange
        else:
            status = "✅ All clear"
            color = 0x00FF00  # Green

        # Weather
        weather_text = f"🌡️ {weather_temp:.1f}°C" if weather_temp else "N/A"

        embed = {
            "title": "🛡️ SENTINEL-K STATUS",
            "color": color,
            "fields": [
                {"name": "Status", "value": status, "inline": True},
                {"name": "Weather", "value": weather_text, "inline": True},
                {"name": "Time", "value": time_str, "inline": True},
            ],
            "footer": {"text": "📡 RSS | 🌤️ Weather | 📱 Social - Monitoring Karachi"},
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "username": "Sentinel-K",
            "avatar_url": "https://i.imgur.com/4M34hi2.png",
            "embeds": [embed]
        }

        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info("Discord heartbeat sent")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Discord heartbeat: {e}")
            return False

    def send_daily_summary(self, incidents: list, weather: dict) -> bool:
        """Send daily summary to Discord"""
        if not self.webhook_url:
            return False

        high_count = len([i for i in incidents if i.confidence_level == ConfidenceLevel.HIGH])
        medium_count = len([i for i in incidents if i.confidence_level == ConfidenceLevel.MEDIUM])
        temp = weather.get('temperature_c', 'N/A')

        embed = {
            "title": "📊 SENTINEL-K DAILY SUMMARY",
            "color": 0x0099FF,
            "fields": [
                {"name": "🔴 High Alerts", "value": str(high_count), "inline": True},
                {"name": "🟡 Medium Alerts", "value": str(medium_count), "inline": True},
                {"name": "🌡️ Temperature", "value": f"{temp}°C", "inline": True},
            ],
            "footer": {"text": "Stay safe, Karachi!"},
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "username": "Sentinel-K",
            "embeds": [embed]
        }

        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=30)
            return response.status_code == 204
        except:
            return False


# Test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    notifier = DiscordNotifier()
    print(f"Webhook configured: {bool(notifier.webhook_url)}")

    # Test heartbeat
    result = notifier.send_heartbeat(active_alerts=0, weather_temp=20.4)
    print(f"Heartbeat result: {'SUCCESS' if result else 'FAILED'}")
