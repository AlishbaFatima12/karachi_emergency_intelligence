"""
Sentinel-K Source Model
Data source representation for multi-source correlation
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib


class SourceType(Enum):
    NEWS = "news"
    SOCIAL = "social"
    WEATHER = "weather"
    TRAFFIC = "traffic"
    GOVERNMENT = "government"


@dataclass
class Source:
    """Represents a single data source signal"""
    type: SourceType
    content: str
    timestamp: datetime
    location: Optional[str] = None
    url: Optional[str] = None
    verified: bool = False
    geo_tagged: bool = False
    raw_username: Optional[str] = None  # Will be hashed before storage

    # Base weights per Constitution
    BASE_WEIGHTS = {
        SourceType.NEWS: 0.35,
        SourceType.SOCIAL: 0.25,
        SourceType.WEATHER: 0.30,
        SourceType.TRAFFIC: 0.20,
        SourceType.GOVERNMENT: 0.40,
    }

    @property
    def age_minutes(self) -> float:
        """Calculate age of source in minutes"""
        delta = datetime.now() - self.timestamp
        return delta.total_seconds() / 60

    @property
    def base_weight(self) -> float:
        """Get base weight for this source type"""
        return self.BASE_WEIGHTS.get(self.type, 0.2)

    @property
    def anonymized_username(self) -> Optional[str]:
        """Return SHA-256 hash of username for privacy"""
        if self.raw_username:
            return hashlib.sha256(self.raw_username.encode()).hexdigest()[:16]
        return None

    def get_recency_factor(self) -> float:
        """Calculate recency factor based on age"""
        age = self.age_minutes
        if age < 5:
            return 1.0
        elif age < 15:
            return 0.9
        elif age < 30:
            return 0.7
        elif age < 60:
            return 0.5
        else:
            return 0.3

    def calculate_weight(self) -> float:
        """Calculate final weight including modifiers"""
        weight = self.base_weight

        # Apply reliability modifiers per Constitution
        if self.verified:
            weight += 0.1
        if self.geo_tagged and self.type == SourceType.SOCIAL:
            weight += 0.1

        # Apply recency factor
        weight *= self.get_recency_factor()

        return weight

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location,
            "url": self.url,
            "verified": self.verified,
            "geo_tagged": self.geo_tagged,
            "username_hash": self.anonymized_username,
            "age_minutes": round(self.age_minutes, 2),
            "weight": round(self.calculate_weight(), 3),
        }
