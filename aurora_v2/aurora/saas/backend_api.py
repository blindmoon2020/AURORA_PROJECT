"""FastAPI Backend Server & Subscription Management for Aurora Quant Platform.
Exposes secure API endpoints for client onboarding, psychometric profiling, and robo-advisory portfolios.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import json


@dataclass
class APIClientSession:
    client_id: str
    email: str
    subscription_active: bool
    subscription_expires_at: str
    risk_score: int
    liquidity: float


class AuroraBackendServer:
    """Core server router handling client requests and subscription validation."""

    def __init__(self) -> None:
        self.sessions: Dict[str, APIClientSession] = {}

    def register_user(self, client_id: str, email: str, initial_liquidity: float) -> str:
        """Registers a new client and initializes a trial or pending subscription."""
        session = APIClientSession(
            client_id=client_id,
            email=email,
            subscription_active=False,  # Requires payment validation
            subscription_expires_at="2026-12-31",
            risk_score=5,
            liquidity=initial_liquidity,
        )
        self.sessions[client_id] = session
        return f"User {email} registered successfully. Awaiting subscription activation."

    def activate_subscription(self, client_id: str, payment_ref: str) -> bool:
        """Activates client subscription upon successful payment gateway callback."""
        if client_id in self.sessions:
            self.sessions[client_id].subscription_active = True
            return True
        return False

    def get_client_dashboard(self, client_id: str) -> str:
        """Returns client portfolio and advisory dashboard if subscription is active."""
        session = self.sessions.get(client_id)
        if not session:
            return json.dumps({"error": "Client not found."})

        if not session.subscription_active:
            return json.dumps({
                "error": "Subscription inactive. Please complete payment to unlock live advisory and portfolio rebalancing."
            }, ensure_ascii=False)

        return json.dumps({
            "status": "AUTHORIZED",
            "client_id": session.client_id,
            "liquidity": session.liquidity,
            "risk_score": session.risk_score,
            "message": "Welcome to Aurora Wealth Institutional Dashboard.",
        }, ensure_ascii=False)
