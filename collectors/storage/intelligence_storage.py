from database.database import SessionLocal
from database.models.analysis import Analysis
from database.models.pattern import Pattern


class IntelligenceStorage:


    def __init__(self):
        self.name = "Intelligence Storage"



    def save_analysis(
        self,
        coin_id,
        analysis,
    ):

        db = SessionLocal()


        narrative = analysis["narrative"]


        record = Analysis(

            coin_id=coin_id,

            market_score=analysis["market_score"],

            social_score=analysis["social_score"],

            wallet_score=analysis["wallet_score"],

            combined_score=analysis["combined_score"],

            narrative=narrative["narrative"],

            signal_count=narrative["signal_count"]

        )


        db.add(record)

        db.commit()

        db.refresh(record)

        db.close()


        return record.id



    def save_patterns(
        self,
        patterns
    ):

        db = SessionLocal()

        saved = []


        for item in patterns:

            pattern = (
                db.query(Pattern)
                .filter(
                    Pattern.name == item["pattern"]
                )
                .first()
            )


            if pattern:

                saved.append(pattern)

                continue



            pattern = Pattern(

                name=item["pattern"],

                description="Detected intelligence pattern",

                occurrences=1,

                success_rate=0,

                average_return=0,

                active=True

            )


            db.add(pattern)

            db.commit()

            db.refresh(pattern)


            saved.append(pattern)



        db.close()


        return saved