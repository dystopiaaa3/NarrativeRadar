from core.intelligence.radar_engine import RadarEngine


def main():

    print("Testing Radar Engine...")


    engine = RadarEngine()


    result = engine.analyze(
        85,
        85,
        85,
        85,
        "STRONG_NARRATIVE",
        [
            "strong_market_momentum",
            "social_growth",
            "smart_money_activity",
            "high_conviction_setup",
            "emerging_narrative"
        ]
    )


    print(result)



if __name__ == "__main__":
    main()