from collectors.storage.market_storage import MarketStorage
from collectors.storage.social_storage import SocialStorage
from collectors.storage.wallet_storage import WalletStorage


class EngineStorage:

    def __init__(self):

        self.market = MarketStorage()

        self.social = SocialStorage()

        self.wallet = WalletStorage()


    def save_collection(self, data):

        results = {}


        results["market"] = self.market.save_snapshot(
            data["market"]
        )


        results["social"] = self.social.save_snapshot(
            data["social"]
        )


        return results