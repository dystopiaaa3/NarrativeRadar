from core.analysis.market_analysis import MarketAnalyzer
from core.analysis.social_analysis import SocialAnalyzer
from core.analysis.wallet_analysis import WalletAnalyzer

from core.intelligence.scoring import IntelligenceScorer
from core.narratives.pipeline import NarrativePipeline

from core.intelligence.pattern_engine import PatternEngine
from core.intelligence.pattern_matcher import PatternMatcher
from core.intelligence.pattern_learning import PatternLearning

from core.intelligence.radar_engine import RadarEngine


class FullRadar:

    def __init__(self):

        self.market_analyzer = MarketAnalyzer()

        self.social_analyzer = SocialAnalyzer()

        self.wallet_analyzer = WalletAnalyzer()

        self.scorer = IntelligenceScorer()

        self.narrative_pipeline = NarrativePipeline()

        self.pattern_engine = PatternEngine()

        self.pattern_matcher = PatternMatcher()

        self.pattern_learning = PatternLearning()

        self.radar_engine = RadarEngine()


    def analyze(
        self,
        market_data,
        social_data,
        wallet_data
    ):

        # =========================================
        # ANALYZE RAW INPUTS
        # =========================================

        market_analysis = (
            self.market_analyzer.analyze(
                market_data
            )
        )

        social_analysis = (
            self.social_analyzer.analyze(
                social_data
            )
        )

        wallet_analysis = (
            self.wallet_analyzer.analyze(
                wallet_data
            )
        )


        # =========================================
        # MARKET AVAILABILITY
        # =========================================

        market_available = (
            float(
                market_data.get(
                    "price",
                    0
                )
                or 0
            ) > 0
            and
            float(
                market_data.get(
                    "market_cap",
                    0
                )
                or 0
            ) > 0
        )


        # =========================================
        # SOCIAL AVAILABILITY
        # =========================================

        social_available = bool(
            social_data.get(
                "available",
                False
            )
        )


        # =========================================
        # WALLET AVAILABILITY
        #
        # We require:
        #
        # BUY / SELL direction
        # at least 3 observations
        # >= 60% dominance
        #
        # One random transaction will therefore
        # NOT become a trusted wallet signal.
        # =========================================

        wallet_action = (
            wallet_data.get(
                "action",
                "UNKNOWN"
            )
        )

        wallet_activity_count = int(
            wallet_data.get(
                "activity_count",
                0
            )
            or 0
        )

        wallet_dominance = float(
            wallet_data.get(
                "dominance",
                0
            )
            or 0
        )


        wallet_available = (
            wallet_action
            in (
                "BUY",
                "SELL"
            )
            and
            wallet_activity_count >= 3
            and
            wallet_dominance >= 0.60
        )


        # =========================================
        # INDIVIDUAL SCORES
        # =========================================

        if market_available:

            market_score = (
                self.scorer.score_market(
                    market_analysis
                )
            )

        else:

            market_score = 0.0


        if social_available:

            social_score = (
                self.scorer.score_social(
                    social_analysis
                )
            )

        else:

            social_score = 0.0


        if wallet_available:

            wallet_score = (
                self.scorer.score_wallet(
                    wallet_analysis
                )
            )

        else:

            wallet_score = 0.0


        # =========================================
        # COMBINED SCORE
        # =========================================

        combined_score = (
            self.scorer.combined_score(
                market_score,
                social_score,
                wallet_score,

                market_available=(
                    market_available
                ),

                social_available=(
                    social_available
                ),

                wallet_available=(
                    wallet_available
                )
            )
        )


        # =========================================
        # DATA QUALITY
        # =========================================

        available_sources = sum(
            [
                int(
                    market_available
                ),

                int(
                    social_available
                ),

                int(
                    wallet_available
                )
            ]
        )


        data_quality = round(
            (
                available_sources / 3
            )
            * 100,
            2
        )


        # =========================================
        # NARRATIVE
        # =========================================

        narrative_result = (
            self.narrative_pipeline.analyze(
                market_analysis,
                social_analysis,
                wallet_analysis
            )
        )


        # =========================================
        # PATTERNS
        # =========================================

        detected_patterns = (
            self.pattern_engine.detect_patterns(
                market_score,
                social_score,
                wallet_score,
                combined_score
            )
        )


        matched_patterns = (
            self.pattern_matcher.match(
                detected_patterns[
                    "patterns"
                ],

                market_score,
                social_score,
                wallet_score,
                combined_score
            )
        )


        learning = (
            self.pattern_learning.evaluate(
                detected_patterns[
                    "pattern_count"
                ],

                detected_patterns[
                    "pattern_count"
                ],

                combined_score
            )
        )


        # =========================================
        # FINAL RADAR
        # =========================================

        final = (
            self.radar_engine.analyze(
                market_score,
                social_score,
                wallet_score,
                combined_score,

                narrative_result[
                    "narrative"
                ],

                detected_patterns[
                    "patterns"
                ]
            )
        )


        # =========================================
        # CONFIDENCE GATING
        # =========================================

        final_signal = (
            final.get(
                "signal",
                {}
            )
        )


        final_decision = (
            final.get(
                "decision",
                {}
            )
        )


        raw_confidence = int(
            final_signal.get(
                "confidence",
                0
            )
            or 0
        )


        confidence_cap = int(
            round(
                data_quality
            )
        )


        adjusted_confidence = min(
            raw_confidence,
            confidence_cap
        )


        final_signal[
            "confidence"
        ] = adjusted_confidence


        final_decision[
            "confidence"
        ] = adjusted_confidence


        # =========================================
        # SAFETY:
        #
        # Never produce high conviction from only
        # one live source.
        # =========================================

        if available_sources < 2:

            if (
                final_signal.get(
                    "signal"
                )
                == "HIGH_CONVICTION_ENTRY"
            ):

                final_signal[
                    "signal"
                ] = "LOW_CONFIDENCE"

                final_decision[
                    "signal"
                ] = "LOW_CONFIDENCE"

                final_decision[
                    "decision"
                ] = "IGNORE"

                final_decision[
                    "risk"
                ] = "HIGH"


        # =========================================
        # RETURN
        # =========================================

        return {

            "analysis": {

                "market_score": (
                    market_score
                ),

                "social_score": (
                    social_score
                ),

                "wallet_score": (
                    wallet_score
                ),

                "combined_score": (
                    combined_score
                ),

                "data_quality": (
                    data_quality
                ),

                "available_sources": (
                    available_sources
                ),

                "sources": {

                    "market": (
                        market_available
                    ),

                    "social": (
                        social_available
                    ),

                    "wallet": (
                        wallet_available
                    )
                }
            },


            "narrative": (
                narrative_result
            ),


            "patterns": {

                "detected": (
                    detected_patterns
                ),

                "matched": (
                    matched_patterns
                ),

                "learning": (
                    learning
                )
            },


            "radar": (
                final
            )
        }