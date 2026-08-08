class PatternMatcher:

    def __init__(self):
        self.name = "Pattern Matcher"


    def match(
        self,
        patterns,
        market_score,
        social_score,
        wallet_score,
        combined_score
    ):

        matches = []


        for pattern in patterns:

            confidence = 0


            if pattern == "strong_market_momentum":

                if market_score >= 80:
                    confidence += 40


            if pattern == "social_growth":

                if social_score >= 80:
                    confidence += 40


            if pattern == "smart_money_activity":

                if wallet_score >= 80:
                    confidence += 40


            if pattern == "high_conviction_setup":

                if combined_score >= 80:
                    confidence += 50


            if pattern == "emerging_narrative":

                if (
                    market_score >= 70
                    and social_score >= 70
                    and wallet_score >= 70
                ):
                    confidence += 50


            if confidence > 0:

                matches.append(
                    {
                        "pattern": pattern,
                        "confidence": confidence
                    }
                )


        return {
            "matched_patterns": matches,
            "count": len(matches)
        }