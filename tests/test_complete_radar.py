from core.narratives.pipeline import NarrativePipeline
from core.intelligence.pattern_engine import PatternEngine
from core.intelligence.pattern_matcher import PatternMatcher
from core.intelligence.pattern_learning import PatternLearning
from collectors.storage.intelligence_storage import IntelligenceStorage


def main():

    print("Testing Complete NarrativeRadar...")


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


    analysis = pipeline.analyze(
        market_data,
        social_data,
        wallet_data
    )


    print("\nAnalysis:")
    print(analysis)



    pattern_engine = PatternEngine()


    detected = pattern_engine.detect_patterns(
        analysis["market_score"],
        analysis["social_score"],
        analysis["wallet_score"],
        analysis["combined_score"]
    )


    print("\nDetected Patterns:")
    print(detected)



    matcher = PatternMatcher()


    matched = matcher.match(
        detected["patterns"],
        analysis["market_score"],
        analysis["social_score"],
        analysis["wallet_score"],
        analysis["combined_score"]
    )


    print("\nMatched Patterns:")
    print(matched)



    learner = PatternLearning()


    learning = learner.evaluate(
        detected["pattern_count"],
        detected["pattern_count"],
        analysis["combined_score"]
    )


    print("\nLearning:")
    print(learning)



    storage = IntelligenceStorage()


    saved_analysis = storage.save_analysis(
        1,
        analysis
    )


    print("\nSaved Analysis:")
    print(saved_analysis)



    saved_patterns = storage.save_patterns(
        [
            {
                "pattern": p["pattern"]
            }
            for p in matched["matched_patterns"]
        ]
    )


    print("\nSaved Patterns:")

    for p in saved_patterns:
        print(p.id, p.name)



if __name__ == "__main__":
    main()