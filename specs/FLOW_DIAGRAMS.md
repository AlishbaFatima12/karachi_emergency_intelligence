# SENTINEL-K FLOW DIAGRAMS
## Complete System Flow Visualization

---

# 1. MASTER SYSTEM FLOW

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           SENTINEL-K MASTER FLOW                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │   START     │
                                    │  SYSTEM     │
                                    └──────┬──────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │  Initialize Components  │
                              │  • Watchers (RSS,      │
                              │    Weather, Social)    │
                              │  • Correlation Engine  │
                              │  • Discord Notifier    │
                              │  • Database            │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │   Start Web Server     │
                              │   (FastAPI + WebSocket)│
                              │   http://localhost:8000│
                              └───────────┬────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │              MAIN LOOP                   │
                    │         (Runs every 60 seconds)          │
                    └─────────────────────┬───────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
              ▼                           ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  RSS WATCHER    │         │ WEATHER WATCHER │         │ SOCIAL WATCHER  │
    │  (Every 5 min)  │         │ (Every 15 min)  │         │  (Every 5 min)  │
    └────────┬────────┘         └────────┬────────┘         └────────┬────────┘
             │                           │                           │
             ▼                           ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │ Poll Dawn, Geo  │         │ OpenWeatherMap  │         │  Brave Search   │
    │ ARY, Tribune    │         │ API Request     │         │  API Request    │
    │ Samaa RSS Feeds │         │ Karachi ID:     │         │  "Karachi fire" │
    └────────┬────────┘         │ 1174872         │         │  etc.           │
             │                  └────────┬────────┘         └────────┬────────┘
             ▼                           │                           │
    ┌─────────────────┐                  │                           │
    │ FILTER:         │                  │                           │
    │ • Is Karachi?   │                  │                           │
    │ • Has emergency │                  │                           │
    │   keyword?      │                  │                           │
    │ • Not blocked?  │                  │                           │
    └────────┬────────┘                  │                           │
             │                           │                           ▼
             │                           │                  ┌─────────────────┐
             │                           │                  │ FILTER:         │
             │                           │                  │ • Block Wiki    │
             │                           │                  │ • Block movies  │
             │                           │                  │ • Block sports  │
             │                           │                  │ • Block military│
             │                           │                  │ • Has emergency │
             │                           │                  │   keyword?      │
             │                           │                  └────────┬────────┘
             │                           │                           │
             └───────────────────────────┴───────────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │     ALL SOURCES[]      │
                              │   Collected & Filtered │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │   CORRELATION ENGINE   │
                              │                        │
                              │  1. Group by location  │
                              │  2. Detect type        │
                              │  3. Calculate score    │
                              │  4. Create incidents   │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │    INCIDENTS[]         │
                              │  Ready for delivery    │
                              └───────────┬────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
              ▼                           ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  WEB DASHBOARD  │         │    DISCORD      │         │    DATABASE     │
    │  via WebSocket  │         │   via Webhook   │         │    SQLite       │
    └─────────────────┘         └─────────────────┘         └─────────────────┘
              │                           │                           │
              ▼                           ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  Real-time map  │         │  Alert if       │         │  Persist for    │
    │  Incident feed  │         │  MEDIUM/HIGH    │         │  history        │
    │  Weather panel  │         │  confidence     │         │                 │
    └─────────────────┘         └─────────────────┘         └─────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │    HEARTBEAT CHECK     │
                              │  (Every 5 minutes)     │
                              │  Send status to Discord│
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │      SLEEP 60s         │
                              └───────────┬────────────┘
                                          │
                                          │
                                    LOOP BACK ↑
```

---

# 2. CONFIDENCE SCORING FLOW

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        CONFIDENCE SCORING ALGORITHM                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                ┌─────────────────┐
                                │  Source Input   │
                                │  (News, Social, │
                                │   Weather, etc) │
                                └────────┬────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │  Get Base Weight│
                                └────────┬────────┘
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            │                            │                            │
            ▼                            ▼                            ▼
   ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
   │    NEWS = 0.35   │        │  SOCIAL = 0.25   │        │  WEATHER = 0.30  │
   └────────┬─────────┘        └────────┬─────────┘        └────────┬─────────┘
            │                            │                            │
            └────────────────────────────┼────────────────────────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │ Apply Modifiers │
                                └────────┬────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
           │  Verified?   │     │  Geo-tagged? │     │   Recency    │
           │  +0.10       │     │  +0.05       │     │   Factor     │
           └──────────────┘     └──────────────┘     └──────────────┘
                                                              │
                                         ┌────────────────────┴────────────────────┐
                                         │                                         │
                              ┌──────────┴──────────┐                             │
                              │   Age < 5 min: 1.0  │                             │
                              │   Age 5-15 min: 0.9 │                             │
                              │   Age 15-30 min: 0.7│                             │
                              │   Age 30-60 min: 0.5│                             │
                              │   Age > 60 min: 0.3 │                             │
                              └─────────────────────┘                             │
                                         │                                         │
                                         ▼                                         │
                              ┌─────────────────────┐                             │
                              │  Calculate:         │                             │
                              │  weight × recency   │                             │
                              │  for each source    │                             │
                              └──────────┬──────────┘                             │
                                         │                                         │
                                         ▼                                         │
                              ┌─────────────────────┐                             │
                              │   Sum all weights   │                             │
                              │   Cap at 1.0 (100%) │                             │
                              └──────────┬──────────┘                             │
                                         │                                         │
                                         ▼                                         │
                    ┌────────────────────────────────────────┐                    │
                    │           CONFIDENCE LEVEL              │                    │
                    ├────────────────────────────────────────┤                    │
                    │  0.00 - 0.39  →  LOW     (Log only)    │                    │
                    │  0.40 - 0.69  →  MEDIUM  (Human review)│                    │
                    │  0.70 - 1.00  →  HIGH    (Auto-notify) │                    │
                    └────────────────────────────────────────┘                    │
```

