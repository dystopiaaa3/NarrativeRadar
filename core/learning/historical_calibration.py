from typing import Any, Dict, List

from sqlalchemy import func

from database.database import SessionLocal

from database.models.pattern import Pattern
from database.models.feed_case import FeedCase
from database.models.feed_outcome import FeedOutcome

from core.intelligence.pattern_learning import (
    PatternLearning,
)


class HistoricalCalibration:

    """
    Converts completed /feed cases into persistent,
    sample-aware historical patterns.

    IMPORTANT:

    Historical memory never replaces live evidence.

    It can only:
        - provide historical context
        - slightly adjust confidence
        - become more influential as sample size grows
    """

    def __init__(self):

        self.name = "Historical Calibration"

        self.pattern_learning = PatternLearning()


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
    def _safe_int(
        value,
        default=0
    ):

        try:

            return int(
                value
                if value is not None
                else default
            )

        except (
            TypeError,
            ValueError,
        ):

            return default


    # =========================================================
    # FEATURE BUCKETS
    # =========================================================

    @staticmethod
    def _score_bucket(
        score
    ):

        score = float(
            score or 0
        )

        if score >= 80:
            return "80_100"

        if score >= 65:
            return "65_79"

        if score >= 50:
            return "50_64"

        if score >= 35:
            return "35_49"

        return "0_34"


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


    # =========================================================
    # PATTERN SIGNATURE
    # =========================================================

    def pattern_name_from_case(
        self,
        feed_case
    ):

        narrative = (
            str(
                feed_case.narrative
                or "UNKNOWN"
            )
            .strip()
            .upper()
            .replace(
                " ",
                "_"
            )
        )

        signal = (
            str(
                feed_case.signal
                or "UNKNOWN"
            )
            .strip()
            .upper()
        )

        risk = (
            str(
                feed_case.risk
                or "UNKNOWN"
            )
            .strip()
            .upper()
        )

        score_bucket = (
            self._score_bucket(
                feed_case.combined_score
            )
        )

        quality_bucket = (
            self._quality_bucket(
                feed_case.data_quality
            )
        )

        return (
            f"{narrative}"
            f"__SCORE_{score_bucket}"
            f"__QUALITY_{quality_bucket}"
            f"__{signal}"
            f"__RISK_{risk}"
        )


    def pattern_name_from_snapshot(
        self,
        narrative: str,
        combined_score: float,
        data_quality: float,
        signal: str,
        risk: str,
    ):

        narrative = (
            str(
                narrative
                or "UNKNOWN"
            )
            .strip()
            .upper()
            .replace(
                " ",
                "_"
            )
        )

        signal = (
            str(
                signal
                or "UNKNOWN"
            )
            .strip()
            .upper()
        )

        risk = (
            str(
                risk
                or "UNKNOWN"
            )
            .strip()
            .upper()
        )

        return (
            f"{narrative}"
            f"__SCORE_"
            f"{self._score_bucket(combined_score)}"
            f"__QUALITY_"
            f"{self._quality_bucket(data_quality)}"
            f"__{signal}"
            f"__RISK_{risk}"
        )


    # =========================================================
    # CASE OUTCOME
    # =========================================================

    def _case_result(
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


        checkpoint_24h = next(
            (
                item
                for item in outcomes
                if item.checkpoint
                == "24h"
            ),
            None
        )

        if checkpoint_24h is None:

            return None


        returns = [
            self._safe_float(
                item.return_pct
            )
            for item in outcomes
        ]

        peak_return = max(
            returns
        )

        final_return = (
            self._safe_float(
                checkpoint_24h.return_pct
            )
        )

        liquidity_change = (
            self._safe_float(
                checkpoint_24h
                .liquidity_change_pct
            )
        )


        # Same preliminary outcome rule used by
        # the /feed completion system.

        success = (
            peak_return >= 50
            and
            final_return > -30
        )


        if (
            final_return <= -50
            or
            liquidity_change <= -80
        ):

            success = False


        return {
            "success": success,
            "peak_return": peak_return,
            "final_return": final_return,
            "liquidity_change": (
                liquidity_change
            ),
        }


    # =========================================================
    # BUILD ONE PATTERN
    # =========================================================

    def rebuild_pattern(
        self,
        pattern_name: str
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


            matching_results = []


            for feed_case in completed_cases:

                current_name = (
                    self.pattern_name_from_case(
                        feed_case
                    )
                )


                if current_name != pattern_name:
                    continue


                result = (
                    self._case_result(
                        db,
                        feed_case
                    )
                )


                if result is None:
                    continue


                matching_results.append(
                    result
                )


            occurrences = len(
                matching_results
            )


            if occurrences == 0:

                return {
                    "success": True,
                    "pattern": pattern_name,
                    "occurrences": 0,
                    "updated": False,
                    "error": None,
                }


            successful = sum(
                1
                for item
                in matching_results
                if item[
                    "success"
                ]
            )


            average_return = (
                sum(
                    item[
                        "final_return"
                    ]
                    for item
                    in matching_results
                )
                / occurrences
            )


            learning = (
                self.pattern_learning.evaluate(
                    occurrences=occurrences,
                    successful=successful,
                    average_return=round(
                        average_return,
                        4
                    ),
                )
            )


            pattern = (
                db.query(
                    Pattern
                )
                .filter(
                    Pattern.name
                    == pattern_name
                )
                .first()
            )


            if pattern is None:

                pattern = Pattern(
                    name=pattern_name,

                    description=(
                        "Outcome-calibrated pattern "
                        "generated from completed "
                        "/feed learning cases."
                    ),

                    occurrences=occurrences,

                    success_rate=(
                        learning[
                            "success_rate"
                        ]
                    ),

                    average_return=round(
                        average_return,
                        4
                    ),

                    active=True,
                )

                db.add(
                    pattern
                )


            else:

                pattern.occurrences = (
                    occurrences
                )

                pattern.success_rate = (
                    learning[
                        "success_rate"
                    ]
                )

                pattern.average_return = (
                    round(
                        average_return,
                        4
                    )
                )

                pattern.active = True


            db.commit()


            return {
                "success": True,

                "pattern": (
                    pattern_name
                ),

                "occurrences": (
                    occurrences
                ),

                "successful": (
                    successful
                ),

                "success_rate": (
                    learning[
                        "success_rate"
                    ]
                ),

                "average_return": (
                    round(
                        average_return,
                        4
                    )
                ),

                "strength": (
                    learning[
                        "strength"
                    ]
                ),

                "updated": True,

                "error": None,
            }


        except Exception as error:

            db.rollback()

            return {
                "success": False,
                "pattern": pattern_name,
                "updated": False,
                "error": str(error),
            }


        finally:

            db.close()


    # =========================================================
    # REBUILD ALL MEMORY
    # =========================================================

    def rebuild_all(
        self
    ):

        db = SessionLocal()

        try:

            cases = (
                db.query(
                    FeedCase
                )
                .filter(
                    FeedCase.status
                    == "COMPLETED"
                )
                .all()
            )


            names = sorted(
                {
                    self.pattern_name_from_case(
                        feed_case
                    )
                    for feed_case
                    in cases
                }
            )


        finally:

            db.close()


        results = []


        for name in names:

            results.append(
                self.rebuild_pattern(
                    name
                )
            )


        return {
            "success": True,

            "patterns_found": (
                len(names)
            ),

            "patterns": (
                results
            ),
        }


    # =========================================================
    # SAMPLE QUALITY
    # =========================================================

    def sample_level(
        self,
        occurrences: int
    ):

        occurrences = int(
            occurrences or 0
        )


        if occurrences < 10:

            return (
                "INSUFFICIENT_HISTORY"
            )


        if occurrences < 30:

            return (
                "EXPERIMENTAL"
            )


        if occurrences < 100:

            return (
                "LIMITED"
            )


        return (
            "ESTABLISHED"
        )


    # =========================================================
    # CONFIDENCE ADJUSTMENT
    # =========================================================

    def confidence_adjustment(
        self,
        occurrences: int,
        success_rate: float,
    ):

        occurrences = int(
            occurrences or 0
        )

        success_rate = float(
            success_rate or 0
        )


        # Absolutely no calibration from
        # tiny historical samples.

        if occurrences < 10:

            return 0


        # 10-29:
        # experimental influence only.

        if occurrences < 30:

            max_adjustment = 3


        # 30-99:
        # useful but still capped.

        elif occurrences < 100:

            max_adjustment = 7


        # 100+:
        # mature pattern history.

        else:

            max_adjustment = 12


        # Center historical performance
        # around 50%.

        edge = (
            success_rate
            - 50
        )


        adjustment = round(
            edge
            / 5
        )


        adjustment = max(
            -max_adjustment,
            min(
                max_adjustment,
                adjustment
            )
        )


        return int(
            adjustment
        )


    # =========================================================
    # CALIBRATE CURRENT SNAPSHOT
    # =========================================================

    def calibrate(
        self,
        narrative: str,
        combined_score: float,
        data_quality: float,
        signal: str,
        risk: str,
        base_confidence: int,
    ) -> Dict[str, Any]:

        pattern_name = (
            self.pattern_name_from_snapshot(
                narrative=narrative,
                combined_score=(
                    combined_score
                ),
                data_quality=(
                    data_quality
                ),
                signal=signal,
                risk=risk,
            )
        )


        db = SessionLocal()


        try:

            pattern = (
                db.query(
                    Pattern
                )
                .filter(
                    Pattern.name
                    == pattern_name
                )
                .filter(
                    Pattern.active.is_(
                        True
                    )
                )
                .first()
            )


            if pattern is None:

                return {
                    "pattern": (
                        pattern_name
                    ),

                    "sample_level": (
                        "INSUFFICIENT_HISTORY"
                    ),

                    "occurrences": 0,

                    "success_rate": 0.0,

                    "average_return": 0.0,

                    "confidence_adjustment": 0,

                    "base_confidence": int(
                        base_confidence
                        or 0
                    ),

                    "calibrated_confidence": int(
                        base_confidence
                        or 0
                    ),

                    "history_available": False,
                }


            occurrences = (
                self._safe_int(
                    pattern.occurrences
                )
            )


            success_rate = (
                self._safe_float(
                    pattern.success_rate
                )
            )


            average_return = (
                self._safe_float(
                    pattern.average_return
                )
            )


            level = (
                self.sample_level(
                    occurrences
                )
            )


            adjustment = (
                self.confidence_adjustment(
                    occurrences=occurrences,
                    success_rate=success_rate,
                )
            )


            base = max(
                0,
                min(
                    100,
                    int(
                        base_confidence
                        or 0
                    )
                )
            )


            calibrated = max(
                0,
                min(
                    100,
                    base
                    + adjustment
                )
            )


            return {
                "pattern": (
                    pattern_name
                ),

                "sample_level": (
                    level
                ),

                "occurrences": (
                    occurrences
                ),

                "success_rate": round(
                    success_rate,
                    2
                ),

                "average_return": round(
                    average_return,
                    2
                ),

                "confidence_adjustment": (
                    adjustment
                ),

                "base_confidence": (
                    base
                ),

                "calibrated_confidence": (
                    calibrated
                ),

                "history_available": (
                    occurrences >= 10
                ),
            }


        finally:

            db.close()