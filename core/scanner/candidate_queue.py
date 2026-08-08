import math

from datetime import (
    datetime,
    timedelta,
)

from typing import (
    Any,
    Dict,
)


class CandidateQueue:

    def __init__(
        self,
        min_liquidity: float = 3000.0,
        min_volume_24h: float = 10000.0,
        min_market_cap: float = 1000.0,
        max_market_cap: float = 100_000_000.0,
        cooldown_minutes: int = 10,
    ):

        self.min_liquidity = float(
            min_liquidity
        )

        self.min_volume_24h = float(
            min_volume_24h
        )

        self.min_market_cap = float(
            min_market_cap
        )

        self.max_market_cap = float(
            max_market_cap
        )

        self.cooldown_minutes = int(
            cooldown_minutes
        )

        self._queue = {}
        self._last_scanned = {}


    # =========================================================
    # SAFE CONVERSION
    # =========================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            if value is None:
                return default

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    @staticmethod
    def _safe_int(
        value,
        default=0,
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
            ValueError,
        ):

            return default


    # =========================================================
    # ADDRESS CHECK
    # =========================================================

    @staticmethod
    def _valid_address(
        value,
    ):

        if not isinstance(
            value,
            str,
        ):

            return False

        value = value.strip()

        return (
            32
            <= len(value)
            <= 44
        )


    # =========================================================
    # SOURCE NORMALIZATION
    # =========================================================

    @staticmethod
    def _source_list(
        candidate,
    ):

        sources = []

        supplied_sources = (
            candidate.get(
                "discovery_sources"
            )
            or
            candidate.get(
                "sources"
            )
            or
            []
        )

        if isinstance(
            supplied_sources,
            str,
        ):

            supplied_sources = [
                supplied_sources
            ]

        if isinstance(
            supplied_sources,
            (
                list,
                tuple,
                set,
            ),
        ):

            for source in supplied_sources:

                source = str(
                    source
                    or ""
                ).strip().lower()

                if (
                    source
                    and
                    source not in sources
                ):

                    sources.append(
                        source
                    )

        direct_source = str(
            candidate.get(
                "source",
                ""
            )
            or ""
        ).strip().lower()

        if (
            direct_source
            and
            direct_source not in sources
        ):

            sources.append(
                direct_source
            )

        if not sources:

            sources = [
                "unknown"
            ]

        return sources


    @staticmethod
    def _reason_list(
        candidate,
    ):

        reasons = []

        supplied_reasons = (
            candidate.get(
                "source_reasons"
            )
            or
            []
        )

        if isinstance(
            supplied_reasons,
            str,
        ):

            supplied_reasons = [
                supplied_reasons
            ]

        if isinstance(
            supplied_reasons,
            (
                list,
                tuple,
                set,
            ),
        ):

            for reason in supplied_reasons:

                reason = str(
                    reason
                    or ""
                ).strip()

                if (
                    reason
                    and
                    reason not in reasons
                ):

                    reasons.append(
                        reason
                    )

        direct_reason = str(
            candidate.get(
                "source_reason",
                ""
            )
            or ""
        ).strip()

        if (
            direct_reason
            and
            direct_reason not in reasons
        ):

            reasons.append(
                direct_reason
            )

        return reasons


    # =========================================================
    # NORMALIZE
    # =========================================================

    def _normalize(
        self,
        candidate: Dict[str, Any],
    ):

        if not isinstance(
            candidate,
            dict,
        ):

            return None

        address = (
            candidate.get(
                "coin_address"
            )
            or
            candidate.get(
                "mint"
            )
            or
            candidate.get(
                "address"
            )
        )

        if not self._valid_address(
            address
        ):

            return None

        address = (
            address.strip()
        )

        sources = (
            self._source_list(
                candidate
            )
        )

        source_reasons = (
            self._reason_list(
                candidate
            )
        )

        source_count = len(
            sources
        )

        cross_source = (
            source_count >= 2
            or
            bool(
                candidate.get(
                    "cross_source",
                    False
                )
            )
        )

        discovery_confidence = (
            self._safe_float(
                candidate.get(
                    "discovery_confidence",
                    (
                        100.0
                        if cross_source
                        else 60.0
                    )
                )
            )
        )

        return {
            "coin_address": (
                address
            ),

            "name": str(
                candidate.get(
                    "name",
                    ""
                )
                or ""
            ),

            "symbol": str(
                candidate.get(
                    "symbol",
                    ""
                )
                or ""
            ),

            "price": (
                self._safe_float(
                    candidate.get(
                        "price"
                    )
                )
            ),

            "market_cap": (
                self._safe_float(
                    candidate.get(
                        "market_cap"
                    )
                )
            ),

            "liquidity": (
                self._safe_float(
                    candidate.get(
                        "liquidity"
                    )
                )
            ),

            "volume_24h": (
                self._safe_float(
                    candidate.get(
                        "volume_24h",
                        candidate.get(
                            "volume",
                            0
                        )
                    )
                )
            ),

            "price_change_1h": (
                self._safe_float(
                    candidate.get(
                        "price_change_1h"
                    )
                )
            ),

            "price_change_24h": (
                self._safe_float(
                    candidate.get(
                        "price_change_24h"
                    )
                )
            ),

            "buys_1h": (
                self._safe_int(
                    candidate.get(
                        "buys_1h"
                    )
                )
            ),

            "sells_1h": (
                self._safe_int(
                    candidate.get(
                        "sells_1h"
                    )
                )
            ),

            "pair_created_at": (
                candidate.get(
                    "pair_created_at"
                )
            ),

            "sources": (
                list(
                    sources
                )
            ),

            "discovery_sources": (
                list(
                    sources
                )
            ),

            "source_count": (
                source_count
            ),

            "cross_source": (
                cross_source
            ),

            "cross_source_bonus": (
                self._safe_float(
                    candidate.get(
                        "cross_source_bonus",
                        0.0
                    )
                )
            ),

            "discovery_confidence": (
                discovery_confidence
            ),

            "source_reasons": (
                source_reasons
            ),

            "source_rank": (
                self._safe_int(
                    candidate.get(
                        "source_rank",
                        0
                    )
                )
            ),

            "discovered_at": (
                candidate.get(
                    "discovered_at"
                )
                or
                datetime.utcnow()
            ),

            "raw": (
                candidate.get(
                    "raw",
                    {}
                )
            ),

            "priority_score": 0.0,
        }


    # =========================================================
    # MERGE DUPLICATES
    # =========================================================

    def _merge(
        self,
        existing,
        incoming,
    ):

        if (
            not existing[
                "name"
            ]
            and
            incoming[
                "name"
            ]
        ):

            existing[
                "name"
            ] = (
                incoming[
                    "name"
                ]
            )

        if (
            not existing[
                "symbol"
            ]
            and
            incoming[
                "symbol"
            ]
        ):

            existing[
                "symbol"
            ] = (
                incoming[
                    "symbol"
                ]
            )

        for field in (
            "price",
            "market_cap",
            "liquidity",
            "volume_24h",
        ):

            if (
                incoming[
                    field
                ]
                >
                existing[
                    field
                ]
            ):

                existing[
                    field
                ] = (
                    incoming[
                        field
                    ]
                )

        if (
            incoming[
                "price_change_1h"
            ]
            != 0
        ):

            existing[
                "price_change_1h"
            ] = (
                incoming[
                    "price_change_1h"
                ]
            )

        if (
            incoming[
                "price_change_24h"
            ]
            != 0
        ):

            existing[
                "price_change_24h"
            ] = (
                incoming[
                    "price_change_24h"
                ]
            )

        existing[
            "buys_1h"
        ] = max(
            existing[
                "buys_1h"
            ],
            incoming[
                "buys_1h"
            ],
        )

        existing[
            "sells_1h"
        ] = max(
            existing[
                "sells_1h"
            ],
            incoming[
                "sells_1h"
            ],
        )

        for source in incoming[
            "sources"
        ]:

            if source not in existing[
                "sources"
            ]:

                existing[
                    "sources"
                ].append(
                    source
                )

        existing[
            "discovery_sources"
        ] = list(
            existing[
                "sources"
            ]
        )

        existing[
            "source_count"
        ] = len(
            existing[
                "sources"
            ]
        )

        existing[
            "cross_source"
        ] = (
            existing[
                "source_count"
            ]
            >= 2
        )

        if existing[
            "cross_source"
        ]:

            existing[
                "discovery_confidence"
            ] = max(
                existing[
                    "discovery_confidence"
                ],
                incoming[
                    "discovery_confidence"
                ],
                100.0,
            )

        else:

            existing[
                "discovery_confidence"
            ] = max(
                existing[
                    "discovery_confidence"
                ],
                incoming[
                    "discovery_confidence"
                ],
            )

        existing[
            "cross_source_bonus"
        ] = max(
            existing[
                "cross_source_bonus"
            ],
            incoming[
                "cross_source_bonus"
            ],
        )

        for reason in incoming[
            "source_reasons"
        ]:

            if reason not in existing[
                "source_reasons"
            ]:

                existing[
                    "source_reasons"
                ].append(
                    reason
                )

        existing_rank = (
            existing.get(
                "source_rank",
                0
            )
        )

        incoming_rank = (
            incoming.get(
                "source_rank",
                0
            )
        )

        if (
            existing_rank <= 0
            and
            incoming_rank > 0
        ):

            existing[
                "source_rank"
            ] = (
                incoming_rank
            )

        elif (
            incoming_rank > 0
            and
            existing_rank > 0
        ):

            existing[
                "source_rank"
            ] = min(
                existing_rank,
                incoming_rank,
            )

        return existing


    # =========================================================
    # COOLDOWN
    # =========================================================

    def _on_cooldown(
        self,
        coin_address,
    ):

        last = (
            self._last_scanned.get(
                coin_address
            )
        )

        if last is None:

            return False

        cutoff = (
            datetime.utcnow()
            - timedelta(
                minutes=(
                    self.cooldown_minutes
                )
            )
        )

        return (
            last >= cutoff
        )


    def mark_scanned(
        self,
        coin_address,
    ):

        self._last_scanned[
            coin_address
        ] = (
            datetime.utcnow()
        )


    # =========================================================
    # FILTER
    # =========================================================

    def passes_filter(
        self,
        candidate,
    ):

        market_cap = (
            candidate[
                "market_cap"
            ]
        )

        liquidity = (
            candidate[
                "liquidity"
            ]
        )

        volume = (
            candidate[
                "volume_24h"
            ]
        )

        has_market_data = any(
            [
                market_cap > 0,
                liquidity > 0,
                volume > 0,
            ]
        )

        if has_market_data:

            if (
                liquidity
                <
                self.min_liquidity
            ):

                return False

            if (
                volume
                <
                self.min_volume_24h
            ):

                return False

            if (
                market_cap > 0
                and
                market_cap
                <
                self.min_market_cap
            ):

                return False

            if (
                market_cap
                >
                self.max_market_cap
            ):

                return False

        return True


    # =========================================================
    # PRIORITY
    # =========================================================

    def calculate_priority(
        self,
        candidate,
    ):

        score = 0.0

        market_cap = (
            candidate[
                "market_cap"
            ]
        )

        liquidity = (
            candidate[
                "liquidity"
            ]
        )

        volume = (
            candidate[
                "volume_24h"
            ]
        )

        buys = (
            candidate[
                "buys_1h"
            ]
        )

        sells = (
            candidate[
                "sells_1h"
            ]
        )

        tx_count = (
            buys
            + sells
        )

        change_1h = (
            candidate[
                "price_change_1h"
            ]
        )

        source_count = len(
            candidate.get(
                "sources",
                []
            )
        )


        if source_count >= 3:

            score += 15

        elif source_count == 2:

            score += 10

        elif source_count == 1:

            score += 4


        if liquidity > 0:

            score += min(
                20,
                max(
                    0,
                    math.log10(
                        liquidity
                    )
                    * 4
                    - 8,
                ),
            )


        if volume > 0:

            score += min(
                20,
                max(
                    0,
                    math.log10(
                        volume
                    )
                    * 4
                    - 8,
                ),
            )


        if tx_count >= 300:

            score += 20

        elif tx_count >= 150:

            score += 16

        elif tx_count >= 75:

            score += 12

        elif tx_count >= 30:

            score += 8

        elif tx_count >= 10:

            score += 4


        if tx_count > 0:

            buy_ratio = (
                buys
                / tx_count
            )

            if buy_ratio >= 0.70:

                score += 10

            elif buy_ratio >= 0.60:

                score += 7

            elif buy_ratio >= 0.52:

                score += 3


        if market_cap > 0:

            if market_cap <= 100_000:

                score += 10

            elif market_cap <= 500_000:

                score += 8

            elif market_cap <= 2_000_000:

                score += 5

            elif market_cap <= 10_000_000:

                score += 2


        if change_1h >= 100:

            score += 10

        elif change_1h >= 50:

            score += 8

        elif change_1h >= 20:

            score += 6

        elif change_1h >= 5:

            score += 4

        elif change_1h > 0:

            score += 2


        if change_1h <= -70:

            score -= 20

        elif change_1h <= -40:

            score -= 12

        elif change_1h <= -20:

            score -= 5


        return round(
            max(
                score,
                0,
            ),
            2,
        )


    # =========================================================
    # ADD
    # =========================================================

    def add(
        self,
        candidate,
    ):

        normalized = (
            self._normalize(
                candidate
            )
        )

        if normalized is None:

            return False

        address = (
            normalized[
                "coin_address"
            ]
        )

        if self._on_cooldown(
            address
        ):

            return False

        if address in self._queue:

            normalized = (
                self._merge(
                    self._queue[
                        address
                    ],
                    normalized,
                )
            )

        if not self.passes_filter(
            normalized
        ):

            self._queue.pop(
                address,
                None,
            )

            return False

        normalized[
            "priority_score"
        ] = (
            self.calculate_priority(
                normalized
            )
        )

        self._queue[
            address
        ] = (
            normalized
        )

        return True


    def add_many(
        self,
        candidates,
    ):

        added = 0

        for candidate in candidates:

            if self.add(
                candidate
            ):

                added += 1

        return added


    # =========================================================
    # SORT / POP
    # =========================================================

    def ranked(
        self,
    ):

        return sorted(
            self._queue.values(),

            key=lambda item: (
                item[
                    "priority_score"
                ],
                item[
                    "source_count"
                ],
                item[
                    "volume_24h"
                ],
                item[
                    "liquidity"
                ],
            ),

            reverse=True,
        )


    def pop_batch(
        self,
        limit: int = 5,
    ):

        limit = max(
            1,
            int(
                limit
            ),
        )

        ranked = (
            self.ranked()[
                :limit
            ]
        )

        for candidate in ranked:

            address = (
                candidate[
                    "coin_address"
                ]
            )

            self._queue.pop(
                address,
                None,
            )

            self.mark_scanned(
                address
            )

        return ranked


    # =========================================================
    # INFO
    # =========================================================

    def size(
        self,
    ):

        return len(
            self._queue
        )


    def clear(
        self,
    ):

        self._queue.clear()