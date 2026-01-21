# SENTINEL-K PRODUCTION DEPLOYMENT GUIDE
## Quick Reference for Operations

---

# QUICK START (5 Minutes)

```bash
# 1. Install Python 3.10+
# 2. Clone and setup
cd D:\sentinel_k
pip install -r requirements.txt

# 3. Configure API keys in .env
# Required:
# - OPENWEATHERMAP_API_KEY
# - BRAVE_API_KEY
# - DISCORD_WEBHOOK_URL

# 4. Run
cd src
python main_enhanced.py

# 5. Open dashboard
# http://localhost:8000
```

---

# API KEYS CHECKLIST

| API | Required | Free Tier | Get From |
|-----|----------|-----------|----------|
| OpenWeatherMap | YES | 1000/day | openweathermap.org/api |
| Brave Search | YES | 2000/month | brave.com/search/api |
| Discord Webhook | YES | Unlimited | Discord Channel Settings |

---

# SYSTEM REQUIREMENTS

```
Minimum:
- CPU: 2 cores
- RAM: 2GB
- Storage: 1GB
- Network: Stable internet

Recommended:
- CPU: 4 cores
- RAM: 4GB
- Storage: 10GB
- Network: Low latency
```

---

# MONITORING

## Check System Status
```bash
# View real-time logs
tail -f Sentinel_Vault/logs/*.log

# Check database
sqlite3 Sentinel_Vault/sentinel_k.db "SELECT COUNT(*) FROM incidents;"

# Test API
curl http://localhost:8000/
```

## Discord Heartbeat
- Should receive message every 5 minutes
- Shows "All clear" or "X active alerts"
- If missing for 10+ min, system may be down

---

# COMMON ISSUES

| Issue | Solution |
|-------|----------|
| No Discord messages | Check DISCORD_WEBHOOK_URL in .env |
| "Brave API error" | Check BRAVE_API_KEY, may be rate limited |
| Dashboard not loading | Check port 8000 not in use |
| Old news appearing | Restart to clear cache |
| Wikipedia showing up | Should be filtered; restart backend |

---

# FILE LOCATIONS

```
sentinel_k/
├── .env                    # API keys (EDIT THIS)
├── src/main_enhanced.py    # Main entry point
├── Sentinel_Vault/         # Data storage
│   ├── incidents/          # Incident JSONs by date
│   └── sentinel_k.db       # SQLite database
└── specs/                  # Documentation
```

---

# EMERGENCY CONTACTS (Reference Only)

| Service | Number |
|---------|--------|
| Police | 15 |
| Rescue 1122 | 1122 |
| Edhi | 115 |

**REMINDER**: Sentinel-K does NOT dispatch emergencies!

---

# RESTART PROCEDURE

```bash
# 1. Kill existing process
taskkill /F /IM python.exe

# 2. Wait 2 seconds
timeout /t 2

# 3. Start fresh
cd D:\sentinel_k\src
python main_enhanced.py
```

---

# POLLING INTERVALS

| Source | Interval | Configurable |
|--------|----------|--------------|
| RSS Feeds | 5 min | Yes (.env) |
| Weather | 15 min | Yes (.env) |
| Social | 5 min | Yes (.env) |
| Heartbeat | 5 min | Hardcoded |
| Dashboard | 60 sec | Hardcoded |

---

**Document Version**: 1.0.0
**Last Updated**: January 2026
