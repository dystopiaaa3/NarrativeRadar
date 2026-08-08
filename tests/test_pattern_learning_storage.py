from collectors.storage.pattern_learning_storage import PatternLearningStorage


def main():

    print("Testing Pattern Learning Storage...")


    storage = PatternLearningStorage()


    pattern = storage.get_or_create_pattern(
        "high_conviction_setup"
    )


    print("Created:")
    print(pattern.name)


    updated = storage.update_pattern(
        "high_conviction_setup",
        80,
        145.5
    )


    print("Updated:")
    print(updated.name)
    print(updated.success_rate)
    print(updated.average_return)



if __name__ == "__main__":
    main()