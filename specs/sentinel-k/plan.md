# Implementation Plan: Sentinel-K

**Branch**: `main` | **Date**: 2026-01-21 | **Spec**: [specs/sentinel-k/spec.md](./spec.md)

---

## Summary

Build a multi-source urban intelligence system for Karachi that correlates data from RSS feeds, social media (via Brave Search), weather APIs, and traffic data to generate confidence-scored early warning alerts.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: feedparser, httpx, pydantic, schedule, rich (CLI output)
**Storage**: JSON files in Sentinel_Vault directory
**Testing**: pytest with mock data
**Target Platform**: Windows/Linux local machine + Claude Desktop MCP
**Performance Goals**: Process data every 5 minutes, alert within 2 minutes of correlation
**Constraints**: No external database, offline-capable for core functions

---

## Project Structure

### Source Code (Repository Root)

```
sentinel_k/
├── src/
│   ├── watchers/
│   │   ├── __init__.py
│   │   ├── rss_watcher.py       # RSS feed polling
│   │   ├── weather_watcher.py   # OpenWeatherMap integration
│   │   └── social_watcher.py    # Brave Search social monitoring
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── correlation_engine.py # Multi-source correlation
│   │   ├── confidence_scorer.py  # Weighted confidence calculation
│   │   └── location_matcher.py   # Karachi location extraction
│   ├── models/
│   │   ├── __init__.py
│   │   ├── incident.py          # Incident data model
│   │   └── source.py            # Source data model
│   └── main.py                  # Orchestrator entry point
├── Sentinel_Vault/
│   ├── incidents/               # Daily incident JSON files
│   ├── logs/                    # API call logs
│   ├── audit/                   # Audit trail
│   └── config/
│       └── thresholds.json      # Configurable thresholds
├── obsidian/
│   └── mission-control.md       # Obsidian dashboard template
├── tests/
│   ├── test_confidence.py
│   ├── test_correlation.py
│   └── mock_data/
├── .env.example                 # Environment variables template
├── requirements.txt
└── claude_desktop_config.json   # MCP server configuration
```

---

## Architecture Components

### 1. Data Watchers (Ingestion Layer)

| Watcher | Source | Polling Interval | Output |
|---------|--------|------------------|--------|
| RSS Watcher | Dawn, Express Tribune, ARY | 5 min | NewsItem objects |
| Weather Watcher | OpenWeatherMap | 15 min | WeatherData object |
| Social Watcher | Brave Search API | 5 min | SocialSignal objects |

### 2. Correlation Engine (Brain)

```
INPUT: List of signals from all watchers
PROCESS:
  1. Group signals by location (Karachi district matching)
  2. Group signals by incident type (fire, flood, traffic, etc.)
  3. Apply time window (signals within 30 minutes)
  4. Calculate confidence using weighted scoring
OUTPUT: Incident objects with confidence scores
```

### 3. Confidence Scorer

| Source Type | Base Weight | Modifiers |
|-------------|-------------|-----------|
| Official News | 0.35 | +0.1 verified outlet |
| Social Cluster | 0.25 | +0.1 geo-tagged |
| Weather API | 0.30 | +0.1 real-time |
| Traffic Anomaly | 0.20 | +0.1 correlated |

### 4. Alert Generator

```
IF confidence >= 0.7: AUTO_NOTIFY (HIGH)
IF confidence >= 0.4: HUMAN_REVIEW (MEDIUM)
IF confidence < 0.4: LOG_ONLY (LOW)
```

---

## MCP Integration

### Claude Desktop Configuration

The system integrates with Claude Desktop via MCP servers:

1. **brave-search**: Query social media and news in real-time
2. **fetch**: Direct API calls to weather services
3. **filesystem**: Read/write Sentinel_Vault
4. **sequential-thinking**: Structured reasoning for confidence decisions

---

## Key Algorithms

### Confidence Calculation

```python
def calculate_confidence(sources: List[Source]) -> float:
    BASE_WEIGHTS = {
        'news': 0.35,
        'social': 0.25,
        'weather': 0.30,
        'traffic': 0.20
    }

    RECENCY_FACTORS = {
        5: 1.0,    # < 5 min
        15: 0.9,   # 5-15 min
        30: 0.7,   # 15-30 min
        60: 0.5,   # 30-60 min
    }

    total = 0.0
    for source in sources:
        weight = BASE_WEIGHTS.get(source.type, 0.2)
        if source.verified:
            weight += 0.1
        weight *= get_recency_factor(source.age_minutes)
        total += weight

    return min(total, 1.0)
```

### Location Extraction

```python
KARACHI_DISTRICTS = {
    'saddar': ['saddar', 'bolton', 'm.a. jinnah', 'empress'],
    'dha': ['dha', 'defence', 'phase 6', 'phase 7', 'phase 8'],
    'clifton': ['clifton', 'sea view', 'boat basin'],
    'korangi': ['korangi', 'landhi'],
    'site': ['site', 's.i.t.e', 'industrial'],
    # ... more districts
}

def extract_location(text: str) -> Optional[str]:
    text_lower = text.lower()
    for district, keywords in KARACHI_DISTRICTS.items():
        if any(kw in text_lower for kw in keywords):
            return district
    return None
```

---

## Security & Privacy

- API keys stored in `.env` file (never committed)
- Social media usernames hashed with SHA-256
- No personal data stored beyond incident context
- All logs include timestamps for audit trail

---

## Deployment Steps

1. Install Python dependencies
2. Configure `.env` with API keys
3. Copy MCP config to Claude Desktop
4. Initialize Sentinel_Vault directories
5. Run `python src/main.py` for continuous monitoring
