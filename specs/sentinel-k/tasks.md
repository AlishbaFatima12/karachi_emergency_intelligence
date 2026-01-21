# 1-DAY IMPLEMENTATION PLAN: Sentinel-K

**Target Date**: Today
**Estimated Duration**: 4-6 hours
**Prerequisite**: Python 3.11+, Node.js 18+, Claude Desktop installed

---

## TASK OVERVIEW

| # | Task | Duration | Dependency |
|---|------|----------|------------|
| 1 | Environment Setup | 30 min | None |
| 2 | Python Watcher Script Setup | 60 min | Task 1 |
| 3 | MCP Server Configuration | 30 min | Task 1 |
| 4 | Confidence Logic Testing | 45 min | Task 2 |
| 5 | Obsidian Dashboard Setup | 30 min | Task 3 |
| 6 | Integration Test | 45 min | Task 4, 5 |

---

## TASK 1: Environment Setup (30 minutes)

### 1.1 Install Python Dependencies

```powershell
# Navigate to project
cd D:\sentinel_k

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables

```powershell
# Copy example env file
copy .env.example .env

# Edit .env with your API keys
notepad .env
```

**Required API Keys**:

1. **OpenWeatherMap** (FREE tier available):
   - Go to: https://openweathermap.org/api
   - Sign up and get API key
   - Add to `.env`: `OPENWEATHERMAP_API_KEY=your_key`

2. **Brave Search** (FREE tier: 2000 queries/month):
   - Go to: https://brave.com/search/api/
   - Sign up and get API key
   - Add to `.env`: `BRAVE_API_KEY=your_key`

### 1.3 Verify Vault Structure

```powershell
# Check Sentinel_Vault exists
dir Sentinel_Vault

# Expected output:
# incidents/
# logs/
# audit/
# config/
```

**Acceptance Criteria**:
- [ ] Virtual environment activated
- [ ] All pip packages installed
- [ ] `.env` file created with at least OpenWeatherMap key
- [ ] Sentinel_Vault directories exist

---

## TASK 2: Python Watcher Script Setup (60 minutes)

### 2.1 Test RSS Watcher

```powershell
# Run RSS watcher standalone
python src/watchers/rss_watcher.py
```

**Expected Output**:
```
Starting RSS poll cycle...
[RSS] Detected: Fire breaks out in... | Location: saddar
RSS poll complete. Found X relevant items.
```

**If no output**: RSS feeds may not have Karachi-related emergency news right now. That's normal.

### 2.2 Test Weather Watcher

```powershell
# Run weather watcher standalone
python src/watchers/weather_watcher.py
```

**Expected Output**:
```
Starting weather poll...
Current conditions: {'temperature_c': 28.5, 'humidity_percent': 65, ...}
```

**Troubleshooting**:
- "No API key configured" → Check your `.env` file
- Connection error → Check internet connection

### 2.3 Test Social Watcher

```powershell
# Run social watcher standalone
python src/watchers/social_watcher.py
```

**Expected Output**:
```
Starting social media poll...
[SOCIAL] Found: Karachi fire... | saddar
Social poll complete. Found X relevant signals.
```

### 2.4 Verify All Watchers Work

Create a quick test script:

```python
# test_watchers.py
import sys
sys.path.insert(0, 'src')

from watchers.rss_watcher import RSSWatcher
from watchers.weather_watcher import WeatherWatcher
from watchers.social_watcher import SocialWatcher

print("Testing RSS Watcher...")
rss = RSSWatcher()
rss_sources = rss.poll_all()
print(f"  Found {len(rss_sources)} RSS sources\n")

print("Testing Weather Watcher...")
weather = WeatherWatcher()
conditions = weather.get_current_conditions()
print(f"  Temperature: {conditions.get('temperature_c', 'N/A')}°C\n")

print("Testing Social Watcher...")
social = SocialWatcher()
social_sources = social.poll()
print(f"  Found {len(social_sources)} social signals\n")

