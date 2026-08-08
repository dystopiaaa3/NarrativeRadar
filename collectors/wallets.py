from datetime import datetime


class WalletCollector:

    def __init__(self):
        self.name = "Wallet Collector"


    def create_activity(
        self,
        wallet_address: str,
        coin_address: str,
        action: str,
        amount_sol: float,
        market_cap: float
    ):

        return {
            "wallet_address": wallet_address,
            "coin_address": coin_address,
            "action": action,
            "amount_sol": float(amount_sol or 0),
            "market_cap": float(market_cap or 0),
            "timestamp": datetime.utcnow()
        }


    def from_transaction_change(
        self,
        wallet_address: str,
        coin_address: str,
        token_change: float,
        sol_change: float,
        market_cap: float = 0.0
    ):

        token_change = float(token_change or 0)
        sol_change = float(sol_change or 0)

        if token_change > 0:
            action = "BUY"

        elif token_change < 0:
            action = "SELL"

        else:
            action = "UNKNOWN"


        activity = self.create_activity(
            wallet_address=wallet_address,
            coin_address=coin_address,
            action=action,
            amount_sol=abs(sol_change),
            market_cap=market_cap
        )

        activity["token_change"] = token_change
        activity["sol_change"] = sol_change

        return activity


    def build_activities(
        self,
        coin_address: str,
        changes: list,
        market_cap: float = 0.0
    ):

        activities = []


        for change in changes:

            wallet_address = change.get(
                "wallet_address",
                ""
            )

            token_change = float(
                change.get(
                    "token_change",
                    0
                )
                or 0
            )

            sol_change = float(
                change.get(
                    "sol_change",
                    0
                )
                or 0
            )


            if not wallet_address:
                continue


            if token_change == 0:
                continue


            activity = self.from_transaction_change(
                wallet_address=wallet_address,
                coin_address=coin_address,
                token_change=token_change,
                sol_change=sol_change,
                market_cap=market_cap
            )


            activity["signature"] = change.get(
                "signature"
            )

            activity["block_time"] = change.get(
                "block_time"
            )


            activities.append(
                activity
            )


        return activities


    def summarize(
        self,
        coin_address: str,
        activities: list,
        market_cap: float = 0.0
    ):

        if not activities:

            return {
                "wallet_address": "",
                "coin_address": coin_address,
                "action": "UNKNOWN",
                "amount_sol": 0.0,
                "market_cap": float(
                    market_cap or 0
                ),
                "buy_count": 0,
                "sell_count": 0,
                "buy_token_volume": 0.0,
                "sell_token_volume": 0.0,
                "buy_volume_sol": 0.0,
                "sell_volume_sol": 0.0,
                "activity_count": 0,
                "dominance": 0.0,
                "timestamp": datetime.utcnow()
            }


        buy_count = 0
        sell_count = 0

        buy_token_volume = 0.0
        sell_token_volume = 0.0

        buy_volume_sol = 0.0
        sell_volume_sol = 0.0


        for activity in activities:

            action = activity.get(
                "action",
                "UNKNOWN"
            )


            token_change = float(
                activity.get(
                    "token_change",
                    0
                )
                or 0
            )


            amount_sol = float(
                activity.get(
                    "amount_sol",
                    0
                )
                or 0
            )


            if action == "BUY":

                buy_count += 1

                buy_token_volume += abs(
                    token_change
                )

                buy_volume_sol += amount_sol


            elif action == "SELL":

                sell_count += 1

                sell_token_volume += abs(
                    token_change
                )

                sell_volume_sol += amount_sol


        total_token_volume = (
            buy_token_volume
            + sell_token_volume
        )


        if total_token_volume > 0:

            buy_share = (
                buy_token_volume
                / total_token_volume
            )

            sell_share = (
                sell_token_volume
                / total_token_volume
            )

        else:

            buy_share = 0.0
            sell_share = 0.0


        # Require meaningful dominance.
        # This prevents 51/49 noise from becoming BUY/SELL.

        if buy_share >= 0.60:

            final_action = "BUY"

            dominance = buy_share


        elif sell_share >= 0.60:

            final_action = "SELL"

            dominance = sell_share


        else:

            final_action = "UNKNOWN"

            dominance = max(
                buy_share,
                sell_share
            )


        # Choose strongest wallet by absolute token change.

        strongest = max(
            activities,
            key=lambda item: abs(
                float(
                    item.get(
                        "token_change",
                        0
                    )
                    or 0
                )
            )
        )


        # amount_sol is deliberately conservative.
        #
        # We use the dominant side rather than adding BUY and
        # SELL together, which previously inflated conviction.

        if final_action == "BUY":

            amount_sol = buy_volume_sol


        elif final_action == "SELL":

            amount_sol = sell_volume_sol


        else:

            amount_sol = 0.0


        return {
            "wallet_address": strongest.get(
                "wallet_address",
                ""
            ),

            "coin_address": coin_address,

            "action": final_action,

            "amount_sol": amount_sol,

            "market_cap": float(
                market_cap or 0
            ),

            "buy_count": buy_count,

            "sell_count": sell_count,

            "buy_token_volume": buy_token_volume,

            "sell_token_volume": sell_token_volume,

            "buy_volume_sol": buy_volume_sol,

            "sell_volume_sol": sell_volume_sol,

            "activity_count": len(
                activities
            ),

            "dominance": dominance,

            "timestamp": datetime.utcnow()
        }