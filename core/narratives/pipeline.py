from core.intelligence.scoring import IntelligenceScorer
from core.narratives.narrative_detector import NarrativeDetector


class NarrativePipeline:

    def __init__(self):
        self.scorer = IntelligenceScorer()
        self.detector = NarrativeDetector()

    def analyze(
        self,
        market_data,
        social_data,
        wallet_data
    ):
        market_score = self.scorer.score_market(
            market_data
        )

        social_score = self.scorer.score_social(
            social_data
        )

        wallet_score = self.scorer.score_wallet(
            wallet_data
        )

        combined_score = self.scorer.combined_score(
            market_score,
            social_score,
            wallet_score
        )

        narrative = self.detector.detect(
            market_score=market_score,
            social_score=social_score,
            wallet_score=wallet_score
        )

        return {
            "market_score": market_score,
            "social_score": social_score,
            "wallet_score": wallet_score,
            "combined_score": combined_score,
            "narrative": narrative
        }