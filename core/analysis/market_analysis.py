from typing import Dict, Any


class MarketAnalyzer:

    def analyze(self, observation: Dict[str, Any]) -> Dict[str, Any]:

        market_cap = observation.get("market_cap", 0)
        liquidity = observation.get("liquidity", 0)
        volume_24h = observation.get("volume_24h", 0)
        holders = observation.get("holders", 0)
        price = observation.get("price", 0)

        liquidity_ratio = 0.0
        volume_ratio = 0.0

        if market_cap > 0:
            liquidity_ratio = liquidity / market_cap
            volume_ratio = volume_24h / market_cap

        return {
            "coin_address": observation.get("coin_address"),
            "price": price,
            "market_cap": market_cap,
            "liquidity": liquidity,
            "volume_24h": volume_24h,
            "holders": holders,
            "liquidity_ratio": liquidity_ratio,
            "volume_ratio": volume_ratio,
        }