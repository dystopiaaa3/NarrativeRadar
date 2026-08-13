from typing import Dict, Any


class WalletAnalyzer:

    def analyze(self, activity: Dict[str, Any]) -> Dict[str, Any]:

        activity = activity or {}
        action = str(activity.get("action", "") or "").upper().strip()

        try:
            amount_sol = float(activity.get("amount_sol", 0) or 0)
        except (TypeError, ValueError):
            amount_sol = 0.0

        try:
            market_cap = float(activity.get("market_cap", 0) or 0)
        except (TypeError, ValueError):
            market_cap = 0.0

        return {
            "wallet_address": activity.get("wallet_address"),
            "coin_address": activity.get("coin_address"),
            "action": action,
            "amount_sol": max(amount_sol, 0.0),
            "market_cap": max(market_cap, 0.0),
            "is_buy": action == "BUY",
            "is_sell": action == "SELL",
        }