---

# 3. CONTENT FILTERING PIPELINE

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          CONTENT FILTERING PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │   Raw Content In    │
                              │  (Title + Summary)  │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  FILTER 1: URL      │
                              │  Block Wikipedia,   │
                              │  IMDB, Cricbuzz,    │
                              │  Bollywood sites    │
                              └──────────┬──────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          │                             │
                     URL BLOCKED                   URL OK
                          │                             │
                          ▼                             ▼
                    ┌──────────┐              ┌─────────────────────┐
                    │  REJECT  │              │  FILTER 2: Content  │
                    └──────────┘              │  Block 60+ keywords │
                                              │  (movies, sports,   │
                                              │   military, etc.)   │
                                              └──────────┬──────────┘
                                                         │
                                          ┌──────────────┴──────────────┐
                                          │                             │
                                    KEYWORD FOUND               NO BLOCKED KEYWORD
                                          │                             │
                                          ▼                             ▼
                                    ┌──────────┐              ┌─────────────────────┐
                                    │  REJECT  │              │  FILTER 3: Emergency│
                                    └──────────┘              │  Must contain:      │
                                                              │  fire, flood, blast,│
                                                              │  accident, etc.     │
                                                              └──────────┬──────────┘
                                                                         │
                                                          ┌──────────────┴──────────────┐
                                                          │                             │
                                                   NO EMERGENCY                  HAS EMERGENCY
                                                     KEYWORD                       KEYWORD
                                                          │                             │
                                                          ▼                             ▼
                                                    ┌──────────┐              ┌─────────────────────┐
                                                    │  REJECT  │              │  FILTER 4: Location │
                                                    └──────────┘              │  Must be Karachi-   │
                                                                              │  related            │
                                                                              └──────────┬──────────┘
                                                                                         │
                                                                          ┌──────────────┴──────────────┐
                                                                          │                             │
                                                                    NOT KARACHI                    KARACHI
                                                                          │                             │
                                                                          ▼                             ▼
                                                                    ┌──────────┐              ┌─────────────────────┐
                                                                    │  REJECT  │              │  FILTER 5: Dedup    │
                                                                    └──────────┘              │  Already seen URL?  │
                                                                                              └──────────┬──────────┘
                                                                                                         │
                                                                                          ┌──────────────┴──────────────┐
                                                                                          │                             │
                                                                                       SEEN                         NEW
                                                                                          │                             │
                                                                                          ▼                             ▼
                                                                                    ┌──────────┐              ┌─────────────────────┐
                                                                                    │  SKIP    │              │     ✓ ACCEPT       │
                                                                                    └──────────┘              │  Create Source     │
                                                                                                              │  Add to seen_urls  │
                                                                                                              └─────────────────────┘
```

---

# 4. INCIDENT LIFECYCLE

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            INCIDENT LIFECYCLE                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   SOURCE    │  "Fire in Saddar market"
    │  DETECTED   │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │     INCIDENT CREATED                 │
    │                                      │
    │  ID: INC-2026-001                   │
    │  Type: FIRE                          │
    │  Location: saddar                    │
    │  Sources: 1                          │
    │  Confidence: 0.35 (LOW)              │
    │  Status: ACTIVE                      │
    └──────┬──────────────────────────────┘
           │
           │ More sources detected (within 30 min window)
           │
           ▼
    ┌─────────────────────────────────────┐
    │     SOURCES ADDED                    │
    │                                      │
    │  Sources: 3                          │
    │  Confidence: 0.72 (HIGH)             │
    │  + News confirmation                 │
    │  + Social corroboration              │
    └──────┬──────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │     ESCALATION TRIGGERED             │
    │                                      │
    │  → Discord notification sent         │
    │  → Dashboard updated                 │
    │  → Database logged                   │
    └──────┬──────────────────────────────┘
           │
           │ Time passes...
           │
           ▼
    ┌──────┴──────────────────────────────┐
    │            RESOLUTION                │
    │                                      │
    │  Option A: Resolved naturally        │
    │            (incident ends)           │
    │                                      │
    │  Option B: Marked FALSE POSITIVE     │
    │            → 30 min cooldown set     │
    │            → Won't alert again       │
    └─────────────────────────────────────┘
```

