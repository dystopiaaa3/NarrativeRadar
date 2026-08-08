from collectors.storage.radar_result_storage import RadarResultStorage


def main():
    print("Testing Radar Result Storage...")

    storage = RadarResultStorage()

    result = storage.save_result(
        1,
        {
            "market_score": 85,
            "social_score": 85,
            "wallet_score": 85,
            "combined_score": 85,
            "narrative": "STRONG_NARRATIVE",
            "signal": "HIGH_CONVICTION_ENTRY",
            "confidence": 92,
            "decision": "ENTER_WATCH",
            "risk": "LOW",
        }
    )

    print("Saved Radar Result:")
    print(result.id)
    print(result.combined_score)
    print(result.signal)
    print(result.decision)


if __name__ == "__main__":
    main()