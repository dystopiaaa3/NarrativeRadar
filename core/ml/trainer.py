import json
import math
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path

import numpy as np

from database.database import SessionLocal
from database.models.feed_case import FeedCase
from database.models.feed_outcome import FeedOutcome

from core.ml.features import (
    FEATURE_NAMES,
    build_case_features,
)


TARGETS = {
    "move20": {
        "description": "Peak return reaches +20% within 24h",
    },

    "move50": {
        "description": "Peak return reaches +50% within 24h",
    },

    "collapse80": {
        "description": "24h return <= -80% or 24h liquidity <= -90%",
    },
}


class XGBTrainer:

    _global_lock = threading.Lock()

    def __init__(
        self,
        model_dir=None,
        min_case_id=None,
        test_fraction=0.20,
    ):
        self.model_dir = Path(
            model_dir
            or self.default_model_dir()
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.min_case_id = int(
            min_case_id
            or os.getenv(
                "ML_MIN_CASE_ID",
                "1388",
            )
        )

        self.test_fraction = min(
            max(
                float(test_fraction),
                0.10,
            ),
            0.35,
        )

    @staticmethod
    def default_model_dir():
        railway_mount = os.getenv(
            "RAILWAY_VOLUME_MOUNT_PATH",
            "",
        ).strip()

        if railway_mount:
            return str(
                Path(railway_mount)
                / "narrativeradar_ml"
            )

        if Path("/data").exists():
            return "/data/narrativeradar_ml"

        return "ml_artifacts"

    def _collect_dataset(self):
        db = SessionLocal()

        try:
            cases = (
                db.query(FeedCase)
                .filter(
                    FeedCase.status
                    == "COMPLETED"
                )
                .filter(
                    FeedCase.id
                    >= self.min_case_id
                )
                .order_by(
                    FeedCase.id.asc()
                )
                .all()
            )

            if not cases:
                return []

            case_ids = [
                row.id
                for row in cases
            ]

            outcomes = (
                db.query(FeedOutcome)
                .filter(
                    FeedOutcome.feed_case_id.in_(
                        case_ids
                    )
                )
                .all()
            )

            by_case = {}

            for outcome in outcomes:
                by_case.setdefault(
                    outcome.feed_case_id,
                    {},
                )[
                    outcome.checkpoint
                ] = outcome

            dataset = []

            for case in cases:
                checkpoint_map = by_case.get(
                    case.id,
                    {},
                )

                final = checkpoint_map.get(
                    "24h"
                )

                if final is None:
                    continue

                returns = [
                    float(
                        checkpoint_map[name].return_pct
                        or 0.0
                    )
                    for name in (
                        "15m",
                        "1h",
                        "6h",
                        "24h",
                    )
                    if name in checkpoint_map
                ]

                if not returns:
                    continue

                # Training needs real T0 market context.
                if float(
                    case.t0_market_cap
                    or 0.0
                ) <= 0:
                    continue

                if float(
                    case.t0_price
                    or 0.0
                ) <= 0:
                    continue

                peak_return = max(
                    returns
                )

                final_return = float(
                    final.return_pct
                    or 0.0
                )

                final_liquidity_change = float(
                    final.liquidity_change_pct
                    or 0.0
                )

                labels = {
                    "move20": (
                        1
                        if peak_return >= 20.0
                        else 0
                    ),

                    "move50": (
                        1
                        if peak_return >= 50.0
                        else 0
                    ),

                    "collapse80": (
                        1
                        if (
                            final_return <= -80.0
                            or
                            final_liquidity_change <= -90.0
                        )
                        else 0
                    ),
                }

                dataset.append(
                    {
                        "case_id": case.id,
                        "created_at": (
                            case.created_at.isoformat()
                            if case.created_at
                            else None
                        ),
                        "features": build_case_features(
                            case
                        ),
                        "labels": labels,
                        "peak_return": peak_return,
                        "return_24h": final_return,
                    }
                )

            return dataset

        finally:
            db.close()

    @staticmethod
    def _binary_logloss(
        y_true,
        y_prob,
    ):
        eps = 1e-7

        p = np.clip(
            np.asarray(
                y_prob,
                dtype=float,
            ),
            eps,
            1.0 - eps,
        )

        y = np.asarray(
            y_true,
            dtype=float,
        )

        return float(
            -np.mean(
                (
                    y
                    * np.log(p)
                )
                +
                (
                    (1.0 - y)
                    * np.log(
                        1.0 - p
                    )
                )
            )
        )

    @staticmethod
    def _brier(
        y_true,
        y_prob,
    ):
        y = np.asarray(
            y_true,
            dtype=float,
        )

        p = np.asarray(
            y_prob,
            dtype=float,
        )

        return float(
            np.mean(
                (
                    p - y
                )
                ** 2
            )
        )

    @staticmethod
    def _top_fraction_metrics(
        y_true,
        y_prob,
        fraction,
    ):
        y = np.asarray(
            y_true,
            dtype=int,
        )

        p = np.asarray(
            y_prob,
            dtype=float,
        )

        count = len(y)

        if count <= 0:
            return {
                "selected": 0,
                "event_rate": 0.0,
                "lift": 0.0,
            }

        take = max(
            1,
            int(
                math.ceil(
                    count
                    * fraction
                )
            ),
        )

        order = np.argsort(
            -p
        )

        selected = y[
            order[:take]
        ]

        base_rate = float(
            np.mean(y)
        )

        event_rate = float(
            np.mean(
                selected
            )
        )

        lift = (
            event_rate / base_rate
            if base_rate > 0
            else 0.0
        )

        return {
            "selected": int(take),
            "event_rate": round(
                event_rate,
                6,
            ),
            "lift": round(
                lift,
                4,
            ),
        }

    def _fit_target(
        self,
        target_name,
        train_rows,
        test_rows,
    ):
        try:
            import xgboost as xgb
        except Exception as error:
            raise RuntimeError(
                "xgboost is not installed. "
                "Run: pip install xgboost"
            ) from error

        X_train = np.asarray(
            [
                row["features"]
                for row in train_rows
            ],
            dtype=np.float32,
        )

        X_test = np.asarray(
            [
                row["features"]
                for row in test_rows
            ],
            dtype=np.float32,
        )

        y_train = np.asarray(
            [
                row["labels"][
                    target_name
                ]
                for row in train_rows
            ],
            dtype=np.float32,
        )

        y_test = np.asarray(
            [
                row["labels"][
                    target_name
                ]
                for row in test_rows
            ],
            dtype=np.float32,
        )

        positives = int(
            np.sum(
                y_train
            )
        )

        negatives = int(
            len(y_train)
            - positives
        )

        if positives < 10:
            return {
                "success": False,
                "target": target_name,
                "error": (
                    "Too few positive training examples: "
                    f"{positives}"
                ),
            }

        if negatives < 10:
            return {
                "success": False,
                "target": target_name,
                "error": (
                    "Too few negative training examples: "
                    f"{negatives}"
                ),
            }

        scale_pos_weight = (
            negatives
            /
            max(
                positives,
                1,
            )
        )

        dtrain = xgb.DMatrix(
            X_train,
            label=y_train,
            feature_names=FEATURE_NAMES,
        )

        dtest = xgb.DMatrix(
            X_test,
            label=y_test,
            feature_names=FEATURE_NAMES,
        )

        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",

            # Conservative trees because our dataset is still small.
            "max_depth": 4,
            "min_child_weight": 5,

            "eta": 0.04,

            "subsample": 0.80,
            "colsample_bytree": 0.80,

            "lambda": 2.0,
            "alpha": 0.20,

            "scale_pos_weight": float(
                scale_pos_weight
            ),

            "tree_method": "hist",

            # Keep Railway CPU use modest.
            "nthread": 2,

            "seed": 42,
        }

        booster = xgb.train(
            params,
            dtrain,
            num_boost_round=350,

            evals=[
                (
                    dtest,
                    "validation",
                )
            ],

            early_stopping_rounds=30,
            verbose_eval=False,
        )

        probabilities = booster.predict(
            dtest
        )

        base_rate = float(
            np.mean(
                y_test
            )
        )

        metrics = {
            "test_cases": int(
                len(y_test)
            ),

            "test_positives": int(
                np.sum(
                    y_test
                )
            ),

            "base_rate": round(
                base_rate,
                6,
            ),

            "logloss": round(
                self._binary_logloss(
                    y_test,
                    probabilities,
                ),
                6,
            ),

            "brier": round(
                self._brier(
                    y_test,
                    probabilities,
                ),
                6,
            ),

            "top_10pct": (
                self._top_fraction_metrics(
                    y_test,
                    probabilities,
                    0.10,
                )
            ),

            "top_20pct": (
                self._top_fraction_metrics(
                    y_test,
                    probabilities,
                    0.20,
                )
            ),

            "best_iteration": int(
                getattr(
                    booster,
                    "best_iteration",
                    0,
                )
                or 0
            ),
        }

        temp_path = (
            self.model_dir
            / f"{target_name}.candidate.json"
        )

        final_path = (
            self.model_dir
            / f"{target_name}.json"
        )

        booster.save_model(
            temp_path
        )

        # Shadow mode is safe, but don't replace an already-working
        # model with a challenger that shows no ranking lift.
        top20_lift = float(
            metrics[
                "top_20pct"
            ][
                "lift"
            ]
        )

        accepted = (
            top20_lift >= 1.05
            and
            metrics[
                "test_positives"
            ] >= 5
        )

        if (
            accepted
            or
            not final_path.exists()
        ):
            shutil.move(
                str(temp_path),
                str(final_path),
            )

            installed = True

        else:
            temp_path.unlink(
                missing_ok=True
            )

            installed = False

        return {
            "success": True,
            "target": target_name,
            "accepted": bool(
                accepted
            ),
            "installed": bool(
                installed
            ),
            "metrics": metrics,
            "scale_pos_weight": round(
                float(
                    scale_pos_weight
                ),
                4,
            ),
        }

    def train(
        self,
        force=False,
    ):
        if not self._global_lock.acquire(
            blocking=False
        ):
            return {
                "success": False,
                "error": (
                    "Training is already running"
                ),
            }

        try:
            dataset = (
                self._collect_dataset()
            )

            total = len(
                dataset
            )

            if total < 250:
                return {
                    "success": False,
                    "error": (
                        "Need at least 250 completed "
                        f"clean cases; found {total}"
                    ),
                }

            split_index = int(
                total
                * (
                    1.0
                    -
                    self.test_fraction
                )
            )

            # Keep enough chronological holdout data.
            split_index = min(
                max(
                    split_index,
                    200,
                ),
                total - 50,
            )

            train_rows = dataset[
                :split_index
            ]

            test_rows = dataset[
                split_index:
            ]

            target_results = {}

            for target_name in TARGETS:
                target_results[
                    target_name
                ] = self._fit_target(
                    target_name,
                    train_rows,
                    test_rows,
                )

            trained_through_case_id = int(
                dataset[-1][
                    "case_id"
                ]
            )

            metadata = {
                "version": 1,
                "mode": "SHADOW",
                "created_at": (
                    datetime.utcnow()
                    .isoformat()
                ),

                "min_case_id": (
                    self.min_case_id
                ),

                "trained_through_case_id": (
                    trained_through_case_id
                ),

                "dataset_cases": total,

                "train_cases": len(
                    train_rows
                ),

                "test_cases": len(
                    test_rows
                ),

                "feature_names": (
                    FEATURE_NAMES
                ),

                "targets": (
                    target_results
                ),
            }

            metadata_path = (
                self.model_dir
                / "metadata.json"
            )

            metadata_path.write_text(
                json.dumps(
                    metadata,
                    indent=2,
                ),
                encoding="utf-8",
            )

            return {
                "success": True,
                "model_dir": str(
                    self.model_dir
                ),
                "metadata": metadata,
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(
                    error
                ),
            }

        finally:
            self._global_lock.release()

    def completed_case_count(self):
        db = SessionLocal()

        try:
            return int(
                db.query(
                    FeedCase
                )
                .filter(
                    FeedCase.status
                    == "COMPLETED"
                )
                .filter(
                    FeedCase.id
                    >= self.min_case_id
                )
                .count()
            )

        finally:
            db.close()
