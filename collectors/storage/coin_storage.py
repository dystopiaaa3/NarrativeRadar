from database.database import SessionLocal
from database.models.coin import Coin
from datetime import datetime


class CoinStorage:


    def __init__(self):

        self.name = "Coin Storage"



    def get_or_create_coin(
        self,
        address: str
    ):

        db = SessionLocal()


        coin = (
            db.query(Coin)
            .filter(
                Coin.address == address
            )
            .first()
        )


        if coin:

            db.close()

            return coin



        coin = Coin(

            address=address,

            name="Unknown",

            symbol="UNKNOWN",

            chain="solana",

            first_seen=datetime.utcnow(),

            active=True

        )


        db.add(coin)

        db.commit()

        db.refresh(coin)


        db.close()


        return coin