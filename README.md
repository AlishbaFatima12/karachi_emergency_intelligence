# SENTINEL-K: Karachi Urban Emergency Intelligence System

<div align="center">

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![City](https://img.shields.io/badge/City-Karachi-orange)

**A 24/7 Digital FTE (Full-Time Employee) for Urban Emergency Detection**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API Reference](#-api-reference)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [The Problem](#-the-problem-we-solve)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Dashboard](#-dashboard)
- [Safety Protocols](#-safety-protocols)
- [Project Structure](#-project-structure)
- [Flow Diagrams](#-flow-diagrams)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**Sentinel-K** operates as an autonomous **Urban Intelligence Officer** for Karachi, Pakistan. It provides early warning alerts for urban emergencies through **multi-source correlation** - not first response.

### What Sentinel-K Does

| ✅ DOES | ❌ DOES NOT |
|---------|-------------|
| Detects emergencies 10-15 min before news | Dispatch emergency services |
| Correlates multiple data sources | Make decisions for users |
| Provides confidence-scored alerts | Store personal information |
| Supports English, Urdu, Roman Urdu | Auto-notify without human review |

---

## 🔥 The Problem We Solve

In a megacity of 20+ million people like Karachi:

```
❌ News spreads chaotically on social media
❌ Fake news causes unnecessary panic
❌ Real emergencies get lost in the noise
❌ No centralized situational awareness
❌ Language barriers (English/Urdu/Roman Urdu mix)
```

### Our Solution: The Triangulation Principle

```
Instead of:  "Someone said there's a fire!" (PANIC)

We provide:  "3 sources confirm fire in Saddar.
             85% confidence.
             VERIFY with Rescue 1122."
```

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Source Correlation** | Cross-references RSS, social media, weather data |
| **Confidence Scoring** | 0-100% reliability rating based on source count |
| **3-Language Support** | English, Urdu, and Roman Urdu keywords |
| **Real-Time Dashboard** | Interactive WebGL map with live updates |
| **Discord Notifications** | Instant alerts + 5-minute heartbeat status |
| **Content Filtering** | 60+ blocked keywords (movies, sports, military) |
| **Deduplication** | No repeated news across polling cycles |

### Incident Types Detected

| Type | English Keywords | Roman Urdu Keywords |
|------|-----------------|---------------------|
| 🔥 Fire | fire, blaze, smoke | aag, dhuaan, jalaya |
| 🌊 Flood | flood, rain, water logging | sailaab, paani, baarish |
| 💥 Explosion | blast, explosion, bomb | dhamaaka, dhamaka |
| 🔫 Shooting | shooting, firing | goli, firing |
| 🚗 Traffic | accident, crash | hadsa, gaari palat |
| ⚡ Power Outage | blackout, power outage | bijli gayi, load shedding |
| 📢 Protest | protest, strike, rally | dharna, jalao |

### Dashboard Features

- **Interactive Map**: Deck.gl + MapLibre with 50+ Karachi neighborhoods
- **Satellite View**: FREE ESRI satellite imagery toggle
- **Traffic Layer**: 20 major traffic hotspots
- **Weather Panel**: Real-time temperature, humidity, wind, rain
- **Incident Feed**: Live updates via WebSocket
- **Click-to-Query**: Click any location for area status
- **Mode Switching**: Normal / Monsoon / Heatwave modes

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SENTINEL-K ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   SENSES     │  │    BRAIN     │  │   OUTPUT     │          │
│  │  (Ingestion) │──│  (Reasoning) │──│  (Delivery)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                  │                  │
│    RSS Feeds         Correlation        Web Dashboard           │
│    Weather API       Engine             Discord Alerts          │
│    Brave Search      Confidence         SQLite Storage          │
│                      Scorer                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
RSS Feeds ──┐
            │
Weather ────┼──▶ Correlation Engine ──▶ Confidence Score ──▶ Alerts
            │         │
Social ─────┘         ▼
                  Incidents[]
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    Dashboard     Discord      Database
```

---

## 🛠 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.10+ | Main application |
| **Web Framework** | FastAPI | REST API + WebSocket |
| **HTTP Client** | httpx | Async API calls |
| **RSS Parsing** | feedparser | News feed processing |
| **Database** | SQLite | Incident persistence |
| **Frontend** | HTML/CSS/JS | Single-file dashboard |
| **Mapping** | Deck.gl + MapLibre | WebGL visualization |
| **Notifications** | Discord Webhooks | Real-time alerts |

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Internet connection

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/AlishbaFatima12/karachi_emergency_intelligence.git
cd karachi_emergency_intelligence

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run the application
cd src
python main_enhanced.py
```

### Access Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

---

## ⚙️ Configuration

### Required API Keys

Create a `.env` file with the following:

```env
# OpenWeatherMap (FREE: 1000 calls/day)
# Get from: https://openweathermap.org/api
OPENWEATHERMAP_API_KEY=your_key_here

# Brave Search (FREE: 2000 queries/month)
# Get from: https://brave.com/search/api/
BRAVE_API_KEY=your_key_here

# Discord Webhook (FREE: Unlimited)
# Get from: Discord Channel Settings → Integrations → Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/xxx
```

### Optional Settings

```env
# Logging level
LOG_LEVEL=INFO

# Dashboard port
DASHBOARD_PORT=8000

# Polling intervals (seconds)
RSS_POLL_INTERVAL=300
WEATHER_POLL_INTERVAL=900
SOCIAL_POLL_INTERVAL=300
```

---

## 🚀 Usage

### Starting the System

```bash
cd src
python main_enhanced.py
```

### Expected Output

```
================================================================
              SENTINEL-K ENHANCED
        Karachi Urban Intelligence Officer

  Features:
  * Multi-source correlation      * Discord alerts
  * Web dashboard                 * SQLite history
  * Roman Urdu detection          * Confidence scoring

  WARNING: NOT AN EMERGENCY DISPATCHER
  For emergencies: Police 15 | Rescue 1122 | Edhi 115
================================================================

🌐 Web dashboard started at http://localhost:8000
📰 Polling RSS feeds...
🌤️ Polling weather data...
📱 Polling social media...
```

### Discord Notifications

**Heartbeat (Every 5 minutes):**
```
🛡️ SENTINEL-K STATUS
Status: ✅ All clear
Weather: 🌡️ 25.5°C
Time: 21:30 PKT
```

**Alert (When incident detected):**
```
🔥 FIRE ALERT
**Gul Plaza fire death toll rises to 28...**
📍 Location: SITE Area
📊 Confidence: 🔴 HIGH (85%)
📰 Sources: 4 corroborating
🕐 Time: 20:53 PKT
⚠️ VERIFY with official sources
```

---

## 📡 API Reference

### Data Sources

| Source | API | Rate Limit | Cost |
|--------|-----|------------|------|
| Weather | OpenWeatherMap | 1000/day | FREE |
| Social/News | Brave Search | 2000/month | FREE |
| RSS Feeds | Direct HTTP | Unlimited | FREE |
| Notifications | Discord Webhooks | 30/min | FREE |

### RSS Feeds Monitored

| Source | URL | Reliability |
|--------|-----|-------------|
| Dawn News | dawn.com/feeds/home | 0.9 |
| Express Tribune | tribune.com.pk/feed/home | 0.85 |
| ARY News | arynews.tv/feed/ | 0.8 |
| Geo News | geo.tv/rss/1/1 | 0.8 |
| Samaa TV | samaa.tv/feed/ | 0.75 |

---

## 📊 Dashboard

### Main Components

| Component | Description |
|-----------|-------------|
| **Map View** | Interactive Karachi map with incident markers |
| **Incident Feed** | Real-time list of active incidents |
| **Weather Panel** | Current conditions (temp, humidity, wind, rain) |
| **System Health** | Source status and polling indicators |
| **Command Bar** | Mode switching, satellite toggle, search |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Toggle Satellite View |
| `T` | Toggle Traffic Layer |
| `3` | Toggle 3D View |
| `R` | Refresh Data |

---

## 🛡 Safety Protocols

### Core Rules

```
╔════════════════════════════════════════════════════════════════╗
║                    STRICT PROHIBITIONS                          ║
╠════════════════════════════════════════════════════════════════╣
║  Sentinel-K SHALL NOT:                                          ║
║  • Directly contact emergency services                          ║
║  • Issue evacuation orders                                      ║
║  • Claim to be an official authority                           ║
║  • Auto-dispatch any emergency response                         ║
║  • Store personal identifying information                       ║
╚════════════════════════════════════════════════════════════════╝
```

### Confidence Levels & Actions

| Sources | Confidence | Level | Action |
|---------|------------|-------|--------|
| 1 | 0-39% | LOW | Log only |
| 2 | 40-69% | MEDIUM | Human review |
| 3+ | 70-100% | HIGH | Auto-notify (with disclaimer) |

### Mandatory Disclaimer

Every alert includes:
```
⚠️ VERIFY FIRST: This is automated analysis.
Confirm with official sources before taking action.
For emergencies: Police 15 | Rescue 1122 | Edhi 115
```

---

## 📁 Project Structure

```
sentinel_k/
├── .env.example              # API key template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── requirements.txt          # Python dependencies
│
├── src/                      # SOURCE CODE
│   ├── main_enhanced.py      # Main entry point
│   │
│   ├── watchers/             # DATA INGESTION
│   │   ├── rss_watcher.py    # RSS feed polling
│   │   ├── weather_watcher.py # OpenWeatherMap
│   │   └── social_watcher.py # Brave Search
│   │
│   ├── engines/              # PROCESSING
│   │   ├── correlation_engine.py
│   │   └── confidence_scorer.py
│   │
│   ├── models/               # DATA MODELS
│   │   ├── source.py
│   │   └── incident.py
│   │
│   ├── notifiers/            # OUTPUT
│   │   ├── telegram_bot.py
│   │   └── discord_bot.py
│   │
│   ├── dashboard/            # WEB INTERFACE
│   │   ├── web_server.py
│   │   └── karachi_data.py
│   │
│   └── storage/              # PERSISTENCE
│       └── database.py
│
├── specs/                    # DOCUMENTATION
│   ├── SENTINEL_K_PRESENTATION.md
│   ├── FLOW_DIAGRAMS.md
│   └── PRODUCTION_GUIDE.md
│
├── Sentinel_Vault/           # DATA STORAGE (gitignored)
│   ├── incidents/
│   ├── logs/
│   └── config/
│
└── .specify/                 # PROJECT GOVERNANCE
    └── memory/
        └── constitution.md
```

---

## 📈 Flow Diagrams

### Main Polling Loop

```
START ──▶ [Poll RSS] ──▶ [Poll Weather] ──▶ [Poll Social]
              │                │                  │
              └────────────────┴──────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │   CORRELATION   │
                    │     ENGINE      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         Dashboard       Discord       Database
              │              │              │
         (WebSocket)    (Webhook)     (SQLite)
```

### Confidence Scoring

```
Source ──▶ Base Weight ──▶ Modifiers ──▶ Recency ──▶ Score
              │               │            │
           NEWS: 0.35    Verified: +0.1   <5min: 1.0
          SOCIAL: 0.25   Geo-tag: +0.05   5-15min: 0.9
         WEATHER: 0.30                    15-30min: 0.7
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Never commit API keys or secrets

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Data Sources**: Dawn News, Geo News, ARY News, Express Tribune, Samaa TV
- **APIs**: OpenWeatherMap, Brave Search
- **Mapping**: Deck.gl, MapLibre, ESRI
- **City**: Karachi, Pakistan 🇵🇰

---

## 📞 Emergency Numbers (Reference Only)

| Service | Number |
|---------|--------|
| Police Emergency | 15 |
| Rescue 1122 | 1122 |
| Edhi Ambulance | 115 |
| Chhipa Foundation | 1021 |

**⚠️ REMINDER: Sentinel-K is an early warning system, NOT an emergency dispatcher!**

---

<div align="center">

**Built with ❤️ for Karachi**

*Sentinel-K v1.0.0 | January 2026*

</div>
