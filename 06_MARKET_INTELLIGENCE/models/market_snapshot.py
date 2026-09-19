from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class EMAState:

    ema20: float

    ema40: float

    ema200: float



@dataclass(frozen=True)
class IchimokuState:

    tenkan: float

    kijun: float

    senkou_a: float

    senkou_b: float



@dataclass(frozen=True)
class FibonacciState:

    level_236: float

    level_382: float

    level_500: float

    level_618: float

    level_786: float



@dataclass(frozen=True)
class ATRState:

    value: float



@dataclass(frozen=True)
class VolumeProfileState:

    poc: float

    vah: float

    val: float

    hvn: List[float]

    lvn: List[float]



@dataclass(frozen=True)
class StructureState:

    trend: str

    bos: bool

    choch: bool

    strength: int



@dataclass(frozen=True)
class PriceActionState:

    bullish_engulfing: bool

    bearish_engulfing: bool

    pin_bar: bool

    inside_bar: bool



@dataclass(frozen=True)
class MarketSnapshot:


    symbol: str


    timeframe: str


    price: float



    ema: Optional[EMAState]


    ichimoku: Optional[IchimokuState]


    fibonacci: Optional[FibonacciState]


    atr: Optional[ATRState]


    volume_profile: Optional[VolumeProfileState]


    structure: Optional[StructureState]


    price_action: Optional[PriceActionState]


    volume: float



    def is_bullish_environment(
        self
    ) -> bool:


        if self.structure is None:
            return False


        if self.ema is None:
            return False


        return (

            self.structure.trend
            ==
            "BULLISH"

            and

            self.ema.ema20
            >
            self.ema.ema200

        )



    def is_bearish_environment(
        self
    ) -> bool:


        if self.structure is None:
            return False


        if self.ema is None:
            return False


        return (

            self.structure.trend
            ==
            "BEARISH"

            and

            self.ema.ema20
            <
            self.ema.ema200

        )



    def summary(self):


        return {


            "symbol":
                self.symbol,


            "timeframe":
                self.timeframe,


            "price":
                self.price,


            "trend":
                (
                    self.structure.trend
                    if self.structure
                    else
                    "UNKNOWN"
                ),


            "bos":
                (
                    self.structure.bos
                    if self.structure
                    else
                    False
                ),


            "volume_profile_poc":
                (
                    self.volume_profile.poc
                    if self.volume_profile
                    else
                    None
                )

        }