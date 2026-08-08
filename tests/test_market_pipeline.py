from collectors.market import MarketCollector
from collectors.storage.market_storage import MarketStorage


def main():

    print("Testing Market Pipeline...")

    collector = MarketCollector()

    snapshot = collector.create_snapshot(
        coin_address="PIPELINE_TEST",
        price=0.05,
        market_cap=500000,
        liquidity=75000,
        volume_24h=300000,
        holders=8000
    )

    print("Collected:")
    print(snapshot)


    storage = MarketStorage()

    saved = storage.save_snapshot(
        snapshot
    )

    print("\nSaved to database:")
    print(saved.coin_id)


if __name__ == "__main__":
    main()