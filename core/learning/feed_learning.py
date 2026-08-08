import threading

from datetime import (
    datetime,
    timedelta,
)

from collectors.market import MarketCollector
from collectors.dexscreener_discovery import (
    DexScreenerDiscoveryCollector,
)
from collectors.storage.coin_storage import (
    CoinStorage,
)

from core.intelligence.live_radar import (
    LiveRadar,
)
from core.intelligence.narrative_assignment import (
    NarrativeAssignmentEngine,
)

from core.learning.historical_calibration import (
    HistoricalCalibration,
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
from database.models.case import (
    CaseStudy,
)


class FeedLearningService:

    CHECKPOINTS = {
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
    }


    def __init__(
        self,
        check_interval: int = 60
    ):

        self.check_interval = max(
            30,
            int(check_interval)
        )

        self.market = MarketCollector()

        self.dex = (
            DexScreenerDiscoveryCollector()
        )

        self.coin_storage = (
            CoinStorage()
        )

        self.narratives = (
            NarrativeAssignmentEngine()
        )

        self.calibration = (
            HistoricalCalibration()
        )

        self.stop_event = (
            threading.Event()
        )


    # =========================================================
    # HELPERS
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
    def _pct_change(
        current,
        original
    ):

        current = float(
            current or 0
        )

        original = float(
            original or 0
        )

        if original <= 0:

            return 0.0

        return round(
            (
                (
                    current
                    - original
                )
                / original
            )
            * 100,
            4
        )


    # =========================================================
    # TOKEN METADATA
    # =========================================================

    def _metadata(
        self,
        address
    ):

        pairs = (
            self.dex.get_token_pairs(
                address
            )
        )

        if not pairs:

            return {
                "name": "Unknown",
                "symbol": "UNKNOWN",
                "topic": None,
            }


        best = max(
            pairs,
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
            )
        )


        base = (
            best.get(
                "baseToken"
            )
            or {}
        )

        quote = (
            best.get(
                "quoteToken"
            )
            or {}
        )


        if (
            base.get(
                "address"
            )
            == address
        ):

            token = base

        elif (
            quote.get(
                "address"
            )
            == address
        ):

            token = quote

        else:

            token = base


        name = (
            token.get(
                "name"
            )
            or "Unknown"
        )

        symbol = (
            token.get(
                "symbol"
            )
            or "UNKNOWN"
        )

        topic = (
            symbol
            .replace(
                "$",
                ""
            )
            .strip()
            .lower()
        )

        if topic in (
            "",
            "unknown",
        ):

            topic = None


        return {
            "name": name,
            "symbol": symbol,
            "topic": topic,
        }


    # =========================================================
    # CREATE T0 LEARNING CASE
    # =========================================================

    def feed(
        self,
        coin_address: str
    ):

        address = (
            coin_address
            .strip()
        )


        metadata = (
            self._metadata(
                address
            )
        )


        coin = (
            self.coin_storage
            .get_or_create_coin(
                address
            )
        )


        radar = LiveRadar()


        result = radar.run(
            coin_id=coin.id,
            coin_address=address,
            signature_limit=20,
            social_topic=(
                metadata[
                    "topic"
                ]
            ),
        )


        candidate = {
            "coin_address": address,
            "name": metadata["name"],
            "symbol": metadata["symbol"],
            "source": "feed",
            "source_reasons": [
                "manual_feed"
            ],
        }


        narrative_result = (
            self.narratives.assign(
                coin_id=coin.id,
                candidate=candidate,
            )
        )


        assignments = (
            narrative_result.get(
                "assignments",
                []
            )
        )


        narrative_name = (
            assignments[0]["name"]
            if assignments
            else "UNKNOWN"
        )


        collected = (
            result[
                "collected"
            ]
        )

        market = (
            collected.get(
                "market",
                {}
            )
        )


        radar_data = (
            result[
                "radar"
            ]
        )


        analysis = (
            radar_data[
                "analysis"
            ]
        )


        signal = (
            radar_data[
                "radar"
            ][
                "signal"
            ]
        )


        decision = (
            radar_data[
                "radar"
            ][
                "decision"
            ]
        )


        db = SessionLocal()


        try:

            feed_case = FeedCase(
                coin_id=coin.id,

                coin_address=address,

                name=(
                    metadata[
                        "name"
                    ]
                ),

                symbol=(
                    metadata[
                        "symbol"
                    ]
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

                signal=(
                    signal.get(
                        "signal",
                        "UNKNOWN"
                    )
                ),

                confidence=int(
                    signal.get(
                        "confidence",
                        0
                    )
                    or 0
                ),

                decision=(
                    decision.get(
                        "decision",
                        "UNKNOWN"
                    )
                ),

                risk=(
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
                "success": True,

                "feed_case_id": (
                    feed_case.id
                ),

                "coin_address": (
                    address
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

                "price": (
                    feed_case.t0_price
                ),

                "market_cap": (
                    feed_case.t0_market_cap
                ),

                "liquidity": (
                    feed_case.t0_liquidity
                ),

                "volume_24h": (
                    feed_case.t0_volume_24h
                ),

                "combined_score": (
                    feed_case.combined_score
                ),

                "signal": (
                    feed_case.signal
                ),

                "confidence": (
                    feed_case.confidence
                ),

                "decision": (
                    feed_case.decision
                ),

                "risk": (
                    feed_case.risk
                ),

                "status": (
                    feed_case.status
                ),

                "error": None,
            }


        except Exception as error:

            db.rollback()

            return {
                "success": False,
                "error": str(error),
            }


        finally:

            db.close()


    # =========================================================
    # CHECKPOINT HELPERS
    # =========================================================

    def _already_checked(
        self,
        db,
        case_id,
        checkpoint
    ):

        return (
            db.query(
                FeedOutcome
            )
            .filter(
                FeedOutcome.feed_case_id
                == case_id
            )
            .filter(
                FeedOutcome.checkpoint
                == checkpoint
            )
            .first()
            is not None
        )


    def _due_checkpoints(
        self,
        db,
        feed_case,
        now
    ):

        due = []


        for (
            checkpoint,
            offset
        ) in self.CHECKPOINTS.items():

            checkpoint_time = (
                feed_case.created_at
                + offset
            )


            if now < checkpoint_time:

                continue


            if self._already_checked(
                db,
                feed_case.id,
                checkpoint
            ):

                continue


            due.append(
                checkpoint
            )


        return due


    # =========================================================
    # RECORD CHECKPOINT
    # =========================================================

    def _record_outcome(
        self,
        db,
        feed_case,
        checkpoint,
        market
    ):

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

        volume = self._safe_float(
            market.get(
                "volume_24h"
            )
        )


        outcome = FeedOutcome(
            feed_case_id=(
                feed_case.id
            ),

            checkpoint=(
                checkpoint
            ),

            price=price,

            market_cap=market_cap,

            liquidity=liquidity,

            volume_24h=volume,

            return_pct=(
                self._pct_change(
                    price,
                    feed_case.t0_price
                )
            ),

            liquidity_change_pct=(
                self._pct_change(
                    liquidity,
                    feed_case.t0_liquidity
                )
            ),

            volume_change_pct=(
                self._pct_change(
                    volume,
                    feed_case.t0_volume_24h
                )
            ),

            checked_at=(
                datetime.utcnow()
            )
        )


        db.add(
            outcome
        )


        return outcome


    # =========================================================
    # COMPLETE CASE
    # =========================================================

    def _complete_case(
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


        if not outcomes:

            return None


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
            float(
                item.return_pct
                or 0
            )
            for item
            in outcomes
        ]


        peak_return = max(
            returns
        )

        worst_return = min(
            returns
        )

        final_return = float(
            final.return_pct
            or 0
        )


        # =========================================
        # PRELIMINARY OUTCOME LABELS
        #
        # Later these thresholds themselves can
        # be calibrated from enough history.
        # =========================================

        if (
            peak_return >= 50
            and
            final_return > -30
        ):

            outcome_name = (
                "WINNER"
            )

            success = True


        elif (
            final_return <= -50
            or
            float(
                final.liquidity_change_pct
                or 0
            )
            <= -80
        ):

            outcome_name = (
                "FAILED"
            )

            success = False


        else:

            outcome_name = (
                "MIXED"
            )

            success = False


        peak_multiplier = max(
            0.0,
            1.0
            + (
                peak_return
                / 100
            )
        )


        explanation = (
            f"T0 score="
            f"{feed_case.combined_score}, "
            f"signal="
            f"{feed_case.signal}, "
            f"confidence="
            f"{feed_case.confidence}%. "
            f"Peak return="
            f"{peak_return:.2f}%, "
            f"worst return="
            f"{worst_return:.2f}%, "
            f"24h return="
            f"{final_return:.2f}%, "
            f"24h liquidity change="
            f"{float(final.liquidity_change_pct or 0):.2f}%."
        )


        learned_case = CaseStudy(
            name=(
                feed_case.name
            ),

            symbol=(
                feed_case.symbol
            ),

            category=(
                feed_case.narrative
            ),

            outcome=(
                outcome_name
            ),

            peak_multiplier=(
                peak_multiplier
            ),

            success=(
                success
            ),

            explanation=(
                explanation[:500]
            ),

            created_at=(
                datetime.utcnow()
            ),
        )


        db.add(
            learned_case
        )


        feed_case.status = (
            "COMPLETED"
        )

        feed_case.completed_at = (
            datetime.utcnow()
        )


        # Calculate the historical pattern name
        # while we still have the FeedCase object.
        #
        # Actual rebuild happens AFTER commit so
        # the calibration engine can see this
        # completed case from its own DB session.

        pattern_name = (
            self.calibration
            .pattern_name_from_case(
                feed_case
            )
        )


        return {
            "pattern_name": (
                pattern_name
            ),

            "outcome": (
                outcome_name
            ),

            "success": (
                success
            ),

            "peak_return": round(
                peak_return,
                4
            ),

            "final_return": round(
                final_return,
                4
            ),
        }


    # =========================================================
    # CHECK ALL DUE LEARNING CASES
    # =========================================================

    def check_due_outcomes(
        self
    ):

        db = SessionLocal()

        recorded = 0

        completed = 0

        completed_results = []

        patterns_to_rebuild = set()


        try:

            now = (
                datetime.utcnow()
            )


            cases = (
                db.query(
                    FeedCase
                )
                .filter(
                    FeedCase.status
                    == "TRACKING"
                )
                .all()
            )


            for feed_case in cases:

                due = (
                    self._due_checkpoints(
                        db,
                        feed_case,
                        now
                    )
                )


                if not due:

                    continue


                market = (
                    self.market
                    .fetch_market_data(
                        feed_case.coin_address
                    )
                )


                if not market:

                    continue


                for checkpoint in due:

                    self._record_outcome(
                        db,
                        feed_case,
                        checkpoint,
                        market
                    )

                    recorded += 1


                # Make newly inserted checkpoints
                # available to queries in this session.

                db.flush()


                if "24h" in due:

                    completion = (
                        self._complete_case(
                            db,
                            feed_case
                        )
                    )


                    if completion:

                        completed += 1

                        completed_results.append(
                            {
                                "feed_case_id": (
                                    feed_case.id
                                ),

                                "symbol": (
                                    feed_case.symbol
                                ),

                                **completion,
                            }
                        )


                        patterns_to_rebuild.add(
                            completion[
                                "pattern_name"
                            ]
                        )


            # =========================================
            # COMMIT OUTCOMES FIRST
            #
            # HistoricalCalibration uses another
            # SQLAlchemy session, so it must only run
            # after COMPLETED status is committed.
            # =========================================

            db.commit()


        except Exception as error:

            db.rollback()

            return {
                "success": False,

                "recorded": (
                    recorded
                ),

                "completed": (
                    completed
                ),

                "pattern_updates": [],

                "error": str(
                    error
                ),
            }


        finally:

            db.close()


        # =====================================================
        # UPDATE HISTORICAL MEMORY
        # =====================================================

        pattern_updates = []


        for pattern_name in (
            patterns_to_rebuild
        ):

            try:

                result = (
                    self.calibration
                    .rebuild_pattern(
                        pattern_name
                    )
                )

                pattern_updates.append(
                    result
                )


            except Exception as error:

                pattern_updates.append(
                    {
                        "success": False,
                        "pattern": pattern_name,
                        "error": str(
                            error
                        ),
                    }
                )


        return {
            "success": True,

            "recorded": (
                recorded
            ),

            "completed": (
                completed
            ),

            "completed_cases": (
                completed_results
            ),

            "pattern_updates": (
                pattern_updates
            ),

            "error": None,
        }


    # =========================================================
    # BACKGROUND LEARNING LOOP
    # =========================================================

    def run_forever(self):

        print(
            "Feed learning tracker ONLINE"
        )


        while not self.stop_event.is_set():

            try:

                result = (
                    self.check_due_outcomes()
                )


                if (
                    result.get(
                        "recorded",
                        0
                    )
                    > 0
                    or
                    result.get(
                        "completed",
                        0
                    )
                    > 0
                ):

                    print(
                        "\n"
                        "LEARNING UPDATE"
                    )

                    print(
                        "Recorded:",
                        result.get(
                            "recorded",
                            0
                        )
                    )

                    print(
                        "Completed:",
                        result.get(
                            "completed",
                            0
                        )
                    )


                    for case in result.get(
                        "completed_cases",
                        []
                    ):

                        print(
                            (
                                f"{case['symbol']} | "
                                f"{case['outcome']} | "
                                f"Peak "
                                f"{case['peak_return']:+.2f}% | "
                                f"24H "
                                f"{case['final_return']:+.2f}%"
                            )
                        )


                    for pattern in result.get(
                        "pattern_updates",
                        []
                    ):

                        if pattern.get(
                            "success"
                        ):

                            print(
                                (
                                    "Pattern updated | "
                                    f"{pattern['pattern']} | "
                                    f"N="
                                    f"{pattern.get('occurrences', 0)} | "
                                    f"Win="
                                    f"{pattern.get('success_rate', 0)}%"
                                )
                            )


            except Exception as error:

                print(
                    "Feed learning error:",
                    str(error)
                )


            self.stop_event.wait(
                self.check_interval
            )


    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        self.stop_event.set()