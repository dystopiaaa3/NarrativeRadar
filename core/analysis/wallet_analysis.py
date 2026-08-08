from typing import Dict, Any


class WalletAnalyzer:

    def analyze(self, activity: Dict[str, Any]) -> Dict[str, Any]:

        action = activity.get("action", "").upper()
        amount_sol = activity.get("amount_sol", 0)
        market_cap = activity.get("market_cap", 0)

        is_buy = action == "BUY"
        is_sell = action == "SELL"

        return {
            "wallet_address": activity.get("wallet_address"),
            "coin_address": activity.get("coin_address"),
            "action": action,
            "amount_sol": amount_sol,
            "market_cap": market_cap,
            "is_buy": is_buy,
            "is_sell": is_sell,
        }