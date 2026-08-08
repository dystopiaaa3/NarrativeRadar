from collectors.social import SocialCollector


def main():

    print("Testing Social Collector...")

    collector = SocialCollector()

    snapshot = collector.create_snapshot(
        coin_address="TEST123",
        mentions=500,
        engagement=2500,
        community_size=1000,
        growth_rate=75.5
    )

    print(snapshot)


if __name__ == "__main__":
    main()