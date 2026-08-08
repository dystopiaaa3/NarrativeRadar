from core.intelligence.decision_engine import DecisionEngine


def main():

    print("Testing Decision Engine...")


    engine = DecisionEngine()


    result = engine.decide(
        "HIGH_CONVICTION_ENTRY",
        92,
        "STRONG_NARRATIVE",
        [
            "strong_market_momentum",
            "social_growth",
            "smart_money_activity"
        ]
    )


    print(result)



if __name__ == "__main__":
    main()