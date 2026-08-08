from collectors.market import MarketCollector


def main():

    print("Testing Market Collector...")

    collector = MarketCollector()

    snapshot = collector.create_snapshot(
        coin_address="TEST123",
        price=0.01,
        market_cap=1000000,
        liquidity=50000,
        volume_24h=250000,
        holders=5000
    )

    print(snapshot)


if __name__ == "__main__":
    main()