class SignalEngine:

    def __init__(self):
        pass


    def generate_signal(
        self,
        market_score,
        social_score,
        wallet_score,
        combined_score
    ):

        signals = []
        confidence = 0


        # Market strength
        if market_score >= 80:
            signals.append("strong_market")
            confidence += 25


        elif market_score >= 60:
            signals.append("healthy_market")
            confidence += 15



        # Social strength
        if social_score >= 80:
            signals.append("social_growth")
            confidence += 25


        elif social_score >= 60:
            signals.append("social_activity")
            confidence += 15



        # Wallet strength
        if wallet_score >= 80:
            signals.append("smart_money")
            confidence += 25


        elif wallet_score >= 60:
            signals.append("wallet_activity")
            confidence += 15



        # Combined decision
        if combined_score >= 85 and len(signals) >= 3:

            signal = "HIGH_CONVICTION_ENTRY"

            confidence += 17


        elif combined_score >= 70:

            signal = "WATCHLIST"

            confidence += 10


        else:

            signal = "LOW_CONFIDENCE"



        return {
            "signal": signal,
            "confidence": min(confidence, 100),
            "signals": signals
        }