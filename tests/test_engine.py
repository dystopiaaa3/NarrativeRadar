from collectors.engine import CollectionEngine


def main():

    print("Testing Collection Engine...")


    engine = CollectionEngine()


    result = engine.collect_coin(
        "ENGINE_TEST"
    )


    print("\nCollected Full Data:")
    print(result)



if __name__ == "__main__":
    main()