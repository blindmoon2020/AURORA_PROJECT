from strategies.smc_strategy import SMCStrategy



def test_smc_valid_setup():


    engine = SMCStrategy()


    result = engine.analyze(

        liquidity_sweep=True,

        bos=True,

        order_block=True,

        fvg=True,

        volume_confirmation=True

    )


    assert result.valid is True

    assert result.score == 100



def test_smc_invalid_setup():


    engine = SMCStrategy()


    result = engine.analyze(

        liquidity_sweep=False,

        bos=False,

        order_block=False,

        fvg=False,

        volume_confirmation=False

    )


    assert result.valid is False