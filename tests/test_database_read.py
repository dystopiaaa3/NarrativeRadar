from database.database import SessionLocal
from database.models.market import MarketObservation
from database.models.social import SocialObservation


def main():

    print("Reading database...")


    db = SessionLocal()


    markets = db.query(MarketObservation).all()

    socials = db.query(SocialObservation).all()


    print("\nMarket Records:")
    for market in markets:
        print(
            market.coin_address,
            market.price,
            market.market_cap
        )


    print("\nSocial Records:")
    for social in socials:
        print(
            social.coin_address,
            social.mentions,
            social.engagement
        )


    db.close()



if __name__ == "__main__":
    main()