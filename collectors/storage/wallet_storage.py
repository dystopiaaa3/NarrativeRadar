from database.session import session

from database.models.wallet import Wallet
from database.models.wallet_activity import WalletActivity
from database.models.coin import Coin

from datetime import datetime


class WalletStorage:


    def save_activity(self, data: dict):

        db = session()

        try:

            # -----------------------
            # Wallet
            # -----------------------

            wallet = (
                db.query(Wallet)
                .filter_by(
                    address=data["wallet_address"]
                )
                .first()
            )


            if not wallet:

                wallet = Wallet(
                    address=data["wallet_address"],
                    label=None,
                    is_smart_wallet=False,
                    success_rate=0,
                    average_roi=0,
                    first_seen=datetime.utcnow(),
                    active=True
                )

                db.add(wallet)
                db.flush()



            # -----------------------
            # Coin
            # -----------------------

            coin = (
                db.query(Coin)
                .filter_by(
                    address=data["coin_address"]
                )
                .first()
            )


            if not coin:

                coin = Coin(
                    address=data["coin_address"],
                    name="Unknown",
                    symbol="UNKNOWN",
                    chain="solana",
                    active=True
                )

                db.add(coin)
                db.flush()



            # -----------------------
            # Activity
            # -----------------------

            activity = WalletActivity(

                wallet_id=wallet.id,

                coin_id=coin.id,

                action=data["action"],

                amount_sol=data["amount_sol"],

                token_amount=0,

                market_cap_at_time=data["market_cap"]

            )


            db.add(activity)

            db.commit()

            db.refresh(activity)


            return activity


        finally:

            db.close()