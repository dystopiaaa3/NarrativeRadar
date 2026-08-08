class NarrativeDetector:

    def detect(
        self,
        market_score,
        social_score,
        wallet_score
    ):
        signals = []

        if market_score >= 70:
            signals.append("strong_market")

        if social_score >= 70:
            signals.append("strong_social")

        if wallet_score >= 70:
            signals.append("strong_wallet")

        if len(signals) == 3:
            narrative = "STRONG_NARRATIVE"
        elif len(signals) == 2:
            narrative = "EMERGING_NARRATIVE"
        elif len(signals) == 1:
            narrative = "WEAK_NARRATIVE"
        else:
            narrative = "NO_NARRATIVE"

        return {
            "narrative": narrative,
            "signals": signals,
            "signal_count": len(signals)
        }