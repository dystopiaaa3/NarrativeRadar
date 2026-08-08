from collectors.social import SocialCollector
from collectors.storage.social_storage import SocialStorage


def main():

    print("Testing Social Pipeline...")

    collector = SocialCollector()

    snapshot = collector.create_snapshot(
        coin_address="SOCIAL_TEST",
        mentions=2500,
        engagement=12000,
        community_size=5000,
        growth_rate=150.5
    )

    print("Collected:")
    print(snapshot)


    storage = SocialStorage()

    saved = storage.save_snapshot(
        snapshot
    )

    print("\nSaved to database:")
    print(saved.coin_id)


if __name__ == "__main__":
    main()