---

# 5. DASHBOARD DATA FLOW

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          DASHBOARD DATA FLOW                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

   BACKEND (Python)                              FRONTEND (Browser)
   ═══════════════                              ═════════════════

   ┌─────────────────┐                          ┌─────────────────┐
   │ FastAPI Server  │◀─── HTTP GET ────────────│  User opens     │
   │ localhost:8000  │                          │  browser        │
   └────────┬────────┘                          └────────┬────────┘
            │                                            │
            │ Send HTML                                  │
            ▼                                            ▼
   ┌─────────────────┐      HTML/JS/CSS        ┌─────────────────┐
   │ web_server.py   │─────────────────────────│  Dashboard      │
   │ returns full    │                          │  renders        │
   │ HTML document   │                          │  (Deck.gl map)  │
   └─────────────────┘                          └────────┬────────┘
                                                         │
                                                         │ Connect WebSocket
                                                         ▼
   ┌─────────────────┐                          ┌─────────────────┐
   │ WebSocket       │◀═══ WS Connection ═══════│  ws://          │
   │ /ws endpoint    │                          │  localhost:8000 │
   └────────┬────────┘                          │  /ws            │
            │                                   └────────┬────────┘
            │                                            │
            │ Every 60 seconds:                          │
            │                                            │
            ▼                                            │
   ┌─────────────────┐                                   │
   │ Generate        │                                   │
   │ dashboard_data: │                                   │
   │ • incidents[]   │                                   │
   │ • weather{}     │                                   │
   │ • stats{}       │                                   │
   └────────┬────────┘                                   │
            │                                            │
            │ Send JSON                                  │
            ▼                                            ▼
   ┌─────────────────┐      JSON message       ┌─────────────────┐
   │ ws.send_text()  │═══════════════════════▶│  onmessage()    │
   └─────────────────┘                          │  updateUI()     │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Update:         │
                                                │ • Incident feed │
                                                │ • Map markers   │
                                                │ • Weather panel │
                                                │ • System health │
                                                └─────────────────┘
```

---

# 6. DISCORD NOTIFICATION FLOW

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DISCORD NOTIFICATION FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │    Incident     │
                              │   Detected      │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Check Confidence│
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │     LOW      │  │    MEDIUM    │  │     HIGH     │
            │   (< 40%)    │  │  (40-69%)    │  │   (70%+)     │
            └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                   │                 │                 │
                   ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │   LOG ONLY   │  │ SEND ALERT   │  │ SEND ALERT   │
            │ No Discord   │  │ to Discord   │  │ to Discord   │
            └──────────────┘  └──────┬───────┘  └──────┬───────┘
                                     │                 │
                                     └────────┬────────┘
                                              │
                                              ▼
                              ┌─────────────────────────┐
                              │  Check Type             │
                              │  Is it UNKNOWN?         │
                              └───────────┬─────────────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                         UNKNOWN                 VALID TYPE
                              │                       │
                              ▼                       ▼
                       ┌──────────┐           ┌──────────────┐
                       │  SKIP    │           │ Check content│
                       │ (too     │           │ for blocked  │
                       │  vague)  │           │ keywords     │
                       └──────────┘           └──────┬───────┘
                                                     │
                                          ┌──────────┴──────────┐
                                          │                     │
                                      BLOCKED               ALLOWED
                                          │                     │
                                          ▼                     ▼
                                   ┌──────────┐         ┌──────────────┐
                                   │  SKIP    │         │ Build Embed  │
                                   └──────────┘         │ • Title      │
                                                        │ • Location   │
                                                        │ • Confidence │
                                                        │ • Sources    │
                                                        │ • Disclaimer │
                                                        └──────┬───────┘
                                                               │
                                                               ▼
                                                ┌──────────────────────┐
                                                │ POST to Webhook URL  │
                                                │ discord.com/api/     │
                                                │ webhooks/xxx/xxx     │
                                                └──────────┬───────────┘
                                                           │
                                                           ▼
                                                ┌──────────────────────┐
                                                │   Discord Channel    │
                                                │   Shows Alert        │
                                                └──────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════════

                              HEARTBEAT FLOW (Every 5 min)

                              ┌─────────────────┐
                              │  Timer Check    │
                              │  5 min passed?  │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Get current     │
                              │ status:         │
                              │ • Active alerts │
                              │ • Weather temp  │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Build Heartbeat │
                              │ • Status        │
                              │ • Temperature   │
                              │ • Time          │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ POST to Discord │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  "All clear"    │
                              │  or             │
                              │  "X alerts"     │
                              └─────────────────┘
```

---

**END OF FLOW DIAGRAMS**
