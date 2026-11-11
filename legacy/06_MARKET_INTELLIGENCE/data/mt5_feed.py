from datetime import datetime

import MetaTrader5 as mt5

from models.candle import Candle



class MT5Feed:


    def __init__(self):

        if not mt5.initialize():

            raise RuntimeError(
                f"MT5 init failed: {mt5.last_error()}"
            )


    def get_candles(
        self,
        symbol,
        timeframe,
        count=200
    ):


        rates = mt5.copy_rates_from_pos(
            symbol,
            timeframe,
            0,
            count
        )


        if rates is None:

            raise RuntimeError(
                f"No data for {symbol}"
            )


        candles=[]


        for r in rates:

            candles.append(

                Candle(

                    symbol=symbol,

                    timeframe=str(timeframe),

                    timestamp=datetime.fromtimestamp(
                        r["time"]
                    ),

                    open=float(r["open"]),

                    high=float(r["high"]),

                    low=float(r["low"]),

                    close=float(r["close"]),

                    volume=float(r["tick_volume"])

                )
            )


        return candles



    def shutdown(self):

        mt5.shutdown()