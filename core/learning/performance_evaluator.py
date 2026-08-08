from statistics import median

from database.database import SessionLocal

from database.models.feed_case import FeedCase
from database.models.feed_outcome import FeedOutcome


class PerformanceEvaluator:

    def __init__(self):

        self.name = "Performance Evaluator"


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
            ValueError
        ):
            return default


    @staticmethod
    def _score_bucket(
        score
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
        quality
    ):

        quality = float(
            quality or 0
        )

        if quality >= 90:
            return "HIGH"

        if quality >= 60:
            return "MEDIUM"

        return "LOW"


    def _case_outcomes(
        self,
        db,
        feed_case
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


        final = by_checkpoint.get(
            "24h"
        )

        if final is None:
            return None


        returns = [
            self._safe_float(
                row.return_pct
            )
            for row in rows
        ]


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

        final_liquidity = (
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
            final_liquidity <= -80
        ):
            winner = False


        return {
            "15m": self._safe_float(
                by_checkpoint.get(
                    "15m"
                ).return_pct
                if by_checkpoint.get(
                    "15m"
                )
                else 0
            ),

            "1h": self._safe_float(
                by_checkpoint.get(
                    "1h"
                ).return_pct
                if by_checkpoint.get(
                    "1h"
                )
                else 0
            ),

            "6h": self._safe_float(
                by_checkpoint.get(
                    "6h"
                ).return_pct
                if by_checkpoint.get(
                    "6h"
                )
                else 0
            ),

            "24h": final_return,

            "peak": peak_return,

            "drawdown": worst_return,

            "liquidity_24h": final_liquidity,

            "winner": winner,
        }


    def _group_stats(
        self,
        cases
    ):

        groups = {}


        for item in cases:

            key = item[
                "group"
            ]

            if key not in groups:

                groups[
                    key
                ] = {
                    "count": 0,
                    "wins": 0,
                    "returns": [],
                    "peaks": [],
                    "drawdowns": [],
                }


            group = groups[
                key
            ]

            group[
                "count"
            ] += 1


            if item[
                "winner"
            ]:

                group[
                    "wins"
                ] += 1


            group[
                "returns"
            ].append(
                item[
                    "return_24h"
                ]
            )

            group[
                "peaks"
            ].append(
                item[
                    "peak"
                ]
            )

            group[
                "drawdowns"
            ].append(
                item[
                    "drawdown"
                ]
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


            result[
                key
            ] = {
                "count": count,

                "wins": wins,

                "win_rate": round(
                    (
                        wins
                        / count
                        * 100
                    )
                    if count
                    else 0,
                    2
                ),

                "median_24h": round(
                    median(
                        group[
                            "returns"
                        ]
                    ),
                    2
                ),

                "median_peak": round(
                    median(
                        group[
                            "peaks"
                        ]
                    ),
                    2
                ),

                "median_drawdown": round(
                    median(
                        group[
                            "drawdowns"
                        ]
                    ),
                    2
                ),
            }


        return result


    def evaluate(
        self
    ):

        db = SessionLocal()


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
                        feed_case
                    )
                )

                if outcome is None:
                    continue


                case_rows.append(
                    {
                        "id": feed_case.id,

                        "symbol": (
                            feed_case.symbol
                        ),

                        "narrative": (
                            feed_case.narrative
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
                            feed_case.signal
                        ),

                        "decision": (
                            feed_case.decision
                        ),

                        "winner": (
                            outcome[
                                "winner"
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
                    }
                )


            total = len(
                case_rows
            )

            wins = sum(
                1
                for item
                in case_rows
                if item[
                    "winner"
                ]
            )


            false_positives = [
                item
                for item
                in case_rows
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
                for item
                in case_rows
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


            score_groups = []

            quality_groups = []

            narrative_groups = []


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
                        )
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
                        )
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
                        )
                    }
                )


            if total > 0:

                median_15m = median(
                    [
                        item[
                            "return_15m"
                        ]
                        for item
                        in case_rows
                    ]
                )

                median_1h = median(
                    [
                        item[
                            "return_1h"
                        ]
                        for item
                        in case_rows
                    ]
                )

                median_6h = median(
                    [
                        item[
                            "return_6h"
                        ]
                        for item
                        in case_rows
                    ]
                )

                median_24h = median(
                    [
                        item[
                            "return_24h"
                        ]
                        for item
                        in case_rows
                    ]
                )

                median_peak = median(
                    [
                        item[
                            "peak"
                        ]
                        for item
                        in case_rows
                    ]
                )

                median_drawdown = median(
                    [
                        item[
                            "drawdown"
                        ]
                        for item
                        in case_rows
                    ]
                )

            else:

                median_15m = 0
                median_1h = 0
                median_6h = 0
                median_24h = 0
                median_peak = 0
                median_drawdown = 0


            return {
                "completed_cases": total,

                "wins": wins,

                "losses_or_mixed": (
                    total
                    - wins
                ),

                "win_rate": round(
                    (
                        wins
                        / total
                        * 100
                    )
                    if total
                    else 0,
                    2
                ),

                "median_returns": {
                    "15m": round(
                        median_15m,
                        2
                    ),

                    "1h": round(
                        median_1h,
                        2
                    ),

                    "6h": round(
                        median_6h,
                        2
                    ),

                    "24h": round(
                        median_24h,
                        2
                    ),

                    "peak": round(
                        median_peak,
                        2
                    ),

                    "drawdown": round(
                        median_drawdown,
                        2
                    ),
                },

                "false_positives": len(
                    false_positives
                ),

                "false_negatives": len(
                    false_negatives
                ),

                "score_buckets": (
                    self._group_stats(
                        score_groups
                    )
                ),

                "quality_buckets": (
                    self._group_stats(
                        quality_groups
                    )
                ),

                "narratives": (
                    self._group_stats(
                        narrative_groups
                    )
                ),

                "cases": (
                    case_rows
                ),
            }


        finally:

            db.close()
            