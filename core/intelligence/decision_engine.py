class DecisionEngine:

    def __init__(self):
        pass


    def decide(
        self,
        signal,
        confidence,
        narrative,
        patterns
    ):

        risk = "HIGH"

        if confidence >= 90:
            risk = "LOW"

        elif confidence >= 70:
            risk = "MEDIUM"


        decision = "IGNORE"


        if signal == "HIGH_CONVICTION_ENTRY":
            decision = "ENTER_WATCH"


        elif signal == "WATCHLIST":
            decision = "MONITOR"



        return {
            "decision": decision,
            "signal": signal,
            "confidence": confidence,
            "risk": risk,
            "narrative": narrative,
            "patterns": patterns
        }