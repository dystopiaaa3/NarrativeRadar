from core.narratives.pipeline import NarrativePipeline
from core.intelligence.pattern_pipeline import PatternPipeline


class FullIntelligence:

    def __init__(self):

        self.narrative_pipeline = NarrativePipeline()
        self.pattern_pipeline = PatternPipeline()


    def analyze(
        self,
        market_data,
        social_data,
        wallet_data
    ):

        narrative_result = self.narrative_pipeline.analyze(
            market_data,
            social_data,
            wallet_data
        )


        pattern_result = self.pattern_pipeline.analyze(
            narrative_result["market_score"],
            narrative_result["social_score"],
            narrative_result["wallet_score"],
            narrative_result["combined_score"]
        )


        return {
            "analysis": narrative_result,
            "patterns": pattern_result
        }