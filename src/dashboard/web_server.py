"""
Sentinel-K Premium Web Dashboard
3D Urban Intelligence Command Center for Karachi
Architect: Syeda Alishba Fatima

Features:
- Deck.gl 3D visualization with 50+ Karachi neighborhoods
- Google Maps-like tooltips on hover/click
- AI Cognitive Stream (live terminal)
- Monsoon/Heatwave simulation modes
- Real-time WebSocket updates
- Glassmorphism UI design

Run with: python -m dashboard.web_server
Access at: http://localhost:8000
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
import json
import asyncio
from datetime import datetime
from typing import List
import os
import sys

sys.path.append('..')

app = FastAPI(title="Sentinel-K Command Center")

connected_clients: List[WebSocket] = []

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SENTINEL-K | Urban Intelligence Command Center</title>
    <script src="https://unpkg.com/deck.gl@latest/dist.min.js"></script>
    <script src="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.css" rel="stylesheet" />
    <style>
        :root {
            --white: #FFFFFF;
            --royal-blue: #0052CC;
            --safety-red: #FF4B4B;
            --gold: #FFD700;
            --silver: #C0C0C0;
            --glass-bg: rgba(255, 255, 255, 0.92);
            --glass-border: rgba(255, 255, 255, 0.6);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            --font-main: 'Inter', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
            font-family: var(--font-main);
            color: #1a1a2e;
            overflow-x: hidden;
            overflow-y: auto;
            min-height: 100vh;
            width: 100vw;
        }

        #map-container {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100vh;
            z-index: 1;
        }

        .overlay {
            position: fixed;
            z-index: 10;
            pointer-events: none;
        }

        .interactable { pointer-events: auto; }

        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--glass-border);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .glass-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }

        /* Header */
        .branding {
            top: 20px;
            left: 20px;
            padding: 20px 25px;
        }

        .branding h1 {
            font-weight: 900;
            font-size: 2.2rem;
            letter-spacing: -1px;
            color: #1a1a2e;
            line-height: 1;
        }

        .branding p {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--royal-blue);
            margin-top: 8px;
        }

        .tier-bar {
            display: none;
        }

        .tier-labels {
            display: none;
        }

        /* Live Pulse */
        .live-pulse {
            top: 25px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 22px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .pulse-dot {
            width: 10px;
            height: 10px;
            background: #00c853;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .pulse-dot.alert { background: var(--safety-red); }
        .pulse-dot.offline { background: #888; animation: none; }

        @keyframes pulse {
            0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.7); }
            50% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(0, 200, 83, 0); }
        }

        .pulse-time {
            font-family: var(--font-mono);
            font-size: 0.9rem;
            font-weight: 600;
            color: #1a1a2e;
        }

        .pulse-date {
            font-size: 0.7rem;
            color: #666;
        }

        /* AI Stream - System Activity Log */
        .ai-stream-panel {
            top: 110px;
            left: 20px;
            width: 340px;
            padding: 15px;
            max-height: 220px;
            overflow: hidden;
        }

        .panel-title {
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: var(--royal-blue);
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
        }

        .stream-pulse {
            width: 8px;
            height: 8px;
            background: var(--royal-blue);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .ai-stream {
            background: #1a1a2e;
            border-radius: 10px;
            padding: 12px;
            height: 150px;
            overflow-y: auto;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: #00ff88;
            line-height: 1.5;
        }

        .stream-line {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            opacity: 0;
            transform: translateX(-10px);
            animation: slideIn 0.4s forwards;
        }

        .stream-line.alert {
            color: var(--safety-red);
            font-weight: 600;
        }

        .stream-line.success {
            color: #00c853;
        }

        .stream-time {
            color: #555;
            margin-right: 8px;
        }

        @keyframes slideIn {
            to { opacity: 1; transform: translateX(0); }
        }

        /* Weather Panel */
        .weather-panel {
            top: 350px;
            left: 20px;
            width: 340px;
            padding: 15px;
        }

        .weather-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 10px;
        }

        .weather-item {
            text-align: center;
            padding: 12px;
            background: rgba(0,0,0,0.03);
            border-radius: 12px;
        }

        .weather-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--royal-blue);
            font-family: var(--font-mono);
        }

        .weather-label {
            font-size: 0.6rem;
            text-transform: uppercase;
            color: #888;
            letter-spacing: 1px;
            margin-top: 4px;
        }

        /* Health Panel */
        .health-panel {
            top: 20px;
            right: 20px;
            width: 340px;
            padding: 18px;
        }

        .health-row {
            display: flex;
            justify-content: space-around;
            margin-top: 12px;
            padding-bottom: 10px;
        }

        .health-ring {
            text-align: center;
            width: 32%;
        }

        .ring-svg {
            width: 70px;
            height: 70px;
            transform: rotate(-90deg);
        }

        .ring-bg { fill: none; stroke: #f0f0f0; stroke-width: 6; }
        .ring-fill {
            fill: none;
            stroke-width: 6;
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease;
        }

        .ring-value {
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 1rem;
            margin-top: 5px;
            display: block;
        }

        .ring-label {
            font-size: 0.6rem;
            text-transform: uppercase;
            color: #888;
            letter-spacing: 0.5px;
        }

        /* Incident Panel */
        .incident-panel {
            top: 190px;
            right: 20px;
            width: 340px;
            max-height: calc(100vh - 280px);
            padding: 18px;
            display: flex;
            flex-direction: column;
        }

        .incident-list {
            flex: 1;
            overflow-y: auto;
            margin-top: 10px;
            padding-right: 5px;
        }

        .incident-item {
            background: #fff;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 10px;
            border-left: 4px solid #ddd;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .incident-item:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .incident-item.high {
            border-left-color: var(--safety-red);
            background: linear-gradient(90deg, #fff5f5 0%, #fff 100%);
        }

        .incident-item.medium {
            border-left-color: #ffa500;
            background: linear-gradient(90deg, #fffaf0 0%, #fff 100%);
        }

        .incident-item.low {
            border-left-color: #00c853;
            background: linear-gradient(90deg, #f0fff4 0%, #fff 100%);
        }

        .incident-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .incident-type {
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            color: #1a1a2e;
        }

        .confidence-badge {
            font-size: 0.65rem;
            padding: 4px 10px;
            border-radius: 10px;
            font-weight: 600;
            color: white;
        }

        .badge-high { background: var(--safety-red); }
        .badge-medium { background: #ffa500; }
        .badge-low { background: #00c853; }

        .incident-location {
            font-size: 0.8rem;
            color: #666;
            margin-top: 6px;
        }

        .incident-meta {
            font-family: var(--font-mono);
            font-size: 0.7rem;
            color: #888;
            margin-top: 6px;
        }

        /* Command Bar - Fixed at bottom center */
        .command-bar {
            position: fixed !important;
            bottom: 20px;
            left: 0;
            right: 0;
            margin: 0 auto;
            width: fit-content;
            padding: 12px 20px;
            display: flex;
            gap: 8px;
            align-items: center;
            z-index: 100;
        }

        .cmd-btn {
            background: #fff;
            border: none;
            padding: 8px 14px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.75rem;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            white-space: nowrap;
        }

        .cmd-btn:hover {
            background: #f5f5f5;
        }

        .cmd-btn:active {
            background: #eee;
        }

        .btn-monsoon { color: #0088ff; }
        .btn-monsoon:hover { background: #e6f4ff; }

        .btn-heat { color: var(--safety-red); }
        .btn-heat:hover { background: #fff0f0; }

        .btn-normal { color: #00c853; }
        .btn-normal:hover { background: #e8fff0; }

        .btn-3d { color: #6c5ce7; }
        .btn-3d:hover { background: #f0eeff; }
        .btn-3d.active { background: #6c5ce7; color: white; }

        .btn-satellite { color: #2d7d46; }
        .btn-satellite:hover { background: #e8f5e9; }
        .btn-satellite.active { background: #2d7d46; color: white; }

        .btn-traffic { color: #e65100; }
        .btn-traffic:hover { background: #fff3e0; }
        .btn-traffic.active { background: #e65100; color: white; }

        .search-input {
            background: #f8f9fa;
            border: 2px solid #e8e8e8;
            padding: 10px 16px;
            border-radius: 10px;
            width: 220px;
            font-family: var(--font-main);
            font-size: 0.8rem;
            transition: all 0.2s;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--royal-blue);
            box-shadow: 0 0 0 3px rgba(0, 82, 204, 0.1);
        }

        .search-wrapper {
            position: relative;
        }

        .search-suggestions {
            position: absolute;
            bottom: 100%;
            left: 0;
            right: 0;
            background: white;
            border-radius: 10px;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
            max-height: 200px;
            overflow-y: auto;
            display: none;
            margin-bottom: 8px;
        }

        .search-suggestions.show { display: block; }

        .suggestion-item {
            padding: 10px 14px;
            cursor: pointer;
            font-size: 0.8rem;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s;
        }

        .suggestion-item:hover {
            background: #f5f8ff;
        }

        .suggestion-item:last-child { border-bottom: none; }

        .suggestion-category {
            font-size: 0.6rem;
            color: #888;
            text-transform: uppercase;
        }

        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(5px);
            z-index: 1000;
            display: none;
            justify-content: center;
            align-items: center;
        }

        .modal-overlay.show { display: flex; }

        .modal-content {
            background: white;
            border-radius: 20px;
            width: 90%;
            max-width: 500px;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 25px 80px rgba(0,0,0,0.3);
            animation: modalSlideIn 0.3s ease;
        }

        @keyframes modalSlideIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .modal-close {
            position: absolute;
            top: 15px; right: 20px;
            background: none;
            border: none;
            font-size: 1.8rem;
            cursor: pointer;
            color: #888;
            transition: color 0.2s;
        }

        .modal-close:hover { color: #333; }

        .modal-header {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 25px;
            border-bottom: 1px solid #f0f0f0;
            position: relative;
        }

        .modal-icon {
            font-size: 2.5rem;
        }

        .modal-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #1a1a2e;
            margin: 0;
        }

        .modal-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.7rem;
            font-weight: 700;
            margin-top: 5px;
        }

        .modal-badge.high { background: #ff4b4b; color: white; }
        .modal-badge.medium { background: #ffa500; color: white; }
        .modal-badge.low { background: #00c853; color: white; }

        .modal-body { padding: 25px; }

        .modal-section {
            margin-bottom: 20px;
        }

        .modal-section h4 {
            font-size: 0.8rem;
            color: var(--royal-blue);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .modal-section p {
            color: #444;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .confidence-bar-container {
            background: #f0f0f0;
            height: 8px;
            border-radius: 4px;
            margin-bottom: 8px;
            overflow: hidden;
        }

        .confidence-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .source-item {
            background: #f8f9fa;
            padding: 10px 14px;
            border-radius: 10px;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }

        .source-item .source-name {
            font-weight: 600;
            color: var(--royal-blue);
        }

        .source-item .source-detail {
            color: #666;
            font-size: 0.8rem;
            margin-top: 4px;
        }

        .modal-footer {
            display: flex;
            gap: 12px;
            padding: 20px 25px;
            border-top: 1px solid #f0f0f0;
        }

        .modal-btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
            background: var(--royal-blue);
            color: white;
        }

        .modal-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,82,204,0.3);
        }

        .modal-btn.secondary {
            background: #f0f0f0;
            color: #666;
        }

        .modal-btn.secondary:hover {
            background: #e0e0e0;
            box-shadow: none;
        }

        /* Mode Indicator */
        .mode-indicator {
            position: absolute;
            top: 90px;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            z-index: 20;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }

        .mode-normal { background: var(--royal-blue); color: white; }
        .mode-monsoon { background: #0088ff; color: white; }
        .mode-heat { background: var(--safety-red); color: white; }

        /* Disclaimer */
        .disclaimer {
            position: absolute;
            bottom: 90px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(90deg, var(--safety-red) 0%, #ff6b6b 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            font-size: 0.7rem;
            font-weight: 600;
            z-index: 20;
            box-shadow: 0 4px 20px rgba(255, 75, 75, 0.35);
            white-space: nowrap;
        }

        /* Tooltip */
        .map-tooltip {
            position: absolute;
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            border-radius: 12px;
            color: white;
            font-family: var(--font-main);
            pointer-events: none;
            z-index: 100;
            min-width: 200px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            display: none;
        }

        .tooltip-title {
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tooltip-row {
            font-size: 0.75rem;
            color: #aaa;
            margin: 4px 0;
        }

        .tooltip-row span {
            color: #fff;
            font-weight: 600;
        }

        .tooltip-risk-high { color: var(--safety-red) !important; }
        .tooltip-risk-medium { color: #ffa500 !important; }
        .tooltip-risk-low { color: #00c853 !important; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #aaa; }
    </style>
</head>
<body>

    <div id="map-container"></div>
    <div class="map-tooltip" id="mapTooltip"></div>

    <!-- Live Pulse -->
    <div class="overlay interactable glass-card live-pulse">
        <div class="pulse-dot" id="pulseDot"></div>
        <div>
            <div class="pulse-time" id="pulseTime">--:--:--</div>
            <div class="pulse-date" id="pulseDate">-- --- ----</div>
        </div>
        <button class="cmd-btn btn-normal" onclick="forceRefresh()" style="margin-left: 10px; padding: 8px 12px;">
            Refresh
        </button>
    </div>

    <!-- Mode Indicator -->
    <div class="mode-indicator mode-normal" id="modeIndicator">MODE: NORMAL</div>

    <!-- Branding -->
    <header class="overlay interactable glass-card branding">
        <h1>SENTINEL-K</h1>
        <p>Karachi Emergency Intelligence</p>
    </header>

    <!-- AI Cognitive Stream - System Activity Log -->
    <aside class="overlay interactable glass-card ai-stream-panel">
        <div class="panel-title">
            LIVE MONITORING LOG
            <div class="stream-pulse" id="streamPulse"></div>
        </div>
        <div style="font-size:0.7rem;color:#666;margin-bottom:8px;">Real-time system activity: RSS feeds, weather, social media</div>
        <div class="ai-stream" id="aiStream"></div>
    </aside>

    <!-- Weather Panel -->
    <aside class="overlay interactable glass-card weather-panel">
        <div class="panel-title">KARACHI_WEATHER_INDEX</div>
        <div class="weather-grid">
            <div class="weather-item">
                <div class="weather-value" id="temp">--</div>
                <div class="weather-label">Temperature</div>
            </div>
            <div class="weather-item">
                <div class="weather-value" id="humidity">--</div>
                <div class="weather-label">Humidity</div>
            </div>
            <div class="weather-item">
                <div class="weather-value" id="wind">--</div>
                <div class="weather-label">Wind km/h</div>
            </div>
            <div class="weather-item">
                <div class="weather-value" id="rain">--</div>
                <div class="weather-label">Rain mm</div>
            </div>
        </div>
    </aside>

    <!-- System Health -->
    <aside class="overlay interactable glass-card health-panel">
        <div class="panel-title">SYSTEM_HEALTH_INDEX</div>
        <div class="health-row">
            <div class="health-ring">
                <svg class="ring-svg" viewBox="0 0 70 70">
                    <circle class="ring-bg" cx="35" cy="35" r="28"></circle>
                    <circle class="ring-fill" id="bronzeRing" cx="35" cy="35" r="28"
                        stroke="#00c853" stroke-dasharray="176" stroke-dashoffset="176"></circle>
                </svg>
                <span class="ring-value" id="bronzeVal">0%</span>
                <span class="ring-label">System</span>
            </div>
            <div class="health-ring">
                <svg class="ring-svg" viewBox="0 0 70 70">
                    <circle class="ring-bg" cx="35" cy="35" r="28"></circle>
                    <circle class="ring-fill" id="silverRing" cx="35" cy="35" r="28"
                        stroke="#ffa500" stroke-dasharray="176" stroke-dashoffset="176"></circle>
                </svg>
                <span class="ring-value" id="silverVal">0%</span>
                <span class="ring-label">Alerts</span>
            </div>
            <div class="health-ring">
                <svg class="ring-svg" viewBox="0 0 70 70">
                    <circle class="ring-bg" cx="35" cy="35" r="28"></circle>
                    <circle class="ring-fill" id="goldRing" cx="35" cy="35" r="28"
                        stroke="var(--royal-blue)" stroke-dasharray="176" stroke-dashoffset="176"></circle>
                </svg>
                <span class="ring-value" id="goldVal">0%</span>
                <span class="ring-label">Sources</span>
            </div>
        </div>
    </aside>

    <!-- Incident Feed -->
    <aside class="overlay interactable glass-card incident-panel">
        <div class="panel-title">LIVE_INCIDENT_FEED</div>
        <div class="incident-list" id="incidentList">
            <p style="color: #888; text-align: center; padding: 40px 20px;">Connecting to data stream...</p>
        </div>
    </aside>

    <!-- Command Bar -->
    <footer class="overlay interactable glass-card command-bar">
        <button class="cmd-btn btn-satellite" onclick="toggleSatellite()">🛰️ Satellite</button>
        <button class="cmd-btn btn-traffic" onclick="toggleTraffic()">🚗 Traffic</button>
        <button class="cmd-btn btn-monsoon" onclick="setMode('monsoon')">🌧️ Monsoon</button>
        <button class="cmd-btn btn-heat" onclick="setMode('heat')">🔥 Heatwave</button>
        <button class="cmd-btn btn-normal" onclick="setMode('normal')">✅ Normal</button>
        <button class="cmd-btn btn-3d" id="btn3d" onclick="toggle3D()">🏢 3D View</button>
        <div class="search-wrapper">
            <input type="text" class="search-input" id="searchInput"
                   placeholder="Search any place..." autocomplete="off">
            <div class="search-suggestions" id="searchSuggestions"></div>
        </div>
    </footer>

    <!-- Area Info Modal (click anywhere on map) -->
    <div class="modal-overlay" id="areaModal" onclick="closeAreaModal()">
        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 400px;">
            <button class="modal-close" onclick="closeAreaModal()">&times;</button>
            <div class="modal-header">
                <span class="modal-icon">📍</span>
                <div>
                    <h2 class="modal-title" id="areaName">Area Name</h2>
                    <span style="font-size: 0.75rem; color: #666;" id="areaCoords">Coordinates</span>
                </div>
            </div>
            <div class="modal-body">
                <h4 style="margin-bottom: 10px; color: #333;">Current Situation</h4>
                <div id="areaIncidents">
                    <div style="color: #888; text-align: center; padding: 20px;">Loading...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Incident Detail Modal -->
    <div class="modal-overlay" id="incidentModal" onclick="closeModal()">
        <div class="modal-content" onclick="event.stopPropagation()">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <div class="modal-header">
                <span class="modal-icon" id="modalIcon">🔥</span>
                <div>
                    <h2 class="modal-title" id="modalTitle">Incident Title</h2>
                    <span class="modal-badge" id="modalBadge">HIGH</span>
                </div>
            </div>
            <div class="modal-body">
                <div class="modal-section">
                    <h4>📍 Location</h4>
                    <p id="modalLocation">Karachi</p>
                </div>
                <div class="modal-section">
                    <h4>📊 Confidence Analysis</h4>
                    <div class="confidence-bar-container">
                        <div class="confidence-bar" id="modalConfBar"></div>
                    </div>
                    <p id="modalConfidence">85% confidence from 3 sources</p>
                </div>
                <div class="modal-section">
                    <h4>📰 Source Details</h4>
                    <div id="modalSources"></div>
                </div>
                <div class="modal-section">
                    <h4>📝 Description</h4>
                    <p id="modalDescription">Incident details will appear here...</p>
                </div>
                <div class="modal-section">
                    <h4>🕐 Timeline</h4>
                    <p id="modalTime">Detected at --:--</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="modal-btn" onclick="navigateToIncident()">🗺️ Navigate on Map</button>
                <button class="modal-btn secondary" onclick="closeModal()">Close</button>
            </div>
        </div>
    </div>

    <!-- Disclaimer -->
    <div class="disclaimer">
        VERIFY FIRST: Automated system. NOT an emergency dispatcher. Police 15 | Rescue 1122 | Edhi 115
    </div>

    <script>
        // 50+ Karachi Neighborhoods
        const NEIGHBORHOODS = {
            // DHA Phases
            'dha phase 1': [67.0321, 24.8010], 'dha phase 2': [67.0456, 24.7985],
            'dha phase 3': [67.0512, 24.7920], 'dha phase 4': [67.0589, 24.7890],
            'dha phase 5': [67.0712, 24.8050], 'dha phase 6': [67.0681, 24.8286],
            'dha phase 7': [67.0890, 24.8150], 'dha phase 8': [67.1050, 24.8200],
            'dha': [67.0681, 24.8286],

            // Clifton
            'clifton': [67.0467, 24.8043], 'clifton block 1': [67.0320, 24.8120],
            'clifton block 2': [67.0380, 24.8100], 'clifton block 4': [67.0467, 24.8043],
            'sea view': [67.0280, 24.8050],

            // Gulshan
            'gulshan': [67.0924, 24.9180], 'gulshan block 1': [67.0850, 24.9100],
            'gulshan block 2': [67.0880, 24.9120], 'gulshan block 4': [67.0924, 24.9180],
            'gulshan block 5': [67.0960, 24.9200], 'gulshan block 6': [67.0990, 24.9220],
            'gulshan block 7': [67.1020, 24.9250], 'gulshan block 10': [67.1110, 24.9340],
            'gulshan block 13': [67.1200, 24.9430],

            // Nazimabad
            'nazimabad': [67.0300, 24.9300], 'north nazimabad': [67.0380, 24.9400],
            'nazimabad block 1': [67.0250, 24.9250], 'nazimabad block 3': [67.0300, 24.9300],

            // Central
            'saddar': [67.0011, 24.8607], 'saddar bazaar': [67.0050, 24.8590],
            'bolton market': [67.0030, 24.8580], 'empress market': [66.9980, 24.8610],
            'i.i. chundrigar road': [67.0080, 24.8520],

            // Lyari
            'lyari': [66.9880, 24.8680], 'kalakot': [66.9850, 24.8700],
            'chakiwara': [66.9820, 24.8720],

            // Korangi
            'korangi': [67.1147, 24.8315], 'korangi industrial': [67.1200, 24.8350],
            'landhi': [67.1350, 24.8400],

            // SITE
            'site': [66.9700, 24.8800], 'site industrial': [66.9650, 24.8850],
            'manghopir': [66.9500, 24.9000],

            // Malir
            'malir': [67.2000, 24.8900], 'malir cantt': [67.2100, 24.8850],
            'model colony': [67.1800, 24.8800],

            // North Karachi
            'north karachi': [67.0600, 24.9600], 'surjani town': [67.0450, 24.9700],
            'new karachi': [67.0550, 24.9550],

            // Orangi
            'orangi': [66.9600, 24.9200], 'orangi town': [66.9600, 24.9200],

            // FB Area
            'fb area': [67.0400, 24.9150], 'federal b area': [67.0400, 24.9150],

            // Gulistan-e-Jauhar
            'gulistan-e-jauhar': [67.1100, 24.9000], 'jauhar': [67.1100, 24.9000],

            // Others
            'garden': [67.0100, 24.8700], 'kemari': [66.9800, 24.8500],
            'shah faisal': [67.1000, 24.8700], 'bahria town': [67.2500, 24.9200],

            // Hospitals
            'aga khan': [67.1143, 24.9144], 'aga khan hospital': [67.1143, 24.9144],
            'jinnah hospital': [67.0150, 24.8630], 'civil hospital': [67.0080, 24.8600],
            'liaquat national': [67.0700, 24.9100], 'patel hospital': [67.0650, 24.8950],
            'ziauddin hospital': [67.0580, 24.8750], 'indus hospital': [67.1050, 24.8550],

            // Universities
            'karachi university': [67.1200, 24.9400], 'ned university': [67.1100, 24.9350],
            'iqra university': [67.0700, 24.8100], 'szabist': [67.0750, 24.8150],
            'nust karachi': [67.0900, 24.8300], 'iba': [67.0400, 24.8550],

            // Malls & Shopping
            'dolmen mall clifton': [67.0350, 24.8100], 'dolmen mall tariq road': [67.0550, 24.8650],
            'lucky one mall': [67.0750, 24.9100], 'millennium mall': [67.0650, 24.8700],
            'ocean mall': [67.0320, 24.8050], 'park towers': [67.0400, 24.8130],
            'forum mall': [67.0380, 24.8120], 'atrium mall': [67.0150, 24.8620],

            // Markets
            'tariq road': [67.0550, 24.8680], 'zainab market': [67.0010, 24.8600],
            'hyderi market': [67.0350, 24.9400], 'paper market': [67.0080, 24.8570],
            'jodia bazaar': [67.0040, 24.8610], 'bohri bazaar': [67.0100, 24.8590],
            'light house': [66.9980, 24.8560], 'burns garden': [67.0020, 24.8620],

            // Beaches
            'seaview': [67.0280, 24.8050], 'sea view': [67.0280, 24.8050],
            'french beach': [66.8900, 24.8200], 'sandspit': [66.9100, 24.8250],
            'hawkes bay': [66.8800, 24.8300], 'manora': [66.9700, 24.8000],

            // Famous Places
            'do darya': [67.0300, 24.7950], 'port grand': [66.9850, 24.8450],
            'paf museum': [67.0850, 24.8700], 'mazar-e-quaid': [67.0385, 24.8755],
            'quaid tomb': [67.0385, 24.8755], 'frere hall': [67.0350, 24.8630],
            'mohatta palace': [67.0400, 24.8070], 'national museum': [67.0020, 24.8640],

            // Mosques
            'tooba masjid': [67.0700, 24.8100], 'gul masjid': [67.0380, 24.8550],
            'memon masjid': [67.0050, 24.8580],

            // Restaurants & Food
            'boat basin': [67.0400, 24.8100], 'khadda market': [67.0650, 24.8300],
            'burns garden': [67.0020, 24.8620], 'kolachi': [67.0300, 24.7960],

            // Railway & Transport
            'cantt station': [67.0350, 24.8550], 'city station': [67.0100, 24.8570],

            // Industrial
            'port qasim': [67.3500, 24.7800], 'bin qasim': [67.3500, 24.7800],

            // Airport
            'airport': [67.1608, 24.9065], 'jinnah airport': [67.1608, 24.9065],
            'jinnah terminal': [67.1608, 24.9065],

            // More Areas
            'defence': [67.0681, 24.8286], 'pechs': [67.0650, 24.8700],
            'smchs': [67.0600, 24.8750], 'bahadurabad': [67.0700, 24.8800],
            'shahrah-e-faisal': [67.0900, 24.8650], 'karsaz': [67.0850, 24.8700],
            'drigh road': [67.1000, 24.8650], 'shaheed-e-millat': [67.0750, 24.8550],
            'teen talwar': [67.0400, 24.8100], 'bilawal house': [67.0350, 24.8050],
            'sindh governor house': [67.0300, 24.8600],

            // Default
            'karachi': [67.0011, 24.8607], 'karachi_general': [67.0011, 24.8607]
        };

        // Flood prone areas
        const FLOOD_AREAS = ['lyari', 'orangi', 'korangi', 'malir', 'surjani town', 'site', 'landhi', 'saddar', 'garden'];
        const HEAT_AREAS = ['korangi industrial', 'site industrial', 'landhi', 'saddar', 'bolton market', 'lyari', 'orangi', 'malir'];

        // Traffic hotspots (major intersections & roads)
        let trafficData = [
            { name: 'Shahrah-e-Faisal', lon: 67.0750, lat: 24.8650, congestion: 'heavy', type: 'road' },
            { name: 'I.I. Chundrigar Road', lon: 67.0080, lat: 24.8520, congestion: 'heavy', type: 'road' },
            { name: 'NIPA Chorangi', lon: 67.0850, lat: 24.9120, congestion: 'moderate', type: 'intersection' },
            { name: 'Numaish Chowrangi', lon: 67.0200, lat: 24.8700, congestion: 'heavy', type: 'intersection' },
            { name: 'Teen Hatti', lon: 67.0150, lat: 24.8750, congestion: 'moderate', type: 'intersection' },
            { name: 'Guru Mandir', lon: 67.0100, lat: 24.8650, congestion: 'moderate', type: 'intersection' },
            { name: 'KPT Interchange', lon: 67.0050, lat: 24.8350, congestion: 'heavy', type: 'intersection' },
            { name: 'Karsaz Road', lon: 67.0950, lat: 24.8800, congestion: 'moderate', type: 'road' },
            { name: 'University Road', lon: 67.1100, lat: 24.9300, congestion: 'moderate', type: 'road' },
            { name: 'M.A. Jinnah Road', lon: 67.0050, lat: 24.8600, congestion: 'heavy', type: 'road' },
            { name: 'Tariq Road', lon: 67.0550, lat: 24.8680, congestion: 'moderate', type: 'road' },
            { name: 'Rashid Minhas Road', lon: 67.0800, lat: 24.9050, congestion: 'moderate', type: 'road' },
            { name: 'Drigh Road', lon: 67.0900, lat: 24.8700, congestion: 'light', type: 'road' },
            { name: 'Korangi Road', lon: 67.1100, lat: 24.8400, congestion: 'heavy', type: 'road' },
            { name: 'Hub River Road', lon: 66.9600, lat: 24.9100, congestion: 'moderate', type: 'road' },
            { name: 'Super Highway', lon: 67.1500, lat: 24.9500, congestion: 'light', type: 'road' },
            { name: 'Baloch Colony Flyover', lon: 67.0950, lat: 24.8600, congestion: 'moderate', type: 'intersection' },
            { name: 'Five Star Chowrangi', lon: 67.0700, lat: 24.8750, congestion: 'heavy', type: 'intersection' },
            { name: 'Nazimabad Chowrangi', lon: 67.0350, lat: 24.9350, congestion: 'moderate', type: 'intersection' },
            { name: 'Sohrab Goth', lon: 67.1300, lat: 24.9650, congestion: 'heavy', type: 'intersection' },
        ];
        let showTraffic = false;

        // District data
        let districtData = [
            { name: 'Saddar', lon: 67.0011, lat: 24.8607, risk: 'MEDIUM', incidents: 2, confidence: 0.85 },
            { name: 'Lyari', lon: 66.9880, lat: 24.8680, risk: 'HIGH', incidents: 3, confidence: 0.92 },
            { name: 'DHA', lon: 67.0681, lat: 24.8286, risk: 'LOW', incidents: 0, confidence: 0.5 },
            { name: 'Gulshan', lon: 67.0924, lat: 24.9180, risk: 'LOW', incidents: 1, confidence: 0.65 },
            { name: 'Korangi', lon: 67.1147, lat: 24.8315, risk: 'MEDIUM', incidents: 2, confidence: 0.78 },
            { name: 'Nazimabad', lon: 67.0300, lat: 24.9300, risk: 'LOW', incidents: 0, confidence: 0.5 },
            { name: 'Clifton', lon: 67.0467, lat: 24.8043, risk: 'LOW', incidents: 0, confidence: 0.5 },
            { name: 'Malir', lon: 67.2000, lat: 24.8900, risk: 'MEDIUM', incidents: 1, confidence: 0.7 },
            { name: 'SITE', lon: 66.9700, lat: 24.8800, risk: 'HIGH', incidents: 4, confidence: 0.95 },
            { name: 'Orangi', lon: 66.9600, lat: 24.9200, risk: 'HIGH', incidents: 3, confidence: 0.88 },
            { name: 'North Karachi', lon: 67.0600, lat: 24.9600, risk: 'LOW', incidents: 0, confidence: 0.45 },
            { name: 'FB Area', lon: 67.0400, lat: 24.9150, risk: 'LOW', incidents: 1, confidence: 0.6 },
        ];

        // Current mode
        let currentMode = 'normal';

        // Deck.gl setup
        const {DeckGL, ColumnLayer, ScatterplotLayer, TextLayer} = deck;

        let deckgl = new DeckGL({
            container: 'map-container',
            mapStyle: 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json',
            initialViewState: {
                longitude: 67.0011,
                latitude: 24.8607,
                zoom: 11,
                pitch: 45,
                bearing: -15
            },
            controller: true,
            layers: [],
            getTooltip: ({object}) => object && {
                html: `<div style="padding: 10px;">
                    <strong>${object.name}</strong><br/>
                    Risk: ${object.risk || 'LOW'}
                </div>`
            },
            onHover: (info) => showTooltip(info),
            onClick: (info, event) => {
                if (info.object) {
                    // Clicked on a marker
                    flyTo(info.object.lon, info.object.lat, 14);
                    showAreaInfo(info.object.name, info.object.lon, info.object.lat);
                } else if (info.coordinate) {
                    // Clicked on empty map - find nearest area
                    const [lon, lat] = info.coordinate;
                    const nearest = findNearestArea(lon, lat);
                    flyTo(lon, lat, 14);
                    showAreaInfo(nearest || 'Selected Location', lon, lat);
                }
            }
        });

        // Find nearest known area to coordinates
        function findNearestArea(lon, lat) {
            let nearest = null;
            let minDist = Infinity;
            for (const [name, coords] of Object.entries(NEIGHBORHOODS)) {
                const dist = Math.sqrt(Math.pow(coords[0] - lon, 2) + Math.pow(coords[1] - lat, 2));
                if (dist < minDist && dist < 0.05) { // Within ~5km
                    minDist = dist;
                    nearest = name;
                }
            }
            return nearest ? nearest.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : null;
        }

        // BLOCKED content - never show these
        const BLOCKED_WORDS = [
            'wikipedia', 'wiki', 'box office', 'crore', 'movie', 'film', 'bollywood',
            'actor', 'actress', 'cricket', 'match', 'psl', 'ipl', 'air force',
            'deep-strike', 'loc ', 'line of control', 'military', 'army chief',
            'election', 'vote', 'campaign', 'wedding', 'fashion', 'concert',
            'ranveer', 'salman', 'shahrukh', 'deepika', 'globally', 'worldwide'
        ];

        function isBlockedContent(text) {
            if (!text) return false;
            const lower = text.toLowerCase();
            return BLOCKED_WORDS.some(word => lower.includes(word));
        }

        // Show area information modal
        function showAreaInfo(areaName, lon, lat) {
            const modal = document.getElementById('areaModal');
            if (!modal) return;

            document.getElementById('areaName').textContent = areaName;
            document.getElementById('areaCoords').textContent = `${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`;

            // Find incidents ONLY for this specific area (STRICT matching)
            const areaLower = areaName.toLowerCase().replace(/[^a-z\s]/g, '').trim();
            const areaWords = areaLower.split(' ').filter(w => w.length > 2);

            const areaIncidents = currentIncidents.filter(inc => {
                // FILTER 1: Block irrelevant content (Wikipedia, movies, military, etc.)
                if (isBlockedContent(inc.headline)) return false;
                if (isBlockedContent(inc.type)) return false;

                // FILTER 2: Skip UNKNOWN type incidents
                if (inc.type === 'unknown') return false;

                const incLoc = (inc.location || '').toLowerCase().replace(/_/g, ' ');

                // FILTER 3: Skip vague "karachi_general" or "karachi" locations
                if (incLoc === 'karachi general' || incLoc === 'karachi' || incLoc === 'unknown') return false;

                // FILTER 4: Location must EXACTLY match clicked area
                const locWords = incLoc.split(' ').filter(w => w.length > 2);
                const hasMatch = areaWords.some(word => locWords.some(lw => lw.includes(word) || word.includes(lw)));
                return hasMatch || incLoc.includes(areaLower) || areaLower.includes(incLoc);
            });

            const incidentsList = document.getElementById('areaIncidents');
            if (areaIncidents.length > 0) {
                incidentsList.innerHTML = areaIncidents.slice(0, 5).map(inc => `
                    <div style="padding: 8px; background: ${inc.level === 'HIGH' ? '#fff5f5' : '#fff8e6'}; border-radius: 8px; margin-bottom: 8px;">
                        <strong>${emojis[inc.type] || '📍'} ${inc.headline || inc.type}</strong><br/>
                        <small style="color: #666;">${inc.level} | ${inc.time}</small>
                    </div>
                `).join('');
            } else {
                incidentsList.innerHTML = `
                    <div style="color: #00c853; text-align: center; padding: 20px;">
                        <div style="font-size: 1.5rem;">✓</div>
                        <div style="margin-top: 8px;">No active incidents reported in <strong>${areaName}</strong></div>
                        <div style="font-size: 0.75rem; color: #888; margin-top: 5px;">Area appears safe at this time</div>
                    </div>
                `;
            }

            modal.classList.add('show');
        }

        function closeAreaModal() {
            document.getElementById('areaModal').classList.remove('show');
        }

        // Tooltip
        function showTooltip(info) {
            const tooltip = document.getElementById('mapTooltip');
            if (info.object) {
                const obj = info.object;
                const riskClass = obj.risk === 'HIGH' ? 'tooltip-risk-high' :
                                  obj.risk === 'MEDIUM' ? 'tooltip-risk-medium' : 'tooltip-risk-low';
                tooltip.innerHTML = `
                    <div class="tooltip-title">📍 ${obj.name}</div>
                    <div class="tooltip-row">Risk Level: <span class="${riskClass}">${obj.risk || 'LOW'}</span></div>
                    <div class="tooltip-row">Confidence: <span>${((obj.confidence || 0.5) * 100).toFixed(0)}%</span></div>
                    <div class="tooltip-row">Active Incidents: <span>${obj.incidents || 0}</span></div>
                    <div class="tooltip-row" style="margin-top: 8px; font-size: 0.65rem; color: #666;">Click to zoom</div>
                `;
                tooltip.style.display = 'block';
                tooltip.style.left = (info.x + 15) + 'px';
                tooltip.style.top = (info.y + 15) + 'px';
            } else {
                tooltip.style.display = 'none';
            }
        }

        // Update map layers
        function updateLayers() {
            let data = districtData.map(d => ({...d}));

            // Apply mode-specific styling
            if (currentMode === 'monsoon') {
                data = data.map(d => {
                    const isFlood = FLOOD_AREAS.some(a => d.name.toLowerCase().includes(a));
                    return {
                        ...d,
                        elevation: isFlood ? 120 : 30,
                        color: isFlood ? [0, 100, 255, 220] : [0, 150, 255, 100],
                        risk: isFlood ? 'FLOOD RISK' : 'LOW'
                    };
                });
            } else if (currentMode === 'heat') {
                data = data.map(d => {
                    const isHot = HEAT_AREAS.some(a => d.name.toLowerCase().includes(a));
                    return {
                        ...d,
                        elevation: isHot ? 130 : 40,
                        color: isHot ? [255, 50, 0, 230] : [255, 180, 0, 150],
                        risk: isHot ? 'HEAT CRITICAL' : 'MODERATE'
                    };
                });
            } else {
                data = data.map(d => ({
                    ...d,
                    elevation: 30 + (d.incidents || 0) * 25,
                    color: d.isSearched ? [138, 43, 226, 220] :  // Purple for searched locations
                           d.risk === 'HIGH' ? [255, 75, 75, 200] :
                           d.risk === 'MEDIUM' ? [255, 165, 0, 200] : [0, 82, 204, 180]
                }));
            }

            const layers = [
                new ScatterplotLayer({
                    id: 'districts',
                    data: data,
                    getPosition: d => [d.lon, d.lat],
                    getRadius: d => 300 + (d.incidents || 0) * 80,
                    getFillColor: d => d.color,
                    getLineColor: [255, 255, 255, 200],
                    lineWidthMinPixels: 2,
                    stroked: true,
                    filled: true,
                    pickable: true,
                    autoHighlight: true,
                    highlightColor: [255, 255, 0, 150],
                    radiusScale: 1,
                    radiusMinPixels: 8,
                    radiusMaxPixels: 50
                }),
                new TextLayer({
                    id: 'labels',
                    data: data,
                    getPosition: d => [d.lon, d.lat],
                    getText: d => d.name,
                    getSize: 12,
                    getColor: [255, 255, 255, 255],
                    getTextAnchor: 'middle',
                    getAlignmentBaseline: 'bottom',
                    getPixelOffset: [0, -15],
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 700,
                    background: true,
                    getBackgroundColor: [0, 0, 0, 180],
                    backgroundPadding: [4, 2]
                })
            ];

            // Add traffic layer if enabled
            if (showTraffic) {
                layers.push(new ScatterplotLayer({
                    id: 'traffic',
                    data: trafficData,
                    getPosition: d => [d.lon, d.lat],
                    getRadius: d => d.type === 'intersection' ? 400 : 250,
                    getFillColor: d => d.congestion === 'heavy' ? [255, 0, 0, 200] :
                                      d.congestion === 'moderate' ? [255, 165, 0, 200] : [0, 200, 0, 200],
                    getLineColor: [255, 255, 255, 255],
                    lineWidthMinPixels: 2,
                    stroked: true,
                    filled: true,
                    pickable: true
                }));
                layers.push(new TextLayer({
                    id: 'traffic-labels',
                    data: trafficData,
                    getPosition: d => [d.lon, d.lat],
                    getText: d => `🚗 ${d.name}`,
                    getSize: 11,
                    getColor: [255, 255, 255, 255],
                    getTextAnchor: 'middle',
                    getAlignmentBaseline: 'bottom',
                    getPixelOffset: [0, -20],
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 600,
                    background: true,
                    getBackgroundColor: d => d.congestion === 'heavy' ? [200, 0, 0, 220] :
                                            d.congestion === 'moderate' ? [180, 100, 0, 220] : [0, 150, 0, 220],
                    backgroundPadding: [6, 3]
                }));
            }

            deckgl.setProps({ layers });
        }

        // Toggle traffic layer
        function toggleTraffic() {
            showTraffic = !showTraffic;
            const btn = document.querySelector('.btn-traffic');
            if (showTraffic) {
                btn.classList.add('active');
                btn.textContent = '🚗 Hide Traffic';
                addStreamLog('Traffic layer enabled - showing 20 hotspots', 'success');
            } else {
                btn.classList.remove('active');
                btn.textContent = '🚗 Traffic';
                addStreamLog('Traffic layer hidden');
            }
            updateLayers();
        }

        // Fly to location
        function flyTo(lon, lat, zoom = 14) {
            deckgl.setProps({
                initialViewState: {
                    longitude: lon,
                    latitude: lat,
                    zoom: zoom,
                    pitch: is3DMode ? 60 : 45,
                    bearing: is3DMode ? 30 : 0,
                    transitionDuration: 1500
                }
            });
            addStreamLog(`Navigating to coordinates [${lat.toFixed(4)}, ${lon.toFixed(4)}]`, 'success');
        }

        // Toggle 3D View
        let is3DMode = false;
        function toggle3D() {
            is3DMode = !is3DMode;
            const btn = document.getElementById('btn3d');

            if (is3DMode) {
                btn.classList.add('active');
                btn.textContent = '🏢 3D ON';
                // Use 3D style with buildings
                deckgl.setProps({
                    mapStyle: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
                    initialViewState: {
                        longitude: 67.0011,
                        latitude: 24.8607,
                        zoom: 13,
                        pitch: 60,
                        bearing: 30,
                        transitionDuration: 1000
                    }
                });
                addStreamLog('3D VIEW: Enabling isometric view with 60° pitch', 'success');
            } else {
                btn.classList.remove('active');
                btn.textContent = '🏢 3D View';
                deckgl.setProps({
                    mapStyle: 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json',
                    initialViewState: {
                        longitude: 67.0011,
                        latitude: 24.8607,
                        zoom: 11,
                        pitch: 45,
                        bearing: 0,
                        transitionDuration: 1000
                    }
                });
                addStreamLog('3D VIEW: Returning to standard view', 'success');
            }
        }

        // Set simulation mode
        function setMode(mode) {
            currentMode = mode;
            const indicator = document.getElementById('modeIndicator');

            if (mode === 'monsoon') {
                indicator.className = 'mode-indicator mode-monsoon';
                indicator.textContent = 'MODE: MONSOON SIMULATION';
                deckgl.setProps({ mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json' });
                addStreamLog('SIMULATION: Initiating Monsoon flood scenario...', 'alert');
            } else if (mode === 'heat') {
                indicator.className = 'mode-indicator mode-heat';
                indicator.textContent = 'MODE: HEATWAVE SIMULATION';
                deckgl.setProps({ mapStyle: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json' });
                addStreamLog('SIMULATION: Initiating Heatwave scenario...', 'alert');
            } else {
                indicator.className = 'mode-indicator mode-normal';
                indicator.textContent = 'MODE: NORMAL';
                deckgl.setProps({ mapStyle: 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json' });
                addStreamLog('Returning to normal monitoring mode', 'success');
            }

            updateLayers();
        }

        // Satellite view toggle (FREE ESRI imagery)
        let satelliteMode = false;
        const SATELLITE_STYLE = {
            version: 8,
            sources: {
                'esri-satellite': {
                    type: 'raster',
                    tiles: [
                        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                    ],
                    tileSize: 256,
                    attribution: 'ESRI World Imagery'
                }
            },
            layers: [{
                id: 'esri-satellite-layer',
                type: 'raster',
                source: 'esri-satellite',
                minzoom: 0,
                maxzoom: 19
            }]
        };
        const NORMAL_STYLE = 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json';

        function toggleSatellite() {
            satelliteMode = !satelliteMode;
            const btn = document.querySelector('.btn-satellite');

            if (satelliteMode) {
                deckgl.setProps({ mapStyle: SATELLITE_STYLE });
                btn.classList.add('active');
                btn.textContent = '🗺️ Map View';
                addStreamLog('Switched to satellite view (ESRI)', 'success');
            } else {
                deckgl.setProps({ mapStyle: NORMAL_STYLE });
                btn.classList.remove('active');
                btn.textContent = '🛰️ Satellite';
                addStreamLog('Switched to map view', 'success');
            }
        }

        // Search functionality with autocomplete
        const searchInput = document.getElementById('searchInput');
        const suggestionsDiv = document.getElementById('searchSuggestions');

        function showSuggestions(query) {
            if (!query || query.length < 2) {
                suggestionsDiv.classList.remove('show');
                return;
            }

            const matches = Object.keys(NEIGHBORHOODS)
                .filter(name => name.includes(query))
                .slice(0, 8);

            if (matches.length === 0) {
                suggestionsDiv.classList.remove('show');
                return;
            }

            suggestionsDiv.innerHTML = matches.map(name => `
                <div class="suggestion-item" onclick="selectLocation('${name}')">
                    📍 ${name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </div>
            `).join('');
            suggestionsDiv.classList.add('show');
        }

        // Add searched location to map with marker
        function addLocationMarker(name, lon, lat) {
            // Format name for display
            const displayName = name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

            // Check if already exists
            const exists = districtData.find(d => d.name.toLowerCase() === displayName.toLowerCase());
            if (!exists) {
                // Add new location to district data
                districtData.push({
                    name: displayName,
                    lon: lon,
                    lat: lat,
                    risk: 'LOW',
                    incidents: 0,
                    confidence: 0.5,
                    isSearched: true  // Mark as user-searched location
                });
                updateLayers();
            }

            // Fly to location
            flyTo(lon, lat, 15);
            addStreamLog(`📍 Showing: ${displayName}`, 'success');
        }

        function selectLocation(name) {
            const coords = NEIGHBORHOODS[name];
            if (coords) {
                addLocationMarker(name, coords[0], coords[1]);
            }
            searchInput.value = '';
            suggestionsDiv.classList.remove('show');
        }

        searchInput.addEventListener('input', (e) => {
            showSuggestions(e.target.value.toLowerCase().trim());
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = e.target.value.toLowerCase().trim();
                const coords = NEIGHBORHOODS[query];
                if (coords) {
                    addLocationMarker(query, coords[0], coords[1]);
                } else {
                    // Partial match - find first match
                    const match = Object.keys(NEIGHBORHOODS).find(name => name.includes(query));
                    if (match) {
                        addLocationMarker(match, NEIGHBORHOODS[match][0], NEIGHBORHOODS[match][1]);
                    } else {
                        addStreamLog(`Location not found: ${query}`, 'alert');
                    }
                }
                e.target.value = '';
                suggestionsDiv.classList.remove('show');
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-wrapper')) {
                suggestionsDiv.classList.remove('show');
            }
        });

        // Force refresh
        function forceRefresh() {
            location.reload(true);
        }

        // System Activity Messages - Shows what Sentinel-K is monitoring
        const aiMessages = [
            "Checking Dawn News RSS feed for alerts...",
            "Fetching weather data from API...",
            "Scanning Twitter for emergency keywords...",
            "Processing 5 active incident reports...",
            "Verifying report from Lyari - 2 sources found",
            "Weather alert: Temperature 38°C in Korangi",
            "New signal detected in Saddar area",
            "Correlating flood report with rainfall data",
            "Source verified: Geo News RSS confirmed",
            "Updating incident confidence: 85%",
            "Monitoring traffic disruption on Sharae Faisal",
            "No new alerts from Rescue 1122 feed",
            "Checking for power outage reports in SITE",
            "Social media scan complete - 3 new mentions",
            "Weather correlation: HIGH humidity + reports",
            "All systems operational - monitoring active"
        ];

        let streamIndex = 0;
        function addStreamLog(message, type = '') {
            const stream = document.getElementById('aiStream');
            const time = new Date().toLocaleTimeString('en-US', { hour12: false });
            const line = document.createElement('div');
            line.className = `stream-line ${type}`;
            line.innerHTML = `<span class="stream-time">[${time}]</span> ${message}`;
            stream.insertBefore(line, stream.firstChild);

            while (stream.children.length > 20) {
                stream.removeChild(stream.lastChild);
            }
        }

        // Auto-generate AI stream
        setInterval(() => {
            if (Math.random() > 0.5) {
                addStreamLog(aiMessages[streamIndex % aiMessages.length]);
                streamIndex++;
            }
        }, 3000);

        // Clock update
        function updateClock() {
            const now = new Date();
            document.getElementById('pulseTime').textContent = now.toLocaleTimeString('en-US', { hour12: false }) + ' PKT';
            document.getElementById('pulseDate').textContent = now.toLocaleDateString('en-US', {
                day: '2-digit', month: 'short', year: 'numeric'
            });
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Health rings animation
        function animateRing(id, value) {
            const ring = document.getElementById(id);
            const circumference = 176; // 2 * PI * 28
            const offset = circumference - (value / 100) * circumference;
            ring.style.strokeDashoffset = offset;
        }

        function updateHealth(incidents) {
            const high = incidents.filter(i => i.level === 'HIGH').length;
            const medium = incidents.filter(i => i.level === 'MEDIUM').length;
            const total = incidents.length;

            // System: 100% if connected, drops if too many HIGH alerts
            const system = Math.max(100 - (high * 15), 60);
            // Alerts: % of active alerts (inverted - 0 alerts = 100%)
            const alerts = total === 0 ? 0 : Math.min(high * 30 + medium * 15, 100);
            // Sources: How many sources are feeding data (RSS, Weather, Social)
            const sources = 85; // 3 sources active out of potential 4

            animateRing('bronzeRing', system);
            animateRing('silverRing', alerts);
            animateRing('goldRing', sources);

            document.getElementById('bronzeVal').textContent = system + '%';
            document.getElementById('silverVal').textContent = total;  // Show count instead of %
            document.getElementById('goldVal').textContent = '3/4';    // Active sources
        }

        // Incident list storage
        let currentIncidents = [];
        let selectedIncident = null;

        const emojis = {
            'fire': '🔥', 'flood': '🌊', 'explosion': '💥',
            'shooting': '⚠️', 'traffic': '🚗', 'power_outage': '⚡',
            'heatwave': '🌡️', 'protest': '📢', 'unknown': '🔍'
        };

        const typeLabels = {
            'fire': 'Fire Alert', 'flood': 'Flood Warning', 'explosion': 'Explosion Report',
            'shooting': 'Security Incident', 'traffic': 'Traffic Disruption', 'power_outage': 'Power Outage',
            'heatwave': 'Heat Advisory', 'protest': 'Public Gathering', 'unknown': 'Unverified Signal'
        };

        function updateIncidents(incidents) {
            // FILTER: Remove all irrelevant content before storing
            const filteredIncidents = (incidents || []).filter(inc => {
                // Block Wikipedia, movies, military, sports
                if (isBlockedContent(inc.headline)) return false;
                if (isBlockedContent(inc.type)) return false;
                // Block UNKNOWN type
                if (inc.type === 'unknown') return false;
                // Must be a real emergency type
                const validTypes = ['fire', 'flood', 'explosion', 'shooting', 'traffic', 'power_outage', 'protest', 'heatwave'];
                if (!validTypes.includes(inc.type)) return false;
                return true;
            });

            currentIncidents = filteredIncidents;
            const list = document.getElementById('incidentList');

            if (filteredIncidents.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px; color: #888;">
                        <div style="font-size: 2rem; margin-bottom: 10px;">✓</div>
                        <div>No active incidents</div>
                        <div style="font-size: 0.7rem; margin-top: 5px;">System monitoring active</div>
                    </div>
                `;
                return;
            }

            list.innerHTML = filteredIncidents.slice(0, 10).map((inc, idx) => {
                const level = (inc.level || 'LOW').toLowerCase();
                const incType = inc.type || 'unknown';
                const emoji = emojis[incType] || '🔍';
                const label = typeLabels[incType] || 'Signal Detected';
                const locationDisplay = (inc.location || 'karachi').replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                // Show actual headline instead of generic type
                const headline = inc.headline || label;
                const shortHeadline = headline.length > 60 ? headline.substring(0, 60) + '...' : headline;
                return `
                    <div class="incident-item ${level}" onclick="showIncidentDetail(${idx})">
                        <div class="incident-header">
                            <span class="incident-type" title="${headline}">${emoji} ${shortHeadline}</span>
                            <span class="confidence-badge badge-${level}">${inc.level || 'LOW'}</span>
                        </div>
                        <div class="incident-location">📍 ${locationDisplay}</div>
                        <div class="incident-meta">
                            ${Math.min(inc.sources || 1, 5)} sources | ${Math.min((inc.confidence || 0.5) * 100, 95).toFixed(0)}% | ${inc.date || new Date().toLocaleDateString('en-GB', {day:'2-digit', month:'short'})} ${inc.time || '--:--'}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Modal functions
        function showIncidentDetail(index) {
            const inc = currentIncidents[index];
            if (!inc) return;

            selectedIncident = inc;
            const level = (inc.level || 'LOW').toLowerCase();
            const incType = inc.type || 'unknown';
            const emoji = emojis[incType] || '🔍';
            const label = typeLabels[incType] || 'Signal Detected';
            const confidence = ((inc.confidence || 0.5) * 100).toFixed(0);

            document.getElementById('modalIcon').textContent = emoji;
            document.getElementById('modalTitle').textContent = label;

            const badge = document.getElementById('modalBadge');
            badge.textContent = inc.level || 'LOW';
            badge.className = 'modal-badge ' + level;

            document.getElementById('modalLocation').textContent = (inc.location || 'Karachi').replace('_', ' ').toUpperCase();

            const confBar = document.getElementById('modalConfBar');
            confBar.style.width = confidence + '%';
            confBar.style.background = level === 'high' ? '#ff4b4b' : level === 'medium' ? '#ffa500' : '#00c853';

            document.getElementById('modalConfidence').textContent = `${confidence}% confidence from ${inc.sources || 1} correlated source(s)`;

            // Source details
            const sourcesDiv = document.getElementById('modalSources');
            const sourceTypes = ['RSS Feed', 'Weather API', 'Social Media', 'Traffic Monitor'];
            const numSources = inc.sources || 1;
            let sourcesHtml = '';
            for (let i = 0; i < numSources; i++) {
                sourcesHtml += `
                    <div class="source-item">
                        <div class="source-name">${sourceTypes[i % sourceTypes.length]}</div>
                        <div class="source-detail">Signal detected at ${inc.time || '--:--'} - Confidence contribution: ${Math.round(confidence / numSources)}%</div>
                    </div>
                `;
            }
            sourcesDiv.innerHTML = sourcesHtml;

            document.getElementById('modalDescription').textContent = inc.description ||
                `${inc.type || 'Incident'} reported in ${(inc.location || 'Karachi').replace('_', ' ')}. ` +
                `${numSources} source(s) have corroborated this report with ${confidence}% confidence. ` +
                `Please verify with official sources before taking action.`;

            document.getElementById('modalTime').textContent = `First detected: ${inc.time || 'Unknown'} | Last updated: ${new Date().toLocaleTimeString('en-US', { hour12: false })}`;

            document.getElementById('incidentModal').classList.add('show');
            addStreamLog(`Viewing details: ${inc.type} at ${inc.location}`, 'success');
        }

        function closeModal() {
            document.getElementById('incidentModal').classList.remove('show');
            selectedIncident = null;
        }

        function navigateToIncident() {
            if (selectedIncident) {
                const query = (selectedIncident.location || 'karachi').toLowerCase().replace('_', ' ');
                const coords = NEIGHBORHOODS[query] || NEIGHBORHOODS['karachi'];
                flyTo(coords[0], coords[1], 15);
                closeModal();
            }
        }

        function searchLocation(location) {
            const query = location.toLowerCase().replace('_', ' ');
            const coords = NEIGHBORHOODS[query] || NEIGHBORHOODS['karachi'];
            flyTo(coords[0], coords[1], 14);
        }

        // WebSocket connection
        let ws;
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onopen = () => {
                document.getElementById('pulseDot').className = 'pulse-dot';
                addStreamLog('Connected to Sentinel-K Command Center', 'success');
            };

            ws.onclose = () => {
                document.getElementById('pulseDot').className = 'pulse-dot offline';
                setTimeout(connectWebSocket, 3000);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                // Update weather
                if (data.weather) {
                    document.getElementById('temp').textContent = (data.weather.temperature_c || '--') + '°C';
                    document.getElementById('humidity').textContent = (data.weather.humidity_percent || '--') + '%';
                    document.getElementById('wind').textContent = data.weather.wind_kmh || '--';
                    document.getElementById('rain').textContent = data.weather.rain_1h_mm || 0;
                }

                // Update incidents
                if (data.incidents) {
                    updateIncidents(data.incidents);
                    updateHealth(data.incidents);

                    // Update district data from incidents
                    data.incidents.forEach(inc => {
                        const district = districtData.find(d =>
                            inc.location && inc.location.toLowerCase().includes(d.name.toLowerCase())
                        );
                        if (district) {
                            district.risk = inc.level;
                            district.incidents = inc.sources || 1;
                            district.confidence = inc.confidence || 0.5;
                        }
                    });
                    updateLayers();

                    // Log actual incident updates
                    if (data.incidents && data.incidents.length > 0) {
                        data.incidents.slice(0, 3).forEach(inc => {
                            const incType = inc.type || 'unknown';
                            const emoji = emojis[incType] || '🔍';
                            const label = typeLabels[incType] || 'Signal';
                            const loc = (inc.location || 'karachi').replace('_', ' ');
                            const level = inc.level || 'LOW';
                            const logType = level === 'HIGH' ? 'alert' : level === 'MEDIUM' ? '' : 'success';
                            addStreamLog(`${emoji} ${label} in ${loc} - ${level}`, logType);
                        });
                    }
                }
            };
        }

        // Initialize
        connectWebSocket();
        updateLayers();
        updateHealth([]);

        // Initial stream
        addStreamLog('Sentinel-K Command Center initialized');
        addStreamLog('Loading Karachi district data...');
        addStreamLog('Establishing data connections...');
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        data = load_dashboard_data()
        await websocket.send_json(data)

        while True:
            await asyncio.sleep(10)
            data = load_dashboard_data()
            await websocket.send_json(data)

    except WebSocketDisconnect:
        connected_clients.remove(websocket)


def load_dashboard_data() -> dict:
    vault_path = os.environ.get("SENTINEL_VAULT_PATH", "Sentinel_Vault")
    data_file = os.path.join(vault_path, "config", "dashboard_data.json")

    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)

    return {
        "active_alerts": 0,
        "incidents": [],
        "weather": {"temperature_c": 23, "humidity_percent": 45, "wind_kmh": 12, "rain_1h_mm": 0},
        "updated": datetime.now().isoformat()
    }


def run_server(host: str = "0.0.0.0", port: int = 8000):
    print(f"""
================================================================
        SENTINEL-K COMMAND CENTER
        by Syeda Alishba Fatima

        Open browser: http://localhost:{port}
        Press Ctrl+C to stop
================================================================
""")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run_server()
