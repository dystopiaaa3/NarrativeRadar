class IntelligenceScorer:

    def score_market(self, analysis):

        score = 0.0

        liquidity_ratio = float(
            analysis.get("liquidity_ratio", 0) or 0
        )

        volume_ratio = float(
            analysis.get("volume_ratio", 0) or 0
        )

        holders = int(
            analysis.get("holders", 0) or 0
        )

        if liquidity_ratio >= 0.10:
            score += 35
        elif liquidity_ratio >= 0.05:
            score += 30
        elif liquidity_ratio >= 0.02:
            score += 25
        elif liquidity_ratio >= 0.01:
            score += 20
        elif liquidity_ratio >= 0.005:
            score += 12
        elif liquidity_ratio > 0:
            score += 5

        if volume_ratio >= 1.00:
            score += 35
        elif volume_ratio >= 0.50:
            score += 32
        elif volume_ratio >= 0.20:
            score += 28
        elif volume_ratio >= 0.10:
            score += 23
        elif volume_ratio >= 0.05:
            score += 18
        elif volume_ratio >= 0.01:
            score += 10
        elif volume_ratio > 0:
            score += 5

        if holders >= 100000:
            score += 30
        elif holders >= 25000:
            score += 25
        elif holders >= 5000:
            score += 20
        elif holders >= 1000:
            score += 12

        return min(
            round(score, 2),
            100.0
        )


    def score_social(self, analysis):

        score = 0.0

        growth_rate = float(
            analysis.get("growth_rate", 0) or 0
        )

        engagement = int(
            analysis.get("engagement", 0) or 0
        )

        social_dominance = float(
            analysis.get("social_dominance", 0) or 0
        )

        galaxy_score = float(
            analysis.get("galaxy_score", 0) or 0
        )

        # SOCIAL GROWTH - MAX 30
        if growth_rate >= 100:
            score += 30
        elif growth_rate >= 50:
            score += 27
        elif growth_rate >= 25:
            score += 23
        elif growth_rate >= 15:
            score += 19
        elif growth_rate >= 10:
            score += 15
        elif growth_rate >= 5:
            score += 10
        elif growth_rate > 0:
            score += 5

        # GALAXY SCORE - MAX 35
        if galaxy_score >= 85:
            score += 35
        elif galaxy_score >= 75:
            score += 30
        elif galaxy_score >= 65:
            score += 25
        elif galaxy_score >= 55:
            score += 20
        elif galaxy_score >= 45:
            score += 12
        elif galaxy_score > 0:
            score += 5

        # SOCIAL DOMINANCE - MAX 20
        if social_dominance >= 2.0:
            score += 20
        elif social_dominance >= 1.0:
            score += 18
        elif social_dominance >= 0.50:
            score += 15
        elif social_dominance >= 0.20:
            score += 10
        elif social_dominance >= 0.10:
            score += 7
        elif social_dominance > 0:
            score += 3

        # ENGAGEMENT - MAX 15
        if engagement >= 5000000:
            score += 15
        elif engagement >= 1000000:
            score += 14
        elif engagement >= 500000:
            score += 12
        elif engagement >= 100000:
            score += 10
        elif engagement >= 25000:
            score += 7
        elif engagement >= 5000:
            score += 4
        elif engagement > 0:
            score += 2

        return min(
            round(score, 2),
            100.0
        )


    def score_wallet(self, analysis):

        score = 0.0

        is_buy = bool(
            analysis.get("is_buy", False)
        )

        is_sell = bool(
            analysis.get("is_sell", False)
        )

        amount_sol = float(
            analysis.get("amount_sol", 0) or 0
        )

        if is_buy:
            score += 60
        elif is_sell:
            score += 10

        if amount_sol >= 25:
            score += 40
        elif amount_sol >= 10:
            score += 35
        elif amount_sol >= 5:
            score += 25
        elif amount_sol >= 1:
            score += 18
        elif amount_sol >= 0.10:
            score += 10
        elif amount_sol >= 0.01:
            score += 5
        elif amount_sol > 0:
            score += 2

        return min(
            round(score, 2),
            100.0
        )


    def combined_score(
        self,
        market_score,
        social_score,
        wallet_score,
        market_available=True,
        social_available=True,
        wallet_available=True
    ):

        weighted_score = 0.0
        total_weight = 0.0

        if market_available:
            weighted_score += market_score * 0.40
            total_weight += 0.40

        if social_available:
            weighted_score += social_score * 0.35
            total_weight += 0.35

        if wallet_available:
            weighted_score += wallet_score * 0.25
            total_weight += 0.25

        if total_weight <= 0:
            return 0.0

        return round(
            weighted_score / total_weight,
            2
        )

    def opportunity_score(self, market_analysis, market_score, social_score=0.0, wallet_score=0.0, social_available=False, wallet_available=False):
        """V3: score near-term upside separately from downside risk."""
        liq_ratio = float(market_analysis.get("liquidity_ratio", 0) or 0)
        vol_ratio = float(market_analysis.get("volume_ratio", 0) or 0)

        # Market remains the anchor. Reward useful activity, but avoid assuming
        # that ever-higher churn is automatically better.
        score = float(market_score) * 0.65
        if 0.02 <= liq_ratio <= 0.30:
            score += 10
        elif liq_ratio >= 0.01:
            score += 5

        if 0.05 <= vol_ratio <= 1.50:
            score += 12
        elif vol_ratio > 0:
            score += 4

        if social_available:
            score += float(social_score) * 0.12
        if wallet_available:
            score += float(wallet_score) * 0.13

        return min(round(score, 2), 100.0)

    def risk_score(self, market_analysis, data_quality=100.0, wallet_score=0.0, wallet_available=False):
        """V3: 0 = lower observed risk, 100 = higher observed risk."""
        market_cap = float(market_analysis.get("market_cap", 0) or 0)
        liquidity = float(market_analysis.get("liquidity", 0) or 0)
        liq_ratio = float(market_analysis.get("liquidity_ratio", 0) or 0)
        vol_ratio = float(market_analysis.get("volume_ratio", 0) or 0)
        risk = 0.0

        if liquidity < 5000:
            risk += 35
        elif liquidity < 15000:
            risk += 25
        elif liquidity < 30000:
            risk += 15

        if market_cap <= 0:
            risk += 25
        elif liq_ratio < 0.005:
            risk += 30
        elif liq_ratio < 0.01:
            risk += 18

        if vol_ratio > 5.0:
            risk += 25
        elif vol_ratio > 2.0:
            risk += 15

        if float(data_quality) < 34:
            risk += 20
        elif float(data_quality) < 67:
            risk += 10

        # Strong validated buy-side wallet evidence can reduce, never erase, risk.
        if wallet_available and float(wallet_score) >= 80:
            risk -= 10

        return max(0.0, min(round(risk, 2), 100.0))

    def v3_action(self, opportunity_score, risk_score):
        if opportunity_score >= 75 and risk_score <= 35:
            return "ENTER_WATCH"
        if opportunity_score >= 70 and risk_score <= 65:
            return "SPECULATIVE"
        if opportunity_score >= 50 and risk_score <= 75:
            return "MONITOR"
        return "IGNORE"