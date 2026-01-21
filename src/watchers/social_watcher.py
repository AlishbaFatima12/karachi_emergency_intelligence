"""
Sentinel-K Social Watcher
Monitors social media via Brave Search for emergency signals
Per Constitution Section V.2 - Includes Roman Urdu keywords
"""
import httpx
import os
from datetime import datetime
from typing import List, Optional
import logging
import hashlib
import re

import sys
sys.path.append('..')
from models.source import Source, SourceType

logger = logging.getLogger(__name__)


class SocialWatcher:
    """
    Monitors social media and news via Brave Search API
    Supports English, Urdu, and Roman Urdu keywords
    """

    # Brave Search API
    API_BASE = "https://api.search.brave.com/res/v1/web/search"

    # Keywords per Constitution Section V.2
    ROMAN_URDU_KEYWORDS = [
        # Fire-related
        "Aag", "Aag lagi", "Aag lagi hai", "Dhuaan", "Dhuaan uth raha hai",
        "Jalaya", "Jal raha hai",
        # Explosion/Violence
        "Dhamaaka", "Dhamaka", "Blast", "Goli", "Goli chal gayi",
        "Firing", "Firing ho rahi hai", "Target killing",
        # Traffic/Road
        "Band hai", "Road band", "Rasta band", "Jam hai", "Traffic jam",
        "Accident ho gaya", "Hadsa", "Gaari palat gayi",
        # Weather/Flood
        "Baarish", "Barish", "Paani", "Paani aa gaya", "Sailaab",
        "Bijli gayi", "Light gayi", "Load shedding",
        # Emergency
        "Madad", "Help chahiye", "Emergency", "Ambulance",
        "Hospital", "Zakhmi", "Injured",
    ]

    ENGLISH_KEYWORDS = [
        "karachi fire", "karachi blast", "karachi accident",
        "karachi flood", "karachi rain", "karachi traffic jam",
        "karachi shooting", "karachi protest", "dha fire",
        "clifton accident", "saddar blast", "gulshan fire",
        "korangi fire", "site fire", "lyari shooting",
    ]

    # Karachi districts for location extraction
    KARACHI_DISTRICTS = {
        "saddar": ["saddar", "bolton", "empress", "m.a. jinnah", "preedy"],
        "clifton": ["clifton", "sea view", "boat basin", "zamzama", "seaview"],
        "dha": ["dha", "defence", "phase 6", "phase 7", "phase 8", "phase 5"],
        "gulshan": ["gulshan", "gulshan-e-iqbal", "rashid minhas", "johar"],
        "korangi": ["korangi", "landhi", "korangi industrial"],
        "site": ["site", "s.i.t.e", "industrial"],
        "lyari": ["lyari", "baghdadi", "kalakot", "chakiwara"],
        "malir": ["malir", "malir cantt", "airport", "jinnah airport"],
        "nazimabad": ["nazimabad", "north nazimabad", "buffer zone", "sakhi hassan"],
        "fb_area": ["fb area", "federal b area", "karimabad", "aisha manzil"],
        "tariq_road": ["tariq road", "bahadurabad", "pechs"],
        "surjani": ["surjani", "surjani town"],
        "orangi": ["orangi", "orangi town"],
        "shah_faisal": ["shah faisal", "shah faisal colony"],
        "karsaz": ["karsaz", "drigh road"],
    }

    # Incident type detection
    INCIDENT_PATTERNS = {
        "fire": ["aag", "fire", "blaze", "jalaya", "dhuaan", "smoke", "burning"],
        "flood": ["sailaab", "flood", "paani", "baarish", "rain", "water logging"],
        "explosion": ["dhamaaka", "blast", "explosion", "bomb"],
        "shooting": ["goli", "firing", "shooting", "gunfire", "target killing"],
        "traffic": ["accident", "hadsa", "jam", "band hai", "road block", "collision"],
        "power": ["bijli gayi", "load shedding", "power outage", "blackout"],
        "protest": ["protest", "dharna", "strike", "jalao", "rally"],
    }

    # IRRELEVANT content keywords - filter out entertainment/sports/celebrity news
    EXCLUDED_KEYWORDS = [
        # Bollywood/Movies
        "box office", "collection", "crore", "movie", "film", "bollywood", "lollywood",
        "actor", "actress", "celebrity", "star cast", "trailer", "teaser", "ott",
        "netflix", "amazon prime", "hotstar", "zee5", "cinema", "premiere",
        "ranveer", "salman", "shahrukh", "aamir", "deepika", "alia", "ranbir",
        "hrithik", "katrina", "priyanka", "kareena", "anushka", "fawad", "mahira",
        "dhurandhar", "spy thriller", "globally", "worldwide",
        # Sports
        "cricket", "match", "psl", "ipl", "world cup", "batting", "bowling",
        "football", "hockey", "tennis", "olympics", "tournament", "league",
        "babar azam", "virat kohli", "shaheen", "rizwan",
        # Entertainment/Lifestyle
        "wedding", "shaadi", "fashion", "red carpet", "award", "concert", "song",
        "album", "music video", "tiktok", "instagram", "influencer", "viral video",
        "birthday", "anniversary", "baby shower", "pregnancy", "divorce",
        # Business/Stock (not emergencies)
        "stock market", "shares", "profit", "revenue", "quarterly", "earnings",
        "ipo", "investment", "startup", "funding",
        # Politics/Military (not local emergencies)
        "election", "vote", "campaign", "speech", "interview", "statement",
        "loc ", "line of control", "air force", "deep-strike", "targets inside",
        "indian air force", "pakistan air force", "military", "army chief",
        # Reference/Educational (not emergencies)
        "wikipedia", "wiki", "- wikipedia", "encyclopedia", "history of",
        "population", "geography", "district", "division", "administrative",
        # General irrelevant
        "recipe", "food review", "restaurant", "hotel", "travel", "tourism",
        "property", "real estate", "apartment", "flat for sale", "rent",
        "job", "vacancy", "hiring", "salary", "herzindagi",
    ]

    # BLOCKED URLs - never use these sources
    BLOCKED_URLS = [
        "wikipedia.org", "wiki", "imdb.com", "rottentomatoes.com",
        "bollywoodhungama.com", "pinkvilla.com", "filmfare.com",
        "espncricinfo.com", "cricbuzz.com", "sportskeeda.com",
        "indiatoday.in/movies", "indiatoday.in/entertainment",
        "tribuneindia.com", "hindustantimes.com/cricket",
        "timesofindia.indiatimes.com/entertainment",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.seen_urls = set()  # Track already processed URLs to avoid duplicates
        if not self.api_key:
            logger.warning("No Brave API key configured. Social monitoring limited.")

    def _hash_username(self, username: str) -> str:
        """Hash username for privacy per Constitution Section XIV"""
        return hashlib.sha256(username.encode()).hexdigest()[:16]

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract Karachi district from text"""
        text_lower = text.lower()
        for district, keywords in self.KARACHI_DISTRICTS.items():
            if any(kw in text_lower for kw in keywords):
                return district
        if "karachi" in text_lower:
            return "karachi_general"
        return None

    def _detect_incident_type(self, text: str) -> str:
        """Detect incident type from text"""
        text_lower = text.lower()
        for incident_type, patterns in self.INCIDENT_PATTERNS.items():
            if any(p in text_lower for p in patterns):
                return incident_type
        return "unknown"

    def _is_irrelevant_content(self, text: str) -> bool:
        """Check if content is irrelevant (entertainment, sports, etc.)"""
        text_lower = text.lower()
        for keyword in self.EXCLUDED_KEYWORDS:
            if keyword in text_lower:
                logger.debug(f"Filtered irrelevant content (keyword: {keyword}): {text[:50]}...")
                return True
        return False

    def _is_blocked_url(self, url: str) -> bool:
        """Check if URL is from a blocked source"""
        url_lower = url.lower()
        for blocked in self.BLOCKED_URLS:
            if blocked in url_lower:
                logger.debug(f"Blocked URL: {url[:60]}...")
                return True
        return False

    def _search_brave(self, query: str) -> List[dict]:
        """Execute Brave Search API query"""
        if not self.api_key:
            return []

        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key,
            }
            params = {
                "q": query,
                "count": 10,
                "freshness": "pd",  # Past day
            }
            response = httpx.get(
                self.API_BASE,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("web", {}).get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Brave Search error: {e}")
            return []

    def _parse_result(self, result: dict, query: str) -> Optional[Source]:
        """Parse a search result into a Source object"""
        title = result.get("title", "")
        description = result.get("description", "")
        url = result.get("url", "")
        content = f"{title} {description}"

        # FILTER 1: Block Wikipedia and entertainment URLs
        if self._is_blocked_url(url):
            return None

        # FILTER 2: Skip irrelevant content (movies, sports, entertainment)
        if self._is_irrelevant_content(content):
            return None

        # FILTER 3: Must contain actual emergency keywords to be relevant
        emergency_keywords = [
            "fire", "aag", "blaze", "smoke", "burning", "flames",
            "flood", "rain", "water", "sailaab", "baarish", "paani",
            "blast", "explosion", "bomb", "dhamaka",
            "shooting", "firing", "goli", "gunfire", "killed", "murder",
            "accident", "crash", "collision", "hadsa", "injured",
            "protest", "strike", "dharna", "rally", "road block",
            "power outage", "blackout", "bijli", "load shedding",
            "robbery", "theft", "dacoity", "snatching",
            "rescue", "emergency", "ambulance", "hospital",
        ]
        content_lower = content.lower()
        if not any(kw in content_lower for kw in emergency_keywords):
            logger.debug(f"Filtered (no emergency keywords): {title[:50]}...")
            return None

        # Extract location
        location = self._extract_location(content)

        # Only include if Karachi-related
        if not location:
            return None

        # Detect if from social media platform
        is_social = any(
            platform in url.lower()
            for platform in ["twitter.com", "x.com", "facebook.com", "reddit.com"]
        )

        source = Source(
            type=SourceType.SOCIAL if is_social else SourceType.NEWS,
            content=title,
            timestamp=datetime.now(),  # Brave doesn't always provide timestamp
            location=location,
            url=url,
            verified=not is_social,  # News sources are verified, social is not
            geo_tagged=False,
        )

        return source

    def search_keywords(self, keywords: List[str], location_context: str = "Karachi") -> List[Source]:
        """Search for a list of keywords"""
        all_sources = []

        for keyword in keywords:
            query = f"{keyword} {location_context}"
            results = self._search_brave(query)

            for result in results:
                url = result.get("url", "")
                # Skip if already seen in THIS poll or PREVIOUS polls
                if url in self.seen_urls:
                    continue

                source = self._parse_result(result, query)
                if source:
                    self.seen_urls.add(url)  # Mark as seen across all polls
                    all_sources.append(source)
                    logger.info(f"[SOCIAL] Found: {source.content[:50]}... | {source.location}")

        return all_sources

    def poll(self) -> List[Source]:
        """Poll social media using priority keywords from local news sources"""
        logger.info("Starting social media poll...")

        # Target Karachi local news channels for LIVE updates
        # Geo News, ARY News, Samaa TV, Dawn, Express Tribune, Bol News
        priority_keywords = [
            # Live breaking news from local channels
            "Karachi fire breaking news",
            "Karachi blast breaking",
            "Karachi accident breaking",
            "Karachi shooting breaking",
            "Karachi robbery today",

            # Specific news channels + emergency
            "Geo News Karachi fire",
            "ARY News Karachi accident",
            "Samaa Karachi breaking",
            "Dawn Karachi emergency",
            "Express Tribune Karachi incident",

            # Roman Urdu from Twitter/Social
            "Karachi aag lagi today",
            "Karachi dhamaaka aaj",
            "Karachi firing aaj",
            "Karachi hadsa aaj",
            "Karachi loot maar",
        ]

        # Traffic-specific from live sources
        priority_keywords.extend([
            "Karachi traffic accident today",
            "Karachi road block today",
            "Shahrah-e-Faisal accident",
            "Karachi traffic jam now",
        ])

        sources = self.search_keywords(priority_keywords)
        logger.info(f"Social poll complete. Found {len(sources)} relevant signals.")

        return sources

    def search_specific(self, incident_type: str, location: str) -> List[Source]:
        """Search for specific incident type at location"""
        keywords = self.INCIDENT_PATTERNS.get(incident_type, [])
        queries = [f"{kw} {location} Karachi" for kw in keywords[:3]]

        all_sources = []
        for query in queries:
            results = self._search_brave(query)
            for result in results:
                source = self._parse_result(result, query)
                if source:
                    all_sources.append(source)

        return all_sources


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watcher = SocialWatcher()
    sources = watcher.poll()
    print(f"\nFound {len(sources)} social signals:")
    for source in sources:
        print(f"- [{source.type.value}] {source.content[:60]}... | {source.location}")
