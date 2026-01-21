"""
Sentinel-K Confidence Scorer
Weighted confidence calculation per Constitution Section VI.2
"""
from typing import List
import logging

import sys
sys.path.append('..')
from models.source import Source, SourceType
from models.incident import ConfidenceLevel

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Calculates confidence scores using weighted multi-source correlation
    Implements the algorithm defined in Constitution Section VI.2
    """

    # Base weights per source type
    BASE_WEIGHTS = {
        SourceType.NEWS: 0.35,
        SourceType.SOCIAL: 0.25,
        SourceType.WEATHER: 0.30,
        SourceType.TRAFFIC: 0.20,
        SourceType.GOVERNMENT: 0.40,
    }

    # Recency factors (data age in minutes)
    RECENCY_THRESHOLDS = [
        (5, 1.0),    # < 5 minutes: full weight
        (15, 0.9),   # 5-15 minutes
        (30, 0.7),   # 15-30 minutes
        (60, 0.5),   # 30-60 minutes
        (float('inf'), 0.3),  # > 60 minutes
    ]

    @classmethod
    def get_recency_factor(cls, age_minutes: float) -> float:
        """Get recency factor based on data age"""
        for threshold, factor in cls.RECENCY_THRESHOLDS:
            if age_minutes < threshold:
                return factor
        return 0.3

    @classmethod
    def calculate_source_weight(cls, source: Source) -> float:
        """
        Calculate weight for a single source
        Includes base weight, modifiers, and recency factor
        """
        # Base weight for source type
        weight = cls.BASE_WEIGHTS.get(source.type, 0.2)

        # Reliability modifiers per Constitution
        if source.verified:
            weight += 0.1
        if source.geo_tagged and source.type == SourceType.SOCIAL:
            weight += 0.1

        # Apply recency factor
        recency = cls.get_recency_factor(source.age_minutes)
        weight *= recency

        return weight

    @classmethod
    def calculate_confidence(cls, sources: List[Source]) -> float:
        """
        Calculate overall confidence score from multiple sources
        Returns value between 0.0 and 1.0
        """
        if not sources:
            return 0.0

        # Sum weights from all sources
        total_weight = sum(
            cls.calculate_source_weight(source)
            for source in sources
        )

        # Cap at 1.0
        confidence = min(total_weight, 1.0)

        logger.debug(f"Confidence calculated: {confidence:.3f} from {len(sources)} sources")
        return confidence

    @classmethod
    def get_confidence_level(cls, score: float) -> ConfidenceLevel:
        """Map confidence score to level"""
        if score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    @classmethod
    def should_escalate(cls, sources: List[Source]) -> str:
        """
        Determine escalation action per Constitution Protocol S3
        CRITICAL: Single-source alerts NEVER escalate (anti-panic)
        """
        # Anti-panic logic: minimum 2 sources required
        if len(sources) < 2:
            return "LOG_ONLY"

        score = cls.calculate_confidence(sources)
        level = cls.get_confidence_level(score)

        if level == ConfidenceLevel.HIGH:
            return "AUTO_NOTIFY"
        elif level == ConfidenceLevel.MEDIUM:
            return "HUMAN_REVIEW"
        else:
            return "LOG_ONLY"

    @classmethod
    def generate_reasoning_chain(cls, sources: List[Source]) -> List[str]:
        """
        Generate Sequential Thinking reasoning chain
        For use with MCP sequential-thinking server
        """
        reasoning = []
        score = cls.calculate_confidence(sources)
        level = cls.get_confidence_level(score)

        reasoning.append(f"Analyzing incident with {len(sources)} source(s)...")

        for i, source in enumerate(sources, 1):
            weight = cls.calculate_source_weight(source)
            reasoning.append(
                f"Source {i}: {source.type.value} | "
                f"Weight: {weight:.2f} | "
                f"Age: {source.age_minutes:.1f}min | "
                f"Verified: {source.verified}"
            )

        reasoning.append(f"Total confidence score: {score:.3f}")
        reasoning.append(f"Confidence level: {level.value}")

        escalation = cls.should_escalate(sources)
        if escalation == "LOG_ONLY":
            if len(sources) < 2:
                reasoning.append("DECISION: Single source detected - logging only (anti-panic protocol)")
            else:
                reasoning.append("DECISION: Low confidence - logging only, continue monitoring")
        elif escalation == "HUMAN_REVIEW":
            reasoning.append("DECISION: Medium confidence - flagging for human review")
        else:
            reasoning.append("DECISION: High confidence - triggering immediate notification")

        return reasoning


# Test the scorer
if __name__ == "__main__":
    from datetime import datetime, timedelta

    # Create test sources
    test_sources = [
        Source(
            type=SourceType.NEWS,
            content="Fire reported in Saddar market",
            timestamp=datetime.now() - timedelta(minutes=3),
            location="saddar",
            verified=True,
        ),
        Source(
            type=SourceType.SOCIAL,
            content="Aag lagi hai Saddar mein",
            timestamp=datetime.now() - timedelta(minutes=5),
            location="saddar",
            verified=False,
            geo_tagged=True,
        ),
    ]

    scorer = ConfidenceScorer()

    print("=== Confidence Scoring Test ===")
    print(f"Sources: {len(test_sources)}")

    for source in test_sources:
        weight = scorer.calculate_source_weight(source)
        print(f"  - {source.type.value}: weight={weight:.3f}")

    confidence = scorer.calculate_confidence(test_sources)
    level = scorer.get_confidence_level(confidence)
    action = scorer.should_escalate(test_sources)

    print(f"\nTotal Confidence: {confidence:.3f}")
    print(f"Level: {level.value}")
    print(f"Action: {action}")

    print("\n=== Reasoning Chain ===")
    for step in scorer.generate_reasoning_chain(test_sources):
        print(f"  > {step}")
