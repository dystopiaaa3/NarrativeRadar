from database.database import SessionLocal
from database.models.pattern import Pattern


class PatternLearningStorage:

    def __init__(self):
        self.name = "Pattern Learning Storage"


    def get_or_create_pattern(
        self,
        name: str
    ):

        db = SessionLocal()

        pattern = (
            db.query(Pattern)
            .filter(
                Pattern.name == name
            )
            .first()
        )


        if pattern:
            db.close()
            return pattern


        pattern = Pattern(
            name=name,
            description="",
            occurrences=0,
            success_rate=0,
            average_return=0,
            active=True
        )


        db.add(pattern)
        db.commit()
        db.refresh(pattern)

        db.close()

        return pattern



    def update_pattern(
        self,
        name,
        success_rate,
        average_return
    ):

        db = SessionLocal()


        pattern = (
            db.query(Pattern)
            .filter(
                Pattern.name == name
            )
            .first()
        )


        if not pattern:
            db.close()
            return None


        pattern.occurrences += 1
        pattern.success_rate = success_rate
        pattern.average_return = average_return


        db.commit()
        db.refresh(pattern)

        db.close()

        return pattern