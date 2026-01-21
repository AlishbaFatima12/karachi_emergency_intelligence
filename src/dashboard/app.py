"""
SENTINEL-K | Urban Intelligence Command Center
Advanced Streamlit Dashboard with PyDeck 3D Visualization
Architect: Syeda Alishba Fatima

Features:
- 3D PyDeck map with Google Maps-like interactivity
- AI Cognitive Stream (live terminal)
- Monsoon/Heatwave simulation modes
- 50+ Karachi neighborhood search
- Real-time incident monitoring
"""

import streamlit as st
import pydeck as pdk
import pandas as pd
import plotly.graph_objects as go
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path

# Import Karachi data
from karachi_data import (
    KARACHI_NEIGHBORHOODS,
    get_neighborhoods_df,
    search_neighborhood,
    get_flood_data,
    get_heat_data,
    AI_STREAM_MESSAGES,
    FLOOD_PRONE_AREAS,
    HEAT_HOTSPOTS
)

# Page config
st.set_page_config(
    page_title="SENTINEL-K | Urban Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for premium white theme
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Glassmorphism header */
    .main-header {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 20px 30px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.5);
    }

    .header-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1a1a2e;
        letter-spacing: -1px;
        margin: 0;
    }

    .header-subtitle {
        font-size: 0.85rem;
        color: #0052CC;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-top: 5px;
    }

    /* Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.6);
        margin-bottom: 15px;
    }

    .card-title {
        font-size: 0.7rem;
        font-weight: 600;
        color: #0052CC;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* AI Stream Terminal */
    .ai-stream {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 15px;
        height: 300px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #00ff88;
        border: 1px solid #2a2a4a;
    }

    .stream-line {
        padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        animation: fadeIn 0.3s ease-in;
    }

    .stream-time {
        color: #666;
        margin-right: 10px;
    }

    .stream-alert {
        color: #ff4b4b;
        font-weight: bold;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-10px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Incident Feed */
    .incident-feed {
        max-height: 400px;
        overflow-y: auto;
        padding-right: 10px;
    }

    .incident-item {
        background: #fff;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 4px solid #ccc;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .incident-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .incident-high {
        border-left-color: #ff4b4b;
        background: linear-gradient(90deg, #fff5f5 0%, #fff 100%);
    }

    .incident-medium {
        border-left-color: #ffa500;
        background: linear-gradient(90deg, #fffaf0 0%, #fff 100%);
    }

    .incident-low {
        border-left-color: #00c853;
        background: linear-gradient(90deg, #f0fff4 0%, #fff 100%);
    }

    .incident-type {
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        color: #1a1a2e;
    }

    .incident-location {
        font-size: 0.8rem;
        color: #666;
        margin-top: 4px;
    }

    .incident-meta {
        font-size: 0.7rem;
        color: #888;
        margin-top: 8px;
        font-family: 'JetBrains Mono', monospace;
    }

    .confidence-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.65rem;
        font-weight: 600;
        margin-left: 10px;
    }

    .badge-high { background: #ff4b4b; color: white; }
    .badge-medium { background: #ffa500; color: white; }
    .badge-low { background: #00c853; color: white; }

    /* Health Index Rings */
    .health-container {
        display: flex;
        justify-content: space-around;
        padding: 15px 0;
        margin-top: 10px;
    }

    .health-ring {
        text-align: center;
    }

    .health-value {
        font-size: 1.5rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    .health-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: #888;
        letter-spacing: 1px;
    }

    /* Weather Panel */
    .weather-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
    }

    .weather-item {
        text-align: center;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 12px;
    }

    .weather-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0052CC;
    }

    .weather-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: #888;
        letter-spacing: 1px;
    }

    /* Buttons */
    .sim-btn {
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
        border: none;
        margin: 5px;
    }

    .btn-monsoon {
        background: linear-gradient(135deg, #0052CC 0%, #00a8ff 100%);
        color: white;
    }

    .btn-heatwave {
        background: linear-gradient(135deg, #ff4b4b 0%, #ff8c00 100%);
        color: white;
    }

    /* Live Pulse */
    .live-pulse {
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(255,255,255,0.9);
        padding: 10px 20px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .pulse-dot {
        width: 10px;
        height: 10px;
        background: #00c853;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }

    .pulse-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #1a1a2e;
    }

    /* Search Box */
    .search-container input {
        background: #f8f9fa !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        font-size: 0.9rem !important;
    }

    .search-container input:focus {
        border-color: #0052CC !important;
        box-shadow: 0 0 0 3px rgba(0, 82, 204, 0.1) !important;
    }

    /* Disclaimer */
    .disclaimer {
        background: linear-gradient(90deg, #ff4b4b 0%, #ff6b6b 100%);
        color: white;
        padding: 12px 25px;
        border-radius: 25px;
        font-size: 0.75rem;
        font-weight: 600;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f0f0f0; border-radius: 3px; }
    ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #aaa; }

    /* Fix column spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    div[data-testid="stVerticalBlock"] > div {
        padding: 0;
    }
</style>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Initialize session state
if 'view_state' not in st.session_state:
    st.session_state.view_state = {
        'longitude': 67.0011,
        'latitude': 24.8607,
        'zoom': 11,
        'pitch': 45,
        'bearing': -20
    }

if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = 'normal'

if 'ai_stream' not in st.session_state:
    st.session_state.ai_stream = []

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Load incident data
def load_incidents():
    """Load incidents from dashboard_data.json"""
    vault_path = os.environ.get("SENTINEL_VAULT_PATH", "Sentinel_Vault")
    data_file = Path(__file__).parent.parent.parent / vault_path / "config" / "dashboard_data.json"

    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    return {
        "incidents": [],
        "weather": {"temperature_c": 23, "humidity_percent": 45, "wind_kmh": 12, "rain_1h_mm": 0},
        "active_alerts": 0
    }

# Get map data based on simulation mode
def get_map_data():
    """Get data for PyDeck visualization"""
    if st.session_state.simulation_mode == 'monsoon':
        return get_flood_data()
    elif st.session_state.simulation_mode == 'heatwave':
        return get_heat_data()
    else:
        return get_neighborhoods_df()

# Create PyDeck layers
def create_map_layers(data, incidents):
    """Create PyDeck layers with tooltips"""
    layers = []

    # Simulation-specific styling
    if st.session_state.simulation_mode == 'monsoon':
        # Flood columns
        layers.append(pdk.Layer(
            'ColumnLayer',
            data=data,
            get_position='[lon, lat]',
            get_elevation='water_level * 50',
            elevation_scale=1,
            radius=400,
            get_fill_color='color',
            pickable=True,
            auto_highlight=True,
            extruded=True,
        ))
    elif st.session_state.simulation_mode == 'heatwave':
        # Heat hexagons
        layers.append(pdk.Layer(
            'ColumnLayer',
            data=data,
            get_position='[lon, lat]',
            get_elevation='temperature * 30',
            elevation_scale=1,
            radius=500,
            get_fill_color='color',
            pickable=True,
            auto_highlight=True,
            extruded=True,
        ))
    else:
        # Normal mode - district columns
        df = data.copy()
        df['color'] = df['risk_level'].apply(lambda x:
            [255, 75, 75, 200] if x == 'HIGH' else
            [255, 165, 0, 200] if x == 'MEDIUM' else
            [0, 82, 204, 180]
        )
        df['elevation'] = df['incidents'].apply(lambda x: max(30, x * 20 + 30))

        layers.append(pdk.Layer(
            'ColumnLayer',
            data=df,
            get_position='[lon, lat]',
            get_elevation='elevation',
            elevation_scale=50,
            radius=350,
            get_fill_color='color',
            pickable=True,
            auto_highlight=True,
            extruded=True,
        ))

    # Incident markers
    if incidents:
        incident_data = []
        for inc in incidents:
            coords = search_neighborhood(inc.get('location', 'Saddar'))
            if coords:
                incident_data.append({
                    'lon': coords[0],
                    'lat': coords[1],
                    'type': inc.get('type', 'unknown'),
                    'level': inc.get('level', 'LOW'),
                    'confidence': inc.get('confidence', 0.5),
                    'sources': inc.get('sources', 1),
                    'color': [255, 0, 0, 255] if inc.get('level') == 'HIGH' else [255, 165, 0, 255]
                })

        if incident_data:
            layers.append(pdk.Layer(
                'ScatterplotLayer',
                data=incident_data,
                get_position='[lon, lat]',
                get_fill_color='color',
                get_radius=800,
                pickable=True,
                auto_highlight=True,
                highlight_color=[255, 255, 0, 200],
            ))

    return layers

# Main layout
def main():
    data = load_incidents()
    incidents = data.get('incidents', [])
    weather = data.get('weather', {})

    # Header with Live Pulse
    col_header, col_pulse = st.columns([4, 1])

    with col_header:
        st.markdown("""
        <div class="main-header">
            <h1 class="header-title">SENTINEL-K</h1>
            <p class="header-subtitle">Urban Intelligence Architect: Syeda Alishba Fatima</p>
        </div>
        """, unsafe_allow_html=True)

    with col_pulse:
        current_time = datetime.now().strftime("%H:%M:%S PKT")
        current_date = datetime.now().strftime("%d %b %Y")
        st.markdown(f"""
        <div class="live-pulse" style="margin-top: 20px;">
            <div class="pulse-dot"></div>
            <div>
                <div class="pulse-time">{current_time}</div>
                <div style="font-size: 0.7rem; color: #666;">{current_date}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Refresh", key="refresh_btn"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()

    # Control bar
    col_search, col_sim1, col_sim2, col_reset = st.columns([3, 1, 1, 1])

    with col_search:
        search_query = st.text_input(
            "Search Neighborhood",
            placeholder="Type: DHA Phase 6, Gulshan Block 13, Lyari...",
            key="search_input",
            label_visibility="collapsed"
        )

        if search_query:
            coords = search_neighborhood(search_query)
            if coords:
                st.session_state.view_state = {
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'zoom': 14,
                    'pitch': 50,
                    'bearing': 0
                }
                st.success(f"📍 Navigating to {search_query}")

    with col_sim1:
        if st.button("🌊 Monsoon Mode", key="monsoon_btn", use_container_width=True):
            st.session_state.simulation_mode = 'monsoon'
            st.rerun()

    with col_sim2:
        if st.button("🔥 Heatwave Mode", key="heat_btn", use_container_width=True):
            st.session_state.simulation_mode = 'heatwave'
            st.rerun()

    with col_reset:
        if st.button("🔄 Normal", key="normal_btn", use_container_width=True):
            st.session_state.simulation_mode = 'normal'
            st.session_state.view_state = {
                'longitude': 67.0011,
                'latitude': 24.8607,
                'zoom': 11,
                'pitch': 45,
                'bearing': -20
            }
            st.rerun()

    # Show current mode
    mode_colors = {'normal': '#0052CC', 'monsoon': '#0088ff', 'heatwave': '#ff4b4b'}
    mode_labels = {'normal': 'NORMAL', 'monsoon': 'MONSOON SIMULATION', 'heatwave': 'HEATWAVE SIMULATION'}
    st.markdown(f"""
    <div style="text-align: center; margin: 10px 0;">
        <span style="background: {mode_colors[st.session_state.simulation_mode]}; color: white;
                     padding: 5px 15px; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">
            MODE: {mode_labels[st.session_state.simulation_mode]}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Main content - 3 columns
    col_left, col_center, col_right = st.columns([1.2, 2.5, 1.3])

    # LEFT COLUMN - AI Stream + Weather
    with col_left:
        # AI Cognitive Stream
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">AI_COGNITIVE_STREAM</div>', unsafe_allow_html=True)

        # Generate stream messages
        stream_html = '<div class="ai-stream">'
        current_messages = random.sample(AI_STREAM_MESSAGES, min(12, len(AI_STREAM_MESSAGES)))
        for i, msg in enumerate(current_messages):
            time_str = (datetime.now()).strftime("%H:%M:%S")
            is_alert = 'alert' in msg.lower() or 'detect' in msg.lower()
            css_class = 'stream-alert' if is_alert else ''
            stream_html += f'''
            <div class="stream-line {css_class}">
                <span class="stream-time">[{time_str}]</span> {msg}
            </div>
            '''
        stream_html += '</div>'
        st.markdown(stream_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Weather Panel
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">KARACHI_WEATHER_INDEX</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="weather-grid">
            <div class="weather-item">
                <div class="weather-value">{weather.get("temperature_c", "--")}°C</div>
                <div class="weather-label">Temperature</div>
            </div>
            <div class="weather-item">
                <div class="weather-value">{weather.get("humidity_percent", "--")}%</div>
                <div class="weather-label">Humidity</div>
            </div>
            <div class="weather-item">
                <div class="weather-value">{weather.get("wind_kmh", "--")}</div>
                <div class="weather-label">Wind km/h</div>
            </div>
            <div class="weather-item">
                <div class="weather-value">{weather.get("rain_1h_mm", 0)}</div>
                <div class="weather-label">Rain mm</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # CENTER COLUMN - 3D Map
    with col_center:
        st.markdown('<div class="glass-card" style="padding: 10px;">', unsafe_allow_html=True)

        map_data = get_map_data()
        layers = create_map_layers(map_data, incidents)

        # Map style based on simulation mode
        if st.session_state.simulation_mode == 'monsoon':
            map_style = 'mapbox://styles/mapbox/dark-v10'
        elif st.session_state.simulation_mode == 'heatwave':
            map_style = 'mapbox://styles/mapbox/satellite-streets-v11'
        else:
            map_style = 'mapbox://styles/mapbox/light-v10'

        # Create PyDeck chart with tooltip
        tooltip = {
            "html": """
            <div style="background: rgba(0,0,0,0.8); padding: 15px; border-radius: 10px;
                        font-family: 'Inter', sans-serif; min-width: 200px;">
                <div style="font-weight: 700; font-size: 14px; color: #fff; margin-bottom: 8px;">
                    📍 {name}
                </div>
                <div style="color: #aaa; font-size: 12px;">
                    Risk Level: <span style="color: #ff4b4b; font-weight: 600;">{risk_level}</span>
                </div>
                <div style="color: #aaa; font-size: 12px; margin-top: 4px;">
                    Confidence: {confidence:.0%}
                </div>
            </div>
            """,
            "style": {"backgroundColor": "transparent", "color": "white"}
        }

        view_state = pdk.ViewState(
            longitude=st.session_state.view_state['longitude'],
            latitude=st.session_state.view_state['latitude'],
            zoom=st.session_state.view_state['zoom'],
            pitch=st.session_state.view_state['pitch'],
            bearing=st.session_state.view_state['bearing']
        )

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style=map_style,
            tooltip=tooltip
        )

        st.pydeck_chart(deck, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT COLUMN - Health Index + Incidents
    with col_right:
        # System Health Index
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">SYSTEM_HEALTH_INDEX</div>', unsafe_allow_html=True)

        # Calculate health metrics
        high_count = len([i for i in incidents if i.get('level') == 'HIGH'])
        bronze_val = 82 if incidents else 50
        silver_val = min(71 + high_count * 5, 100)
        gold_val = min(24 + high_count * 15, 100)

        # Create donut charts with Plotly
        fig = go.Figure()

        # Create 3 mini donut charts side by side
        colors_bronze = ['#0052CC', '#f0f0f0']
        colors_silver = ['#C0C0C0', '#f0f0f0']
        colors_gold = ['#FFD700', '#f0f0f0']

        fig.add_trace(go.Pie(
            values=[bronze_val, 100-bronze_val],
            hole=0.7,
            marker_colors=colors_bronze,
            textinfo='none',
            domain={'x': [0, 0.3], 'y': [0, 1]},
            showlegend=False
        ))

        fig.add_trace(go.Pie(
            values=[silver_val, 100-silver_val],
            hole=0.7,
            marker_colors=colors_silver,
            textinfo='none',
            domain={'x': [0.35, 0.65], 'y': [0, 1]},
            showlegend=False
        ))

        fig.add_trace(go.Pie(
            values=[gold_val, 100-gold_val],
            hole=0.7,
            marker_colors=colors_gold,
            textinfo='none',
            domain={'x': [0.7, 1], 'y': [0, 1]},
            showlegend=False
        ))

        # Add annotations for values
        fig.add_annotation(x=0.15, y=0.5, text=f"{bronze_val}%", showarrow=False,
                          font=dict(size=16, color='#0052CC', family='JetBrains Mono'))
        fig.add_annotation(x=0.15, y=0.1, text="BRONZE", showarrow=False,
                          font=dict(size=8, color='#888'))

        fig.add_annotation(x=0.5, y=0.5, text=f"{silver_val}%", showarrow=False,
                          font=dict(size=16, color='#888', family='JetBrains Mono'))
        fig.add_annotation(x=0.5, y=0.1, text="SILVER", showarrow=False,
                          font=dict(size=8, color='#888'))

        fig.add_annotation(x=0.85, y=0.5, text=f"{gold_val}%", showarrow=False,
                          font=dict(size=16, color='#B8860B', family='JetBrains Mono'))
        fig.add_annotation(x=0.85, y=0.1, text="GOLD", showarrow=False,
                          font=dict(size=8, color='#888'))

        fig.update_layout(
            height=150,
            margin=dict(l=0, r=0, t=0, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Live Incident Feed
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">LIVE_INCIDENT_FEED</div>', unsafe_allow_html=True)

        incidents_html = '<div class="incident-feed">'

        if not incidents:
            incidents_html += '''
            <div style="text-align: center; padding: 30px; color: #888;">
                <div style="font-size: 2rem; margin-bottom: 10px;">✓</div>
                <div>No active incidents</div>
            </div>
            '''
        else:
            emojis = {
                'fire': '🔥', 'flood': '🌊', 'explosion': '💥',
                'shooting': '⚠️', 'traffic': '🚗', 'power_outage': '⚡',
                'heatwave': '🌡️', 'protest': '📢', 'unknown': '📡'
            }

            for inc in incidents[:8]:  # Show max 8 incidents
                level = inc.get('level', 'LOW').lower()
                inc_type = inc.get('type', 'unknown')
                emoji = emojis.get(inc_type, '📡')

                incidents_html += f'''
                <div class="incident-item incident-{level}">
                    <div class="incident-type">
                        {emoji} {inc_type}
                        <span class="confidence-badge badge-{level}">{inc.get('level', 'LOW')}</span>
                    </div>
                    <div class="incident-location">📍 {inc.get('location', 'Karachi')}</div>
                    <div class="incident-meta">
                        {inc.get('sources', 1)} sources | {inc.get('confidence', 0.5)*100:.0f}% confidence | {inc.get('time', '--:--')}
                    </div>
                </div>
                '''

        incidents_html += '</div>'
        st.markdown(incidents_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        ⚠️ VERIFY FIRST: Automated early-warning system. NOT an emergency dispatcher.
        For emergencies: Police 15 | Rescue 1122 | Edhi 115
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
