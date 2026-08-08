from datetime import (
    datetime,
    timedelta,
)

from statistics import mean

from sqlalchemy import (
    func,
)

from database.database import (
    SessionLocal,
)

from database.models.narrative import (
    Narrative,
)

from database.models.coin_narrative import (
    CoinNarrative,
)

from database.models.coin import (
    Coin,
)

from database.models.market import (
    MarketObservation,
)

from database.models.radar_result import (
    RadarResult,
)


class NarrativeService:

    def __init__(self):

        self.name = (
            "Narrative Service"
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
    def _duration_to_hours(
        duration: str,
    ) -> int:

        value = str(
            duration
            or "6h"
        ).lower().strip()

        mapping = {
            "1h": 1,
            "3h": 3,
            "6h": 6,
            "12h": 12,
            "24h": 24,
        }

        return mapping.get(
            value,
            6,
        )


    def _coin_ids_for_narrative(
        self,
        db,
        narrative_id,
    ):

        rows = (
            db.query(
                CoinNarrative.coin_id
            )
            .filter(
                CoinNarrative.narrative_id
                == narrative_id
            )
            .all()
        )

        return list(
            {
                int(
                    row[0]
                )
                for row
                in rows
            }
        )


    def _latest_market_observation(
        self,
        db,
        coin_id,
    ):

        return (
            db.query(
                MarketObservation
            )
            .filter(
                MarketObservation.coin_id
                == coin_id
            )
            .filter(
                MarketObservation.market_cap
                > 0
            )
            .order_by(
                MarketObservation.timestamp.desc()
            )
            .first()
        )


    def _latest_market_stats(
        self,
        db,
        coin_ids,
    ):

        market_caps = []
        volumes = []
        liquidities = []

        for coin_id in coin_ids:

            observation = (
                self._latest_market_observation(
                    db,
                    coin_id,
                )
            )

            if observation is None:

                continue

            market_cap = (
                self._safe_float(
                    observation.market_cap
                )
            )

            volume = (
                self._safe_float(
                    observation.volume_24h
                )
            )

            liquidity = (
                self._safe_float(
                    observation.liquidity
                )
            )

            if market_cap > 0:

                market_caps.append(
                    market_cap
                )

            if volume > 0:

                volumes.append(
                    volume
                )

            if liquidity > 0:

                liquidities.append(
                    liquidity
                )


        return {
            "avg_market_cap": round(
                mean(
                    market_caps
                )
                if market_caps
                else 0.0,
                2,
            ),

            "avg_volume": round(
                mean(
                    volumes
                )
                if volumes
                else 0.0,
                2,
            ),

            "avg_liquidity": round(
                mean(
                    liquidities
                )
                if liquidities
                else 0.0,
                2,
            ),

            "market_samples": len(
                market_caps
            ),
        }


    def _average_narrative_confidence(
        self,
        db,
        narrative_id,
    ):

        value = (
            db.query(
                func.avg(
                    CoinNarrative.confidence
                )
            )
            .filter(
                CoinNarrative.narrative_id
                == narrative_id
            )
            .scalar()
        )

        return round(
            self._safe_float(
                value
            ),
            2,
        )


    def _average_radar_score(
        self,
        db,
        coin_ids,
        since=None,
    ):

        if not coin_ids:

            return 0.0

        query = (
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
        )

        if since is not None:

            query = query.filter(
                RadarResult.timestamp
                >= since
            )

        value = (
            query.scalar()
            or 0
        )

        return round(
            self._safe_float(
                value
            ),
            2,
        )


    # =========================================================
    # TRENDING
    # =========================================================

    def trending(
        self,
        duration: str = "6h",
        limit: int = 10,
    ):

        hours = (
            self._duration_to_hours(
                duration
            )
        )

        since = (
            datetime.utcnow()
            - timedelta(
                hours=hours
            )
        )

        db = SessionLocal()

        try:

            narratives = (
                db.query(
                    Narrative
                )
                .filter(
                    Narrative.active.is_(
                        True
                    )
                )
                .all()
            )

            results = []


            for narrative in narratives:

                coin_ids = (
                    self._coin_ids_for_narrative(
                        db,
                        narrative.id,
                    )
                )

                if not coin_ids:

                    continue


                score = (
                    self._average_radar_score(
                        db,
                        coin_ids,
                        since=since,
                    )
                )


                # No radar activity in selected period.

                radar_count = (
                    db.query(
                        func.count(
                            RadarResult.id
                        )
                    )
                    .filter(
                        RadarResult.coin_id.in_(
                            coin_ids
                        )
                    )
                    .filter(
                        RadarResult.timestamp
                        >= since
                    )
                    .scalar()
                    or 0
                )

                if radar_count <= 0:

                    continue


                market = (
                    self._latest_market_stats(
                        db,
                        coin_ids,
                    )
                )


                results.append(
                    {
                        "id": (
                            narrative.id
                        ),

                        "name": (
                            narrative.name
                        ),

                        "category": (
                            narrative.category
                        ),

                        "coin_count": len(
                            coin_ids
                        ),

                        "avg_confidence": (
                            self._average_narrative_confidence(
                                db,
                                narrative.id,
                            )
                        ),

                        "avg_market_cap": (
                            market[
                                "avg_market_cap"
                            ]
                        ),

                        "market_samples": (
                            market[
                                "market_samples"
                            ]
                        ),

                        "score": (
                            score
                        ),
                    }
                )


            results.sort(
                key=lambda item: (
                    item[
                        "score"
                    ],
                    item[
                        "avg_confidence"
                    ],
                    item[
                        "coin_count"
                    ],
                ),
                reverse=True,
            )


            return results[
                :max(
                    1,
                    int(
                        limit
                    ),
                )
            ]


        finally:

            db.close()


    # =========================================================
    # TOP NARRATIVES
    # =========================================================

    def top_narratives(
        self,
        limit: int = 10,
    ):

        db = SessionLocal()

        try:

            narratives = (
                db.query(
                    Narrative
                )
                .filter(
                    Narrative.active.is_(
                        True
                    )
                )
                .all()
            )

            results = []


            for narrative in narratives:

                coin_ids = (
                    self._coin_ids_for_narrative(
                        db,
                        narrative.id,
                    )
                )

                if not coin_ids:

                    continue


                results.append(
                    {
                        "id": (
                            narrative.id
                        ),

                        "name": (
                            narrative.name
                        ),

                        "category": (
                            narrative.category
                        ),

                        "score": (
                            self._average_radar_score(
                                db,
                                coin_ids,
                            )
                        ),

                        "confidence": (
                            self._average_narrative_confidence(
                                db,
                                narrative.id,
                            )
                        ),

                        "coin_count": len(
                            coin_ids
                        ),
                    }
                )


            results.sort(
                key=lambda item: (
                    item[
                        "score"
                    ],
                    item[
                        "confidence"
                    ],
                ),
                reverse=True,
            )


            return results[
                :max(
                    1,
                    int(
                        limit
                    ),
                )
            ]


        finally:

            db.close()


    # =========================================================
    # EMERGING
    # =========================================================

    def emerging(
        self,
        hours: int = 6,
        limit: int = 10,
    ):

        since = (
            datetime.utcnow()
            - timedelta(
                hours=hours
            )
        )

        db = SessionLocal()

        try:

            narratives = (
                db.query(
                    Narrative
                )
                .filter(
                    Narrative.active.is_(
                        True
                    )
                )
                .all()
            )

            results = []

            now = (
                datetime.utcnow()
            )


            for narrative in narratives:

                coin_rows = (
                    db.query(
                        Coin
                    )
                    .join(
                        CoinNarrative,
                        CoinNarrative.coin_id
                        == Coin.id
                    )
                    .filter(
                        CoinNarrative.narrative_id
                        == narrative.id
                    )
                    .filter(
                        Coin.first_seen
                        >= since
                    )
                    .all()
                )


                if not coin_rows:

                    continue


                coin_ids = list(
                    {
                        coin.id
                        for coin
                        in coin_rows
                    }
                )


                first_seen = min(
                    coin.first_seen
                    for coin
                    in coin_rows
                    if coin.first_seen
                )


                age_minutes = int(
                    (
                        now
                        - first_seen
                    ).total_seconds()
                    / 60
                )


                market = (
                    self._latest_market_stats(
                        db,
                        coin_ids,
                    )
                )


                results.append(
                    {
                        "id": (
                            narrative.id
                        ),

                        "name": (
                            narrative.name
                        ),

                        "category": (
                            narrative.category
                        ),

                        "launches": len(
                            coin_ids
                        ),

                        "confidence": (
                            self._average_narrative_confidence(
                                db,
                                narrative.id,
                            )
                        ),

                        "avg_market_cap": (
                            market[
                                "avg_market_cap"
                            ]
                        ),

                        "age_minutes": (
                            age_minutes
                        ),
                    }
                )


            results.sort(
                key=lambda item: (
                    item[
                        "confidence"
                    ],
                    item[
                        "launches"
                    ],
                ),
                reverse=True,
            )


            return results[
                :max(
                    1,
                    int(
                        limit
                    ),
                )
            ]


        finally:

            db.close()


    # =========================================================
    # NARRATIVE SUMMARY
    # =========================================================

    def _narrative_summary(
        self,
        narrative_name: str,
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


            if narrative is None:

                return None


            coin_ids = (
                self._coin_ids_for_narrative(
                    db,
                    narrative.id,
                )
            )


            market = (
                self._latest_market_stats(
                    db,
                    coin_ids,
                )
            )


            return {
                "name": (
                    narrative.name
                ),

                "category": (
                    narrative.category
                ),

                "coin_count": len(
                    coin_ids
                ),

                "confidence": (
                    self._average_narrative_confidence(
                        db,
                        narrative.id,
                    )
                ),

                "avg_market_cap": (
                    market[
                        "avg_market_cap"
                    ]
                ),

                "avg_volume": (
                    market[
                        "avg_volume"
                    ]
                ),

                "score": (
                    self._average_radar_score(
                        db,
                        coin_ids,
                    )
                ),
            }


        finally:

            db.close()


    # =========================================================
    # COMPARE
    # =========================================================

    def compare(
        self,
        narrative_a: str,
        narrative_b: str,
    ):

        return {
            "first": (
                self._narrative_summary(
                    narrative_a
                )
            ),

            "second": (
                self._narrative_summary(
                    narrative_b
                )
            ),
        }


    # =========================================================
    # PULSE
    # =========================================================

    def pulse(self):

        db = SessionLocal()

        try:

            total_results = (
                db.query(
                    func.count(
                        RadarResult.id
                    )
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
                .scalar()
                or 0
            )


            bullish = (
                db.query(
                    func.count(
                        RadarResult.id
                    )
                )
                .filter(
                    RadarResult.combined_score
                    >= 60
                )
                .scalar()
                or 0
            )


            bearish = (
                db.query(
                    func.count(
                        RadarResult.id
                    )
                )
                .filter(
                    RadarResult.combined_score
                    < 40
                )
                .scalar()
                or 0
            )


            if average_score >= 65:

                state = "BULLISH"

            elif average_score >= 40:

                state = "NEUTRAL"

            else:

                state = "BEARISH"


            return {
                "state": (
                    state
                ),

                "average_score": round(
                    float(
                        average_score
                    ),
                    2,
                ),

                "bullish_results": int(
                    bullish
                ),

                "bearish_results": int(
                    bearish
                ),

                "total_results": int(
                    total_results
                ),
            }


        finally:

            db.close()


    # =========================================================
    # RADAR
    # =========================================================

    def radar(self):

        return {
            "trending": (
                self.trending(
                    "6h",
                    limit=3,
                )
            ),

            "emerging": (
                self.emerging(
                    hours=6,
                    limit=3,
                )
            ),

            "pulse": (
                self.pulse()
            ),
        }