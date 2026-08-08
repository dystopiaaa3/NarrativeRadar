class PatternEngine:

    def __init__(self):
        self.name = "Pattern Engine"


    def detect_patterns(
        self,
        market_score: float,
        social_score: float,
        wallet_score: float,
        combined_score: float
    ):

        patterns = []


        if market_score >= 80:
            patterns.append(
                "strong_market_momentum"
            )


        if social_score >= 80:
            patterns.append(
                "social_growth"
            )


        if wallet_score >= 80:
            patterns.append(
                "smart_money_activity"
            )


        if combined_score >= 85:
            patterns.append(
                "high_conviction_setup"
            )


        if (
            market_score >= 80
            and social_score >= 80
            and wallet_score >= 80
        ):
            patterns.append(
                "emerging_narrative"
            )


        return {
            "pattern_count": len(patterns),
            "patterns": patterns
        }