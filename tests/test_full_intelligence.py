from core.intelligence.full_intelligence import FullIntelligence


def main():

    print("Testing Full Intelligence...")


    intelligence = FullIntelligence()


    result = intelligence.analyze(

        {
            "liquidity_ratio":0.15,
            "volume_ratio":0.60,
            "holders":8000
        },

        {
            "growth_rate":150.5,
            "engagement_ratio":4.8
        },

        {
            "is_buy":True,
            "amount_sol":5
        }

    )


    print()
    print("Analysis:")
    print(result["analysis"])


    print()
    print("Patterns:")
    print(result["patterns"])



if __name__ == "__main__":
    main()