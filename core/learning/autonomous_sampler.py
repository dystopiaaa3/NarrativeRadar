import hashlib

from datetime import (
    datetime,
    timedelta,
)

from database.database import (
    SessionLocal,
)

from database.models.feed_case import (
    FeedCase,
)


class AutonomousLearningSampler:

    """
    Creates silent learning cases from completed
    BackgroundScanner / LiveRadar scans.

    This does NOT run another LiveRadar scan.

    It reuses the scan that already happened, so
    autonomous learning adds almost no latency.

    The existing FeedLearningService later handles:
        15m
        1h
        6h
        24h

    outcomes for these cases exactly like /feed cases.
    """

    def __init__(
        self,
        max_cases_per_hour: int = 12,
        coin_cooldown_hours: int = 24,
        minimum_data_quality: float = 33.0,
        strong_score: float = 55.0,
        control_sample_rate: int = 4,
    ):

        self.max_cases_per_hour = max(
            1,
            int(
                max_cases_per_hour
            ),
        )

        self.coin_cooldown_hours = max(
            1,
            int(
                coin_cooldown_hours
            ),
        )

        self.minimum_data_quality = float(
            minimum_data_quality
        )

        self.strong_score = float(
            strong_score
        )

        # 4 means approximately 1 in 4 weaker
        # candidates become control examples.

        self.control_sample_rate = max(
            2,
            int(
                control_sample_rate
            ),
        )


    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
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
    def _safe_int(
        value,
        default=0,
    ):

        try:

            return int(
                float(
                    value
                    if value is not None
                    else default
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    # =========================================================
    # CONTROL SAMPLE
    # =========================================================

    def _is_control_sample(
        self,
        coin_address,
    ):

        """
        Deterministic sampling.

        Same address always produces the same decision,
        which is better than random behavior while testing.
        """

        digest = hashlib.sha256(
            coin_address.encode(
                "utf-8"
            )
        ).hexdigest()

        bucket = int(
            digest[:8],
            16,
        )

        return (
            bucket
            %
            self.control_sample_rate
            == 0
        )


    # =========================================================
    # DATABASE LIMITS
    # =========================================================

    def _recent_case_exists(
        self,
        db,
        coin_address,
    ):

        cutoff = (
            datetime.utcnow()
            - timedelta(
                hours=(
                    self.coin_cooldown_hours
                )
            )
        )

        return (
            db.query(
                FeedCase
            )
            .filter(
                FeedCase.coin_address
                == coin_address
            )
            .filter(
                FeedCase.created_at
                >= cutoff
            )
            .first()
            is not None
        )


    def _hourly_case_count(
        self,
        db,
    ):

        cutoff = (
            datetime.utcnow()
            - timedelta(
                hours=1
            )
        )

        return (
            db.query(
                FeedCase
            )
            .filter(
                FeedCase.created_at
                >= cutoff
            )
            .count()
        )


    # =========================================================
    # ELIGIBILITY
    # =========================================================

    def evaluate(
        self,
        candidate,
        result,
    ):

        try:

            collected = (
                result[
                    "collected"
                ]
            )

            radar = (
                result[
                    "radar"
                ]
            )

            analysis = (
                radar[
                    "analysis"
                ]
            )

            signal = (
                radar[
                    "radar"
                ][
                    "signal"
                ]
            )

            decision = (
                radar[
                    "radar"
                ][
                    "decision"
                ]
            )

        except (
            KeyError,
            TypeError,
        ):

            return {
                "eligible": False,
                "reason": (
                    "invalid_scan_result"
                ),
            }


        market = (
            collected.get(
                "market",
                {}
            )
        )


        price = self._safe_float(
            market.get(
                "price"
            )
        )

        market_cap = self._safe_float(
            market.get(
                "market_cap"
            )
        )

        liquidity = self._safe_float(
            market.get(
                "liquidity"
            )
        )

        combined = self._safe_float(
            analysis.get(
                "combined_score"
            )
        )

        quality = self._safe_float(
            analysis.get(
                "data_quality"
            )
        )

        confidence = self._safe_int(
            signal.get(
                "confidence"
            )
        )


        # -----------------------------------------------------
        # REQUIRE REAL MARKET DATA
        # -----------------------------------------------------

        if (
            price <= 0
            or
            market_cap <= 0
            or
            liquidity <= 0
        ):

            return {
                "eligible": False,
                "reason": (
                    "missing_market_data"
                ),
            }


        # -----------------------------------------------------
        # REQUIRE MINIMUM DATA COVERAGE
        # -----------------------------------------------------

        if (
            quality
            <
            self.minimum_data_quality
        ):

            return {
                "eligible": False,
                "reason": (
                    "low_data_quality"
                ),
            }


        # -----------------------------------------------------
        # STRONG / INTERESTING CASES
        # -----------------------------------------------------

        if (
            combined
            >=
            self.strong_score
        ):

            return {
                "eligible": True,
                "sample_type": (
                    "signal"
                ),
                "reason": (
                    "qualified_signal"
                ),
            }


        # -----------------------------------------------------
        # CONFIDENT WATCH CASES
        # -----------------------------------------------------

        decision_name = str(
            decision.get(
                "decision",
                ""
            )
            or ""
        ).upper()


        if (
            decision_name
            in (
                "MONITOR",
                "ENTER_WATCH",
                "ENTER",
            )
            and
            confidence >= 25
        ):

            return {
                "eligible": True,
                "sample_type": (
                    "signal"
                ),
                "reason": (
                    "qualified_decision"
                ),
            }


        # -----------------------------------------------------
        # CONTROL CASE
        #
        # We intentionally retain some weaker setups.
        #
        # Otherwise the learning dataset would be biased
        # toward tokens the model already likes.
        # -----------------------------------------------------

        address = str(
            candidate.get(
                "coin_address",
                ""
            )
            or ""
        )


        if self._is_control_sample(
            address
        ):

            return {
                "eligible": True,
                "sample_type": (
                    "control"
                ),
                "reason": (
                    "control_sample"
                ),
            }


        return {
            "eligible": False,
            "reason": (
                "not_sampled"
            ),
        }


    # =========================================================
    # CREATE CASE FROM EXISTING SCAN
    # =========================================================

    def record(
        self,
        coin_id,
        candidate,
        result,
        narrative_result,
    ):

        evaluation = (
            self.evaluate(
                candidate,
                result,
            )
        )


        if not evaluation.get(
            "eligible"
        ):

            return {
                "created": False,
                "reason": (
                    evaluation.get(
                        "reason"
                    )
                ),
            }


        address = str(
            candidate.get(
                "coin_address",
                ""
            )
            or ""
        ).strip()


        if not address:

            return {
                "created": False,
                "reason": (
                    "missing_address"
                ),
            }


        db = SessionLocal()


        try:

            # -------------------------------------------------
            # DON'T LEARN SAME TOKEN REPEATEDLY
            # -------------------------------------------------

            if self._recent_case_exists(
                db,
                address,
            ):

                return {
                    "created": False,
                    "reason": (
                        "coin_cooldown"
                    ),
                }


            # -------------------------------------------------
            # GLOBAL STORAGE / API CONTROL
            # -------------------------------------------------

            hourly_count = (
                self._hourly_case_count(
                    db
                )
            )


            if (
                hourly_count
                >=
                self.max_cases_per_hour
            ):

                return {
                    "created": False,
                    "reason": (
                        "hourly_limit"
                    ),
                }


            collected = (
                result[
                    "collected"
                ]
            )

            radar = (
                result[
                    "radar"
                ]
            )

            analysis = (
                radar[
                    "analysis"
                ]
            )

            signal = (
                radar[
                    "radar"
                ][
                    "signal"
                ]
            )

            decision = (
                radar[
                    "radar"
                ][
                    "decision"
                ]
            )

            market = (
                collected.get(
                    "market",
                    {}
                )
            )


            assignments = (
                narrative_result.get(
                    "assignments",
                    []
                )
            )


            narrative_name = (
                assignments[0][
                    "name"
                ]
                if assignments
                else
                "UNKNOWN"
            )


            name = str(
                candidate.get(
                    "name"
                )
                or
                "Unknown"
            )


            symbol = str(
                candidate.get(
                    "symbol"
                )
                or
                "UNKNOWN"
            )


            feed_case = FeedCase(
                coin_id=(
                    coin_id
                ),

                coin_address=(
                    address
                ),

                name=(
                    name
                ),

                symbol=(
                    symbol
                ),

                narrative=(
                    narrative_name
                ),

                t0_price=(
                    self._safe_float(
                        market.get(
                            "price"
                        )
                    )
                ),

                t0_market_cap=(
                    self._safe_float(
                        market.get(
                            "market_cap"
                        )
                    )
                ),

                t0_liquidity=(
                    self._safe_float(
                        market.get(
                            "liquidity"
                        )
                    )
                ),

                t0_volume_24h=(
                    self._safe_float(
                        market.get(
                            "volume_24h"
                        )
                    )
                ),

                market_score=(
                    self._safe_float(
                        analysis.get(
                            "market_score"
                        )
                    )
                ),

                social_score=(
                    self._safe_float(
                        analysis.get(
                            "social_score"
                        )
                    )
                ),

                wallet_score=(
                    self._safe_float(
                        analysis.get(
                            "wallet_score"
                        )
                    )
                ),

                combined_score=(
                    self._safe_float(
                        analysis.get(
                            "combined_score"
                        )
                    )
                ),

                data_quality=(
                    self._safe_float(
                        analysis.get(
                            "data_quality"
                        )
                    )
                ),

                signal=str(
                    signal.get(
                        "signal",
                        "UNKNOWN"
                    )
                ),

                confidence=(
                    self._safe_int(
                        signal.get(
                            "confidence"
                        )
                    )
                ),

                decision=str(
                    decision.get(
                        "decision",
                        "UNKNOWN"
                    )
                ),

                risk=str(
                    decision.get(
                        "risk",
                        "UNKNOWN"
                    )
                ),

                status="TRACKING",

                created_at=(
                    datetime.utcnow()
                ),
            )


            db.add(
                feed_case
            )

            db.commit()

            db.refresh(
                feed_case
            )


            return {
                "created": True,

                "feed_case_id": (
                    feed_case.id
                ),

                "sample_type": (
                    evaluation.get(
                        "sample_type"
                    )
                ),

                "reason": (
                    evaluation.get(
                        "reason"
                    )
                ),

                "symbol": (
                    feed_case.symbol
                ),

                "combined_score": (
                    feed_case.combined_score
                ),

                "data_quality": (
                    feed_case.data_quality
                ),
            }


        except Exception as error:

            db.rollback()

            return {
                "created": False,

                "reason": (
                    "database_error"
                ),

                "error": str(
                    error
                ),
            }


        finally:

            db.close()