from collectors.storage.pattern_storage import PatternStorage


def main():

    print("Testing Pattern Storage...")


    storage = PatternStorage()


    pattern = storage.get_or_create_pattern(
        "high_conviction_setup"
    )


    print("Saved pattern:")
    print(pattern.id)
    print(pattern.name)



if __name__ == "__main__":
    main()