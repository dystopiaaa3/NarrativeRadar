from collectors.storage.intelligence_storage import IntelligenceStorage


def main():

    print("Testing Intelligence Storage...")


    storage = IntelligenceStorage()


    analysis_id = storage.save_analysis(
        1,
        {
            "market_score":85,
            "social_score":85,
            "wallet_score":85,
            "combined_score":85,
            "narrative":{
                "narrative":"STRONG_NARRATIVE",
                "signal_count":3
            }
        }
    )


    print("Saved Analysis:")
    print(analysis_id)


    patterns = storage.save_patterns(
        [
            {
                "pattern":"strong_market_momentum"
            },
            {
                "pattern":"emerging_narrative"
            }
        ]
    )


    print("Saved Patterns:")

    for p in patterns:
        print(p.id,p.name)


if __name__ == "__main__":
    main()