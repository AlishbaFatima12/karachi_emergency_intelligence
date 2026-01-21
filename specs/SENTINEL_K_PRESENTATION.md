# SENTINEL-K: Urban Emergency Intelligence System
## Complete Technical Presentation & Production Guide

**Version**: 1.0.0 | **Date**: January 2026 | **Status**: Production Ready

---

# EXECUTIVE SUMMARY

## What is Sentinel-K?

Sentinel-K is a **Digital Full-Time Employee (FTE)** that operates as a **24/7 Urban Intelligence Officer** for Karachi, Pakistan. It solves the **Information Chaos Problem** by correlating data from multiple sources to provide early warning alerts for urban emergencies.

### The Problem It Solves

```
In a city of 20+ million people:
- News spreads chaotically on social media
- Fake news causes panic
- Real emergencies get lost in noise
- No centralized situational awareness
- Language barriers (English/Urdu/Roman Urdu)
```

### The Solution

```
SENTINEL-K = Multi-Source Correlation + Confidence Scoring + Human-in-the-Loop

Instead of:  "Someone said there's a fire!" (PANIC)
We provide:  "3 sources confirm fire in Saddar. 85% confidence. VERIFY with Rescue 1122."
```

---

# PART 1: PROJECT OBJECTIVES

## 1.1 Primary Objectives

| Objective | Description | Success Metric |
|-----------|-------------|----------------|
| **Early Detection** | Detect emergencies 10-15 min before mainstream news | Detection lead time > 10 min |
| **Reduce False Alarms** | Eliminate single-source panic alerts | False positive rate < 15% |
| **Multi-Language Support** | Process English, Urdu, Roman Urdu | 3 language coverage |
| **Real-Time Correlation** | Cross-reference 4+ data sources | Correlation within 2 min |
| **Human Oversight** | No auto-dispatch; human verification required | 100% human approval for actions |

## 1.2 What Sentinel-K IS vs IS NOT

| IS | IS NOT |
|----|--------|
| Early Warning System | Emergency Dispatcher |
| Intelligence Aggregator | First Responder |
| Confidence Scorer | Decision Maker |
| Situation Monitor | Surveillance Tool |
| Alert Generator | Auto-Notification System |

---

# PART 2: SYSTEM ARCHITECTURE

## 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SENTINEL-K ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │     SENSES       │    │      BRAIN       │    │     OUTPUT       │      │
│  │  (Data Sources)  │───▶│   (Correlation)  │───▶│   (Delivery)     │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│          │                       │                       │                  │
│          ▼                       ▼                       ▼                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │ • RSS Watcher    │    │ • Correlation    │    │ • Web Dashboard  │      │
│  │ • Weather API    │    │   Engine         │    │ • Discord Alerts │      │
│  │ • Social Search  │    │ • Confidence     │    │ • Obsidian Sync  │      │
│  │   (Brave API)    │    │   Scorer         │    │ • SQLite DB      │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Data Flow Diagram

```
                              ┌─────────────────┐
                              │   BRAVE SEARCH  │
                              │   (Social API)  │
                              └────────┬────────┘
                                       │
┌─────────────────┐                    ▼                    ┌─────────────────┐
│   RSS FEEDS     │──────────▶ ┌──────────────────┐ ◀──────│ OPENWEATHERMAP  │
│ Dawn, Geo, ARY  │            │                  │        │   Weather API   │
│ Tribune, Samaa  │            │   CORRELATION    │        └─────────────────┘
└─────────────────┘            │     ENGINE       │
                               │                  │
                               │  ┌────────────┐  │
                               │  │ Confidence │  │
                               │  │   Scorer   │  │
                               │  └────────────┘  │
                               │                  │
                               └────────┬─────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
           ▼                            ▼                            ▼
   ┌───────────────┐           ┌───────────────┐           ┌───────────────┐
   │ WEB DASHBOARD │           │    DISCORD    │           │   OBSIDIAN    │
   │  (FastAPI +   │           │   WEBHOOKS    │           │    VAULT      │
   │   Deck.gl)    │           │  (Instant)    │           │  (Markdown)   │
   └───────────────┘           └───────────────┘           └───────────────┘
```

