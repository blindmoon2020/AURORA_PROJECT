"""Aurora SaaS & Robo-Advisor Web Platform Core.
Handles client onboarding, psychometric risk profiling, dynamic asset allocation,
subscription validation, and automated portfolio rebalancing recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ClientProfile:
    client_id: str
    full_name: str
    liquidity_capital: float
    risk_tolerance_score: int  # Scale 1 (Conservative) to 10 (Aggressive)
    subscription_active: bool
    currency: str = "USD"


@dataclass(frozen=True)
class PortfolioAllocationItem:
    symbol: str
    asset_name: str
    target_weight_pct: float
    current_value: float
    recommended_action: str  # "BUY", "SELL", "HOLD"
    adjustment_amount: float  # Currency amount to add or remove


class AuroraRoboAdvisorPlatform:
    """Core platform logic for automated client onboarding, risk profiling, and portfolio management."""

    def __init__(self) -> None:
        self.clients: Dict[str, ClientProfile] = {}

    def register_client(self, profile: ClientProfile) -> None:
        """Onboards a new client into the Aurora platform."""
        self.clients[profile.client_id] = profile

    def evaluate_risk_profile(self, answers: List[int]) -> int:
        """Evaluates psychometric risk tolerance based on a standard questionnaire (1-10 scale)."""
        if not answers:
            return 5
        avg_score = sum(answers) / len(answers)
        return max(1, min(10, int(round(avg_score))))

    def generate_tailored_portfolio(self, client_id: str) -> List[PortfolioAllocationItem]:
        """Designs a customized multi-asset portfolio based on client's liquidity and risk score."""
        client = self.clients.get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found.")

        if not client.subscription_active:
            raise PermissionError("Access denied: Client subscription has expired or is inactive.")

        capital = client.liquidity_capital
        risk = client.risk_tolerance_score

        # Define strategic asset allocation templates based on risk score
        if risk <= 3:
            # Conservative (Bonds, Gold, Fixed Income, Cash)
            weights = {"AKHAZA_IR": 0.40, "GLD": 0.30, "BND": 0.20, "US30": 0.10}
        elif risk <= 7:
            # Balanced (Equities, Gold, Bonds, Tech)
            weights = {"SPY": 0.35, "GLD": 0.25, "NAS100": 0.20, "US30": 0.20}
        else:
            # Aggressive / Growth (Tech Equities, Crypto, Emerging Markets)
            weights = {"NVDA": 0.30, "NAS100": 0.30, "BTCUSDT": 0.20, "INDA": 0.20}

        allocation: List[PortfolioAllocationItem] = []
        for symbol, target_pct in weights.items():
            target_alloc_value = capital * target_pct
            # Simulated current holding check (assume 0 for new onboarding, or existing balance)
            current_holding_val = 0.0 
            diff_val = target_alloc_value - current_holding_val

            if diff_val > 0:
                action = "BUY"
                amount = round(diff_val, 2)
            else:
                action = "SELL"
                amount = round(abs(diff_val), 2)

            allocation.append(
                PortfolioAllocationItem(
                    symbol=symbol,
                    asset_name=symbol,
                    target_weight_pct=target_pct * 100,
                    current_value=current_holding_val,
                    recommended_action=action,
                    adjustment_amount=amount,
                )
            )
        return allocation
