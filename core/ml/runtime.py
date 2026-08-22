import json
import os
import threading
import time
from pathlib import Path

import numpy as np

from core.ml.features import (
    FEATURE_NAMES,
    build_live_features,
)

from core.ml.trainer import (
    XGBTrainer,
)


class MLRuntime:

    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self.trainer = XGBTrainer()

        self.model_dir = (
            self.trainer.model_dir
        )

        self._models = {}
        self._metadata = None
        self._metadata_mtime = None

        self._model_lock = (
            threading.RLock()
        )

        self._stop_event = (
            threading.Event()
        )

        self.retrain_every_cases = int(
            os.getenv(
                "ML_RETRAIN_EVERY_CASES",
                "100",
            )
        )

        self.poll_seconds = int(
            os.getenv(
                "ML_RETRAIN_POLL_SECONDS",
                "1800",
            )
        )

        self.enabled = (
            os.getenv(
                "ML_ENABLED",
                "1",
            )
            .strip()
            .lower()
            not in (
                "0",
                "false",
                "no",
                "off",
            )
        )

        self._load_if_changed()

        if self.enabled:
            self._start_background_retrainer()

    @classmethod
    def get_instance(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()

            return cls._instance

    def _metadata_path(self):
        return (
            self.model_dir
            / "metadata.json"
        )

    def _load_if_changed(self):
        metadata_path = (
            self._metadata_path()
        )

        if not metadata_path.exists():
            return False

        try:
            mtime = (
                metadata_path.stat()
                .st_mtime
            )

            if (
                self._metadata_mtime
                is not None
                and
                mtime
                == self._metadata_mtime
            ):
                return False

            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            import xgboost as xgb

            models = {}

            for target_name in (
                "move20",
                "move50",
                "collapse80",
            ):
                model_path = (
                    self.model_dir
                    / f"{target_name}.json"
                )

                if not model_path.exists():
                    continue

                booster = (
                    xgb.Booster()
                )

                booster.load_model(
                    model_path
                )

                models[
                    target_name
                ] = booster

            with self._model_lock:
                self._models = models
                self._metadata = metadata
                self._metadata_mtime = mtime

            return True

        except Exception as error:
            print(
                "ML model load error:",
                str(error),
            )

            return False

    def status(self):
        self._load_if_changed()

        with self._model_lock:
            trained_through = (
                (
                    self._metadata
                    or {}
                ).get(
                    "trained_through_case_id"
                )
            )

            return {
                "enabled": (
                    self.enabled
                ),

                "mode": "SHADOW",

                "model_dir": str(
                    self.model_dir
                ),

                "models_loaded": sorted(
                    self._models.keys()
                ),

                "trained_through_case_id": (
                    trained_through
                ),
            }

    def predict(
        self,
        market_data,
        analysis,
        signal=None,
    ):
        if not self.enabled:
            return {
                "available": False,
                "mode": "SHADOW",
                "error": "ML_DISABLED",
            }

        self._load_if_changed()

        with self._model_lock:
            models = dict(
                self._models
            )

            metadata = dict(
                self._metadata
                or {}
            )

        required = {
            "move20",
            "move50",
            "collapse80",
        }

        if not required.issubset(
            set(
                models.keys()
            )
        ):
            return {
                "available": False,
                "mode": "SHADOW",
                "error": (
                    "ML_MODELS_NOT_READY"
                ),
                "models_loaded": sorted(
                    models.keys()
                ),
            }

        try:
            import xgboost as xgb

            features = build_live_features(
                market_data,
                analysis,
                signal=signal,
            )

            matrix = xgb.DMatrix(
                np.asarray(
                    [
                        features
                    ],
                    dtype=np.float32,
                ),
                feature_names=FEATURE_NAMES,
            )

            move20 = float(
                models[
                    "move20"
                ].predict(
                    matrix
                )[0]
            )

            move50 = float(
                models[
                    "move50"
                ].predict(
                    matrix
                )[0]
            )

            collapse80 = float(
                models[
                    "collapse80"
                ].predict(
                    matrix
                )[0]
            )

            action = self._shadow_action(
                move20,
                move50,
                collapse80,
            )

            return {
                "available": True,
                "mode": "SHADOW",

                "move20_probability": round(
                    move20,
                    4,
                ),

                "move50_probability": round(
                    move50,
                    4,
                ),

                "collapse80_probability": round(
                    collapse80,
                    4,
                ),

                "move20_pct": round(
                    move20 * 100.0,
                    1,
                ),

                "move50_pct": round(
                    move50 * 100.0,
                    1,
                ),

                "collapse80_pct": round(
                    collapse80 * 100.0,
                    1,
                ),

                "shadow_action": action,

                "trained_through_case_id": (
                    metadata.get(
                        "trained_through_case_id"
                    )
                ),
            }

        except Exception as error:
            return {
                "available": False,
                "mode": "SHADOW",
                "error": str(
                    error
                ),
            }

    @staticmethod
    def _shadow_action(
        move20,
        move50,
        collapse80,
    ):
        # These labels are deliberately conservative.
        # They DO NOT override V3 or Discord decisions.
        if (
            move20 >= 0.55
            and
            move50 >= 0.20
            and
            collapse80 <= 0.45
        ):
            return "ML_STRONG_WATCH"

        if (
            move20 >= 0.35
            and
            collapse80 <= 0.60
        ):
            return "ML_WATCH"

        if (
            move20 >= 0.25
            and
            collapse80 <= 0.70
        ):
            return "ML_SPECULATIVE"

        return "ML_IGNORE"

    def _start_background_retrainer(self):
        thread = threading.Thread(
            target=self._retrainer_loop,
            name="NarrativeRadarMLRetrainer",
            daemon=True,
        )

        thread.start()

    def _retrainer_loop(self):
        # Give bot startup a little room before touching CPU/database.
        self._stop_event.wait(
            60
        )

        while not self._stop_event.is_set():
            try:
                if self._should_retrain():
                    print(
                        "ML retraining started..."
                    )

                    result = (
                        self.trainer.train()
                    )

                    if result.get(
                        "success"
                    ):
                        metadata = result.get(
                            "metadata",
                            {},
                        )

                        print(
                            "ML retraining complete | "
                            "cases="
                            f"{metadata.get('dataset_cases')} | "
                            "through_case="
                            f"{metadata.get('trained_through_case_id')}"
                        )

                        self._load_if_changed()

                    else:
                        print(
                            "ML retraining skipped/failed:",
                            result.get(
                                "error"
                            ),
                        )

            except Exception as error:
                print(
                    "ML retrainer error:",
                    str(error),
                )

            self._stop_event.wait(
                max(
                    self.poll_seconds,
                    300,
                )
            )

    def _should_retrain(self):
        metadata_path = (
            self._metadata_path()
        )

        if not metadata_path.exists():
            return True

        self._load_if_changed()

        with self._model_lock:
            metadata = dict(
                self._metadata
                or {}
            )

        trained_through = int(
            metadata.get(
                "trained_through_case_id",
                0,
            )
            or 0
        )

        # Count completed cases through the DB only every polling cycle.
        db_count = (
            self.trainer.completed_case_count()
        )

        dataset_cases = int(
            metadata.get(
                "dataset_cases",
                0,
            )
            or 0
        )

        return (
            db_count
            >= (
                dataset_cases
                +
                max(
                    self.retrain_every_cases,
                    25,
                )
            )
            or
            trained_through <= 0
        )

    def stop(self):
        self._stop_event.set()