print("All watchers operational!")
```

Run it:
```powershell
python test_watchers.py
```

**Acceptance Criteria**:
- [ ] RSS watcher polls without errors
- [ ] Weather watcher returns current Karachi temperature
- [ ] Social watcher returns results (may be 0 if no recent news)

---

## TASK 3: MCP Server Configuration (30 minutes)

### 3.1 Locate Claude Desktop Config

**Windows path**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Or typically:
```
C:\Users\[YourUsername]\AppData\Roaming\Claude\claude_desktop_config.json
```

### 3.2 Backup Existing Config

```powershell
# Backup existing config
copy "$env:APPDATA\Claude\claude_desktop_config.json" "$env:APPDATA\Claude\claude_desktop_config.backup.json"
```

### 3.3 Merge MCP Configuration

Open `claude_desktop_config.json` and add/merge the Sentinel-K MCP servers:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_actual_brave_api_key_here"
      }
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "D:/sentinel_k/Sentinel_Vault"
      ]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

**IMPORTANT**: Replace `your_actual_brave_api_key_here` with your real API key!

### 3.4 Restart Claude Desktop

1. Close Claude Desktop completely
2. Reopen Claude Desktop
3. Check MCP servers are loaded (tools menu should show new capabilities)

### 3.5 Test MCP Connection

In Claude Desktop, ask:
> "Using the fetch MCP, get the current weather for Karachi from OpenWeatherMap"

**Acceptance Criteria**:
- [ ] MCP config file updated
- [ ] Claude Desktop restarted
- [ ] MCP tools visible in Claude Desktop

---

## TASK 4: Confidence Logic Testing (45 minutes)

### 4.1 Run Confidence Scorer Tests

```powershell
# Run confidence scorer test
python src/engines/confidence_scorer.py
```

**Expected Output**:
```
=== Confidence Scoring Test ===
Sources: 2
  - news: weight=0.315
  - social: weight=0.315
Total Confidence: 0.630
Level: MEDIUM
Action: HUMAN_REVIEW

=== Reasoning Chain ===
  > Analyzing incident with 2 source(s)...
  > Source 1: news | Weight: 0.32 | Age: 3.0min | Verified: True
  ...
```

### 4.2 Run Correlation Engine Tests

```powershell
# Run correlation engine test
python src/engines/correlation_engine.py
```

**Expected Output**:
```
[CORRELATION] fire at saddar: 3 sources, confidence=0.82
[ALERT] HIGH confidence incident - AUTO NOTIFY: abc123

=== Correlation Engine Test ===
Alertable incidents: 1

## GOLD ALERT - HIGH CONFIDENCE
**Incident ID**: abc123
**Type**: FIRE
**Location**: saddar
**Confidence**: 0.82 (HIGH)
...
```

### 4.3 Verify Anti-Panic Logic

Create test for single-source scenario:

```python
# test_anti_panic.py
import sys
sys.path.insert(0, 'src')
from datetime import datetime
from models.source import Source, SourceType
from engines.confidence_scorer import ConfidenceScorer

# Single source test
single_source = [
    Source(
        type=SourceType.SOCIAL,
        content="Fire in Saddar!",
        timestamp=datetime.now(),
        location="saddar",
        verified=False
    )
]

