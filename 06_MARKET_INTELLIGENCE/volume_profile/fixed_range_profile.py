from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class VolumeNode:

    price: float
    volume: float



@dataclass(frozen=True)
class VolumeProfileResult:

    poc: float

    vah: float

    val: float

    hvn: list

    lvn: list



class FixedRangeVolumeProfile:


    def __init__(
        self,
        bins:int = 100,
        value_area:float = 0.70
    ):

        self.bins = bins

        self.value_area = value_area



    def calculate(
        self,
        candles:List
    ):


        highest=max(
            c.high
            for c in candles
        )


        lowest=min(
            c.low
            for c in candles
        )


        step = (
            highest-lowest
        ) / self.bins


        profile={}



        for candle in candles:


            index=int(
                (
                    candle.close-lowest
                )
                /
                step
            )


            price=(
                lowest
                +
                index*step
            )


            profile[price]=(
                profile.get(price,0)
                +
                candle.volume
            )



        nodes=[]


        for price,volume in profile.items():

            nodes.append(
                VolumeNode(
                    price,
                    volume
                )
            )



        nodes.sort(
            key=lambda x:x.volume,
            reverse=True
        )



        poc=nodes[0].price



        total_volume=sum(
            n.volume
            for n in nodes
        )



        target=(
            total_volume
            *
            self.value_area
        )


        current=0

        value_prices=[]



        for node in nodes:


            current += node.volume


            value_prices.append(
                node.price
            )


            if current >= target:
                break



        vah=max(
            value_prices
        )


        val=min(
            value_prices
        )



        average=(
            total_volume
            /
            len(nodes)
        )



        hvn=[]

        lvn=[]



        for node in nodes:


            if node.volume > average*1.5:

                hvn.append(
                    node.price
                )


            if node.volume < average*0.5:

                lvn.append(
                    node.price
                )



        return VolumeProfileResult(

            poc=poc,

            vah=vah,

            val=val,

            hvn=hvn,

            lvn=lvn

        )