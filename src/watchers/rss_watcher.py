"""
Sentinel-K RSS Watcher
Monitors Pakistani news RSS feeds for emergency-related headlines
Per Constitution Section V.1
"""
import feedparser
from datetime import datetime
from typing import List, Optional
import re
import logging

import sys
sys.path.append('..')
from models.source import Source, SourceType

logger = logging.getLogger(__name__)


class RSSWatcher:
    """
    Polls RSS feeds from Pakistani news outlets
    Detects emergency-related content using keyword matching
    """

    # RSS feeds per Constitution Section V.1
    FEEDS = {
        "dawn": {
            "url": "https://www.dawn.com/feeds/home",
            "reliability": 0.9,
            "verified": True,
        },
        "tribune": {
            "url": "https://tribune.com.pk/feed/home",
            "reliability": 0.85,
            "verified": True,
        },
        "ary": {
            "url": "https://arynews.tv/feed/",
            "reliability": 0.8,
            "verified": True,
        },
        "geo": {
            "url": "https://www.geo.tv/rss/1/1",
            "reliability": 0.8,
            "verified": True,
        },
        "samaa": {
            "url": "https://www.samaa.tv/feed/",
            "reliability": 0.75,
            "verified": True,
        },
    }

    # Emergency keywords (English)
    EMERGENCY_KEYWORDS = [
        # Fire
        "fire", "blaze", "inferno", "flames", "burning", "burnt",
        # Explosion
        "blast", "explosion", "bomb", "explosive",
        # Violence
        "shooting", "gunfire", "killed", "murder", "attack",
        # Traffic
        "accident", "collision", "crash", "road blocked",
        # Weather
        "flood", "flooding", "rain", "downpour", "storm",
        "heatwave", "heat stroke", "temperature",
        # Infrastructure
        "power outage", "blackout", "load shedding",
        # Civil
        "protest", "strike", "riot", "unrest",
    ]

    # Karachi location keywords
    KARACHI_KEYWORDS = [
        "karachi", "saddar", "clifton", "dha", "defence",
        "gulshan", "korangi", "site", "lyari", "malir",
        "nazimabad", "north nazimabad", "fb area", "gulberg",
        "tariq road", "bahadurabad", "pechs", "kemari",
        "shah faisal", "landhi", "bin qasim", "gadap",
    ]

    # BLOCKED content - filter out entertainment/sports/military/reference
    EXCLUDED_KEYWORDS = [
        # Movies/Entertainment
        "box office", "collection", "crore", "movie", "film", "bollywood", "lollywood",
        "actor", "actress", "celebrity", "trailer", "teaser", "premiere",
        "ranveer", "salman", "shahrukh", "deepika", "dhurandhar",
        # Sports
        "cricket", "match", "psl", "ipl", "world cup", "batting", "bowling",
        "football", "hockey", "tennis", "olympics", "tournament",
        # Military/Political (not local emergencies)
        "loc ", "line of control", "air force", "deep-strike", "targets inside",
        "indian air force", "pakistan air force", "army chief", "uttar pradesh",
        "rajasthan", "punjab india", "modi", "parliament", "senate",
        # Reference/Educational
        "wikipedia", "wiki", "encyclopedia", "history of",
        # Lifestyle
        "wedding", "fashion", "concert", "birthday", "anniversary",
        # Other irrelevant
        "recipe", "food review", "restaurant", "hotel", "travel", "tourism",
        "property", "real estate", "job", "vacancy", "hiring",
        "lahore", "islamabad", "peshawar", "quetta",  # Not Karachi cities
    ]

    def __init__(self):
        self.last_check = {}  # Track last seen entries per feed
        self.seen_urls = set()  # Track already processed URLs to avoid duplicates

    def _is_karachi_related(self, text: str) -> bool:
        """Check if content mentions Karachi or its areas"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.KARACHI_KEYWORDS)

    def _contains_emergency_keyword(self, text: str) -> bool:
        """Check if content contains emergency-related keywords"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.EMERGENCY_KEYWORDS)

    def _is_blocked_content(self, text: str) -> bool:
        """Check if content should be blocked (entertainment, military, etc.)"""
        text_lower = text.lower()
        for keyword in self.EXCLUDED_KEYWORDS:
            if keyword in text_lower:
                logger.debug(f"Blocked content (keyword: {keyword}): {text[:40]}...")
                return True
        return False

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract Karachi district from text"""
        text_lower = text.lower()

        # District mapping
        districts = {
            "saddar": ["saddar", "bolton", "empress market", "m.a. jinnah road"],
            "clifton": ["clifton", "sea view", "boat basin", "zamzama"],
            "dha": ["dha", "defence", "phase 6", "phase 7", "phase 8"],
            "gulshan": ["gulshan", "gulshan-e-iqbal", "rashid minhas"],
            "korangi": ["korangi", "landhi", "korangi industrial"],
            "site": ["site", "s.i.t.e", "industrial area"],
            "lyari": ["lyari", "baghdadi", "kalakot"],
            "malir": ["malir", "malir cantt", "airport"],
            "nazimabad": ["nazimabad", "north nazimabad", "buffer zone"],
            "fb_area": ["fb area", "federal b area", "karimabad"],
        }

        for district, keywords in districts.items():
            if any(kw in text_lower for kw in keywords):
                return district

        # Generic Karachi if no specific district
        if "karachi" in text_lower:
            return "karachi_general"

        return None

    def _parse_entry_time(self, entry) -> datetime:
        """Parse entry timestamp, default to now if unavailable"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        return datetime.now()

    def poll_feed(self, feed_name: str, feed_config: dict) -> List[Source]:
        """Poll a single RSS feed and extract relevant sources"""
        sources = []

        try:
            feed = feedparser.parse(feed_config["url"])

            if feed.bozo:
                logger.warning(f"Feed error for {feed_name}: {feed.bozo_exception}")
                return sources

            for entry in feed.entries[:20]:  # Check last 20 entries
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                content = f"{title} {summary}"

                # SKIP: Already seen this URL (avoid duplicates)
                if link in self.seen_urls:
                    continue

                # FILTER 1: Block irrelevant content (movies, military, Wikipedia, etc.)
                if self._is_blocked_content(content):
                    continue

                # FILTER 2: Must be Karachi-related AND contain emergency keyword
                if self._is_karachi_related(content) and self._contains_emergency_keyword(content):
                    location = self._extract_location(content)
                    timestamp = self._parse_entry_time(entry)

                    source = Source(
                        type=SourceType.NEWS,
                        content=title,
                        timestamp=timestamp,
                        location=location,
                        url=link,
                        verified=feed_config.get("verified", True),
                    )
                    sources.append(source)
                    self.seen_urls.add(link)  # Mark as seen to avoid duplicates
                    logger.info(f"[RSS] Detected: {title[:60]}... | Location: {location}")

        except Exception as e:
            logger.error(f"Error polling {feed_name}: {e}")

        return sources

    def poll_all(self) -> List[Source]:
        """Poll all configured RSS feeds"""
        all_sources = []
        logger.info("Starting RSS poll cycle...")

        for feed_name, feed_config in self.FEEDS.items():
            sources = self.poll_feed(feed_name, feed_config)
            all_sources.extend(sources)

        logger.info(f"RSS poll complete. Found {len(all_sources)} relevant items.")
        return all_sources


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watcher = RSSWatcher()
    sources = watcher.poll_all()
    for source in sources:
        print(f"- [{source.type.value}] {source.content[:50]}... | {source.location}")