scorer = ConfidenceScorer()
action = scorer.should_escalate(single_source)
print(f"Single source escalation: {action}")
assert action == "LOG_ONLY", "Anti-panic failed! Single source should NOT escalate"
print("Anti-panic logic working correctly!")
```

Run it:
```powershell
python test_anti_panic.py
```

**Acceptance Criteria**:
- [ ] Confidence scorer calculates correct weights
- [ ] Correlation engine detects incidents
- [ ] Single-source NEVER escalates (anti-panic working)

---

## TASK 5: Obsidian Dashboard Setup (30 minutes)

### 5.1 Install Obsidian (if not installed)

Download from: https://obsidian.md/

### 5.2 Open Sentinel-K Vault in Obsidian

1. Open Obsidian
2. Click "Open folder as vault"
3. Select `D:\sentinel_k\obsidian`

### 5.3 Install Required Plugins

Open Settings → Community Plugins → Browse:

1. **Leaflet** - For the risk map
   - Search "Leaflet"
   - Install and enable

2. **Dataview** (optional) - For dynamic queries
   - Search "Dataview"
   - Install and enable

### 5.4 Configure Leaflet Plugin

1. Settings → Leaflet
2. Set default map to use OpenStreetMap tiles
3. Test by opening `mission-control.md`

### 5.5 Verify Dashboard

Open `mission-control.md` and verify:
- KPI strip displays
- Map renders (may show blank until first data)
- Incident feed table visible

**Acceptance Criteria**:
- [ ] Obsidian vault opened
- [ ] Leaflet plugin installed
- [ ] Mission Control dashboard renders

---

## TASK 6: Integration Test (45 minutes)

### 6.1 Run Full System (Single Cycle)

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run single cycle test
python src/main.py --single --debug
```

**Expected Output**:
```
╔══════════════════════════════════════════════════════════════════╗
║                        SENTINEL-K                                 ║
║            Karachi Urban Intelligence Officer                     ║
...
Starting Sentinel-K monitoring loop...
Polling RSS feeds...
Polling weather data...
Polling social media...
Processing X sources...
```

### 6.2 Verify Vault Logs

```powershell
# Check if incidents are being logged
dir Sentinel_Vault\incidents
dir Sentinel_Vault\config

# View dashboard data
type Sentinel_Vault\config\dashboard_data.json
```

### 6.3 Run Continuous Monitoring (Optional)

```powershell
# Run continuous monitoring
python src/main.py

# Press Ctrl+C to stop
```

### 6.4 Integration Checklist

- [ ] System starts without errors
- [ ] All watchers poll successfully
- [ ] Incidents logged to Sentinel_Vault
- [ ] Dashboard data file generated
- [ ] No unhandled exceptions

---

## POST-IMPLEMENTATION: Claude Desktop Usage

### How to Use Sentinel-K with Claude Desktop

Once configured, you can ask Claude Desktop:

**Real-time Monitoring**:
> "Search for recent news about fires in Karachi using Brave Search"
> "Fetch current weather conditions for Karachi"
> "Read the latest incidents from Sentinel_Vault"

**Analysis**:
> "Analyze the confidence of this report: 'Fire in Saddar' mentioned on Twitter and Dawn News"
> "What is the nearest hospital to SITE Area?"

**Dashboard Updates**:
> "Write the current incident data to Sentinel_Vault/config/dashboard_data.json"

---

## TROUBLESHOOTING

### Common Issues

| Issue | Solution |
|-------|----------|
| "No API key configured" | Check `.env` file exists and has correct keys |
| RSS timeout | Check internet connection; some feeds may be blocked |
| MCP not loading | Restart Claude Desktop; check JSON syntax |
| Map not rendering | Verify Leaflet plugin enabled in Obsidian |
| Permission denied | Run PowerShell as Administrator |

### Getting Help

1. Check logs: `Sentinel_Vault/logs/`
2. Enable debug mode: `python src/main.py --debug`
3. Test individual components first

---

## COMPLETION CHECKLIST

- [ ] **Task 1**: Environment configured, API keys set
- [ ] **Task 2**: All watchers operational
- [ ] **Task 3**: MCP servers configured in Claude Desktop
- [ ] **Task 4**: Confidence logic tested
- [ ] **Task 5**: Obsidian dashboard set up
- [ ] **Task 6**: Integration test passed

**Congratulations!** Sentinel-K is now operational.

---

## NEXT STEPS (Future Enhancements)

1. **Add Traffic API Integration**: Google Maps or local traffic APIs
2. **Implement Telegram Bot**: For mobile notifications
3. **Add Historical Analysis**: Track patterns over time
4. **Build Web Dashboard**: Real-time web interface
5. **Expand Keywords**: Add more Roman Urdu variations

---

*Sentinel-K v1.0 | 1-Day Implementation Complete*
