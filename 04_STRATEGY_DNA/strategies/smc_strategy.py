from models.strategy_result import StrategyResult



class SMCStrategy:


    name = "SMART_MONEY_CONCEPT"



    def analyze(
        self,
        liquidity_sweep: bool,
        bos: bool,
        order_block: bool,
        fvg: bool,
        volume_confirmation: bool,
    ):


        score = 0

        reasons = []


        # Liquidity Sweep
        if liquidity_sweep:
            score += 25
            reasons.append(
                "liquidity_sweep_confirmed"
            )


        # Break Of Structure
        if bos:
            score += 25
            reasons.append(
                "bos_confirmed"
            )


        # Order Block
        if order_block:
            score += 25
            reasons.append(
                "order_block_valid"
            )


        # Fair Value Gap
        if fvg:
            score += 15
            reasons.append(
                "fvg_detected"
            )


        # Volume
        if volume_confirmation:
            score += 10
            reasons.append(
                "volume_confirmed"
            )


        valid = score >= 70


        bias = (
            "BULLISH"
            if valid
            else
            "NEUTRAL"
        )


        return StrategyResult(

            name=self.name,

            score=score,

            bias=bias,

            valid=valid,

            reasons=tuple(reasons)

        )