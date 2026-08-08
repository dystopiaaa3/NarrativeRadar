from datetime import datetime

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
                "User-Agent": "NarrativeRadar/1.0"
            }
        )

    def _safe_float(
        self,
        value,
        default=0.0
    ):

        try:

            if value is None:
                return default

            return float(value)

        except (
            TypeError,
            ValueError
        ):

            return default

    def create_snapshot(
        self,
        coin_address: str,
        price: float = 0.0,
        market_cap: float = 0.0,
        liquidity: float = 0.0,
        volume_24h: float = 0.0,
        holders: int = 0
    ):

        return {
            "coin_address": coin_address,
            "price": float(price or 0),
            "market_cap": float(market_cap or 0),
            "liquidity": float(liquidity or 0),
            "volume_24h": float(volume_24h or 0),
            "holders": int(holders or 0),
            "timestamp": datetime.utcnow()
        }

    def fetch_market_data(
        self,
        coin_address: str
    ):

        if not coin_address:

            raise ValueError(
                "coin_address is required"
            )

        url = (
            f"{self.base_url}/solana/"
            f"{coin_address}"
        )

        response = self.session.get(
            url,
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(
            data,
            list
        ):

            return self.create_snapshot(
                coin_address=coin_address
            )

        valid_pairs = []

        for pair in data:

            if pair.get(
                "chainId"
            ) != "solana":

                continue

            base_token = (
                pair.get(
                    "baseToken"
                )
                or {}
            )

            if (
                base_token.get(
                    "address"
                )
                != coin_address
            ):

                continue

            price = self._safe_float(
                pair.get(
                    "priceUsd"
                )
            )

            liquidity = self._safe_float(
                (
                    pair.get(
                        "liquidity"
                    )
                    or {}
                ).get(
                    "usd"
                )
            )

            if (
                price <= 0
                or liquidity <= 0
            ):

                continue

            valid_pairs.append(
                pair
            )

        if not valid_pairs:

            return self.create_snapshot(
                coin_address=coin_address
            )

        valid_pairs.sort(
            key=lambda pair: self._safe_float(
                (
                    pair.get(
                        "liquidity"
                    )
                    or {}
                ).get(
                    "usd"
                )
            ),
            reverse=True
        )

        best_pair = valid_pairs[0]

        price = self._safe_float(
            best_pair.get(
                "priceUsd"
            )
        )

        market_cap = self._safe_float(
            best_pair.get(
                "marketCap"
            )
        )

        if market_cap <= 0:

            market_cap = self._safe_float(
                best_pair.get(
                    "fdv"
                )
            )

        total_liquidity = 0.0
        total_volume_24h = 0.0

        for pair in valid_pairs:

            total_liquidity += (
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

            total_volume_24h += (
                self._safe_float(
                    (
                        pair.get(
                            "volume"
                        )
                        or {}
                    ).get(
                        "h24"
                    )
                )
            )

        return self.create_snapshot(
            coin_address=coin_address,
            price=price,
            market_cap=market_cap,
            liquidity=total_liquidity,
            volume_24h=total_volume_24h,
            holders=0
        )