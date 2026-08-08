from core.intelligence.signal_engine import SignalEngine
from core.intelligence.decision_engine import DecisionEngine


class RadarEngine:

    def __init__(self):
        self.signal_engine = SignalEngine()
        self.decision_engine = DecisionEngine()


    def analyze(
        self,
        market_score,
        social_score,
        wallet_score,
        combined_score,
        narrative,
        patterns
    ):

        signal_result = self.signal_engine.generate_signal(
            market_score,
            social_score,
            wallet_score,
            combined_score
        )


        decision_result = self.decision_engine.decide(
            signal_result["signal"],
            signal_result["confidence"],
            narrative,
            patterns
        )


        return {
            "scores": {
                "market": market_score,
                "social": social_score,
                "wallet": wallet_score,
                "combined": combined_score
            },

            "signal": signal_result,

            "decision": decision_result
        }