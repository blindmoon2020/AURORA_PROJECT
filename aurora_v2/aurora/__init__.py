"""Aurora v2: a small trading core that runs and can be measured.

Four ideas carry over from AURORA_PROJECT:
  1. strategy as data           -> aurora/strategies/dna.py
  2. risk engine separate from signal engine -> aurora/risk
  3. event bus between layers   -> aurora/core/events.py
  4. a decision record per trade -> aurora/journal
"""

__version__ = "0.1.0"