## 2.3 Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MAIN POLLING LOOP (5 min cycle)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  START ──▶ [Poll RSS] ──▶ [Poll Weather] ──▶ [Poll Social]                 │
│              │                │                  │                          │
│              ▼                ▼                  ▼                          │
│         Sources[]        Weather{}          Sources[]                       │
│              │                │                  │                          │
│              └────────────────┴──────────────────┘                          │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────┐                                      │
│                    │  CORRELATION    │                                      │
│                    │     ENGINE      │                                      │
│                    │                 │                                      │
│                    │ 1. Filter       │                                      │
│                    │ 2. Group by     │                                      │
│                    │    Location     │                                      │
│                    │ 3. Score        │                                      │
│                    │ 4. Classify     │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│                             ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │   Incidents[]   │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│              ┌──────────────┼──────────────┐                                │
│              ▼              ▼              ▼                                │
│         [Dashboard]    [Discord]     [Database]                             │
│              │              │              │                                │
│              ▼              ▼              ▼                                │
│          WebSocket      Webhook       SQLite                                │
│          Real-time      Instant       Persist                               │
│                                                                              │
│  ──▶ SLEEP 60s ──▶ LOOP                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# PART 3: PROJECT STRUCTURE

## 3.1 Directory Structure

```
sentinel_k/
├── .env                          # API keys (NEVER commit)
├── .env.example                  # Template for API keys
├── requirements.txt              # Python dependencies
│
├── src/                          # SOURCE CODE
│   ├── main_enhanced.py          # Main orchestrator (entry point)
│   │
│   ├── watchers/                 # DATA INGESTION LAYER
│   │   ├── rss_watcher.py        # RSS feed polling
│   │   ├── weather_watcher.py    # OpenWeatherMap API
│   │   └── social_watcher.py     # Brave Search API
│   │
│   ├── engines/                  # PROCESSING LAYER
│   │   ├── correlation_engine.py # Multi-source correlation
│   │   └── confidence_scorer.py  # Confidence calculation
│   │
│   ├── models/                   # DATA MODELS
│   │   ├── source.py             # Source data model
│   │   └── incident.py           # Incident data model
│   │
│   ├── notifiers/                # OUTPUT LAYER
│   │   ├── telegram_bot.py       # Telegram notifications
│   │   └── discord_bot.py        # Discord webhooks
│   │
│   ├── dashboard/                # WEB INTERFACE
│   │   ├── web_server.py         # FastAPI + Dashboard HTML
│   │   └── karachi_data.py       # Karachi geographic data
│   │
│   └── storage/                  # PERSISTENCE
│       └── database.py           # SQLite database
│
├── Sentinel_Vault/               # DATA STORAGE
│   ├── incidents/                # Incident JSON files
│   ├── logs/                     # System logs
│   ├── audit/                    # Audit trail
│   └── config/                   # Configuration files
│
├── obsidian/                     # OBSIDIAN INTEGRATION
│   └── mission-control.md        # Auto-updated dashboard
│
└── .specify/                     # PROJECT GOVERNANCE
    └── memory/
        └── constitution.md       # System constitution
```

## 3.2 Key Files Explained

| File | Purpose | Lines |
|------|---------|-------|
| `main_enhanced.py` | Main orchestrator, polling loop, heartbeat | ~300 |
| `correlation_engine.py` | Multi-source correlation, incident detection | ~350 |
| `web_server.py` | FastAPI server + Full dashboard HTML/JS | ~1800 |
| `social_watcher.py` | Brave Search integration, content filtering | ~350 |
| `rss_watcher.py` | RSS feed polling with filtering | ~220 |
| `discord_bot.py` | Discord webhook notifications | ~250 |

---

# PART 4: APIs & EXTERNAL SERVICES

## 4.1 APIs Used

| API | Purpose | Cost | Rate Limit |
|-----|---------|------|------------|
| **OpenWeatherMap** | Weather data for Karachi | FREE | 1000 calls/day |
| **Brave Search** | Social media & news search | FREE | 2000 queries/month |
| **Discord Webhooks** | Instant notifications | FREE | 30 msg/min |

## 4.2 API Configuration

```python
# .env file structure
OPENWEATHERMAP_API_KEY=db33abc58f336f972baa0287ebcdf777
BRAVE_API_KEY=BSAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/xxx
```

