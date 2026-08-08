from database.database import SessionLocal
from database.models.pattern import Pattern


class PatternStorage:

    def __init__(self):
        self.name = "Pattern Storage"


    def get_or_create_pattern(
        self,
        pattern_name: str
    ):

        db = SessionLocal()

        try:

            pattern = (
                db.query(Pattern)
                .filter(
                    Pattern.name == pattern_name
                )
                .first()
            )


            if pattern:
                return pattern


            pattern = Pattern(
                name=pattern_name,
                description="Detected narrative pattern",
                occurrences=0,
                success_rate=0,
                average_return=0,
                active=True
            )


            db.add(pattern)

            db.commit()

            db.refresh(pattern)


            return pattern


        finally:

            db.close()