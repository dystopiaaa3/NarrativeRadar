import os
from datetime import datetime

import requests
from dotenv import load_dotenv


load_dotenv()


LUNARCRUSH_API_KEY = os.getenv(
    "LUNARCRUSH_API_KEY",
    ""
)

LUNARCRUSH_BASE_URL = "https://lunarcrush.ai"


class SocialCollector:

    def __init__(self):

        self.name = "Social Collector"

        self.api_key = LUNARCRUSH_API_KEY

        self.base_url = LUNARCRUSH_BASE_URL

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "NarrativeRadar/1.0"
            }
        )

        if self.api_key:

            self.session.headers.update(
                {
                    "Authorization": (
                        f"Bearer {self.api_key}"
                    )
                }
            )


    def create_snapshot(
        self,
        coin_address: str,
        mentions: int = 0,
        engagement: int = 0,
        community_size: int = 0,
        growth_rate: float = 0.0,
        sentiment: float = 0.0,
        social_dominance: float = 0.0,
        galaxy_score: float = 0.0,
        alt_rank: int = 0,
        available: bool = False,
        source: str = "none",
        error=None,
        raw_status=None
    ):

        return {
            "coin_address": coin_address,

            "mentions": int(
                mentions or 0
            ),

            "engagement": int(
                engagement or 0
            ),

            "community_size": int(
                community_size or 0
            ),

            "growth_rate": float(
                growth_rate or 0
            ),

            "sentiment": float(
                sentiment or 0
            ),

            "social_dominance": float(
                social_dominance or 0
            ),

            "galaxy_score": float(
                galaxy_score or 0
            ),

            "alt_rank": int(
                alt_rank or 0
            ),

            "available": bool(
                available
            ),

            "source": source,

            "error": error,

            "raw_status": raw_status,

            "timestamp": datetime.utcnow()
        }


    def _safe_float(
        self,
        value,
        default=0.0
    ):

        try:

            if value is None:
                return default

            return float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return default


    def _safe_int(
        self,
        value,
        default=0
    ):

        try:

            if value is None:
                return default

            return int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return default


    def _first_value(
        self,
        dictionaries,
        keys,
        default=None
    ):

        for dictionary in dictionaries:

            if not isinstance(
                dictionary,
                dict
            ):
                continue

            for key in keys:

                value = dictionary.get(
                    key
                )

                if value is not None:
                    return value

        return default


    def fetch_social_data(
        self,
        coin_address: str,
        topic: str = None
    ):

        if not self.api_key:

            return self.create_snapshot(
                coin_address=coin_address,
                available=False,
                source="lunarcrush",
                error=(
                    "LUNARCRUSH_API_KEY "
                    "is missing"
                )
            )


        search_term = (
            topic
            if topic
            else coin_address
        )


        search_term = str(
            search_term
        ).strip()


        if not search_term:

            return self.create_snapshot(
                coin_address=coin_address,
                available=False,
                source="lunarcrush",
                error=(
                    "Social topic is empty"
                )
            )


        url = (
            f"{self.base_url}/"
            f"topic/"
            f"{search_term}"
        )


        try:

            response = self.session.get(
                url,
                params={
                    "format": "json"
                },
                timeout=5
            )


            status_code = (
                response.status_code
            )


            if status_code != 200:

                return self.create_snapshot(
                    coin_address=coin_address,
                    available=False,
                    source="lunarcrush",
                    error=(
                        f"HTTP "
                        f"{status_code}: "
                        f"{response.text[:500]}"
                    ),
                    raw_status=status_code
                )


            try:

                body = response.json()

            except Exception as e:

                return self.create_snapshot(
                    coin_address=coin_address,
                    available=False,
                    source="lunarcrush",
                    error=(
                        "Invalid JSON: "
                        f"{str(e)}"
                    ),
                    raw_status=status_code
                )


            # =========================================
            # EXACT LUNARCRUSH STRUCTURE
            #
            # {
            #   "data": {
            #       "topic": "$bonk",
            #       "asset": {...},
            #       "ai_summary": {...}
            #   }
            # }
            # =========================================

            data = (
                body.get(
                    "data"
                )
                or {}
            )


            if not isinstance(
                data,
                dict
            ):

                data = {}


            asset = (
                data.get(
                    "asset"
                )
                or {}
            )


            if not isinstance(
                asset,
                dict
            ):

                asset = {}


            ai_summary = (
                data.get(
                    "ai_summary"
                )
                or {}
            )


            if not isinstance(
                ai_summary,
                dict
            ):

                ai_summary = {}


            # =========================================
            # ENGAGEMENT
            #
            # LunarCrush response:
            #
            # interactions_24h: 842482
            # =========================================

            engagement = (
                self._safe_int(
                    self._first_value(
                        [
                            asset,
                            data
                        ],
                        [
                            "interactions_24h",
                            "interactions",
                            "engagements",
                            "engagement"
                        ],
                        0
                    )
                )
            )


            # =========================================
            # MENTIONS / ACTIVE POSTS
            #
            # Different LunarCrush topic responses may
            # expose these under different names.
            # =========================================

            mentions = (
                self._safe_int(
                    self._first_value(
                        [
                            asset,
                            data
                        ],
                        [
                            "posts_active",
                            "posts_created_24h",
                            "posts_24h",
                            "mentions_24h",
                            "mentions",
                            "posts"
                        ],
                        0
                    )
                )
            )


            # =========================================
            # COMMUNITY / CONTRIBUTORS
            # =========================================

            community_size = (
                self._safe_int(
                    self._first_value(
                        [
                            asset,
                            data
                        ],
                        [
                            "contributors_active",
                            "contributors_24h",
                            "contributors",
                            "creators_active",
                            "creators"
                        ],
                        0
                    )
                )
            )


            # =========================================
            # SOCIAL GROWTH
            #
            # Exact JSON supplied:
            #
            # ai_summary.social_growth = 12
            # =========================================

            growth_rate = (
                self._safe_float(
                    self._first_value(
                        [
                            ai_summary,
                            asset,
                            data
                        ],
                        [
                            "social_growth",
                            "social_growth_24h"
                        ],
                        0
                    )
                )
            )


            # =========================================
            # SOCIAL DOMINANCE
            #
            # Exact JSON supplied:
            #
            # asset.social_dominance
            # =========================================

            social_dominance = (
                self._safe_float(
                    asset.get(
                        "social_dominance",
                        0
                    )
                )
            )


            # =========================================
            # GALAXY SCORE
            #
            # Exact JSON supplied:
            #
            # asset.galaxy_score
            # =========================================

            galaxy_score = (
                self._safe_float(
                    asset.get(
                        "galaxy_score",
                        0
                    )
                )
            )


            # =========================================
            # ALT RANK
            # =========================================

            alt_rank = (
                self._safe_int(
                    asset.get(
                        "alt_rank",
                        0
                    )
                )
            )


            # =========================================
            # SENTIMENT
            #
            # Check all possible locations.
            # =========================================

            sentiment = (
                self._safe_float(
                    self._first_value(
                        [
                            asset,
                            data,
                            ai_summary
                        ],
                        [
                            "sentiment",
                            "sentiment_score"
                        ],
                        0
                    )
                )
            )


            # =========================================
            # AVAILABILITY
            #
            # We now know engagement/social growth/etc.
            # can prove that LunarCrush returned useful
            # data even when mentions is unavailable.
            # =========================================

            available = any(
                [
                    mentions > 0,
                    engagement > 0,
                    community_size > 0,
                    growth_rate != 0,
                    sentiment != 0,
                    social_dominance > 0,
                    galaxy_score > 0
                ]
            )


            error = None


            if not available:

                error = (
                    "LunarCrush returned "
                    "no usable social metrics"
                )


            return self.create_snapshot(
                coin_address=coin_address,

                mentions=mentions,

                engagement=engagement,

                community_size=community_size,

                growth_rate=growth_rate,

                sentiment=sentiment,

                social_dominance=(
                    social_dominance
                ),

                galaxy_score=(
                    galaxy_score
                ),

                alt_rank=alt_rank,

                available=available,

                source="lunarcrush",

                error=error,

                raw_status=status_code
            )


        except requests.Timeout:

            return self.create_snapshot(
                coin_address=coin_address,
                available=False,
                source="lunarcrush",
                error=(
                    "LunarCrush request "
                    "timed out"
                )
            )


        except requests.RequestException as e:

            return self.create_snapshot(
                coin_address=coin_address,
                available=False,
                source="lunarcrush",
                error=(
                    "LunarCrush request "
                    f"failed: {str(e)}"
                )
            )


        except Exception as e:

            return self.create_snapshot(
                coin_address=coin_address,
                available=False,
                source="lunarcrush",
                error=(
                    "Unexpected LunarCrush "
                    f"error: {str(e)}"
                )
            )