"""
Karachi Neighborhoods Data
Comprehensive coordinates for 50+ areas in Karachi
For Sentinel-K Urban Intelligence Dashboard
"""

import pandas as pd
from typing import Dict, List, Tuple

# Karachi Neighborhoods with coordinates
KARACHI_NEIGHBORHOODS: Dict[str, Tuple[float, float]] = {
    # DHA Phases
    "DHA Phase 1": (67.0321, 24.8010),
    "DHA Phase 2": (67.0456, 24.7985),
    "DHA Phase 3": (67.0512, 24.7920),
    "DHA Phase 4": (67.0589, 24.7890),
    "DHA Phase 5": (67.0712, 24.8050),
    "DHA Phase 6": (67.0681, 24.8286),
    "DHA Phase 7": (67.0890, 24.8150),
    "DHA Phase 8": (67.1050, 24.8200),

    # Clifton
    "Clifton Block 1": (67.0320, 24.8120),
    "Clifton Block 2": (67.0380, 24.8100),
    "Clifton Block 3": (67.0420, 24.8080),
    "Clifton Block 4": (67.0467, 24.8043),
    "Clifton Block 5": (67.0510, 24.8010),
    "Sea View": (67.0280, 24.8050),

    # Gulshan-e-Iqbal
    "Gulshan Block 1": (67.0850, 24.9100),
    "Gulshan Block 2": (67.0880, 24.9120),
    "Gulshan Block 3": (67.0910, 24.9140),
    "Gulshan Block 4": (67.0924, 24.9180),
    "Gulshan Block 5": (67.0960, 24.9200),
    "Gulshan Block 6": (67.0990, 24.9220),
    "Gulshan Block 7": (67.1020, 24.9250),
    "Gulshan Block 8": (67.1050, 24.9280),
    "Gulshan Block 9": (67.1080, 24.9310),
    "Gulshan Block 10": (67.1110, 24.9340),
    "Gulshan Block 11": (67.1140, 24.9370),
    "Gulshan Block 12": (67.1170, 24.9400),
    "Gulshan Block 13": (67.1200, 24.9430),

    # Nazimabad
    "Nazimabad Block 1": (67.0250, 24.9250),
    "Nazimabad Block 2": (67.0280, 24.9270),
    "Nazimabad Block 3": (67.0300, 24.9300),
    "Nazimabad Block 4": (67.0320, 24.9320),
    "Nazimabad Block 5": (67.0350, 24.9350),
    "North Nazimabad": (67.0380, 24.9400),

    # Central Areas
    "Saddar": (67.0011, 24.8607),
    "Saddar Bazaar": (67.0050, 24.8590),
    "I.I. Chundrigar Road": (67.0080, 24.8520),
    "Bolton Market": (67.0030, 24.8580),
    "Empress Market": (66.9980, 24.8610),
    "Burns Garden": (66.9950, 24.8590),

    # Lyari
    "Lyari": (66.9880, 24.8680),
    "Kalakot": (66.9850, 24.8700),
    "Chakiwara": (66.9820, 24.8720),
    "Agra Taj Colony": (66.9900, 24.8650),

    # Korangi
    "Korangi": (67.1147, 24.8315),
    "Korangi Industrial Area": (67.1200, 24.8350),
    "Korangi Crossing": (67.1100, 24.8280),
    "Landhi": (67.1350, 24.8400),

    # SITE Area
    "SITE": (66.9700, 24.8800),
    "SITE Industrial Area": (66.9650, 24.8850),
    "Manghopir": (66.9500, 24.9000),

    # Malir
    "Malir": (67.2000, 24.8900),
    "Malir Cantt": (67.2100, 24.8850),
    "Malir City": (67.1950, 24.8950),
    "Model Colony": (67.1800, 24.8800),

    # North Karachi
    "North Karachi": (67.0600, 24.9600),
    "Surjani Town": (67.0450, 24.9700),
    "New Karachi": (67.0550, 24.9550),

    # Orangi
    "Orangi Town": (66.9600, 24.9200),
    "Orangi Sector 5": (66.9550, 24.9250),
    "Orangi Sector 11": (66.9650, 24.9150),

    # Federal B Area
    "FB Area": (67.0400, 24.9150),
    "FB Area Block 1": (67.0380, 24.9130),
    "FB Area Block 10": (67.0450, 24.9180),

    # Shah Faisal
    "Shah Faisal Colony": (67.1000, 24.8700),
    "Shah Faisal Town": (67.0950, 24.8650),

    # Gulistan-e-Jauhar
    "Gulistan-e-Jauhar Block 1": (67.1100, 24.9000),
    "Gulistan-e-Jauhar Block 7": (67.1180, 24.9050),
    "Gulistan-e-Jauhar Block 13": (67.1250, 24.9100),
    "Gulistan-e-Jauhar Block 14": (67.1280, 24.9130),

    # Bahria Town
    "Bahria Town Karachi": (67.2500, 24.9200),
    "Bahria Sports City": (67.2600, 24.9250),

    # Garden
    "Garden East": (67.0100, 24.8700),
    "Garden West": (67.0050, 24.8720),
    "Parsi Colony": (67.0120, 24.8680),

    # Kemari
    "Kemari": (66.9800, 24.8500),
    "Keamari Town": (66.9750, 24.8520),

    # Hospitals (Key Landmarks)
    "Aga Khan Hospital": (67.1143, 24.9144),
    "Jinnah Hospital": (67.0150, 24.8630),
    "Civil Hospital": (67.0080, 24.8600),
    "Liaquat National Hospital": (67.0080, 24.9100),

    # Universities
    "Karachi University": (67.1200, 24.9400),
    "NED University": (67.1100, 24.9350),
    "FAST University": (67.0700, 24.9050),

    # Airports & Ports
    "Jinnah International Airport": (67.1608, 24.9065),
    "Port Qasim": (67.3500, 24.7800),
    "Karachi Port": (66.9900, 24.8400),

    # Beaches
    "Hawkes Bay": (66.8500, 24.8700),
    "Sandspit Beach": (66.8800, 24.8550),
    "French Beach": (66.8200, 24.8900),
}

