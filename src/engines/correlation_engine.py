"""
Sentinel-K Correlation Engine
Multi-source correlation and incident detection
Per Constitution Section VI - The Brain
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import logging
import json
import os

import sys
sys.path.append('..')
from models.source import Source, SourceType
from models.incident import Incident, IncidentType, ConfidenceLevel
from engines.confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """
    The "Brain" of Sentinel-K
    Correlates signals from multiple sources to detect and score incidents
    Implements the Triangulation Principle from Constitution
    """

    # Time window for correlation (signals within this window are grouped)
    CORRELATION_WINDOW_MINUTES = 30

    # Cooldown period for false positives (per Constitution Protocol S4)
    COOLDOWN_MINUTES = 30

    # Incident type detection patterns
    INCIDENT_PATTERNS = {
        IncidentType.FIRE: [
            "fire", "aag", "blaze", "dhuaan", "smoke", "burning", "jalaya", "flames"
        ],
        IncidentType.FLOOD: [
            "flood", "flooding", "sailaab", "paani", "water logging", "rain", "baarish"
        ],
        IncidentType.EXPLOSION: [
            "blast", "dhamaaka", "explosion", "bomb", "explosive"
        ],
        IncidentType.SHOOTING: [
            "shooting", "goli", "firing", "gunfire", "target killing", "killed"
        ],
        IncidentType.TRAFFIC: [
            "accident", "hadsa", "collision", "crash", "jam", "band hai", "road block"
        ],
        IncidentType.POWER_OUTAGE: [
            "power outage", "bijli gayi", "load shedding", "blackout"
        ],
        IncidentType.HEATWAVE: [
            "heatwave", "heat stroke", "extreme heat", "temperature"
        ],
        IncidentType.PROTEST: [
            "protest", "dharna", "strike", "rally", "demonstration"
        ],
    }

    # IRRELEVANT content - filter out entertainment/sports/celebrity news
    EXCLUDED_KEYWORDS = [
        # Bollywood/Movies
        "box office", "collection", "crore", "movie", "film", "bollywood", "lollywood",
        "actor", "actress", "celebrity", "star cast", "trailer", "teaser", "ott",
        "netflix", "amazon prime", "hotstar", "zee5", "cinema", "premiere",
        "ranveer", "salman", "shahrukh", "aamir", "deepika", "alia", "ranbir",
        "hrithik", "katrina", "priyanka", "kareena", "anushka", "fawad", "mahira",
        "dhurandhar", "spy thriller", "globally", "worldwide",
        # Sports
        "cricket", "match", "psl", "ipl", "world cup", "batting", "bowling",
        "football", "hockey", "tennis", "olympics", "tournament", "league",
        "babar azam", "virat kohli", "shaheen", "rizwan",
        # Entertainment/Lifestyle
        "wedding", "shaadi", "fashion", "red carpet", "award", "concert", "song",
        "album", "music video", "tiktok", "influencer", "viral video",
        "birthday", "anniversary", "baby shower", "pregnancy", "divorce",
        # Business/Stock
        "stock market", "shares", "profit", "revenue", "quarterly", "earnings",
        "ipo", "investment", "startup", "funding",
        # Politics/Military (not local emergencies)
        "loc ", "line of control", "air force", "deep-strike", "targets inside",
        "indian air force", "pakistan air force", "military", "army chief",
        # Reference/Educational (not emergencies)
        "wikipedia", "wiki", "- wikipedia", "encyclopedia", "history of",
        "population", "geography", "district", "division", "administrative",
        # General irrelevant
        "recipe", "food review", "restaurant review", "hotel review", "travel",
        "property", "real estate", "apartment", "flat for sale", "rent",
        "job", "vacancy", "hiring", "salary", "herzindagi",
    ]

    # Required emergency keywords - content MUST contain at least one
    REQUIRED_EMERGENCY_KEYWORDS = [
        "fire", "aag", "blaze", "smoke", "burning", "flames",
        "flood", "rain", "water", "sailaab", "baarish",
        "blast", "explosion", "bomb", "dhamaka",
        "shooting", "firing", "goli", "gunfire", "killed", "murder",
        "accident", "crash", "collision", "hadsa", "injured",
        "protest", "strike", "dharna", "rally", "road block",
        "power outage", "blackout", "bijli", "load shedding",
        "robbery", "theft", "dacoity", "snatching",
        "rescue", "emergency", "ambulance",
    ]

    def __init__(self, vault_path: str = "Sentinel_Vault"):
        self.vault_path = vault_path
        self.active_incidents: Dict[str, Incident] = {}
        self.cooldowns: Dict[Tuple[str, str], datetime] = {}  # (location, type) -> cooldown_end
        self.scorer = ConfidenceScorer()

    def _is_irrelevant_content(self, content: str) -> bool:
        """Check if content is irrelevant (entertainment, sports, etc.)"""
        content_lower = content.lower()

        # Check for excluded keywords
        for keyword in self.EXCLUDED_KEYWORDS:
            if keyword in content_lower:
                logger.debug(f"Filtered irrelevant: {keyword} in {content[:40]}...")
                return True

        # Must contain at least one emergency keyword
        has_emergency = any(kw in content_lower for kw in self.REQUIRED_EMERGENCY_KEYWORDS)
        if not has_emergency:
            logger.debug(f"Filtered (no emergency keywords): {content[:40]}...")
            return True

        return False

    def clear_all_incidents(self):
        """Clear all active incidents - use when filters are updated"""
        self.active_incidents.clear()
        logger.info("Cleared all active incidents")

    def _detect_incident_type(self, content: str) -> IncidentType:
        """Detect incident type from content using keyword patterns"""
        content_lower = content.lower()
        for incident_type, patterns in self.INCIDENT_PATTERNS.items():
            if any(pattern in content_lower for pattern in patterns):
                return incident_type
        return IncidentType.UNKNOWN

    def _generate_incident_key(self, location: str, incident_type: IncidentType) -> str:
        """Generate unique key for incident (location + type)"""
        return f"{location}_{incident_type.value}"

    def _is_in_cooldown(self, location: str, incident_type: IncidentType) -> bool:
        """Check if location+type combo is in cooldown period"""
        key = (location, incident_type.value)
        if key in self.cooldowns:
            if datetime.now() < self.cooldowns[key]:
                return True
            else:
                del self.cooldowns[key]
        return False

    def _set_cooldown(self, location: str, incident_type: IncidentType):
        """Set cooldown for location+type combo"""
        key = (location, incident_type.value)
        self.cooldowns[key] = datetime.now() + timedelta(minutes=self.COOLDOWN_MINUTES)
        logger.info(f"Cooldown set for {location}/{incident_type.value} until {self.cooldowns[key]}")

    def _is_within_time_window(self, source: Source) -> bool:
        """Check if source is within correlation time window"""
        return source.age_minutes <= self.CORRELATION_WINDOW_MINUTES

    def _group_sources_by_location_type(
        self, sources: List[Source]
    ) -> Dict[str, List[Source]]:
        """Group sources by location and incident type"""
        grouped = defaultdict(list)

        for source in sources:
            if not self._is_within_time_window(source):
                continue

            # FILTER: Skip irrelevant content (movies, sports, entertainment)
            if self._is_irrelevant_content(source.content or ""):
                continue

            location = source.location or "unknown"
            incident_type = self._detect_incident_type(source.content)

            # FILTER: Skip UNKNOWN type - must be a specific emergency
            if incident_type == IncidentType.UNKNOWN:
                logger.debug(f"Skipping UNKNOWN type: {source.content[:50]}...")
                continue

            # Skip if in cooldown
            if self._is_in_cooldown(location, incident_type):
                logger.debug(f"Skipping source (cooldown): {location}/{incident_type.value}")
                continue

            key = self._generate_incident_key(location, incident_type)
            grouped[key].append(source)

        return grouped

    def correlate(self, sources: List[Source]) -> List[Incident]:
        """
        Main correlation function
        Groups sources, detects incidents, calculates confidence
        Returns list of detected incidents
        """
        if not sources:
            return []

        logger.info(f"Correlating {len(sources)} sources...")

        # Group by location and incident type
        grouped = self._group_sources_by_location_type(sources)

        incidents = []
        for key, source_group in grouped.items():
            location, incident_type_str = key.rsplit("_", 1)
            incident_type = IncidentType(incident_type_str)

            # Check if we already have an active incident for this key
            if key in self.active_incidents:
                incident = self.active_incidents[key]
                # Add new sources to existing incident
                for source in source_group:
                    if source not in incident.sources:
                        incident.add_source(source)
            else:
                # Create new incident
                incident = Incident(
                    incident_type=incident_type,
                    location=location,
                    sources=source_group,
                )
                self.active_incidents[key] = incident

            incidents.append(incident)

            # Log correlation result
            confidence = incident.confidence_score
            logger.info(
                f"[CORRELATION] {incident_type.value} at {location}: "
                f"{len(incident.sources)} sources, confidence={confidence:.2f}"
            )

        return incidents

    def process_and_alert(self, sources: List[Source]) -> List[Incident]:
        """
        Process sources and determine which incidents need alerting
        Implements Constitution Protocol S3 (Anti-Panic Logic)
        """
        incidents = self.correlate(sources)
        alertable = []

        for incident in incidents:
            action = incident.should_escalate()

            if action == "LOG_ONLY":
                self._log_incident(incident)
            elif action == "HUMAN_REVIEW":
                self._log_incident(incident)
                alertable.append(incident)
                logger.warning(f"[ALERT] MEDIUM confidence incident needs review: {incident.id}")
            elif action == "AUTO_NOTIFY":
                self._log_incident(incident)
                alertable.append(incident)
                logger.warning(f"[ALERT] HIGH confidence incident - AUTO NOTIFY: {incident.id}")

        return alertable

    def _log_incident(self, incident: Incident):
        """Log incident to Sentinel_Vault"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        incidents_dir = os.path.join(self.vault_path, "incidents", date_str)
        os.makedirs(incidents_dir, exist_ok=True)

        filename = f"INC-{incident.id}-{incident.incident_type.value}-{incident.location}.json"
        filepath = os.path.join(incidents_dir, filename)

        with open(filepath, "w") as f:
            json.dump(incident.to_dict(), f, indent=2)

        logger.debug(f"Incident logged: {filepath}")

    def mark_false_positive(self, incident_id: str):
        """Mark incident as false positive and set cooldown"""
        for key, incident in self.active_incidents.items():
            if incident.id == incident_id:
                incident.status = "false_positive"
                self._set_cooldown(incident.location, incident.incident_type)
                self._log_incident(incident)
                del self.active_incidents[key]
                logger.info(f"Incident {incident_id} marked as false positive")
                return True
        return False

    def get_active_incidents(self) -> List[Incident]:
        """Get all currently active incidents"""
        return list(self.active_incidents.values())

    def generate_dashboard_data(self) -> dict:
        """Generate data for Obsidian dashboard"""
        all_incidents = self.get_active_incidents()

        # FILTER: Only show real emergency incidents (no UNKNOWN type)
        incidents = [
            i for i in all_incidents
            if i.incident_type != IncidentType.UNKNOWN
            and not self._is_irrelevant_content(
                i.sources[0].content if i.sources and i.sources[0].content else ""
            )
        ]

        return {
            "active_alerts": len([i for i in incidents if i.confidence_level == ConfidenceLevel.HIGH]),
            "monitoring": len([i for i in incidents if i.confidence_level == ConfidenceLevel.MEDIUM]),
            "logged": len([i for i in incidents if i.confidence_level == ConfidenceLevel.LOW]),
            "incidents": [
                {
                    "id": i.id,
                    "type": i.incident_type.value,
                    "location": i.location,
                    "confidence": min(round(i.confidence_score, 2), 0.95),  # Cap at 95%
                    "level": i.confidence_level.value,
                    "sources": min(i.source_count, 5),  # Cap at 5 sources
                    "time": i.created_at.strftime("%H:%M"),
                    "headline": i.sources[0].content[:100] if i.sources and i.sources[0].content else "Multiple reports detected",
                }
                for i in sorted(incidents, key=lambda x: x.confidence_score, reverse=True)
            ],
            "updated": datetime.now().isoformat(),
        }


# Test the engine
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create test sources simulating a fire in Saddar
    test_sources = [
        Source(
            type=SourceType.NEWS,
            content="Fire breaks out in Saddar commercial area",
            timestamp=datetime.now() - timedelta(minutes=5),
            location="saddar",
            verified=True,
        ),
        Source(
            type=SourceType.SOCIAL,
            content="Saddar mein aag lagi hai, dhuaan uth raha hai",
            timestamp=datetime.now() - timedelta(minutes=3),
            location="saddar",
            verified=False,
        ),
        Source(
            type=SourceType.SOCIAL,
            content="Bolton market fire, traffic jam on MA Jinnah Road",
            timestamp=datetime.now() - timedelta(minutes=7),
            location="saddar",
            verified=False,
        ),
    ]

    engine = CorrelationEngine()
    alertable = engine.process_and_alert(test_sources)

    print("\n=== Correlation Engine Test ===")
    print(f"Alertable incidents: {len(alertable)}")

    for incident in alertable:
        print(f"\n{incident.generate_alert()}")
