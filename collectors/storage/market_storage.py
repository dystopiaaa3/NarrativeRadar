from database.database import SessionLocal
from database.models.market import MarketObservation
from collectors.storage.coin_storage import CoinStorage


class MarketStorage:

    def __init__(self):
        self.coin_storage = CoinStorage()


    def save_snapshot(self, data):

        coin = self.coin_storage.get_or_create_coin(
            data["coin_address"]
        )


        db = SessionLocal()

        try:

            observation = MarketObservation(

                coin_id=coin.id,

                price=data["price"],

                market_cap=data["market_cap"],

                liquidity=data["liquidity"],

                volume_24h=data["volume_24h"],

                holders=data["holders"],

                timestamp=data["timestamp"]

            )


            db.add(observation)

            db.commit()

            db.refresh(observation)


            return observation


        finally:

            db.close()