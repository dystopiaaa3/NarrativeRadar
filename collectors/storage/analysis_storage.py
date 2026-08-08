from database.database import SessionLocal

from database.models.analysis import Analysis


class AnalysisStorage:

    def __init__(self):
        self.name = "Analysis Storage"


    def save_analysis(
        self,
        coin_id: int,
        result: dict
    ):

        db = SessionLocal()

        analysis = Analysis(
            coin_id=coin_id,

            market_score=result["market_score"],

            social_score=result["social_score"],

            wallet_score=result["wallet_score"],

            combined_score=result["combined_score"],

            narrative=result["narrative"]["narrative"],

            signal_count=result["narrative"]["signal_count"]
        )


        db.add(analysis)

        db.commit()

        db.refresh(analysis)


        analysis_id = analysis.id


        db.close()


        return analysis_id