## 4.3 RSS Feeds (No API Key Required)

| Source | URL | Reliability |
|--------|-----|-------------|
| Dawn News | `https://www.dawn.com/feeds/home` | 0.9 |
| Express Tribune | `https://tribune.com.pk/feed/home` | 0.85 |
| ARY News | `https://arynews.tv/feed/` | 0.8 |
| Geo News | `https://www.geo.tv/rss/1/1` | 0.8 |
| Samaa TV | `https://www.samaa.tv/feed/` | 0.75 |

---

# PART 5: CORE FEATURES

## 5.1 Multi-Source Correlation (The Brain)

```python
# Triangulation Principle
IF (News = "Fire in Saddar")
   AND (Social = "Aag lagi hai Saddar")
   AND (Traffic = Anomaly detected)
THEN
   Confidence = HIGH (0.85+)
   Action = ALERT
```

### Confidence Levels

| Sources | Confidence | Action |
|---------|------------|--------|
| 1 source | LOW (0-39%) | Log only |
| 2 sources | MEDIUM (40-69%) | Human review |
| 3+ sources | HIGH (70-100%) | Auto-notify |

## 5.2 Incident Types Detected

| Type | Keywords (English) | Keywords (Roman Urdu) |
|------|-------------------|----------------------|
| Fire | fire, blaze, smoke, burning | aag, dhuaan, jalaya |
| Flood | flood, rain, water logging | sailaab, paani, baarish |
| Explosion | blast, explosion, bomb | dhamaaka, dhamaka |
| Shooting | shooting, firing, gunfire | goli, firing |
| Traffic | accident, crash, collision | hadsa, gaari palat |
| Power Outage | power outage, blackout | bijli gayi, load shedding |
| Protest | protest, strike, rally | dharna, jalao |

## 5.3 Content Filtering System

### Blocked Content (Entertainment/Sports/Military)

```python
EXCLUDED_KEYWORDS = [
    # Movies
    "box office", "bollywood", "crore", "movie", "film",
    "ranveer", "salman", "shahrukh", "deepika",

    # Sports
    "cricket", "psl", "ipl", "world cup", "match",

    # Military (not local emergency)
    "air force", "loc", "line of control", "deep-strike",

    # Reference
    "wikipedia", "wiki", "encyclopedia",

    # Other cities
    "lahore", "islamabad", "peshawar", "quetta"
]
```

### Required Emergency Keywords

```python
EMERGENCY_KEYWORDS = [
    "fire", "aag", "blast", "explosion", "shooting", "firing",
    "accident", "crash", "flood", "rain", "robbery", "killed",
    "protest", "strike", "power outage", "blackout", "emergency"
]
```

## 5.4 Web Dashboard Features

| Feature | Description |
|---------|-------------|
| **Real-time Map** | Deck.gl + MapLibre with Karachi data |
| **Incident Feed** | Live updates via WebSocket |
| **Weather Panel** | Current conditions (temp, humidity, wind, rain) |
| **System Health** | Source status indicators |
| **Satellite View** | ESRI free satellite imagery toggle |
| **Traffic Layer** | 20 major Karachi traffic hotspots |
| **Click-to-Query** | Click any location for area status |
| **Mode Switching** | Normal / Monsoon / Heatwave modes |

## 5.5 Discord Notifications

### Heartbeat (Every 5 Minutes)
```
SENTINEL-K STATUS
Status: All clear / X active alerts
Weather: 25.5°C
Time: 21:30 PKT
```

### Alert Format
```
FIRE ALERT
**Gul Plaza fire death toll rises...**
Location: SITE Area
Confidence: HIGH (85%)
Sources: 4 corroborating
Time: 20:53 PKT
VERIFY with official sources | Police 15 | Rescue 1122
```

---

# PART 6: TECHNICAL IMPLEMENTATION

## 6.1 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.10+ | Main application |
| **Web Framework** | FastAPI | REST API + WebSocket |
| **HTTP Client** | httpx | Async API calls |
| **RSS Parsing** | feedparser | RSS feed processing |
| **Database** | SQLite | Incident persistence |
| **Frontend** | HTML/CSS/JS (embedded) | Single-file dashboard |
| **Mapping** | Deck.gl + MapLibre | WebGL map visualization |
| **Notifications** | Discord Webhooks | Real-time alerts |

