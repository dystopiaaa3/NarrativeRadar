from collectors.wallets import WalletCollector


def main():

    print("Testing Wallet Collector...")

    collector = WalletCollector()

    activity = collector.create_activity(
        wallet_address="WALLET123",
        coin_address="TEST123",
        action="BUY",
        amount_sol=10,
        market_cap=250000
    )

    print(activity)


if __name__ == "__main__":
    main()