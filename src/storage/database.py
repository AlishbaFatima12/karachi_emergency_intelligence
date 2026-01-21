"""
Sentinel-K Database
SQLite storage for historical incident tracking and analysis
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
import logging

import sys
sys.path.append('..')
from models.incident import Incident, IncidentType, ConfidenceLevel

logger = logging.getLogger(__name__)


class IncidentDatabase:
    """
    SQLite database for persistent incident storage

    Features:
    - Store all incidents with full source data
    - Query historical patterns
    - Generate analytics and reports
    - Track false positive rates
    """

    def __init__(self, db_path: str = "Sentinel_Vault/sentinel_k.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                incident_type TEXT NOT NULL,
                location TEXT,
                confidence_score REAL,
                confidence_level TEXT,
                source_count INTEGER,
                sources_json TEXT,
                status TEXT DEFAULT 'active',
                escalation_action TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                resolved_at TIMESTAMP,
                notes TEXT
            )
        """)

        # Sources table (for detailed analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT,
                source_type TEXT,
                content TEXT,
                location TEXT,
                url TEXT,
                verified BOOLEAN,
                weight REAL,
                timestamp TIMESTAMP,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            )
        """)

        # Daily summaries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                date DATE PRIMARY KEY,
                total_incidents INTEGER,
                high_confidence INTEGER,
                medium_confidence INTEGER,
                low_confidence INTEGER,
                false_positives INTEGER,
                avg_confidence REAL,
                top_location TEXT,
                top_incident_type TEXT,
                weather_json TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type)")

        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")

    def save_incident(self, incident: Incident):
        """Save incident to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert incident
            cursor.execute("""
                INSERT OR REPLACE INTO incidents
                (id, incident_type, location, confidence_score, confidence_level,
                 source_count, sources_json, status, escalation_action, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident.id,
                incident.incident_type.value,
                incident.location,
                incident.confidence_score,
                incident.confidence_level.value,
                incident.source_count,
                json.dumps([s.to_dict() for s in incident.sources]),
                incident.status,
                incident.should_escalate(),
                incident.created_at.isoformat(),
                incident.updated_at.isoformat(),
            ))

            # Insert sources
            for source in incident.sources:
                cursor.execute("""
                    INSERT INTO sources
                    (incident_id, source_type, content, location, url, verified, weight, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident.id,
                    source.type.value,
                    source.content,
                    source.location,
                    source.url,
                    source.verified,
                    source.calculate_weight(),
                    source.timestamp.isoformat(),
                ))

            conn.commit()
            logger.debug(f"Incident {incident.id} saved to database")

        except Exception as e:
            logger.error(f"Error saving incident: {e}")
            conn.rollback()
        finally:
            conn.close()

    def mark_false_positive(self, incident_id: str, notes: str = ""):
        """Mark incident as false positive"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE incidents
            SET status = 'false_positive', notes = ?, resolved_at = ?
            WHERE id = ?
        """, (notes, datetime.now().isoformat(), incident_id))

        conn.commit()
        conn.close()

    def get_incidents_by_date(self, date: datetime) -> List[Dict]:
        """Get all incidents for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start = date.replace(hour=0, minute=0, second=0)
        end = date.replace(hour=23, minute=59, second=59)

        cursor.execute("""
            SELECT * FROM incidents
            WHERE created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
        """, (start.isoformat(), end.isoformat()))

        columns = [desc[0] for desc in cursor.description]
        incidents = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return incidents

    def get_location_stats(self, days: int = 30) -> Dict:
        """Get incident statistics by location"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT location, COUNT(*) as count,
                   AVG(confidence_score) as avg_confidence
            FROM incidents
            WHERE created_at > ? AND location IS NOT NULL
            GROUP BY location
            ORDER BY count DESC
        """, (since,))

        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                "count": row[1],
                "avg_confidence": round(row[2], 3) if row[2] else 0
            }

        conn.close()
        return stats

    def get_incident_type_stats(self, days: int = 30) -> Dict:
        """Get incident statistics by type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT incident_type, COUNT(*) as count,
                   AVG(confidence_score) as avg_confidence
            FROM incidents
            WHERE created_at > ?
            GROUP BY incident_type
            ORDER BY count DESC
        """, (since,))

        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                "count": row[1],
                "avg_confidence": round(row[2], 3) if row[2] else 0
            }

        conn.close()
        return stats

    def get_hourly_distribution(self, days: int = 7) -> Dict:
        """Get incident distribution by hour of day"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT strftime('%H', created_at) as hour, COUNT(*) as count
            FROM incidents
            WHERE created_at > ?
            GROUP BY hour
            ORDER BY hour
        """, (since,))

        distribution = {str(i).zfill(2): 0 for i in range(24)}
        for row in cursor.fetchall():
            distribution[row[0]] = row[1]

        conn.close()
        return distribution

    def get_accuracy_stats(self, days: int = 30) -> Dict:
        """Calculate accuracy statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        # Total incidents
        cursor.execute("""
            SELECT COUNT(*) FROM incidents WHERE created_at > ?
        """, (since,))
        total = cursor.fetchone()[0]

        # False positives
        cursor.execute("""
            SELECT COUNT(*) FROM incidents
            WHERE created_at > ? AND status = 'false_positive'
        """, (since,))
        false_positives = cursor.fetchone()[0]

        # By confidence level
        cursor.execute("""
            SELECT confidence_level, COUNT(*) FROM incidents
            WHERE created_at > ?
            GROUP BY confidence_level
        """, (since,))
        by_level = dict(cursor.fetchall())

        conn.close()

        return {
            "total_incidents": total,
            "false_positives": false_positives,
            "false_positive_rate": round(false_positives / total * 100, 2) if total > 0 else 0,
            "by_confidence_level": by_level,
            "period_days": days,
        }

    def generate_daily_summary(self, date: datetime = None) -> Dict:
        """Generate summary for a specific day"""
        date = date or datetime.now()
        incidents = self.get_incidents_by_date(date)

        summary = {
            "date": date.strftime("%Y-%m-%d"),
            "total_incidents": len(incidents),
            "high_confidence": len([i for i in incidents if i["confidence_level"] == "HIGH"]),
            "medium_confidence": len([i for i in incidents if i["confidence_level"] == "MEDIUM"]),
            "low_confidence": len([i for i in incidents if i["confidence_level"] == "LOW"]),
            "false_positives": len([i for i in incidents if i["status"] == "false_positive"]),
            "avg_confidence": round(
                sum(i["confidence_score"] or 0 for i in incidents) / len(incidents), 3
            ) if incidents else 0,
        }

        # Top location
        locations = [i["location"] for i in incidents if i["location"]]
        if locations:
            summary["top_location"] = max(set(locations), key=locations.count)
        else:
            summary["top_location"] = None

        # Top incident type
        types = [i["incident_type"] for i in incidents]
        if types:
            summary["top_incident_type"] = max(set(types), key=types.count)
        else:
            summary["top_incident_type"] = None

        return summary


# Test
if __name__ == "__main__":
    db = IncidentDatabase("test_sentinel.db")

    # Create test incident
    from models.source import Source, SourceType

    test_incident = Incident(
        incident_type=IncidentType.FIRE,
        location="saddar",
    )
    test_incident.sources = [
        Source(type=SourceType.NEWS, content="Fire in Saddar", timestamp=datetime.now(), verified=True),
        Source(type=SourceType.SOCIAL, content="Aag lagi", timestamp=datetime.now(), verified=False),
    ]

    db.save_incident(test_incident)

    print("Location stats:", db.get_location_stats())
    print("Type stats:", db.get_incident_type_stats())
    print("Accuracy:", db.get_accuracy_stats())
