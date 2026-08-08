from collectors.market import MarketCollector
from collectors.social import SocialCollector
from collectors.wallets import WalletCollector
from collectors.solana import SolanaCollector


class CollectionEngine:

    def __init__(self):

        self.market = (
            MarketCollector()
        )

        self.social = (
            SocialCollector()
        )

        self.wallets = (
            WalletCollector()
        )

        self.solana = (
            SolanaCollector()
        )


    def collect_coin(
        self,
        coin_address: str,
        signature_limit: int = 20,
        social_topic: str = None
    ):

        print(
            f"Collecting live data for "
            f"{coin_address}"
        )


        # =========================================
        # SOLANA STATUS
        # =========================================

        solana_status = (
            self.solana.check_connection()
        )


        # =========================================
        # MARKET
        # =========================================

        try:

            market_data = (
                self.market.fetch_market_data(
                    coin_address
                )
            )


            market_error = None


        except Exception as e:

            market_data = (
                self.market.create_snapshot(
                    coin_address=coin_address
                )
            )


            market_error = str(
                e
            )


        # =========================================
        # TOKEN SUPPLY
        # =========================================

        supply_data = (
            self.solana.get_token_supply(
                coin_address
            )
        )


        # =========================================
        # WALLET ACTIVITY
        # =========================================

        wallet_result = (
            self.solana.get_recent_wallet_activity(
                coin_address,
                limit=signature_limit
            )
        )


        if wallet_result.get(
            "success"
        ):

            wallet_activities = (
                self.wallets.build_activities(
                    coin_address=coin_address,

                    changes=wallet_result.get(
                        "activities",
                        []
                    ),

                    market_cap=market_data.get(
                        "market_cap",
                        0
                    )
                )
            )


            wallet_error = None


        else:

            wallet_activities = []


            wallet_error = (
                wallet_result.get(
                    "error"
                )
            )


        wallet_summary = (
            self.wallets.summarize(
                coin_address=coin_address,

                activities=wallet_activities,

                market_cap=market_data.get(
                    "market_cap",
                    0
                )
            )
        )


        # =========================================
        # SOCIAL
        # =========================================

        social_data = (
            self.social.fetch_social_data(
                coin_address=coin_address,
                topic=social_topic
            )
        )


        # =========================================
        # RETURN
        # =========================================

        return {

            "coin_address": (
                coin_address
            ),


            "solana": (
                solana_status
            ),


            "supply": (
                supply_data
            ),


            "market": (
                market_data
            ),


            "market_error": (
                market_error
            ),


            "social": (
                social_data
            ),


            "wallets": (
                wallet_activities
            ),


            "wallet_summary": (
                wallet_summary
            ),


            "wallet_activity_count": len(
                wallet_activities
            ),


            "wallet_error": (
                wallet_error
            )
        }