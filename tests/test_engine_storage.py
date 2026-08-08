from collectors.engine import CollectionEngine
from collectors.engine_storage import EngineStorage


def main():

    print("Testing Engine Storage...")


    engine = CollectionEngine()


    data = engine.collect_coin(
        "STORAGE_TEST"
    )


    storage = EngineStorage()


    saved = storage.save_collection(
        data
    )


    print("\nSaved:")
    print(saved)



if __name__ == "__main__":
    main()