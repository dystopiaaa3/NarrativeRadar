from collectors.wallets import WalletCollector
from collectors.storage.wallet_storage import WalletStorage


def main():

    print("Testing Wallet Pipeline...")


    collector = WalletCollector()


    activity = collector.create_activity(
        wallet_address="WALLET_TEST",
        coin_address="COIN_TEST",
        action="BUY",
        amount_sol=5,
        market_cap=100000
    )


    print("Collected:")
    print(activity)


    storage = WalletStorage()


    saved = storage.save_activity(activity)


    print("\nSaved to database:")
    print(saved.id)



if __name__ == "__main__":
    main()