## 6.2 Key Python Libraries

```python
# requirements.txt
fastapi>=0.100.0
uvicorn>=0.22.0
httpx>=0.24.0
feedparser>=6.0.10
python-dotenv>=1.0.0
websockets>=11.0
```

## 6.3 Data Models

### Source Model
```python
@dataclass
class Source:
    type: SourceType      # NEWS, SOCIAL, WEATHER, TRAFFIC
    content: str          # Text content
    timestamp: datetime   # When detected
    location: str         # Karachi district
    url: str              # Source URL
    verified: bool        # Is verified source?
    geo_tagged: bool      # Has geo coordinates?
```

### Incident Model
```python
@dataclass
class Incident:
    id: str                    # Unique ID
    incident_type: IncidentType # FIRE, FLOOD, etc.
    location: str              # District name
    sources: List[Source]      # Corroborating sources
    confidence_score: float    # 0.0 to 1.0
    confidence_level: ConfidenceLevel  # LOW/MEDIUM/HIGH
    created_at: datetime       # First detection
    status: str                # active/resolved/false_positive
```

## 6.4 Confidence Scoring Algorithm

```python
def calculate_confidence(sources: List[Source]) -> float:
    """
    Multi-factor confidence scoring
    """
    # Base weights by source type
    weights = {
        SourceType.NEWS: 0.35,
        SourceType.SOCIAL: 0.25,
        SourceType.WEATHER: 0.30,
        SourceType.TRAFFIC: 0.20,
    }

    total = 0.0
    for source in sources:
        weight = weights.get(source.type, 0.2)

        # Modifiers
        if source.verified:
            weight += 0.1
        if source.geo_tagged:
            weight += 0.05

        # Recency factor (decay over time)
        age_minutes = source.age_minutes
        if age_minutes < 5:
            recency = 1.0
        elif age_minutes < 15:
            recency = 0.9
        elif age_minutes < 30:
            recency = 0.7
        else:
            recency = 0.5

        total += weight * recency

    return min(total, 1.0)  # Cap at 100%
```

---

# PART 7: CHALLENGES & SOLUTIONS

## 7.1 Technical Challenges

| Challenge | Solution |
|-----------|----------|
| **Telegram blocked by ISP** | Switched to Discord webhooks |
| **Google Maps requires payment** | Used FREE ESRI satellite tiles |
| **Irrelevant news (movies, sports)** | 60+ keyword content filter |
| **Wikipedia articles appearing** | URL-based blocking |
| **Military news mixing in** | Added "air force", "loc" to blocklist |
| **Duplicate news on refresh** | URL deduplication with seen_urls set |
| **Roman Urdu processing** | Multi-language keyword lists |
| **Location extraction** | District-specific keyword mapping |

## 7.2 Operational Challenges

| Challenge | Solution |
|-----------|----------|
| **False positives** | 30-min cooldown after marking false |
| **Single-source panic** | Minimum 2 sources for MEDIUM confidence |
| **Alert fatigue** | Only MEDIUM/HIGH sent to Discord |
| **Data freshness** | 30-min correlation window |
| **Privacy concerns** | Hash usernames, aggregate locations |

---

# PART 8: SAFETY PROTOCOLS

## 8.1 Core Safety Rules

```
╔════════════════════════════════════════════════════════════════╗
║                    STRICT PROHIBITIONS                          ║
╠════════════════════════════════════════════════════════════════╣
║  Sentinel-K SHALL NOT:                                          ║
║  • Directly contact emergency services (Police, Rescue 1122)    ║
║  • Issue evacuation orders                                      ║
║  • Claim to be an official authority                           ║
║  • Auto-dispatch any emergency response                         ║
║  • Store personal identifying information                       ║
╚════════════════════════════════════════════════════════════════╝
```

## 8.2 Mandatory Disclaimer

Every alert includes:
```
⚠️ VERIFY FIRST: This is automated analysis.
Confirm with official sources before taking action.
For emergencies: Police 15 | Rescue 1122 | Edhi 115
```

## 8.3 Anti-Panic Logic

