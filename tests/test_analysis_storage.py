from collectors.storage.analysis_storage import AnalysisStorage


def main():

    print("Testing Analysis Storage...")


    storage = AnalysisStorage()


    result = {

        "market_score": 85.0,

        "social_score": 85.0,

        "wallet_score": 85.0,

        "combined_score": 85.0,

        "narrative": {

            "narrative": "STRONG_NARRATIVE",

            "signal_count": 3

        }

    }


    saved = storage.save_analysis(
        coin_id=1,
        result=result
    )


    print("Saved analysis:")
    print(saved)



if __name__ == "__main__":
    main()