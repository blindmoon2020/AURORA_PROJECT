# Phase 6.15.4 Data Contract Layer

Status:
Planned

Phase:
6.15 Architecture Hardening


## Objective

Create external data contracts before
market intelligence expansion.


## Structure

src/lidoma_core/data_contracts/

    __init__.py
    market_price.py
    candle.py
    orderbook.py
    funding.py
    corporate_action.py


## Purpose


market_price.py

Market price contract.


candle.py

OHLCV candle contract.


orderbook.py

Order book contract.


funding.py

Funding rate contract.


corporate_action.py

Corporate action contract.


## Impact

No domain entity modification.

No decision engine modification.

No event breaking change.


## Validation

python -m compileall src\lidoma_core\data_contracts

Data contract API import test.