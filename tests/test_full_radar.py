from core.intelligence.full_radar import FullRadar


def main():

    print("Testing Full Radar...")


    radar = FullRadar()


    result = radar.analyze(

        {
            "coin_address": "RADAR_TEST",
            "price": 0.05,
            "market_cap": 500000,
            "liquidity": 75000,
            "volume_24h": 300000,
            "holders": 8000
        },

        {
            "coin_address": "RADAR_TEST",
            "mentions": 2500,
            "engagement": 12000,
            "community_size": 5000,
            "growth_rate": 150.5
        },

        {
            "wallet_address": "WALLET_TEST",
            "coin_address": "RADAR_TEST",
            "action": "BUY",
            "amount_sol": 5,
            "market_cap": 100000
        }

    )


    print(result)



if __name__ == "__main__":
    main()