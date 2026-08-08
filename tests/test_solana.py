from collectors.solana import SolanaCollector


def main():

    print("Connecting to Solana...")

    collector = SolanaCollector()

    result = collector.check_connection()

    print(result)


if __name__ == "__main__":
    main()