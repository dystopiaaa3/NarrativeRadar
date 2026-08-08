from datetime import datetime

from collectors.engine import CollectionEngine

from core.intelligence.full_radar import FullRadar

from collectors.storage.radar_result_storage import (
    RadarResultStorage,
)

from collectors.storage.market_storage import (
    MarketStorage,
)


class LiveRadar:

    def __init__(self):

        self.collector = (
            CollectionEngine()
        )

        self.radar = (
            FullRadar()
        )

        self.storage = (
            RadarResultStorage()
        )

        self.market_storage = (
            MarketStorage()
        )


    # =========================================
    # SAFE HELPERS
    # =========================================

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
    def _safe_int(
        value,
        default=0
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
            ValueError
        ):

            return default


    # =========================================
    # SAVE MARKET OBSERVATION
    # =========================================

    def _save_market_snapshot(
        self,
        coin_address,
        market_data
    ):

        if not isinstance(
            market_data,
            dict
        ):

            return None


        price = (
            self._safe_float(
                market_data.get(
                    "price"
                )
            )
        )

        market_cap = (
            self._safe_float(
                market_data.get(
                    "market_cap"
                )
            )
        )

        liquidity = (
            self._safe_float(
                market_data.get(
                    "liquidity"
                )
            )
        )

        volume_24h = (
            self._safe_float(
                market_data.get(
                    "volume_24h",
                    market_data.get(
                        "volume",
                        0
                    )
                )
            )
        )

        holders = (
            self._safe_int(
                market_data.get(
                    "holders",
                    0
                )
            )
        )


        # Do not create completely empty market rows.

        has_market_data = any(
            [
                price > 0,
                market_cap > 0,
                liquidity > 0,
                volume_24h > 0,
            ]
        )


        if not has_market_data:

            return None


        payload = {
            "coin_address": (
                coin_address
            ),

            "price": (
                price
            ),

            "market_cap": (
                market_cap
            ),

            "liquidity": (
                liquidity
            ),

            "volume_24h": (
                volume_24h
            ),

            "holders": (
                holders
            ),

            "timestamp": (
                datetime.utcnow()
            ),
        }


        return (
            self.market_storage
            .save_snapshot(
                payload
            )
        )


    # =========================================
    # RUN LIVE RADAR
    # =========================================

    def run(
        self,
        coin_id: int,
        coin_address: str,
        signature_limit: int = 20,
        social_topic: str = None
    ):

        # =====================================
        # LIVE COLLECTION
        # =====================================

        collected = (
            self.collector.collect_coin(
                coin_address=coin_address,

                signature_limit=(
                    signature_limit
                ),

                social_topic=(
                    social_topic
                )
            )
        )


        # =====================================
        # DATA INPUTS
        # =====================================

        market_data = (
            collected.get(
                "market",
                {}
            )
        )

        social_data = (
            collected.get(
                "social",
                {}
            )
        )

        wallet_data = (
            collected.get(
                "wallet_summary",
                {}
            )
        )


        # =====================================
        # SAVE REAL MARKET SNAPSHOT
        #
        # This is what /trending, /emerging,
        # /compare etc. need for narrative
        # market-cap and volume statistics.
        # =====================================

        saved_market = (
            self._save_market_snapshot(
                coin_address,
                market_data
            )
        )


        # =====================================
        # RADAR ANALYSIS
        # =====================================

        radar_result = (
            self.radar.analyze(
                market_data,
                social_data,
                wallet_data
            )
        )


        # =====================================
        # EXTRACT RESULT
        # =====================================

        analysis = (
            radar_result[
                "analysis"
            ]
        )


        narrative_data = (
            radar_result[
                "narrative"
            ][
                "narrative"
            ]
        )


        signal_data = (
            radar_result[
                "radar"
            ][
                "signal"
            ]
        )


        decision_data = (
            radar_result[
                "radar"
            ][
                "decision"
            ]
        )


        # =====================================
        # RADAR RESULT DATABASE PAYLOAD
        # =====================================

        storage_payload = {

            "market_score": (
                analysis[
                    "market_score"
                ]
            ),

            "social_score": (
                analysis[
                    "social_score"
                ]
            ),

            "wallet_score": (
                analysis[
                    "wallet_score"
                ]
            ),

            "combined_score": (
                analysis[
                    "combined_score"
                ]
            ),

            "narrative": (
                narrative_data[
                    "narrative"
                ]
            ),

            "signal": (
                signal_data[
                    "signal"
                ]
            ),

            "confidence": (
                signal_data[
                    "confidence"
                ]
            ),

            "decision": (
                decision_data[
                    "decision"
                ]
            ),

            "risk": (
                decision_data[
                    "risk"
                ]
            )
        }


        # =====================================
        # SAVE RADAR RESULT
        # =====================================

        saved = (
            self.storage.save_result(
                coin_id,
                storage_payload
            )
        )


        # =====================================
        # RETURN COMPLETE LIVE RESULT
        # =====================================

        return {

            "collected": (
                collected
            ),

            "radar": (
                radar_result
            ),

            "saved_result_id": (
                saved.id
            ),

            "saved_market_observation_id": (
                saved_market.id
                if saved_market
                else None
            )
        }