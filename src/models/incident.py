"""
Sentinel-K Incident Model
Core incident representation with confidence scoring
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json
import uuid

from .source import Source


class IncidentType(Enum):
    FIRE = "fire"
    FLOOD = "flood"
    TRAFFIC = "traffic"
    EXPLOSION = "explosion"
    SHOOTING = "shooting"
    PROTEST = "protest"
    POWER_OUTAGE = "power_outage"
    HEATWAVE = "heatwave"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    LOW = "LOW"        # 0.0 - 0.39: Monitor, log only
    MEDIUM = "MEDIUM"  # 0.4 - 0.69: Alert human operator
    HIGH = "HIGH"      # 0.7 - 1.0:  Immediate escalation


@dataclass
class Incident:
    """Represents a detected urban incident"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    incident_type: IncidentType = IncidentType.UNKNOWN
    location: Optional[str] = None
    sources: List[Source] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, monitoring, resolved, false_positive

    # Verification disclaimer per Constitution
    VERIFY_DISCLAIMER = """
---
VERIFY FIRST: This is an automated early-warning assessment.
Confirm with official sources before taking action.
Sentinel-K does NOT dispatch emergency services.
For emergencies: Police 15 | Rescue 1122 | Edhi 115
---
"""

    @property
    def source_count(self) -> int:
        """Number of corroborating sources"""
        return len(self.sources)

    @property
    def confidence_score(self) -> float:
        """
        Calculate confidence score using weighted multi-source correlation
        Per Constitution Section VI.2
        """
        if not self.sources:
            return 0.0

        total_weight = sum(source.calculate_weight() for source in self.sources)
        return min(total_weight, 1.0)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Map confidence score to level"""
        score = self.confidence_score
        if score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def should_escalate(self) -> str:
        """
        Determine escalation action per Constitution Protocol S3
        Single-source alerts NEVER escalate
        """
        if self.source_count < 2:
            return "LOG_ONLY"  # Anti-panic: never escalate single source

        level = self.confidence_level
        if level == ConfidenceLevel.HIGH:
            return "AUTO_NOTIFY"
        elif level == ConfidenceLevel.MEDIUM:
            return "HUMAN_REVIEW"
        else:
            return "LOG_ONLY"

    def add_source(self, source: Source):
        """Add a corroborating source"""
        self.sources.append(source)
        self.updated_at = datetime.now()

    def generate_alert(self) -> str:
        """Generate formatted alert message"""
        level = self.confidence_level
        score = self.confidence_score

        # Determine alert tier per Constitution
        if level == ConfidenceLevel.HIGH:
            tier = "GOLD ALERT - HIGH CONFIDENCE"
            marker = "[!!!]"
        elif level == ConfidenceLevel.MEDIUM:
            tier = "SILVER ALERT - MEDIUM CONFIDENCE"
            marker = "[!!]"
        else:
            tier = "BRONZE ALERT - LOW CONFIDENCE"
            marker = "[!]"

        alert = f"""
## {marker} {tier}

**Incident ID**: {self.id}
**Type**: {self.incident_type.value.upper()}
**Location**: {self.location or 'Unknown'}
**Confidence**: {score:.2f} ({level.value})
**Sources**: {self.source_count}
**Detected**: {self.created_at.strftime('%Y-%m-%d %H:%M PKT')}

### Source Correlation
| Source Type | Weight | Age (min) |
|-------------|--------|-----------|
"""
        for source in self.sources:
            alert += f"| {source.type.value} | {source.calculate_weight():.2f} | {source.age_minutes:.1f} |\n"

        alert += f"""
### Escalation Action
**{self.should_escalate()}**

{self.VERIFY_DISCLAIMER}
"""
        return alert

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "id": self.id,
            "incident_type": self.incident_type.value,
            "location": self.location,
            "sources": [s.to_dict() for s in self.sources],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "confidence_score": round(self.confidence_score, 3),
            "confidence_level": self.confidence_level.value,
            "escalation_action": self.should_escalate(),
            "source_count": self.source_count,
        }

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "Incident":
        """Create incident from dictionary"""
        incident = cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            incident_type=IncidentType(data.get("incident_type", "unknown")),
            location=data.get("location"),
            status=data.get("status", "active"),
        )
        incident.created_at = datetime.fromisoformat(data["created_at"])
        incident.updated_at = datetime.fromisoformat(data["updated_at"])
        return incident
