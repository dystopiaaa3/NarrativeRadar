from database.database import get_session
from database.models.radar_result import RadarResult


class RadarResultStorage:

    def save_result(self, coin_id, result):
        db = get_session()

        try:
            radar_result = RadarResult(
                coin_id=coin_id,
                market_score=result["market_score"],
                social_score=result["social_score"],
                wallet_score=result["wallet_score"],
                combined_score=result["combined_score"],
                narrative=result["narrative"],
                signal=result["signal"],
                confidence=result["confidence"],
                decision=result["decision"],
                risk=result["risk"],
            )

            db.add(radar_result)
            db.commit()
            db.refresh(radar_result)

            return radar_result

        finally:
            db.close()