from core.narratives.pipeline import NarrativePipeline
from collectors.storage.analysis_storage import AnalysisStorage


def main():

    print("Testing Full Narrative Pipeline...")

    pipeline = NarrativePipeline()

    market_data = {
        "liquidity_ratio": 0.15,
        "volume_ratio": 0.60,
        "holders": 8000
    }

    social_data = {
        "growth_rate": 150.5,
        "engagement_ratio": 4.8
    }

    wallet_data = {
        "is_buy": True,
        "amount_sol": 5
    }


    result = pipeline.analyze(
        market_data,
        social_data,
        wallet_data
    )


    print()
    print("Market Score:")
    print(result["market_score"])

    print()
    print("Social Score:")
    print(result["social_score"])

    print()
    print("Wallet Score:")
    print(result["wallet_score"])

    print()
    print("Combined Score:")
    print(result["combined_score"])

    print()
    print("Narrative:")
    print(result["narrative"]["narrative"])

    print()
    print("Signals:")
    print(result["narrative"]["signals"])


    storage = AnalysisStorage()

    saved = storage.save_analysis(
        coin_id=1,
        result=result
    )


    print()
    print("Saved Analysis:")
    print(saved)



if __name__ == "__main__":
    main()