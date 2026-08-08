from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List

import requests


class DexScreenerDiscoveryCollector:

    def __init__(
        self,
        timeout: float = 5.0,
        max_workers: int = 8
    ):

        self.name = "DexScreener Discovery"

        self.timeout = timeout

        self.max_workers = max(
            1,
            min(
                int(max_workers),
                12
            )
        )

        self.base_url = (
            "https://api.dexscreener.com"
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "NarrativeRadar/1.0"
            }
        )


    # =========================================
    # SAFE CONVERSION
    # =========================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0
    ):

        try:

            if value is None:
                return default

            return float(value)

        except (
            TypeError,
            ValueError
        ):

            return default


    # =========================================
    # ADDRESS CHECK
    # =========================================

    @staticmethod
    def _valid_address(
        value
    ):

        if not isinstance(
            value,
            str
        ):
            return False

        value = value.strip()

        return (
            32
            <= len(value)
            <= 44
        )


    # =========================================
    # REQUEST
    # =========================================

    def _get_json(
        self,
        path: str
    ):

        url = (
            f"{self.base_url}"
            f"{path}"
        )

        response = (
            self.session.get(
                url,
                timeout=self.timeout
            )
        )

        response.raise_for_status()

        return response.json()


    # =========================================
    # LATEST TOKEN PROFILES
    # =========================================

    def get_latest_profiles(
        self
    ) -> List[Dict[str, Any]]:

        try:

            data = self._get_json(
                "/token-profiles/latest/v1"
            )

            if not isinstance(
                data,
                list
            ):
                return []

            results = []

            for item in data:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if (
                    item.get(
                        "chainId"
                    )
                    != "solana"
                ):
                    continue

                address = (
                    item.get(
                        "tokenAddress"
                    )
                )

                if not self._valid_address(
                    address
                ):
                    continue

                results.append(
                    {
                        "coin_address": (
                            address
                        ),

                        "source_reason": (
                            "latest_profile"
                        ),

                        "profile": item
                    }
                )

            return results

        except Exception:

            return []


    # =========================================
    # TOP BOOSTED TOKENS
    # =========================================

    def get_top_boosts(
        self
    ) -> List[Dict[str, Any]]:

        try:

            data = self._get_json(
                "/token-boosts/top/v1"
            )

            if not isinstance(
                data,
                list
            ):
                return []

            results = []

            for item in data:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if (
                    item.get(
                        "chainId"
                    )
                    != "solana"
                ):
                    continue

                address = (
                    item.get(
                        "tokenAddress"
                    )
                )

                if not self._valid_address(
                    address
                ):
                    continue

                results.append(
                    {
                        "coin_address": (
                            address
                        ),

                        "source_reason": (
                            "top_boost"
                        ),

                        "boost": item
                    }
                )

            return results

        except Exception:

            return []


    # =========================================
    # LATEST BOOSTED TOKENS
    # =========================================

    def get_latest_boosts(
        self
    ) -> List[Dict[str, Any]]:

        try:

            data = self._get_json(
                "/token-boosts/latest/v1"
            )

            if not isinstance(
                data,
                list
            ):
                return []

            results = []

            for item in data:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if (
                    item.get(
                        "chainId"
                    )
                    != "solana"
                ):
                    continue

                address = (
                    item.get(
                        "tokenAddress"
                    )
                )

                if not self._valid_address(
                    address
                ):
                    continue

                results.append(
                    {
                        "coin_address": (
                            address
                        ),

                        "source_reason": (
                            "latest_boost"
                        ),

                        "boost": item
                    }
                )

            return results

        except Exception:

            return []


    # =========================================
    # FETCH TOKEN PAIRS
    # =========================================

    def get_token_pairs(
        self,
        coin_address: str
    ):

        try:

            data = self._get_json(
                (
                    "/token-pairs/v1/"
                    f"solana/"
                    f"{coin_address}"
                )
            )

            if not isinstance(
                data,
                list
            ):

                return []

            return [
                pair
                for pair in data
                if isinstance(
                    pair,
                    dict
                )
                and
                pair.get(
                    "chainId"
                )
                == "solana"
            ]

        except Exception:

            return []


    # =========================================
    # BEST MARKET
    # =========================================

    def _best_pair(
        self,
        pairs
    ):

        if not pairs:
            return None

        valid = []

        for pair in pairs:

            liquidity = (
                self._safe_float(
                    (
                        pair.get(
                            "liquidity"
                        )
                        or {}
                    ).get(
                        "usd"
                    )
                )
            )

            if liquidity <= 0:
                continue

            valid.append(
                pair
            )

        if not valid:
            return None

        valid.sort(
            key=lambda pair: (
                self._safe_float(
                    (
                        pair.get(
                            "liquidity"
                        )
                        or {}
                    ).get(
                        "usd"
                    )
                )
            ),
            reverse=True
        )

        return valid[0]


    # =========================================
    # ENRICH ONE CANDIDATE
    # =========================================

    def _enrich(
        self,
        item
    ):

        coin_address = (
            item[
                "coin_address"
            ]
        )

        pairs = (
            self.get_token_pairs(
                coin_address
            )
        )

        best = self._best_pair(
            pairs
        )

        if not best:

            return {
                "coin_address": (
                    coin_address
                ),

                "name": "",

                "symbol": "",

                "price": 0.0,

                "market_cap": 0.0,

                "liquidity": 0.0,

                "volume_24h": 0.0,

                "price_change_1h": 0.0,

                "price_change_24h": 0.0,

                "buys_1h": 0,

                "sells_1h": 0,

                "source": (
                    "dexscreener"
                ),

                "source_reason": (
                    item[
                        "source_reason"
                    ]
                ),

                "discovered_at": (
                    datetime.utcnow()
                ),

                "raw": item
            }


        base_token = (
            best.get(
                "baseToken"
            )
            or {}
        )


        # Some pools may list our token
        # as the quote side instead.

        quote_token = (
            best.get(
                "quoteToken"
            )
            or {}
        )


        if (
            base_token.get(
                "address"
            )
            == coin_address
        ):

            token_info = (
                base_token
            )

        elif (
            quote_token.get(
                "address"
            )
            == coin_address
        ):

            token_info = (
                quote_token
            )

        else:

            token_info = (
                base_token
            )


        txns = (
            best.get(
                "txns"
            )
            or {}
        )

        txns_h1 = (
            txns.get(
                "h1"
            )
            or {}
        )


        price_change = (
            best.get(
                "priceChange"
            )
            or {}
        )


        liquidity = (
            self._safe_float(
                (
                    best.get(
                        "liquidity"
                    )
                    or {}
                ).get(
                    "usd"
                )
            )
        )


        volume_24h = (
            self._safe_float(
                (
                    best.get(
                        "volume"
                    )
                    or {}
                ).get(
                    "h24"
                )
            )
        )


        market_cap = (
            self._safe_float(
                best.get(
                    "marketCap"
                )
            )
        )


        if market_cap <= 0:

            market_cap = (
                self._safe_float(
                    best.get(
                        "fdv"
                    )
                )
            )


        return {

            "coin_address": (
                coin_address
            ),

            "name": (
                token_info.get(
                    "name"
                )
                or ""
            ),

            "symbol": (
                token_info.get(
                    "symbol"
                )
                or ""
            ),

            "price": (
                self._safe_float(
                    best.get(
                        "priceUsd"
                    )
                )
            ),

            "market_cap": (
                market_cap
            ),

            "liquidity": (
                liquidity
            ),

            "volume_24h": (
                volume_24h
            ),

            "price_change_1h": (
                self._safe_float(
                    price_change.get(
                        "h1"
                    )
                )
            ),

            "price_change_24h": (
                self._safe_float(
                    price_change.get(
                        "h24"
                    )
                )
            ),

            "buys_1h": int(
                txns_h1.get(
                    "buys",
                    0
                )
                or 0
            ),

            "sells_1h": int(
                txns_h1.get(
                    "sells",
                    0
                )
                or 0
            ),

            "pair_address": (
                best.get(
                    "pairAddress"
                )
            ),

            "dex_id": (
                best.get(
                    "dexId"
                )
            ),

            "pair_created_at": (
                best.get(
                    "pairCreatedAt"
                )
            ),

            "source": (
                "dexscreener"
            ),

            "source_reason": (
                item[
                    "source_reason"
                ]
            ),

            "discovered_at": (
                datetime.utcnow()
            ),

            "raw": best
        }


    # =========================================
    # DISCOVER
    # =========================================

    def discover(
        self,
        limit: int = 20
    ):

        limit = max(
            1,
            min(
                int(limit),
                50
            )
        )


        profiles = (
            self.get_latest_profiles()
        )

        top_boosts = (
            self.get_top_boosts()
        )

        latest_boosts = (
            self.get_latest_boosts()
        )


        combined = (
            top_boosts
            + latest_boosts
            + profiles
        )


        deduped = []

        seen = set()


        for item in combined:

            address = item[
                "coin_address"
            ]

            if address in seen:
                continue

            seen.add(
                address
            )

            deduped.append(
                item
            )

            if len(
                deduped
            ) >= limit:

                break


        if not deduped:

            return {
                "success": True,
                "source": "dexscreener",
                "count": 0,
                "candidates": [],
                "error": None
            }


        candidates = []


        with ThreadPoolExecutor(
            max_workers=(
                self.max_workers
            )
        ) as executor:

            futures = [
                executor.submit(
                    self._enrich,
                    item
                )

                for item in deduped
            ]


            for future in as_completed(
                futures
            ):

                try:

                    candidate = (
                        future.result()
                    )

                    candidates.append(
                        candidate
                    )

                except Exception:

                    continue


        # =========================================
        # PRIORITY SORT
        #
        # This is NOT the final intelligence score.
        #
        # It simply puts active/liquid candidates
        # toward the front of our scanning queue.
        # =========================================

        candidates.sort(
            key=lambda item: (
                item[
                    "volume_24h"
                ],
                item[
                    "liquidity"
                ],
                (
                    item[
                        "buys_1h"
                    ]
                    +
                    item[
                        "sells_1h"
                    ]
                )
            ),
            reverse=True
        )


        return {
            "success": True,

            "source": (
                "dexscreener"
            ),

            "count": len(
                candidates
            ),

            "candidates": (
                candidates
            ),

            "error": None
        }