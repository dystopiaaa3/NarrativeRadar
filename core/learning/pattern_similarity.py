from statistics import median

from database.database import SessionLocal

from database.models.feed_case import FeedCase
from database.models.feed_outcome import FeedOutcome


class PatternSimilarityEngine:

    def __init__(
        self,
        minimum_similarity: float = 55.0,
        max_matches: int = 25,
    ):

        self.minimum_similarity = float(
            minimum_similarity
        )

        self.max_matches = max(
            1,
            int(max_matches)
        )


    # =========================================================
    # SAFE HELPERS
    # =========================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0
    ):

        try:

            return float(
                value
                if value is not None
                else default
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    @staticmethod
    def _ratio(
        numerator,
        denominator
    ):

        numerator = float(
            numerator or 0
        )

        denominator = float(
            denominator or 0
        )

        if denominator <= 0:

            return 0.0

        return (
            numerator
            / denominator
        )


    @staticmethod
    def _numeric_similarity(
        current,
        historical,
        tolerance
    ):

        current = float(
            current or 0
        )

        historical = float(
            historical or 0
        )

        tolerance = max(
            float(tolerance),
            0.000001
        )


        difference = abs(
            current
            - historical
        )


        similarity = (
            1.0
            - (
                difference
                / tolerance
            )
        )


        return max(
            0.0,
            min(
                1.0,
                similarity
            )
        )


    @staticmethod
    def _ratio_similarity(
        current,
        historical
    ):

        current = max(
            float(current or 0),
            0.0
        )

        historical = max(
            float(historical or 0),
            0.0
        )


        if (
            current == 0
            and
            historical == 0
        ):

            return 1.0


        if (
            current <= 0
            or
            historical <= 0
        ):

            return 0.0


        smaller = min(
            current,
            historical
        )

        larger = max(
            current,
            historical
        )


        return (
            smaller
            / larger
        )


    # =========================================================
    # CURRENT FEATURE SNAPSHOT
    # =========================================================

    def build_current_features(
        self,
        narrative,
        analysis,
        market,
        signal,
        decision,
    ):

        market_cap = (
            self._safe_float(
                market.get(
                    "market_cap"
                )
            )
        )

        liquidity = (
            self._safe_float(
                market.get(
                    "liquidity"
                )
            )
        )

        volume = (
            self._safe_float(
                market.get(
                    "volume_24h"
                )
            )
        )


        return {
            "narrative": str(
                narrative
                or "UNKNOWN"
            ),

            "market_score": (
                self._safe_float(
                    analysis.get(
                        "market_score"
                    )
                )
            ),

            "social_score": (
                self._safe_float(
                    analysis.get(
                        "social_score"
                    )
                )
            ),

            "wallet_score": (
                self._safe_float(
                    analysis.get(
                        "wallet_score"
                    )
                )
            ),

            "combined_score": (
                self._safe_float(
                    analysis.get(
                        "combined_score"
                    )
                )
            ),

            "data_quality": (
                self._safe_float(
                    analysis.get(
                        "data_quality"
                    )
                )
            ),

            "liquidity_ratio": (
                self._ratio(
                    liquidity,
                    market_cap
                )
            ),

            "volume_ratio": (
                self._ratio(
                    volume,
                    market_cap
                )
            ),

            "signal": str(
                signal.get(
                    "signal",
                    "UNKNOWN"
                )
            ),

            "risk": str(
                decision.get(
                    "risk",
                    "UNKNOWN"
                )
            ),
        }


    # =========================================================
    # HISTORICAL FEATURE SNAPSHOT
    # =========================================================

    def _historical_features(
        self,
        feed_case
    ):

        return {
            "narrative": str(
                feed_case.narrative
                or "UNKNOWN"
            ),

            "market_score": (
                self._safe_float(
                    feed_case.market_score
                )
            ),

            "social_score": (
                self._safe_float(
                    feed_case.social_score
                )
            ),

            "wallet_score": (
                self._safe_float(
                    feed_case.wallet_score
                )
            ),

            "combined_score": (
                self._safe_float(
                    feed_case.combined_score
                )
            ),

            "data_quality": (
                self._safe_float(
                    feed_case.data_quality
                )
            ),

            "liquidity_ratio": (
                self._ratio(
                    feed_case.t0_liquidity,
                    feed_case.t0_market_cap
                )
            ),

            "volume_ratio": (
                self._ratio(
                    feed_case.t0_volume_24h,
                    feed_case.t0_market_cap
                )
            ),

            "signal": str(
                feed_case.signal
                or "UNKNOWN"
            ),

            "risk": str(
                feed_case.risk
                or "UNKNOWN"
            ),
        }


    # =========================================================
    # SIMILARITY SCORE
    # =========================================================

    def calculate_similarity(
        self,
        current,
        historical
    ):

        score = 0.0

        details = {}


        # -----------------------------------------------------
        # NARRATIVE
        # 20 points
        # -----------------------------------------------------

        narrative_match = (
            current[
                "narrative"
            ].lower()
            ==
            historical[
                "narrative"
            ].lower()
        )


        if narrative_match:

            score += 20.0

            details[
                "narrative"
            ] = 1.0

        else:

            details[
                "narrative"
            ] = 0.0


        # -----------------------------------------------------
        # MARKET STRENGTH
        # 12 points
        # -----------------------------------------------------

        market_similarity = (
            self._numeric_similarity(
                current[
                    "market_score"
                ],
                historical[
                    "market_score"
                ],
                50,
            )
        )

        score += (
            market_similarity
            * 12
        )

        details[
            "market"
        ] = market_similarity


        # -----------------------------------------------------
        # SOCIAL STRENGTH
        # 12 points
        # -----------------------------------------------------

        social_similarity = (
            self._numeric_similarity(
                current[
                    "social_score"
                ],
                historical[
                    "social_score"
                ],
                50,
            )
        )

        score += (
            social_similarity
            * 12
        )

        details[
            "social"
        ] = social_similarity


        # -----------------------------------------------------
        # WALLET STRENGTH
        # 16 points
        # -----------------------------------------------------

        wallet_similarity = (
            self._numeric_similarity(
                current[
                    "wallet_score"
                ],
                historical[
                    "wallet_score"
                ],
                50,
            )
        )

        score += (
            wallet_similarity
            * 16
        )

        details[
            "wallet"
        ] = wallet_similarity


        # -----------------------------------------------------
        # COMBINED STRENGTH
        # 10 points
        # -----------------------------------------------------

        combined_similarity = (
            self._numeric_similarity(
                current[
                    "combined_score"
                ],
                historical[
                    "combined_score"
                ],
                40,
            )
        )

        score += (
            combined_similarity
            * 10
        )

        details[
            "combined"
        ] = combined_similarity


        # -----------------------------------------------------
        # LIQUIDITY / MC STRUCTURE
        # 10 points
        # -----------------------------------------------------

        liquidity_similarity = (
            self._ratio_similarity(
                current[
                    "liquidity_ratio"
                ],
                historical[
                    "liquidity_ratio"
                ],
            )
        )

        score += (
            liquidity_similarity
            * 10
        )

        details[
            "liquidity_ratio"
        ] = liquidity_similarity


        # -----------------------------------------------------
        # VOLUME / MC STRUCTURE
        # 10 points
        # -----------------------------------------------------

        volume_similarity = (
            self._ratio_similarity(
                current[
                    "volume_ratio"
                ],
                historical[
                    "volume_ratio"
                ],
            )
        )

        score += (
            volume_similarity
            * 10
        )

        details[
            "volume_ratio"
        ] = volume_similarity


        # -----------------------------------------------------
        # DATA QUALITY
        # 5 points
        # -----------------------------------------------------

        quality_similarity = (
            self._numeric_similarity(
                current[
                    "data_quality"
                ],
                historical[
                    "data_quality"
                ],
                66.67,
            )
        )

        score += (
            quality_similarity
            * 5
        )

        details[
            "data_quality"
        ] = quality_similarity


        # -----------------------------------------------------
        # SIGNAL
        # 3 points
        # -----------------------------------------------------

        signal_match = (
            current[
                "signal"
            ]
            ==
            historical[
                "signal"
            ]
        )

        if signal_match:

            score += 3

            details[
                "signal"
            ] = 1.0

        else:

            details[
                "signal"
            ] = 0.0


        # -----------------------------------------------------
        # RISK
        # 2 points
        # -----------------------------------------------------

        risk_match = (
            current[
                "risk"
            ]
            ==
            historical[
                "risk"
            ]
        )

        if risk_match:

            score += 2

            details[
                "risk"
            ] = 1.0

        else:

            details[
                "risk"
            ] = 0.0


        return {
            "similarity": round(
                score,
                2
            ),

            "details": (
                details
            ),
        }


    # =========================================================
    # OUTCOME DATA
    # =========================================================

    def _outcome_summary(
        self,
        db,
        feed_case
    ):

        outcomes = (
            db.query(
                FeedOutcome
            )
            .filter(
                FeedOutcome.feed_case_id
                == feed_case.id
            )
            .all()
        )


        final = next(
            (
                item
                for item
                in outcomes
                if item.checkpoint
                == "24h"
            ),
            None
        )


        if final is None:

            return None


        returns = [
            self._safe_float(
                item.return_pct
            )
            for item
            in outcomes
        ]


        if not returns:

            return None


        peak_return = max(
            returns
        )

        worst_return = min(
            returns
        )

        final_return = (
            self._safe_float(
                final.return_pct
            )
        )

        liquidity_change = (
            self._safe_float(
                final.liquidity_change_pct
            )
        )


        winner = (
            peak_return >= 50
            and
            final_return > -30
        )


        if (
            final_return <= -50
            or
            liquidity_change <= -80
        ):

            winner = False


        return {
            "winner": winner,

            "peak_return": (
                peak_return
            ),

            "worst_return": (
                worst_return
            ),

            "final_return": (
                final_return
            ),

            "liquidity_change": (
                liquidity_change
            ),
        }


    # =========================================================
    # MAIN MATCH ENGINE
    # =========================================================

    def match(
        self,
        current_features
    ):

        db = SessionLocal()


        try:

            completed_cases = (
                db.query(
                    FeedCase
                )
                .filter(
                    FeedCase.status
                    == "COMPLETED"
                )
                .all()
            )


            matches = []


            for feed_case in completed_cases:

                outcome = (
                    self._outcome_summary(
                        db,
                        feed_case
                    )
                )


                if outcome is None:

                    continue


                historical = (
                    self._historical_features(
                        feed_case
                    )
                )


                result = (
                    self.calculate_similarity(
                        current_features,
                        historical,
                    )
                )


                similarity = (
                    result[
                        "similarity"
                    ]
                )


                if (
                    similarity
                    <
                    self.minimum_similarity
                ):

                    continue


                matches.append(
                    {
                        "feed_case_id": (
                            feed_case.id
                        ),

                        "name": (
                            feed_case.name
                        ),

                        "symbol": (
                            feed_case.symbol
                        ),

                        "narrative": (
                            feed_case.narrative
                        ),

                        "similarity": (
                            similarity
                        ),

                        "winner": (
                            outcome[
                                "winner"
                            ]
                        ),

                        "peak_return": (
                            outcome[
                                "peak_return"
                            ]
                        ),

                        "worst_return": (
                            outcome[
                                "worst_return"
                            ]
                        ),

                        "final_return": (
                            outcome[
                                "final_return"
                            ]
                        ),

                        "liquidity_change": (
                            outcome[
                                "liquidity_change"
                            ]
                        ),

                        "details": (
                            result[
                                "details"
                            ]
                        ),
                    }
                )


            matches.sort(
                key=lambda item: (
                    item[
                        "similarity"
                    ]
                ),
                reverse=True
            )


            matches = (
                matches[
                    :self.max_matches
                ]
            )


            return self._aggregate(
                matches
            )


        finally:

            db.close()


    # =========================================================
    # AGGREGATE MATCHES
    # =========================================================

    def _aggregate(
        self,
        matches
    ):

        count = len(
            matches
        )


        if count == 0:

            return {
                "history_available": False,

                "sample_level": (
                    "INSUFFICIENT_HISTORY"
                ),

                "match_count": 0,

                "best_similarity": 0.0,

                "weighted_success_rate": 0.0,

                "median_peak_return": 0.0,

                "median_final_return": 0.0,

                "median_worst_return": 0.0,

                "median_liquidity_change": 0.0,

                "matches": [],
            }


        total_weight = sum(
            item[
                "similarity"
            ]
            for item
            in matches
        )


        weighted_wins = sum(
            (
                item[
                    "similarity"
                ]
                if item[
                    "winner"
                ]
                else 0
            )
            for item
            in matches
        )


        if total_weight > 0:

            weighted_success_rate = (
                weighted_wins
                / total_weight
                * 100
            )

        else:

            weighted_success_rate = 0.0


        if count < 10:

            sample_level = (
                "INSUFFICIENT_HISTORY"
            )

            history_available = False


        elif count < 30:

            sample_level = (
                "EXPERIMENTAL"
            )

            history_available = True


        elif count < 100:

            sample_level = (
                "LIMITED"
            )

            history_available = True


        else:

            sample_level = (
                "ESTABLISHED"
            )

            history_available = True


        return {
            "history_available": (
                history_available
            ),

            "sample_level": (
                sample_level
            ),

            "match_count": (
                count
            ),

            "best_similarity": (
                round(
                    matches[0][
                        "similarity"
                    ],
                    2
                )
            ),

            "weighted_success_rate": (
                round(
                    weighted_success_rate,
                    2
                )
            ),

            "median_peak_return": (
                round(
                    median(
                        [
                            item[
                                "peak_return"
                            ]
                            for item
                            in matches
                        ]
                    ),
                    2
                )
            ),

            "median_final_return": (
                round(
                    median(
                        [
                            item[
                                "final_return"
                            ]
                            for item
                            in matches
                        ]
                    ),
                    2
                )
            ),

            "median_worst_return": (
                round(
                    median(
                        [
                            item[
                                "worst_return"
                            ]
                            for item
                            in matches
                        ]
                    ),
                    2
                )
            ),

            "median_liquidity_change": (
                round(
                    median(
                        [
                            item[
                                "liquidity_change"
                            ]
                            for item
                            in matches
                        ]
                    ),
                    2
                )
            ),

            "matches": (
                matches
            ),
        }