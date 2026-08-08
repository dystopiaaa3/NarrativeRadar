from core.intelligence.pattern_engine import PatternEngine
from core.intelligence.pattern_matcher import PatternMatcher
from core.intelligence.pattern_learning import PatternLearning


class PatternPipeline:

    def __init__(self):

        self.engine = PatternEngine()
        self.matcher = PatternMatcher()
        self.learning = PatternLearning()


    def analyze(
        self,
        market_score,
        social_score,
        wallet_score,
        combined_score
    ):


        detected = self.engine.detect_patterns(
            market_score,
            social_score,
            wallet_score,
            combined_score
        )


        matched = self.matcher.match(
            detected["patterns"],
            market_score,
            social_score,
            wallet_score,
            combined_score
        )


        learning = self.learning.evaluate(
            matched["count"],
            matched["count"],
            combined_score
        )


        return {
            "detected_patterns": detected,
            "matched_patterns": matched,
            "learning": learning
        }