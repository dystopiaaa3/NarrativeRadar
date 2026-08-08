from datetime import datetime, timedelta

from sqlalchemy import func, desc

from database.database import SessionLocal

from database.models.narrative import Narrative
from database.models.coin_narrative import CoinNarrative
from database.models.coin import Coin
from database.models.market import MarketObservation
from database.models.radar_result import RadarResult
from database.models.alert import Alert
from database.models.feed_case import FeedCase

from core.services.narrative_service import NarrativeService

from core.learning.performance_evaluator import (
    PerformanceEvaluator,
)


class DiscordService:

    def __init__(self):

        self.narratives = NarrativeService()

        self.performance = PerformanceEvaluator()


    # =========================================================
    # TRENDING
    # =========================================================

    def trending(
        self,
        duration="6h"
    ):

        return self.narratives.trending(
            duration,
            limit=10
        )


    # =========================================================
    # TOP NARRATIVES
    # =========================================================

    def top_narratives(self):

        return self.narratives.top_narratives(
            limit=10
        )


    # =========================================================
    # EMERGING
    # =========================================================

    def emerging(self):

        return self.narratives.emerging(
            hours=6,
            limit=10
        )


    # =========================================================
    # PULSE
    # =========================================================

    def pulse(self):

        return self.narratives.pulse()


    # =========================================================
    # RADAR
    # =========================================================

    def radar(self):

        return self.narratives.radar()


    # =========================================================
    # COMPARE
    # =========================================================

    def compare(
        self,
        first,
        second
    ):

        return self.narratives.compare(
            first,
            second
        )


    # =========================================================
    # ROTATION
    # =========================================================

    def rotation(self):

        db = SessionLocal()

        try:

            now = datetime.utcnow()

            current_start = (
                now
                - timedelta(hours=3)
            )

            previous_start = (
                now
                - timedelta(hours=6)
            )

            narratives = (
                db.query(Narrative)
                .filter(
                    Narrative.active.is_(True)
                )
                .all()
            )

            results = []

            for narrative in narratives:

                coin_ids = [
                    row[0]

                    for row in (
                        db.query(
                            CoinNarrative.coin_id
                        )
                        .filter(
                            CoinNarrative.narrative_id
                            == narrative.id
                        )
                        .all()
                    )
                ]

                if not coin_ids:
                    continue

                current = (
                    db.query(
                        func.avg(
                            RadarResult.combined_score
                        )
                    )
                    .filter(
                        RadarResult.coin_id.in_(
                            coin_ids
                        )
                    )
                    .filter(
                        RadarResult.timestamp
                        >= current_start
                    )
                    .scalar()
                )

                previous = (
                    db.query(
                        func.avg(
                            RadarResult.combined_score
                        )
                    )
                    .filter(
                        RadarResult.coin_id.in_(
                            coin_ids
                        )
                    )
                    .filter(
                        RadarResult.timestamp
                        >= previous_start
                    )
                    .filter(
                        RadarResult.timestamp
                        < current_start
                    )
                    .scalar()
                )

                if (
                    current is None
                    or previous is None
                ):
                    continue

                change = (
                    float(current)
                    - float(previous)
                )

                results.append(
                    {
                        "name": narrative.name,

                        "current": round(
                            float(current),
                            2
                        ),

                        "previous": round(
                            float(previous),
                            2
                        ),

                        "change": round(
                            change,
                            2
                        )
                    }
                )

            results.sort(
                key=lambda item: abs(
                    item["change"]
                ),
                reverse=True
            )

            return results[:10]

        finally:

            db.close()


    # =========================================================
    # REPORT
    # =========================================================

    def report(self):

        db = SessionLocal()

        try:

            since = (
                datetime.utcnow()
                - timedelta(hours=24)
            )

            # -------------------------------------------------
            # MARKET / SCANNER STATS
            # -------------------------------------------------

            coins_scanned = (
                db.query(
                    func.count(
                        func.distinct(
                            RadarResult.coin_id
                        )
                    )
                )
                .filter(
                    RadarResult.timestamp
                    >= since
                )
                .scalar()
                or 0
            )

            scans = (
                db.query(
                    func.count(
                        RadarResult.id
                    )
                )
                .filter(
                    RadarResult.timestamp
                    >= since
                )
                .scalar()
                or 0
            )

            average_score = (
                db.query(
                    func.avg(
                        RadarResult.combined_score
                    )
                )
                .filter(
                    RadarResult.timestamp
                    >= since
                )
                .scalar()
                or 0
            )

            highest = (
                db.query(
                    RadarResult
                )
                .filter(
                    RadarResult.timestamp
                    >= since
                )
                .order_by(
                    desc(
                        RadarResult.combined_score
                    )
                )
                .first()
            )

            alerts = (
                db.query(
                    func.count(
                        Alert.id
                    )
                )
                .filter(
                    Alert.created_at
                    >= since
                )
                .scalar()
                or 0
            )

            narrative_count = (
                db.query(
                    func.count(
                        Narrative.id
                    )
                )
                .filter(
                    Narrative.active.is_(
                        True
                    )
                )
                .scalar()
                or 0
            )

            # -------------------------------------------------
            # LEARNING CASE STATUS
            # -------------------------------------------------

            tracking_cases = (
                db.query(
                    func.count(
                        FeedCase.id
                    )
                )
                .filter(
                    FeedCase.status
                    == "TRACKING"
                )
                .scalar()
                or 0
            )

            total_learning_cases = (
                db.query(
                    func.count(
                        FeedCase.id
                    )
                )
                .scalar()
                or 0
            )

        finally:

            db.close()


        # =====================================================
        # VERIFIED PERFORMANCE
        #
        # Separate DB session inside evaluator.
        # =====================================================

        performance = (
            self.performance.evaluate()
        )

        score_buckets = (
            performance.get(
                "score_buckets",
                {}
            )
        )

        quality_buckets = (
            performance.get(
                "quality_buckets",
                {}
            )
        )


        # -----------------------------------------------------
        # BEST SCORE BUCKET
        #
        # Require at least 3 samples before calling something
        # the "best" range. Tiny samples shouldn't look elite.
        # -----------------------------------------------------

        eligible_score_buckets = [
            (
                name,
                stats
            )

            for (
                name,
                stats
            )
            in score_buckets.items()

            if int(
                stats.get(
                    "count",
                    0
                )
                or 0
            )
            >= 3
        ]


        if eligible_score_buckets:

            best_score_name, best_score_stats = max(
                eligible_score_buckets,

                key=lambda item: (
                    float(
                        item[1].get(
                            "win_rate",
                            0
                        )
                        or 0
                    ),
                    int(
                        item[1].get(
                            "count",
                            0
                        )
                        or 0
                    ),
                )
            )

        else:

            best_score_name = None
            best_score_stats = None


        return {
            # =================================================
            # MARKET
            # =================================================

            "coins_scanned": int(
                coins_scanned
            ),

            "scans": int(
                scans
            ),

            "narratives": int(
                narrative_count
            ),

            "alerts": int(
                alerts
            ),

            "average_score": round(
                float(
                    average_score
                ),
                2
            ),

            "highest_score": (
                round(
                    float(
                        highest.combined_score
                    ),
                    2
                )
                if highest
                else 0.0
            ),

            "highest_signal": (
                highest.signal
                if highest
                else "NONE"
            ),

            # =================================================
            # LEARNING
            # =================================================

            "learning": {
                "total_cases": int(
                    total_learning_cases
                ),

                "tracking_cases": int(
                    tracking_cases
                ),

                "completed_cases": int(
                    performance.get(
                        "completed_cases",
                        0
                    )
                ),

                "wins": int(
                    performance.get(
                        "wins",
                        0
                    )
                ),

                "losses_or_mixed": int(
                    performance.get(
                        "losses_or_mixed",
                        0
                    )
                ),

                "win_rate": float(
                    performance.get(
                        "win_rate",
                        0
                    )
                ),
            },

            # =================================================
            # RETURNS
            # =================================================

            "returns": (
                performance.get(
                    "median_returns",
                    {}
                )
            ),

            # =================================================
            # MODEL HEALTH
            # =================================================

            "model_health": {
                "false_positives": int(
                    performance.get(
                        "false_positives",
                        0
                    )
                ),

                "false_negatives": int(
                    performance.get(
                        "false_negatives",
                        0
                    )
                ),
            },

            # =================================================
            # SCORE PERFORMANCE
            # =================================================

            "score_buckets": (
                score_buckets
            ),

            "best_score_bucket": (
                {
                    "name": (
                        best_score_name
                    ),

                    "count": int(
                        best_score_stats.get(
                            "count",
                            0
                        )
                    ),

                    "win_rate": float(
                        best_score_stats.get(
                            "win_rate",
                            0
                        )
                    ),

                    "median_24h": float(
                        best_score_stats.get(
                            "median_24h",
                            0
                        )
                    ),
                }

                if best_score_stats
                else None
            ),

            # =================================================
            # QUALITY PERFORMANCE
            # =================================================

            "quality_buckets": (
                quality_buckets
            ),
        }


    # =========================================================
    # TIMELINE
    # =========================================================

    def timeline(
        self,
        narrative_name
    ):

        db = SessionLocal()

        try:

            narrative = (
                db.query(
                    Narrative
                )
                .filter(
                    func.lower(
                        Narrative.name
                    )
                    ==
                    narrative_name.lower()
                )
                .first()
            )

            if not narrative:
                return []

            coin_ids = [
                row[0]

                for row in (
                    db.query(
                        CoinNarrative.coin_id
                    )
                    .filter(
                        CoinNarrative.narrative_id
                        == narrative.id
                    )
                    .all()
                )
            ]

            if not coin_ids:
                return []

            rows = (
                db.query(
                    RadarResult
                )
                .filter(
                    RadarResult.coin_id.in_(
                        coin_ids
                    )
                )
                .order_by(
                    RadarResult.timestamp.asc()
                )
                .limit(
                    20
                )
                .all()
            )

            return [
                {
                    "time": row.timestamp,

                    "score": round(
                        float(
                            row.combined_score
                        ),
                        2
                    ),

                    "signal": (
                        row.signal
                    ),

                    "decision": (
                        row.decision
                    ),
                }

                for row in rows
            ]

        finally:

            db.close()


    # =========================================================
    # DISCOVER
    # =========================================================

    def discover(self):

        db = SessionLocal()

        try:

            since = (
                datetime.utcnow()
                - timedelta(hours=12)
            )

            rows = (
                db.query(
                    Narrative.id,
                    Narrative.name,
                    Narrative.category,

                    func.count(
                        func.distinct(
                            Coin.id
                        )
                    ).label(
                        "launches"
                    ),

                    func.avg(
                        CoinNarrative.confidence
                    ).label(
                        "confidence"
                    ),

                    func.avg(
                        MarketObservation.volume_24h
                    ).label(
                        "volume"
                    )
                )

                .join(
                    CoinNarrative,
                    CoinNarrative.narrative_id
                    == Narrative.id
                )

                .join(
                    Coin,
                    Coin.id
                    == CoinNarrative.coin_id
                )

                .outerjoin(
                    MarketObservation,
                    MarketObservation.coin_id
                    == Coin.id
                )

                .filter(
                    Coin.first_seen
                    >= since
                )

                .group_by(
                    Narrative.id,
                    Narrative.name,
                    Narrative.category
                )

                .order_by(
                    desc(
                        "launches"
                    )
                )

                .limit(
                    10
                )

                .all()
            )

            return [
                {
                    "name": (
                        row.name
                    ),

                    "category": (
                        row.category
                    ),

                    "launches": int(
                        row.launches
                        or 0
                    ),

                    "confidence": round(
                        float(
                            row.confidence
                            or 0
                        ),
                        2
                    ),

                    "volume": round(
                        float(
                            row.volume
                            or 0
                        ),
                        2
                    ),
                }

                for row in rows
            ]

        finally:

            db.close()