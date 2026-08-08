from collectors.storage.coin_storage import CoinStorage



def main():

    print("Testing Coin Storage...")


    storage = CoinStorage()


    coin = storage.get_or_create_coin(
        "COIN_TEST_123"
    )


    print("\nCoin Created:")
    print(
        coin.id,
        coin.address,
        coin.chain
    )



if __name__ == "__main__":
    main()