from datetime import datetime
import math

import requests


class MarketCollector:

    def __init__(self):

        self.name = "Market Collector"

        self.base_url = (
            "https://api.dexscreener.com/token-pairs/v1"
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "NarrativeRadar/2.0"
            }
        )


    # =========================================================
    # SAFE HELPERS
    # =========================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0
    ):

        try:

            if value is None:
                return float(
                    default
                )

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return float(
                default
            )


    @staticmethod
    def _same_address(
        left,
        right
    ):

        return (
            str(
                left
                or ""
            ).strip()
            ==
            str(
                right
                or ""
            ).strip()
        )


    @classmethod
    def _liquidity_usd(
        cls,
        pair
    ):

        return cls._safe_float(
            (
                pair.get(
                    "liquidity"
                )
                or {}
            ).get(
                "usd"
            )
        )


    @classmethod
    def _volume_24h(
        cls,
        pair
    ):

        return cls._safe_float(
            (
                pair.get(
                    "volume"
                )
                or {}
            ).get(
                "h24"
            )
        )


    @classmethod
    def _price_usd(
        cls,
        pair
    ):

        return cls._safe_float(
            pair.get(
                "priceUsd"
            )
        )


    @classmethod
    def _market_cap(
        cls,
        pair
    ):

        value = cls._safe_float(
            pair.get(
                "marketCap"
            )
        )

        if value <= 0:

            value = cls._safe_float(
                pair.get(
                    "fdv"
                )
            )

        return value


    @staticmethod
    def _log_distance(
        current,
        reference
    ):

        current = float(
            current
            or 0
        )

        reference = float(
            reference
            or 0
        )

        if (
            current <= 0
            or reference <= 0
        ):

            return float(
                "inf"
            )

        return abs(
            math.log(
                current
                / reference
            )
        )


    # =========================================================
    # SNAPSHOT
    # =========================================================

    def create_snapshot(
        self,
        coin_address: str,
        price: float = 0.0,
        market_cap: float = 0.0,
        liquidity: float = 0.0,
        volume_24h: float = 0.0,
        holders: int = 0,
        valid: bool = False,
        validation_error: str = None,
        pair_address: str = None,
        dex_id: str = None,
        pair_count: int = 0,
        selection_reason: str = None,
    ):

        return {
            "coin_address": (
                str(
                    coin_address
                    or ""
                ).strip()
            ),

            "price": float(
                price
                or 0
            ),

            "market_cap": float(
                market_cap
                or 0
            ),

            "liquidity": float(
                liquidity
                or 0
            ),

            "volume_24h": float(
                volume_24h
                or 0
            ),

            "holders": int(
                holders
                or 0
            ),

            "valid": bool(
                valid
            ),

            "validation_error": (
                validation_error
            ),

            "pair_address": (
                pair_address
            ),

            "dex_id": (
                dex_id
            ),

            "pair_count": int(
                pair_count
                or 0
            ),

            "selection_reason": (
                selection_reason
            ),

            "timestamp": (
                datetime.utcnow()
            ),
        }


    # =========================================================
    # EXACT-MINT PAIR FILTER
    # =========================================================

    def _valid_base_pairs(
        self,
        data,
        coin_address
    ):

        valid_pairs = []

        for pair in (
            data
            or []
        ):

            if not isinstance(
                pair,
                dict
            ):

                continue

            if (
                pair.get(
                    "chainId"
                )
                !=
                "solana"
            ):

                continue

            base_token = (
                pair.get(
                    "baseToken"
                )
                or {}
            )

            # DexScreener priceUsd / marketCap refer to the
            # BASE token. Therefore learning snapshots must
            # only use a pair where the tracked mint is the
            # base token. Quote-side matches are intentionally
            # rejected rather than interpreted with the wrong
            # token price.

            if not self._same_address(
                base_token.get(
                    "address"
                ),
                coin_address,
            ):

                continue

            price = self._price_usd(
                pair
            )

            liquidity = (
                self._liquidity_usd(
                    pair
                )
            )

            market_cap = (
                self._market_cap(
                    pair
                )
            )

            if (
                price <= 0
                or liquidity <= 0
                or market_cap <= 0
            ):

                continue

            valid_pairs.append(
                pair
            )

        return valid_pairs


    # =========================================================
    # PAIR SELECTION
    # =========================================================

    def _select_pair(
        self,
        valid_pairs,
        reference_price=0.0,
        preferred_pair_address=None,
    ):

        if not valid_pairs:

            return (
                None,
                "no_valid_pair"
            )


        # -----------------------------------------------------
        # 1. Exact preferred pair when explicitly supplied.
        # -----------------------------------------------------

        if preferred_pair_address:

            for pair in valid_pairs:

                if self._same_address(
                    pair.get(
                        "pairAddress"
                    ),
                    preferred_pair_address,
                ):

                    return (
                        pair,
                        "preferred_pair"
                    )


        # -----------------------------------------------------
        # 2. Start from the deepest legitimate pool.
        # -----------------------------------------------------

        ranked = sorted(
            valid_pairs,
            key=(
                self._liquidity_usd
            ),
            reverse=True,
        )

        deepest = ranked[
            0
        ]

        deepest_liquidity = max(
            self._liquidity_usd(
                deepest
            ),
            0.0,
        )


        if (
            reference_price <= 0
            or len(
                ranked
            )
            == 1
        ):

            return (
                deepest,
                "highest_liquidity"
            )


        # -----------------------------------------------------
        # 3. Pair-stability guard.
        #
        # If multiple real pools exist, ignore dust pools and
        # prefer a meaningful-liquidity pool whose price is
        # closest to the previous checkpoint/T0 price.
        #
        # This prevents a newly-created distorted pool from
        # taking over simply because its liquidity briefly
        # edges another pool.
        #
        # IMPORTANT:
        # This does NOT prevent genuine crashes. If the token
        # has only one meaningful pool, or all meaningful pools
        # reprice together, the new lower price is accepted.
        # -----------------------------------------------------

        minimum_meaningful_liquidity = max(
            1_000.0,
            deepest_liquidity
            * 0.10,
        )

        meaningful = [
            pair
            for pair in ranked
            if self._liquidity_usd(
                pair
            )
            >= minimum_meaningful_liquidity
        ]


        if len(
            meaningful
        ) <= 1:

            return (
                deepest,
                "highest_liquidity"
            )


        stable = min(
            meaningful,
            key=lambda pair: (
                self._log_distance(
                    self._price_usd(
                        pair
                    ),
                    reference_price,
                ),
                -self._liquidity_usd(
                    pair
                ),
            ),
        )


        return (
            stable,
            "reference_price_stability"
        )


    # =========================================================
    # FETCH MARKET DATA
    # =========================================================

    def fetch_market_data(
        self,
        coin_address: str,
        reference_price: float = 0.0,
        preferred_pair_address: str = None,
    ):

        coin_address = (
            str(
                coin_address
                or ""
            )
            .strip()
        )


        if not coin_address:

            raise ValueError(
                "coin_address is required"
            )


        url = (
            f"{self.base_url}/solana/"
            f"{coin_address}"
        )


        response = (
            self.session.get(
                url,
                timeout=8,
            )
        )

        response.raise_for_status()


        data = (
            response.json()
        )


        if not isinstance(
            data,
            list
        ):

            return self.create_snapshot(
                coin_address=(
                    coin_address
                ),
                valid=False,
                validation_error=(
                    "dex_response_not_list"
                ),
            )


        valid_pairs = (
            self._valid_base_pairs(
                data,
                coin_address,
            )
        )


        if not valid_pairs:

            return self.create_snapshot(
                coin_address=(
                    coin_address
                ),
                valid=False,
                validation_error=(
                    "no_exact_mint_base_pair"
                ),
            )


        best_pair, selection_reason = (
            self._select_pair(
                valid_pairs=(
                    valid_pairs
                ),
                reference_price=(
                    self._safe_float(
                        reference_price
                    )
                ),
                preferred_pair_address=(
                    preferred_pair_address
                ),
            )
        )


        if best_pair is None:

            return self.create_snapshot(
                coin_address=(
                    coin_address
                ),
                valid=False,
                validation_error=(
                    "pair_selection_failed"
                ),
            )


        price = (
            self._price_usd(
                best_pair
            )
        )

        market_cap = (
            self._market_cap(
                best_pair
            )
        )


        # Liquidity and volume are aggregated only across
        # exact-mint BASE pairs. Price and market cap always
        # come from one verified selected pair.

        total_liquidity = sum(
            self._liquidity_usd(
                pair
            )
            for pair in valid_pairs
        )

        total_volume_24h = sum(
            self._volume_24h(
                pair
            )
            for pair in valid_pairs
        )


        valid = (
            price > 0
            and market_cap > 0
            and total_liquidity > 0
        )


        return self.create_snapshot(
            coin_address=(
                coin_address
            ),

            price=(
                price
            ),

            market_cap=(
                market_cap
            ),

            liquidity=(
                total_liquidity
            ),

            volume_24h=(
                total_volume_24h
            ),

            holders=0,

            valid=(
                valid
            ),

            validation_error=(
                None
                if valid
                else
                "invalid_selected_pair_metrics"
            ),

            pair_address=(
                best_pair.get(
                    "pairAddress"
                )
            ),

            dex_id=(
                best_pair.get(
                    "dexId"
                )
            ),

            pair_count=(
                len(
                    valid_pairs
                )
            ),

            selection_reason=(
                selection_reason
            ),
        )