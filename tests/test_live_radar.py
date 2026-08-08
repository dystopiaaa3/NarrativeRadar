from core.intelligence.live_radar import LiveRadar


def main():

    print(
        "Testing LIVE NarrativeRadar..."
    )


    radar = LiveRadar()


    result = radar.run(
        coin_id=1,
        coin_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        signature_limit=50
    )


    print("\nMARKET:")

    print(
        result[
            "collected"
        ][
            "market"
        ]
    )


    print("\nWALLET SUMMARY:")

    print(
        result[
            "collected"
        ][
            "wallet_summary"
        ]
    )


    print("\nANALYSIS:")

    print(
        result[
            "radar"
        ][
            "analysis"
        ]
    )


    print("\nNARRATIVE:")

    print(
        result[
            "radar"
        ][
            "narrative"
        ]
    )


    print("\nSIGNAL:")

    print(
        result[
            "radar"
        ][
            "radar"
        ][
            "signal"
        ]
    )


    print("\nDECISION:")

    print(
        result[
            "radar"
        ][
            "radar"
        ][
            "decision"
        ]
    )


    print("\nSAVED RESULT ID:")

    print(
        result[
            "saved_result_id"
        ]
    )


if __name__ == "__main__":
    main()