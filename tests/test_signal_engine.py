from core.intelligence.signal_engine import SignalEngine


def main():

    print("Testing Signal Engine...")


    engine = SignalEngine()


    result = engine.generate_signal(
        85,
        85,
        85,
        85
    )


    print("Signal:")
    print(result["signal"])


    print("Confidence:")
    print(result["confidence"])


    print("Signals:")
    print(result["signals"])



if __name__ == "__main__":
    main()