# Risk levels for simulation
RISK_LEVELS = {
    "CRITICAL": {"color": [255, 0, 0, 200], "elevation": 150},
    "HIGH": {"color": [255, 75, 75, 200], "elevation": 120},
    "MEDIUM": {"color": [255, 165, 0, 200], "elevation": 80},
    "LOW": {"color": [0, 200, 100, 180], "elevation": 40},
    "SAFE": {"color": [0, 82, 204, 150], "elevation": 20},
}

# Flood prone areas (for Monsoon simulation)
FLOOD_PRONE_AREAS = [
    "Lyari", "Orangi Town", "Korangi", "Malir", "Surjani Town",
    "SITE", "Landhi", "Kemari", "Saddar", "Garden East",
    "Gulshan Block 13", "FB Area", "North Karachi"
]

# Heat hotspots (for Heatwave simulation)
HEAT_HOTSPOTS = [
    "Korangi Industrial Area", "SITE Industrial Area", "Landhi",
    "Saddar", "Bolton Market", "Lyari", "Orangi Town",
    "Malir", "New Karachi", "Surjani Town"
]

def get_neighborhoods_df() -> pd.DataFrame:
    """Get all neighborhoods as a DataFrame"""
    data = []
    for name, (lon, lat) in KARACHI_NEIGHBORHOODS.items():
        data.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "risk_level": "LOW",
            "incidents": 0,
            "confidence": 0.5
        })
    return pd.DataFrame(data)

def search_neighborhood(query: str) -> Tuple[float, float] | None:
    """Search for a neighborhood and return coordinates"""
    query_lower = query.lower().strip()
    for name, coords in KARACHI_NEIGHBORHOODS.items():
        if query_lower in name.lower():
            return coords
    return None

def get_flood_data() -> pd.DataFrame:
    """Get flood simulation data"""
    data = []
    for name, (lon, lat) in KARACHI_NEIGHBORHOODS.items():
        is_flood_prone = name in FLOOD_PRONE_AREAS
        data.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "flood_risk": "HIGH" if is_flood_prone else "LOW",
            "water_level": 80 if is_flood_prone else 20,
            "color": [0, 100, 255, 200] if is_flood_prone else [0, 150, 255, 100]
        })
    return pd.DataFrame(data)

def get_heat_data() -> pd.DataFrame:
    """Get heatwave simulation data"""
    data = []
    for name, (lon, lat) in KARACHI_NEIGHBORHOODS.items():
        is_hotspot = name in HEAT_HOTSPOTS
        data.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "heat_level": "CRITICAL" if is_hotspot else "MODERATE",
            "temperature": 48 if is_hotspot else 38,
            "color": [255, 50, 0, 220] if is_hotspot else [255, 165, 0, 150]
        })
    return pd.DataFrame(data)

# AI Cognitive Stream messages
AI_STREAM_MESSAGES = [
    "Initializing urban scan protocol...",
    "Analyzing traffic patterns on Sharae Faisal...",
    "Detecting heat signature in Orangi Town...",
    "Cross-referencing social media signals...",
    "Monitoring water levels in Lyari Nullah...",
    "Processing RSS feed from Dawn News...",
    "Signal detected in Saddar Sector 4...",
    "Correlating weather data with incident reports...",
    "Scanning for Roman Urdu keywords: 'aag', 'dhamaaka'...",
    "Evaluating confidence threshold: 91%...",
    "Alerting Aga Khan Trauma Center...",
    "Analyzing monsoon cloud formation...",
    "Checking CCTV feeds from Korangi Crossing...",
    "Processing emergency call data...",
    "Triangulating incident location...",
    "Verifying source credibility: HIGH...",
    "Updating risk matrix for DHA Phase 6...",
    "Dispatching virtual scout to Malir...",
    "Computing evacuation routes...",
    "Syncing with Rescue 1122 database...",
    "Analyzing building structural data...",
    "Monitoring power grid status...",
    "Checking gas pipeline integrity...",
    "Processing satellite imagery...",
    "Evaluating crowd density in Saddar...",
]
