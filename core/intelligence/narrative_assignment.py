import re
from typing import Dict, List, Tuple

from database.database import SessionLocal
from database.models.narrative import Narrative
from database.models.coin_narrative import CoinNarrative


class NarrativeAssignmentEngine:

    def __init__(self):

        self.name = "Narrative Assignment Engine"

        self.rules = {

            "AI": {
                "category": "technology",
                "keywords": [
                    "ai",
                    "agent",
                    "gpt",
                    "neural",
                    "model",
                    "llm",
                    "robot",
                    "bot",
                    "machine",
                    "intelligence",
                ],
            },

            "Cats": {
                "category": "animals",
                "keywords": [
                    "cat",
                    "cats",
                    "kitty",
                    "kitten",
                    "meow",
                    "feline",
                    "cate",
                ],
            },

            "Dogs": {
                "category": "animals",
                "keywords": [
                    "dog",
                    "dogs",
                    "doge",
                    "doggo",
                    "puppy",
                    "pup",
                    "shib",
                    "inu",
                ],
            },

            "Frogs": {
                "category": "animals",
                "keywords": [
                    "frog",
                    "frogs",
                    "pepe",
                    "toad",
                ],
            },

            "Food": {
                "category": "culture",
                "keywords": [
                    "ramen",
                    "pizza",
                    "burger",
                    "taco",
                    "food",
                    "noodle",
                    "bread",
                    "cheese",
                    "coffee",
                ],
            },

            "Finance": {
                "category": "finance",
                "keywords": [
                    "cash",
                    "money",
                    "bank",
                    "finance",
                    "rich",
                    "wealth",
                    "dollar",
                    "usd",
                ],
            },

            "Gaming": {
                "category": "gaming",
                "keywords": [
                    "game",
                    "gaming",
                    "gamer",
                    "play",
                    "quest",
                    "rpg",
                    "pixel",
                ],
            },

            "Politics": {
                "category": "politics",
                "keywords": [
                    "trump",
                    "biden",
                    "maga",
                    "president",
                    "politics",
                    "vote",
                    "election",
                    "senate",
                    "congress",
                ],
            },

            "Brainrot": {
                "category": "culture",
                "keywords": [
                    "brainrot",
                    "sigma",
                    "skibidi",
                    "rizz",
                    "gyatt",
                    "npc",
                    "based",
                ],
            },

            "Burn": {
                "category": "token_mechanics",
                "keywords": [
                    "burn",
                    "burncoin",
                    "deflation",
                    "deflationary",
                ],
            },

            "Meme": {
                "category": "meme",
                "keywords": [
                    "meme",
                    "memecoin",
                    "viral",
                    "funny",
                    "lol",
                ],
            },
        }


    def _texts(
        self,
        candidate: Dict
    ):

        name = str(
            candidate.get(
                "name",
                ""
            )
            or ""
        ).lower()

        symbol = str(
            candidate.get(
                "symbol",
                ""
            )
            or ""
        ).lower()

        reasons = (
            candidate.get(
                "source_reasons",
                []
            )
            or []
        )

        joined = " ".join(
            [
                name,
                symbol,
                *[
                    str(reason).lower()
                    for reason in reasons
                ],
            ]
        )

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            joined
        ).strip()

        compact_name = re.sub(
            r"[^a-z0-9]+",
            "",
            name
        )

        compact_symbol = re.sub(
            r"[^a-z0-9]+",
            "",
            symbol
        )

        return {
            "normalized": normalized,
            "compact_name": compact_name,
            "compact_symbol": compact_symbol,
        }


    def _keyword_match(
        self,
        texts,
        keyword: str
    ) -> bool:

        keyword = (
            keyword
            .lower()
            .strip()
        )

        if not keyword:

            return False

        normalized = (
            texts[
                "normalized"
            ]
        )

        # Exact word/phrase detection first.
        pattern = (
            r"\b"
            + re.escape(
                keyword
            )
            + r"\b"
        )

        if re.search(
            pattern,
            normalized
        ):

            return True


        # Compact token detection.
        #
        # Useful for symbols like:
        #
        # CASHCATE -> cash + cate
        # CATWIF   -> cat
        #
        # Only keywords >= 4 chars are allowed
        # here to reduce accidental matches.
        if len(keyword) >= 4:

            if (
                keyword
                in texts[
                    "compact_symbol"
                ]
            ):

                return True

            if (
                keyword
                in texts[
                    "compact_name"
                ]
            ):

                return True


        return False


    def detect(
        self,
        candidate: Dict
    ) -> List[
        Tuple[
            str,
            str,
            float
        ]
    ]:

        texts = self._texts(
            candidate
        )

        matches = []


        for (
            narrative_name,
            rule
        ) in self.rules.items():

            hit_count = 0

            for keyword in rule[
                "keywords"
            ]:

                if self._keyword_match(
                    texts,
                    keyword
                ):

                    hit_count += 1


            if hit_count <= 0:

                continue


            if hit_count >= 3:

                confidence = 95.0

            elif hit_count == 2:

                confidence = 85.0

            else:

                confidence = 70.0


            matches.append(
                (
                    narrative_name,
                    rule[
                        "category"
                    ],
                    confidence
                )
            )


        if not matches:

            matches.append(
                (
                    "Meme",
                    "meme",
                    45.0
                )
            )


        matches.sort(
            key=lambda item: item[2],
            reverse=True
        )


        return matches[:3]


    def _get_or_create_narrative(
        self,
        db,
        name: str,
        category: str
    ):

        narrative = (
            db.query(
                Narrative
            )
            .filter(
                Narrative.name
                == name
            )
            .first()
        )


        if narrative:

            if not narrative.active:

                narrative.active = True

            return narrative


        narrative = Narrative(
            name=name,
            category=category,
            description=(
                f"Automatically detected "
                f"{name} narrative."
            ),
            active=True
        )


        db.add(
            narrative
        )

        db.flush()

        return narrative


    def assign(
        self,
        coin_id: int,
        candidate: Dict
    ):

        matches = self.detect(
            candidate
        )

        db = SessionLocal()


        try:

            assignments = []


            for (
                narrative_name,
                category,
                confidence
            ) in matches:

                narrative = (
                    self._get_or_create_narrative(
                        db,
                        narrative_name,
                        category
                    )
                )


                link = (
                    db.query(
                        CoinNarrative
                    )
                    .filter(
                        CoinNarrative.coin_id
                        == coin_id
                    )
                    .filter(
                        CoinNarrative.narrative_id
                        == narrative.id
                    )
                    .first()
                )


                if link:

                    if (
                        confidence
                        >
                        float(
                            link.confidence
                            or 0
                        )
                    ):

                        link.confidence = (
                            confidence
                        )


                else:

                    link = CoinNarrative(
                        coin_id=coin_id,
                        narrative_id=(
                            narrative.id
                        ),
                        confidence=confidence
                    )

                    db.add(
                        link
                    )


                assignments.append(
                    {
                        "narrative_id": (
                            narrative.id
                        ),
                        "name": (
                            narrative.name
                        ),
                        "category": (
                            narrative.category
                        ),
                        "confidence": (
                            confidence
                        )
                    }
                )


            db.commit()


            return {
                "success": True,
                "count": len(
                    assignments
                ),
                "assignments": (
                    assignments
                ),
                "error": None
            }


        except Exception as e:

            db.rollback()

            return {
                "success": False,
                "count": 0,
                "assignments": [],
                "error": str(e)
            }


        finally:

            db.close()