from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Candle:

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float



@dataclass(frozen=True)
class StructureResult:

    trend: str
    bos: bool
    choch: bool
    swing_high: float
    swing_low: float
    strength: int



class MarketStructureEngine:


    def __init__(
        self,
        swing_length:int=3
    ):

        self.swing_length = swing_length



    def detect_swings(
        self,
        candles:List[Candle]
    ):

        highs=[]
        lows=[]


        l=self.swing_length


        for i in range(
            l,
            len(candles)-l
        ):

            c=candles[i]


            left=candles[
                i-l:i
            ]

            right=candles[
                i+1:i+l+1
            ]


            if (
                c.high >
                max(x.high for x in left)
                and
                c.high >
                max(x.high for x in right)
            ):

                highs.append(
                    c.high
                )



            if (
                c.low <
                min(x.low for x in left)
                and
                c.low <
                min(x.low for x in right)
            ):

                lows.append(
                    c.low
                )


        return highs,lows




    def analyze(
        self,
        candles:List[Candle]
    ):


        highs,lows = self.detect_swings(
            candles
        )


        if len(highs)<2 or len(lows)<2:

            return StructureResult(
                "UNKNOWN",
                False,
                False,
                0,
                0,
                0
            )



        last_high=highs[-1]
        prev_high=highs[-2]


        last_low=lows[-1]
        prev_low=lows[-2]


        trend="RANGE"


        if (
            last_high>prev_high
            and
            last_low>prev_low
        ):

            trend="BULLISH"



        elif (
            last_high<prev_high
            and
            last_low<prev_low
        ):

            trend="BEARISH"



        price=candles[-1].close


        bos=False
        choch=False


        if trend=="BULLISH":

            if price>last_high:
                bos=True


            if price<last_low:
                choch=True



        elif trend=="BEARISH":

            if price<last_low:
                bos=True


            if price>last_high:
                choch=True



        strength=50


        if bos:
            strength+=30


        if choch:
            strength-=20



        return StructureResult(

            trend,
            bos,
            choch,
            last_high,
            last_low,
            strength

        )