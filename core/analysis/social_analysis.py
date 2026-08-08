from typing import Dict, Any


class SocialAnalyzer:

    def analyze(
        self,
        observation: Dict[str, Any]
    ) -> Dict[str, Any]:

        mentions = int(
            observation.get(
                "mentions",
                0
            )
            or 0
        )

        engagement = int(
            observation.get(
                "engagement",
                0
            )
            or 0
        )

        community_size = int(
            observation.get(
                "community_size",
                0
            )
            or 0
        )

        growth_rate = float(
            observation.get(
                "growth_rate",
                0
            )
            or 0
        )

        sentiment = float(
            observation.get(
                "sentiment",
                0
            )
            or 0
        )

        social_dominance = float(
            observation.get(
                "social_dominance",
                0
            )
            or 0
        )

        galaxy_score = float(
            observation.get(
                "galaxy_score",
                0
            )
            or 0
        )

        alt_rank = int(
            observation.get(
                "alt_rank",
                0
            )
            or 0
        )

        available = bool(
            observation.get(
                "available",
                False
            )
        )

        engagement_ratio = 0.0

        mention_ratio = 0.0


        if mentions > 0:

            engagement_ratio = (
                engagement / mentions
            )


        if community_size > 0:

            mention_ratio = (
                mentions
                / community_size
            )


        return {

            "coin_address": observation.get(
                "coin_address"
            ),

            "mentions": mentions,

            "engagement": engagement,

            "community_size": community_size,

            "growth_rate": growth_rate,

            "sentiment": sentiment,

            "social_dominance": social_dominance,

            "galaxy_score": galaxy_score,

            "alt_rank": alt_rank,

            "engagement_ratio": engagement_ratio,

            "mention_ratio": mention_ratio,

            "available": available,

            "source": observation.get(
                "source",
                "none"
            )
        }