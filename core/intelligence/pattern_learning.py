class PatternLearning:

    def __init__(self):
        self.name = "Pattern Learning"


    def evaluate(
        self,
        occurrences,
        successful,
        average_return
    ):

        success_rate = 0


        if occurrences > 0:
            success_rate = (
                successful / occurrences
            ) * 100


        strength = "WEAK"


        if success_rate >= 60:
            strength = "PROMISING"


        if success_rate >= 75:
            strength = "STRONG"


        if success_rate >= 90:
            strength = "ELITE"


        return {
            "occurrences": occurrences,
            "successful": successful,
            "success_rate": round(success_rate, 2),
            "average_return": average_return,
            "strength": strength
        }