from database.session import session

from database.models.social import SocialObservation
from database.models.coin import Coin



class SocialStorage:


    def save_snapshot(self, data: dict):

        db = session()


        try:


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



            observation = SocialObservation(

                coin_id=coin.id,

                coin_address=data["coin_address"],

                mentions=data["mentions"],

                engagement=data["engagement"],

                community_size=data["community_size"],

                growth_rate=data["growth_rate"]

            )


            db.add(observation)

            db.commit()

            db.refresh(observation)


            return observation


        finally:

            db.close()