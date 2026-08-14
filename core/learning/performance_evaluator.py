from statistics import (
    median,
    mean,
)

from database.database import (
    SessionLocal,
)

from database.models.feed_case import (
    FeedCase,
)

from database.models.feed_outcome import (
    FeedOutcome,
)


class PerformanceEvaluator:

    # =========================================================
    # OUTCOME / CALIBRATION SETTINGS
    # =========================================================

    CHECKPOINT_ORDER = (
        "15m",
        "1h",
        "6h",
        "24h",
    )

    # V2 begins with case 823. Case 822 was created at
    # 2026-08-12 20:39:35 UTC; case 823 was created at
    # 2026-08-12 20:58:25 UTC after the hardened market
    # validation deployment went live.
    V2_START_CASE_ID = 823

    def __init__(self):

        self.name = (
            "Performance Evaluator"
        )


    # =========================================================
    # SAFE HELPERS
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

            return float(
                default
            )


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

            return int(
                default
            )


    @staticmethod
    def _safe_text(
        value,
        default="UNKNOWN",
    ):

        text = str(
            value
            if value is not None
            else default
        ).strip()

        return (
            text
            if text
            else default
        )


    @staticmethod
    def _safe_ratio(
        numerator,
        denominator,
    ):

        try:

            numerator = float(
                numerator or 0
            )

            denominator = float(
                denominator or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0


        if denominator <= 0:

            return 0.0


        return (
            numerator
            /
            denominator
        )


    @staticmethod
    def _rounded(
        value,
        digits=2,
    ):

        try:

            return round(
                float(
                    value
                ),
                digits,
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0


    # =========================================================
    # BUCKET HELPERS
    # =========================================================

    @staticmethod
    def _score_bucket(
        score,
    ):

        score = float(
            score or 0
        )


        if score >= 80:

            return "80-100"


        if score >= 65:

            return "65-79"


        if score >= 50:

            return "50-64"


        if score >= 35:

            return "35-49"


        return "0-34"


    @staticmethod
    def _quality_bucket(
        quality,
    ):

        quality = float(
            quality or 0
        )


        if quality >= 90:

            return "HIGH"


        if quality >= 60:

            return "MEDIUM"


        return "LOW"


    @staticmethod
    def _market_cap_bucket(
        market_cap,
    ):

        market_cap = float(
            market_cap or 0
        )


        if market_cap <= 0:

            return "UNKNOWN"


        if market_cap < 10_000:

            return "<10K"


        if market_cap < 25_000:

            return "10K-25K"


        if market_cap < 50_000:

            return "25K-50K"


        if market_cap < 100_000:

            return "50K-100K"


        if market_cap < 250_000:

            return "100K-250K"


        if market_cap < 500_000:

            return "250K-500K"


        if market_cap < 1_000_000:

            return "500K-1M"


        return "1M+"


    @staticmethod
    def _liquidity_bucket(
        liquidity,
    ):

        liquidity = float(
            liquidity or 0
        )


        if liquidity <= 0:

            return "UNKNOWN"


        if liquidity < 5_000:

            return "<5K"


        if liquidity < 10_000:

            return "5K-10K"


        if liquidity < 20_000:

            return "10K-20K"


        if liquidity < 50_000:

            return "20K-50K"


        if liquidity < 100_000:

            return "50K-100K"


        return "100K+"


    @staticmethod
    def _volume_bucket(
        volume,
    ):

        volume = float(
            volume or 0
        )


        if volume <= 0:

            return "UNKNOWN"


        if volume < 10_000:

            return "<10K"


        if volume < 50_000:

            return "10K-50K"


        if volume < 100_000:

            return "50K-100K"


        if volume < 250_000:

            return "100K-250K"


        if volume < 500_000:

            return "250K-500K"


        if volume < 1_000_000:

            return "500K-1M"


        return "1M+"


    @staticmethod
    def _ratio_bucket(
        ratio,
    ):

        ratio = float(
            ratio or 0
        )


        if ratio <= 0:

            return "0"


        if ratio < 0.10:

            return "<0.10"


        if ratio < 0.25:

            return "0.10-0.25"


        if ratio < 0.50:

            return "0.25-0.50"


        if ratio < 1.0:

            return "0.50-1.00"


        if ratio < 2.0:

            return "1.00-2.00"


        if ratio < 5.0:

            return "2.00-5.00"


        return "5.00+"


    @staticmethod
    def _component_score_bucket(
        score,
    ):

        score = float(
            score or 0
        )


        if score >= 80:

            return "80-100"


        if score >= 60:

            return "60-79"


        if score >= 40:

            return "40-59"


        if score >= 20:

            return "20-39"


        return "0-19"


    @staticmethod
    def _confidence_bucket(
        confidence,
    ):

        confidence = float(
            confidence or 0
        )


        if confidence >= 75:

            return "75-100"


        if confidence >= 50:

            return "50-74"


        if confidence >= 25:

            return "25-49"


        return "0-24"


    # =========================================================
    # OUTCOME CLASSIFICATION
    # =========================================================

    def _outcome_class(
        self,
        peak_return,
        final_return,
        worst_return,
        final_liquidity,
    ):

        # -----------------------------------------------------
        # Catastrophic failure
        # -----------------------------------------------------

        if (
            final_return <= -80
            or
            final_liquidity <= -90
        ):

            return "COLLAPSED"


        # -----------------------------------------------------
        # Strong / explosive winner
        # -----------------------------------------------------

        if (
            peak_return >= 100
            and
            final_return > -30
        ):

            return "EXPLOSIVE_WIN"


        # -----------------------------------------------------
        # Original strict winner territory
        # -----------------------------------------------------

        if (
            peak_return >= 50
            and
            final_return > -30
        ):

            return "WIN"


        # -----------------------------------------------------
        # Useful positive setup even if it misses +50%
        # -----------------------------------------------------

        if (
            peak_return >= 25
            and
            final_return > -40
        ):

            return "GOOD_MOVE"


        # -----------------------------------------------------
        # Modest move
        # -----------------------------------------------------

        if (
            peak_return >= 10
            and
            final_return > -50
        ):

            return "SMALL_MOVE"


        # -----------------------------------------------------
        # Flat / mixed
        # -----------------------------------------------------

        if (
            final_return > -50
            and
            worst_return > -70
        ):

            return "MIXED"


        return "FAILED"


    # =========================================================
    # CASE OUTCOMES
    # =========================================================

    def _case_outcomes(
        self,
        db,
        feed_case,
    ):

        rows = (
            db.query(
                FeedOutcome
            )
            .filter(
                FeedOutcome.feed_case_id
                == feed_case.id
            )
            .all()
        )


        if not rows:

            return None


        by_checkpoint = {
            row.checkpoint: row
            for row in rows
        }


        final = (
            by_checkpoint.get(
                "24h"
            )
        )


        if final is None:

            return None


        recorded_returns = [
            self._safe_float(
                row.return_pct
            )
            for row in rows
            if row.checkpoint
            in self.CHECKPOINT_ORDER
        ]


        if not recorded_returns:

            return None


        checkpoint_returns = {}


        for checkpoint in self.CHECKPOINT_ORDER:

            row = (
                by_checkpoint.get(
                    checkpoint
                )
            )

            checkpoint_returns[
                checkpoint
            ] = (
                self._safe_float(
                    row.return_pct
                )
                if row
                else 0.0
            )


        peak_return = max(
            recorded_returns
        )

        worst_return = min(
            recorded_returns
        )


        final_return = (
            self._safe_float(
                final.return_pct
            )
        )


        final_liquidity = (
            self._safe_float(
                final.liquidity_change_pct
            )
        )


        final_volume = (
            self._safe_float(
                final.volume_change_pct
            )
        )


        # =====================================================
        # ORIGINAL STRICT WINNER DEFINITION
        #
        # Keep this unchanged for report compatibility.
        # =====================================================

        winner = (
            peak_return >= 50
            and
            final_return > -30
        )


        if (
            final_return <= -50
            or
            final_liquidity <= -80
        ):

            winner = False


        outcome_class = (
            self._outcome_class(
                peak_return=(
                    peak_return
                ),

                final_return=(
                    final_return
                ),

                worst_return=(
                    worst_return
                ),

                final_liquidity=(
                    final_liquidity
                ),
            )
        )


        practical_success = (
            outcome_class
            in (
                "EXPLOSIVE_WIN",
                "WIN",
                "GOOD_MOVE",
            )
        )


        return {
            "15m": (
                checkpoint_returns[
                    "15m"
                ]
            ),

            "1h": (
                checkpoint_returns[
                    "1h"
                ]
            ),

            "6h": (
                checkpoint_returns[
                    "6h"
                ]
            ),

            "24h": (
                checkpoint_returns[
                    "24h"
                ]
            ),

            "peak": (
                peak_return
            ),

            "drawdown": (
                worst_return
            ),

            "liquidity_24h": (
                final_liquidity
            ),

            "volume_24h_change": (
                final_volume
            ),

            "winner": (
                winner
            ),

            "practical_success": (
                practical_success
            ),

            "outcome_class": (
                outcome_class
            ),
        }


    # =========================================================
    # GROUP STATISTICS
    # =========================================================

    def _group_stats(
        self,
        cases,
    ):

        groups = {}


        for item in cases:

            key = (
                self._safe_text(
                    item.get(
                        "group"
                    )
                )
            )


            if key not in groups:

                groups[
                    key
                ] = {
                    "count": 0,
                    "wins": 0,
                    "practical_successes": 0,
                    "returns_15m": [],
                    "returns_1h": [],
                    "returns_6h": [],
                    "returns_24h": [],
                    "peaks": [],
                    "drawdowns": [],
                }


            group = (
                groups[
                    key
                ]
            )


            group[
                "count"
            ] += 1


            if item.get(
                "winner"
            ):

                group[
                    "wins"
                ] += 1


            if item.get(
                "practical_success"
            ):

                group[
                    "practical_successes"
                ] += 1


            group[
                "returns_15m"
            ].append(
                self._safe_float(
                    item.get(
                        "return_15m"
                    )
                )
            )


            group[
                "returns_1h"
            ].append(
                self._safe_float(
                    item.get(
                        "return_1h"
                    )
                )
            )


            group[
                "returns_6h"
            ].append(
                self._safe_float(
                    item.get(
                        "return_6h"
                    )
                )
            )


            group[
                "returns_24h"
            ].append(
                self._safe_float(
                    item.get(
                        "return_24h"
                    )
                )
            )


            group[
                "peaks"
            ].append(
                self._safe_float(
                    item.get(
                        "peak"
                    )
                )
            )


            group[
                "drawdowns"
            ].append(
                self._safe_float(
                    item.get(
                        "drawdown"
                    )
                )
            )


        result = {}


        for (
            key,
            group
        ) in groups.items():

            count = (
                group[
                    "count"
                ]
            )

            wins = (
                group[
                    "wins"
                ]
            )

            practical_successes = (
                group[
                    "practical_successes"
                ]
            )


            result[
                key
            ] = {
                "count": (
                    count
                ),

                "wins": (
                    wins
                ),

                "win_rate": round(
                    (
                        wins
                        /
                        count
                        *
                        100
                    )
                    if count
                    else 0,
                    2,
                ),

                "practical_successes": (
                    practical_successes
                ),

                "practical_success_rate": round(
                    (
                        practical_successes
                        /
                        count
                        *
                        100
                    )
                    if count
                    else 0,
                    2,
                ),

                "median_15m": round(
                    median(
                        group[
                            "returns_15m"
                        ]
                    ),
                    2,
                ),

                "median_1h": round(
                    median(
                        group[
                            "returns_1h"
                        ]
                    ),
                    2,
                ),

                "median_6h": round(
                    median(
                        group[
                            "returns_6h"
                        ]
                    ),
                    2,
                ),

                "median_24h": round(
                    median(
                        group[
                            "returns_24h"
                        ]
                    ),
                    2,
                ),

                "median_peak": round(
                    median(
                        group[
                            "peaks"
                        ]
                    ),
                    2,
                ),

                "median_drawdown": round(
                    median(
                        group[
                            "drawdowns"
                        ]
                    ),
                    2,
                ),
            }


        return result


    # =========================================================
    # NUMERIC PROFILE
    # =========================================================

    def _numeric_profile(
        self,
        cases,
        field,
    ):

        values = [
            self._safe_float(
                item.get(
                    field
                )
            )
            for item in cases
            if item.get(
                field
            ) is not None
        ]


        if not values:

            return {
                "count": 0,
                "median": 0.0,
                "average": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
            }


        return {
            "count": len(
                values
            ),

            "median": round(
                median(
                    values
                ),
                4,
            ),

            "average": round(
                mean(
                    values
                ),
                4,
            ),

            "minimum": round(
                min(
                    values
                ),
                4,
            ),

            "maximum": round(
                max(
                    values
                ),
                4,
            ),
        }


    # =========================================================
    # WINNERS VS NON-WINNERS
    # =========================================================

    def _winner_comparison(
        self,
        cases,
    ):

        winners = [
            item
            for item in cases
            if item.get(
                "winner"
            )
        ]


        non_winners = [
            item
            for item in cases
            if not item.get(
                "winner"
            )
        ]


        practical = [
            item
            for item in cases
            if item.get(
                "practical_success"
            )
        ]


        fields = (
            "t0_market_cap",
            "t0_liquidity",
            "t0_volume_24h",
            "liquidity_mc_ratio",
            "volume_mc_ratio",
            "market_score",
            "social_score",
            "wallet_score",
            "score",
            "quality",
            "confidence",
            "return_15m",
            "return_1h",
            "return_6h",
            "return_24h",
            "peak",
            "drawdown",
        )


        comparison = {}


        for field in fields:

            comparison[
                field
            ] = {
                "winners": (
                    self._numeric_profile(
                        winners,
                        field,
                    )
                ),

                "non_winners": (
                    self._numeric_profile(
                        non_winners,
                        field,
                    )
                ),

                "practical_successes": (
                    self._numeric_profile(
                        practical,
                        field,
                    )
                ),
            }


        return {
            "winner_count": len(
                winners
            ),

            "non_winner_count": len(
                non_winners
            ),

            "practical_success_count": len(
                practical
            ),

            "features": (
                comparison
            ),
        }


    # =========================================================
    # OUTCOME CLASS SUMMARY
    # =========================================================

    def _outcome_classes(
        self,
        cases,
    ):

        counts = {}


        for item in cases:

            name = (
                item.get(
                    "outcome_class"
                )
                or
                "UNKNOWN"
            )


            counts[
                name
            ] = (
                counts.get(
                    name,
                    0,
                )
                +
                1
            )


        total = len(
            cases
        )


        result = {}


        for (
            name,
            count
        ) in counts.items():

            result[
                name
            ] = {
                "count": (
                    count
                ),

                "rate": round(
                    (
                        count
                        /
                        total
                        *
                        100
                    )
                    if total
                    else 0,
                    2,
                ),
            }


        return result


    # =========================================================
    # EARLY CHECKPOINT ANALYSIS
    # =========================================================

    def _early_checkpoint_analysis(
        self,
        cases,
    ):

        buckets = {
            "15m_positive": [],
            "15m_0_to_-10": [],
            "15m_-10_to_-25": [],
            "15m_below_-25": [],

            "1h_positive": [],
            "1h_0_to_-25": [],
            "1h_-25_to_-50": [],
            "1h_below_-50": [],
        }


        for item in cases:

            r15 = (
                self._safe_float(
                    item.get(
                        "return_15m"
                    )
                )
            )

            r1h = (
                self._safe_float(
                    item.get(
                        "return_1h"
                    )
                )
            )


            if r15 > 0:

                buckets[
                    "15m_positive"
                ].append(
                    item
                )

            elif r15 >= -10:

                buckets[
                    "15m_0_to_-10"
                ].append(
                    item
                )

            elif r15 >= -25:

                buckets[
                    "15m_-10_to_-25"
                ].append(
                    item
                )

            else:

                buckets[
                    "15m_below_-25"
                ].append(
                    item
                )


            if r1h > 0:

                buckets[
                    "1h_positive"
                ].append(
                    item
                )

            elif r1h >= -25:

                buckets[
                    "1h_0_to_-25"
                ].append(
                    item
                )

            elif r1h >= -50:

                buckets[
                    "1h_-25_to_-50"
                ].append(
                    item
                )

            else:

                buckets[
                    "1h_below_-50"
                ].append(
                    item
                )


        result = {}


        for (
            name,
            rows
        ) in buckets.items():

            count = len(
                rows
            )

            wins = sum(
                1
                for item in rows
                if item.get(
                    "winner"
                )
            )

            practical = sum(
                1
                for item in rows
                if item.get(
                    "practical_success"
                )
            )


            result[
                name
            ] = {
                "count": (
                    count
                ),

                "wins": (
                    wins
                ),

                "win_rate": round(
                    (
                        wins
                        /
                        count
                        *
                        100
                    )
                    if count
                    else 0,
                    2,
                ),

                "practical_success_rate": round(
                    (
                        practical
                        /
                        count
                        *
                        100
                    )
                    if count
                    else 0,
                    2,
                ),

                "median_24h": round(
                    median(
                        [
                            self._safe_float(
                                item.get(
                                    "return_24h"
                                )
                            )
                            for item in rows
                        ]
                    )
                    if rows
                    else 0,
                    2,
                ),

                "median_peak": round(
                    median(
                        [
                            self._safe_float(
                                item.get(
                                    "peak"
                                )
                            )
                            for item in rows
                        ]
                    )
                    if rows
                    else 0,
                    2,
                ),
            }


        return result


    # =========================================================
    # BEST / WORST GROUP HELPERS
    # =========================================================

    @staticmethod
    def _rank_groups(
        group_stats,
        minimum_samples=10,
        limit=10,
    ):

        eligible = [
            {
                "name": (
                    name
                ),
                **stats,
            }
            for (
                name,
                stats
            ) in group_stats.items()
            if int(
                stats.get(
                    "count",
                    0,
                )
                or 0
            )
            >= minimum_samples
        ]


        eligible.sort(
            key=lambda item: (
                float(
                    item.get(
                        "win_rate",
                        0,
                    )
                    or 0
                ),

                float(
                    item.get(
                        "practical_success_rate",
                        0,
                    )
                    or 0
                ),

                float(
                    item.get(
                        "median_peak",
                        0,
                    )
                    or 0
                ),

                int(
                    item.get(
                        "count",
                        0,
                    )
                    or 0
                ),
            ),
            reverse=True,
        )


        return eligible[
            :limit
        ]


    # =========================================================
    # OLD VS V2 COHORTS
    # =========================================================

    def _cohort_name(self, feed_case):

        case_id = self._safe_int(
            getattr(feed_case, "id", 0)
        )

        if case_id <= 0:
            return "UNKNOWN"

        return (
            "V2"
            if case_id >= self.V2_START_CASE_ID
            else "OLD"
        )


    def _cohort_summary(self, rows):

        count = len(rows)

        if count <= 0:

            return {
                "cases": 0,
                "wins": 0,
                "win_rate": 0.0,
                "practical_successes": 0,
                "practical_success_rate": 0.0,
                "false_positives": 0,
                "false_positive_rate": 0.0,
                "false_negatives": 0,
                "median_15m": 0.0,
                "median_1h": 0.0,
                "median_6h": 0.0,
                "median_24h": 0.0,
                "median_peak": 0.0,
                "median_drawdown": 0.0,
                "score_buckets": {},
            }


        wins = sum(
            1
            for item in rows
            if item.get("winner")
        )

        practical = sum(
            1
            for item in rows
            if item.get("practical_success")
        )

        false_positives = sum(
            1
            for item in rows
            if (
                self._safe_float(
                    item.get("score")
                )
                >= 65
                and
                not item.get("winner")
            )
        )

        false_negatives = sum(
            1
            for item in rows
            if (
                self._safe_float(
                    item.get("score")
                )
                < 50
                and
                item.get("winner")
            )
        )


        def med(field):

            values = [
                self._safe_float(
                    item.get(field)
                )
                for item in rows
            ]

            return (
                round(median(values), 2)
                if values
                else 0.0
            )


        score_groups = [
            {
                **item,
                "group": self._score_bucket(
                    item.get("score")
                ),
            }
            for item in rows
        ]


        return {
            "cases": count,

            "wins": wins,

            "win_rate": round(
                wins / count * 100,
                2,
            ),

            "practical_successes": practical,

            "practical_success_rate": round(
                practical / count * 100,
                2,
            ),

            "false_positives": (
                false_positives
            ),

            "false_positive_rate": round(
                false_positives / count * 100,
                2,
            ),

            "false_negatives": (
                false_negatives
            ),

            "median_15m": med("return_15m"),

            "median_1h": med("return_1h"),

            "median_6h": med("return_6h"),

            "median_24h": med("return_24h"),

            "median_peak": med("peak"),

            "median_drawdown": med("drawdown"),

            "score_buckets": (
                self._group_stats(
                    score_groups
                )
            ),
        }


    def _cohort_comparison(self, case_rows):

        old = self._cohort_summary(
            [
                item
                for item in case_rows
                if item.get("cohort") == "OLD"
            ]
        )

        v2 = self._cohort_summary(
            [
                item
                for item in case_rows
                if item.get("cohort") == "V2"
            ]
        )


        return {
            "v2_start_case_id": (
                self.V2_START_CASE_ID
            ),

            "old": old,

            "v2": v2,

            "delta_v2_minus_old": {
                "win_rate": round(
                    v2["win_rate"]
                    - old["win_rate"],
                    2,
                ),

                "practical_success_rate": round(
                    v2["practical_success_rate"]
                    - old["practical_success_rate"],
                    2,
                ),

                "false_positive_rate": round(
                    v2["false_positive_rate"]
                    - old["false_positive_rate"],
                    2,
                ),

                "median_24h": round(
                    v2["median_24h"]
                    - old["median_24h"],
                    2,
                ),

                "median_peak": round(
                    v2["median_peak"]
                    - old["median_peak"],
                    2,
                ),

                "median_drawdown": round(
                    v2["median_drawdown"]
                    - old["median_drawdown"],
                    2,
                ),
            },
        }


    # =========================================================
    # BUILD CASE ROW
    # =========================================================

    def _build_case_row(
        self,
        feed_case,
        outcome,
    ):

        market_cap = (
            self._safe_float(
                feed_case.t0_market_cap
            )
        )

        liquidity = (
            self._safe_float(
                feed_case.t0_liquidity
            )
        )

        volume = (
            self._safe_float(
                feed_case.t0_volume_24h
            )
        )


        liquidity_mc_ratio = (
            self._safe_ratio(
                liquidity,
                market_cap,
            )
        )

        volume_mc_ratio = (
            self._safe_ratio(
                volume,
                market_cap,
            )
        )


        return {
            "id": (
                feed_case.id
            ),

            "cohort": (
                self._cohort_name(
                    feed_case
                )
            ),

            "coin_id": (
                feed_case.coin_id
            ),

            "coin_address": (
                feed_case.coin_address
            ),

            "name": (
                feed_case.name
            ),

            "symbol": (
                feed_case.symbol
            ),

            "narrative": (
                self._safe_text(
                    feed_case.narrative
                )
            ),

            "t0_price": (
                self._safe_float(
                    feed_case.t0_price
                )
            ),

            "t0_market_cap": (
                market_cap
            ),

            "t0_liquidity": (
                liquidity
            ),

            "t0_volume_24h": (
                volume
            ),

            "liquidity_mc_ratio": (
                liquidity_mc_ratio
            ),

            "volume_mc_ratio": (
                volume_mc_ratio
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

            "score": (
                self._safe_float(
                    feed_case.combined_score
                )
            ),

            "quality": (
                self._safe_float(
                    feed_case.data_quality
                )
            ),

            "signal": (
                self._safe_text(
                    feed_case.signal
                )
            ),

            "confidence": (
                self._safe_float(
                    feed_case.confidence
                )
            ),

            "decision": (
                self._safe_text(
                    feed_case.decision
                )
            ),

            "risk": (
                self._safe_text(
                    feed_case.risk
                )
            ),

            "winner": (
                outcome[
                    "winner"
                ]
            ),

            "practical_success": (
                outcome[
                    "practical_success"
                ]
            ),

            "outcome_class": (
                outcome[
                    "outcome_class"
                ]
            ),

            "return_15m": (
                outcome[
                    "15m"
                ]
            ),

            "return_1h": (
                outcome[
                    "1h"
                ]
            ),

            "return_6h": (
                outcome[
                    "6h"
                ]
            ),

            "return_24h": (
                outcome[
                    "24h"
                ]
            ),

            "peak": (
                outcome[
                    "peak"
                ]
            ),

            "drawdown": (
                outcome[
                    "drawdown"
                ]
            ),

            "liquidity_24h_change": (
                outcome[
                    "liquidity_24h"
                ]
            ),

            "volume_24h_change": (
                outcome[
                    "volume_24h_change"
                ]
            ),
        }


    # =========================================================
    # EVALUATE
    # =========================================================

    def evaluate(self):

        db = (
            SessionLocal()
        )


        try:

            completed = (
                db.query(
                    FeedCase
                )
                .filter(
                    FeedCase.status
                    == "COMPLETED"
                )
                .all()
            )


            case_rows = []


            for feed_case in completed:

                outcome = (
                    self._case_outcomes(
                        db,
                        feed_case,
                    )
                )


                if outcome is None:

                    continue


                case_rows.append(
                    self._build_case_row(
                        feed_case,
                        outcome,
                    )
                )


            # =================================================
            # BASIC COUNTS
            # =================================================

            total = len(
                case_rows
            )


            wins = sum(
                1
                for item in case_rows
                if item[
                    "winner"
                ]
            )


            practical_successes = sum(
                1
                for item in case_rows
                if item[
                    "practical_success"
                ]
            )


            false_positives = [
                item
                for item in case_rows
                if (
                    item[
                        "score"
                    ]
                    >= 65
                    and
                    not item[
                        "winner"
                    ]
                )
            ]


            false_negatives = [
                item
                for item in case_rows
                if (
                    item[
                        "score"
                    ]
                    < 50
                    and
                    item[
                        "winner"
                    ]
                )
            ]


            # =================================================
            # BUILD GROUP COLLECTIONS
            # =================================================

            score_groups = []

            quality_groups = []

            narrative_groups = []

            market_cap_groups = []

            liquidity_groups = []

            volume_groups = []

            liquidity_ratio_groups = []

            volume_ratio_groups = []

            market_score_groups = []

            social_score_groups = []

            wallet_score_groups = []

            confidence_groups = []

            signal_groups = []

            decision_groups = []

            risk_groups = []


            for item in case_rows:

                score_groups.append(
                    {
                        **item,

                        "group": (
                            self._score_bucket(
                                item[
                                    "score"
                                ]
                            )
                        ),
                    }
                )


                quality_groups.append(
                    {
                        **item,

                        "group": (
                            self._quality_bucket(
                                item[
                                    "quality"
                                ]
                            )
                        ),
                    }
                )


                narrative_groups.append(
                    {
                        **item,

                        "group": (
                            item[
                                "narrative"
                            ]
                            or
                            "UNKNOWN"
                        ),
                    }
                )


                market_cap_groups.append(
                    {
                        **item,

                        "group": (
                            self._market_cap_bucket(
                                item[
                                    "t0_market_cap"
                                ]
                            )
                        ),
                    }
                )


                liquidity_groups.append(
                    {
                        **item,

                        "group": (
                            self._liquidity_bucket(
                                item[
                                    "t0_liquidity"
                                ]
                            )
                        ),
                    }
                )


                volume_groups.append(
                    {
                        **item,

                        "group": (
                            self._volume_bucket(
                                item[
                                    "t0_volume_24h"
                                ]
                            )
                        ),
                    }
                )


                liquidity_ratio_groups.append(
                    {
                        **item,

                        "group": (
                            self._ratio_bucket(
                                item[
                                    "liquidity_mc_ratio"
                                ]
                            )
                        ),
                    }
                )


                volume_ratio_groups.append(
                    {
                        **item,

                        "group": (
                            self._ratio_bucket(
                                item[
                                    "volume_mc_ratio"
                                ]
                            )
                        ),
                    }
                )


                market_score_groups.append(
                    {
                        **item,

                        "group": (
                            self._component_score_bucket(
                                item[
                                    "market_score"
                                ]
                            )
                        ),
                    }
                )


                social_score_groups.append(
                    {
                        **item,

                        "group": (
                            self._component_score_bucket(
                                item[
                                    "social_score"
                                ]
                            )
                        ),
                    }
                )


                wallet_score_groups.append(
                    {
                        **item,

                        "group": (
                            self._component_score_bucket(
                                item[
                                    "wallet_score"
                                ]
                            )
                        ),
                    }
                )


                confidence_groups.append(
                    {
                        **item,

                        "group": (
                            self._confidence_bucket(
                                item[
                                    "confidence"
                                ]
                            )
                        ),
                    }
                )


                signal_groups.append(
                    {
                        **item,

                        "group": (
                            item[
                                "signal"
                            ]
                            or
                            "UNKNOWN"
                        ),
                    }
                )


                decision_groups.append(
                    {
                        **item,

                        "group": (
                            item[
                                "decision"
                            ]
                            or
                            "UNKNOWN"
                        ),
                    }
                )


                risk_groups.append(
                    {
                        **item,

                        "group": (
                            item[
                                "risk"
                            ]
                            or
                            "UNKNOWN"
                        ),
                    }
                )


            # =================================================
            # GROUP STATS
            # =================================================

            score_stats = (
                self._group_stats(
                    score_groups
                )
            )

            quality_stats = (
                self._group_stats(
                    quality_groups
                )
            )

            narrative_stats = (
                self._group_stats(
                    narrative_groups
                )
            )

            market_cap_stats = (
                self._group_stats(
                    market_cap_groups
                )
            )

            liquidity_stats = (
                self._group_stats(
                    liquidity_groups
                )
            )

            volume_stats = (
                self._group_stats(
                    volume_groups
                )
            )

            liquidity_ratio_stats = (
                self._group_stats(
                    liquidity_ratio_groups
                )
            )

            volume_ratio_stats = (
                self._group_stats(
                    volume_ratio_groups
                )
            )

            market_score_stats = (
                self._group_stats(
                    market_score_groups
                )
            )

            social_score_stats = (
                self._group_stats(
                    social_score_groups
                )
            )

            wallet_score_stats = (
                self._group_stats(
                    wallet_score_groups
                )
            )

            confidence_stats = (
                self._group_stats(
                    confidence_groups
                )
            )

            signal_stats = (
                self._group_stats(
                    signal_groups
                )
            )

            decision_stats = (
                self._group_stats(
                    decision_groups
                )
            )

            risk_stats = (
                self._group_stats(
                    risk_groups
                )
            )


            # =================================================
            # MEDIAN RETURNS
            # =================================================

            if total > 0:

                median_15m = median(
                    [
                        item[
                            "return_15m"
                        ]
                        for item in case_rows
                    ]
                )

                median_1h = median(
                    [
                        item[
                            "return_1h"
                        ]
                        for item in case_rows
                    ]
                )

                median_6h = median(
                    [
                        item[
                            "return_6h"
                        ]
                        for item in case_rows
                    ]
                )

                median_24h = median(
                    [
                        item[
                            "return_24h"
                        ]
                        for item in case_rows
                    ]
                )

                median_peak = median(
                    [
                        item[
                            "peak"
                        ]
                        for item in case_rows
                    ]
                )

                median_drawdown = median(
                    [
                        item[
                            "drawdown"
                        ]
                        for item in case_rows
                    ]
                )


            else:

                median_15m = 0.0

                median_1h = 0.0

                median_6h = 0.0

                median_24h = 0.0

                median_peak = 0.0

                median_drawdown = 0.0


            # =================================================
            # ADVANCED CALIBRATION
            # =================================================

            calibration = {
                "outcome_classes": (
                    self._outcome_classes(
                        case_rows
                    )
                ),

                "winner_comparison": (
                    self._winner_comparison(
                        case_rows
                    )
                ),

                "early_checkpoints": (
                    self._early_checkpoint_analysis(
                        case_rows
                    )
                ),

                "market_cap_buckets": (
                    market_cap_stats
                ),

                "liquidity_buckets": (
                    liquidity_stats
                ),

                "volume_buckets": (
                    volume_stats
                ),

                "liquidity_mc_ratio_buckets": (
                    liquidity_ratio_stats
                ),

                "volume_mc_ratio_buckets": (
                    volume_ratio_stats
                ),

                "market_score_buckets": (
                    market_score_stats
                ),

                "social_score_buckets": (
                    social_score_stats
                ),

                "wallet_score_buckets": (
                    wallet_score_stats
                ),

                "confidence_buckets": (
                    confidence_stats
                ),

                "signal_buckets": (
                    signal_stats
                ),

                "decision_buckets": (
                    decision_stats
                ),

                "risk_buckets": (
                    risk_stats
                ),

                "best_score_groups": (
                    self._rank_groups(
                        score_stats,
                        minimum_samples=10,
                    )
                ),

                "best_market_cap_groups": (
                    self._rank_groups(
                        market_cap_stats,
                        minimum_samples=10,
                    )
                ),

                "best_liquidity_groups": (
                    self._rank_groups(
                        liquidity_stats,
                        minimum_samples=10,
                    )
                ),

                "best_volume_groups": (
                    self._rank_groups(
                        volume_stats,
                        minimum_samples=10,
                    )
                ),

                "best_liquidity_ratio_groups": (
                    self._rank_groups(
                        liquidity_ratio_stats,
                        minimum_samples=10,
                    )
                ),

                "best_volume_ratio_groups": (
                    self._rank_groups(
                        volume_ratio_stats,
                        minimum_samples=10,
                    )
                ),

                "best_market_score_groups": (
                    self._rank_groups(
                        market_score_stats,
                        minimum_samples=10,
                    )
                ),

                "best_social_score_groups": (
                    self._rank_groups(
                        social_score_stats,
                        minimum_samples=10,
                    )
                ),

                "best_wallet_score_groups": (
                    self._rank_groups(
                        wallet_score_stats,
                        minimum_samples=10,
                    )
                ),

                "best_confidence_groups": (
                    self._rank_groups(
                        confidence_stats,
                        minimum_samples=10,
                    )
                ),

                "best_signal_groups": (
                    self._rank_groups(
                        signal_stats,
                        minimum_samples=10,
                    )
                ),

                "best_decision_groups": (
                    self._rank_groups(
                        decision_stats,
                        minimum_samples=10,
                    )
                ),

                "best_narratives": (
                    self._rank_groups(
                        narrative_stats,
                        minimum_samples=10,
                    )
                ),
            }


            cohort_comparison = (
                self._cohort_comparison(
                    case_rows
                )
            )


            # =================================================
            # RETURN
            #
            # Keep old keys intact for DiscordService/report.
            # =================================================

            return {
                "completed_cases": (
                    total
                ),

                "wins": (
                    wins
                ),

                "losses_or_mixed": (
                    total
                    -
                    wins
                ),

                "win_rate": round(
                    (
                        wins
                        /
                        total
                        *
                        100
                    )
                    if total
                    else 0,
                    2,
                ),

                "practical_successes": (
                    practical_successes
                ),

                "practical_success_rate": round(
                    (
                        practical_successes
                        /
                        total
                        *
                        100
                    )
                    if total
                    else 0,
                    2,
                ),

                "median_returns": {
                    "15m": round(
                        median_15m,
                        2,
                    ),

                    "1h": round(
                        median_1h,
                        2,
                    ),

                    "6h": round(
                        median_6h,
                        2,
                    ),

                    "24h": round(
                        median_24h,
                        2,
                    ),

                    "peak": round(
                        median_peak,
                        2,
                    ),

                    "drawdown": round(
                        median_drawdown,
                        2,
                    ),
                },

                "false_positives": len(
                    false_positives
                ),

                "false_negatives": len(
                    false_negatives
                ),

                "score_buckets": (
                    score_stats
                ),

                "quality_buckets": (
                    quality_stats
                ),

                "narratives": (
                    narrative_stats
                ),

                "calibration": (
                    calibration
                ),

                "cohort_comparison": (
                    cohort_comparison
                ),

                "cases": (
                    case_rows
                ),
            }


        finally:

            db.close()