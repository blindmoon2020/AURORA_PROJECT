MIN_SCORE = 85


def evaluate_score(
        market_score,
        strategy_score,
        volume_score,
        risk_score
):

    total = (
        market_score
        +
        strategy_score
        +
        volume_score
        +
        risk_score
    )


    if total >= MIN_SCORE:

        return {
            "status":
            "TRADE_CANDIDATE",

            "score":
            total
        }


    elif total >= 70:

        return {
            "status":
            "WAIT",

            "score":
            total
        }


    else:

        return {
            "status":
            "NO_TRADE",

            "score":
            total
        }