```python
def should_escalate(incident):
    # NEVER escalate single-source alerts
    if incident.source_count < 2:
        return "LOG_ONLY"

    if incident.confidence < 0.4:
        return "LOG_ONLY"

    if incident.confidence < 0.7:
        return "HUMAN_REVIEW"

    return "AUTO_NOTIFY"
```

---

# PART 9: PRODUCTION DEPLOYMENT

## 9.1 Prerequisites

```bash
# System Requirements
- Python 3.10+
- 2GB RAM minimum
- Stable internet connection

# API Keys Required
- OpenWeatherMap (FREE)
- Brave Search (FREE)
- Discord Webhook URL
```

## 9.2 Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/your-org/sentinel-k.git
cd sentinel-k

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run the system
cd src
python main_enhanced.py
```

## 9.3 Production Checklist

| Item | Status | Notes |
|------|--------|-------|
| API keys configured | ✅ | .env file |
| Content filters active | ✅ | 60+ blocked keywords |
| Deduplication enabled | ✅ | seen_urls tracking |
| Discord webhooks working | ✅ | 5-min heartbeat |
| Dashboard accessible | ✅ | http://localhost:8000 |
| Safety disclaimers | ✅ | On all alerts |
| Error handling | ✅ | Try-catch on all APIs |
| Logging enabled | ✅ | INFO level |

## 9.4 Monitoring & Maintenance

```bash
# View logs
tail -f Sentinel_Vault/logs/sentinel-k.log

# Check database
sqlite3 Sentinel_Vault/sentinel_k.db "SELECT * FROM incidents LIMIT 10;"

# Monitor Discord
# Check channel for 5-minute heartbeats
```

---

# PART 10: FUTURE ENHANCEMENTS

## 10.1 Roadmap

| Phase | Feature | Priority |
|-------|---------|----------|
| **Phase 2** | WhatsApp Business API | HIGH |
| **Phase 2** | Traffic API integration | HIGH |
| **Phase 3** | Mobile app (Flutter) | MEDIUM |
| **Phase 3** | ML-based classification | MEDIUM |
| **Phase 4** | Government data feeds | LOW |
| **Phase 4** | Multi-city expansion | LOW |

## 10.2 Potential Integrations

- **Rescue 1122 API** (if available)
- **K-Electric power grid status**
- **PDMA (Provincial Disaster Management)**
- **Traffic Police feeds**

---

# APPENDIX A: KARACHI REFERENCE DATA

## Monitored Districts

| District | Primary Risk | Priority |
|----------|-------------|----------|
| Saddar | Fire (markets) | CRITICAL |
| SITE Area | Industrial fire | CRITICAL |
| Korangi | Industrial fire | HIGH |
| Lyari | Civil unrest | HIGH |
| DHA | Flooding | MEDIUM |
| Clifton | Flooding | MEDIUM |
| Gulshan | Traffic | MEDIUM |
| Malir | Flooding | HIGH |

## Emergency Numbers (Reference Only)

| Service | Number |
|---------|--------|
| Police Emergency | 15 |
| Rescue/Fire | 1122 |
| Edhi Ambulance | 115 |
| Chhipa Ambulance | 1021 |
| Rangers | 1101 |

---

# APPENDIX B: API RESPONSE EXAMPLES

## OpenWeatherMap Response
```json
{
  "main": {
    "temp": 291.89,
    "humidity": 68
  },
  "wind": {
    "speed": 3.6
  },
  "rain": {
    "1h": 0.5
  }
}
```

## Brave Search Response
```json
{
  "web": {
    "results": [
      {
        "title": "Fire in Saddar market...",
        "url": "https://dawn.com/...",
        "description": "Multiple shops affected..."
      }
    ]
  }
}
```

---

# APPENDIX C: GLOSSARY

| Term | Definition |
|------|------------|
| **FTE** | Full-Time Employee (digital equivalent) |
| **Triangulation** | Cross-referencing 3+ sources |
| **Confidence Score** | 0-100% reliability rating |
| **Cooldown** | 30-min pause after false positive |
| **Roman Urdu** | Urdu written in Latin script |
| **MCP** | Model Context Protocol (Claude tools) |

---

**END OF PRESENTATION**

*Document generated: January 2026*
*System: Sentinel-K v1.0.0*
*Author: Urban Intelligence Team*
