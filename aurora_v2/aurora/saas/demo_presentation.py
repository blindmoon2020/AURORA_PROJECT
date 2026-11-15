"""Aurora Platform Client Onboarding & Robo-Advisory Demo Presentation.
Simulates client risk assessment, subscription check, and automated portfolio generation.
"""
from __future__ import annotations

from aurora.saas.robo_advisor_platform import AuroraRoboAdvisorPlatform, ClientProfile


def run_demo_presentation() -> None:
    print("==================================================")
    print("   AURORA QUANT PLATFORM - SAAS DEMO PRESENTATION  ")
    print("==================================================")

    platform = AuroraRoboAdvisorPlatform()

    # 1. Register a new client with active subscription and liquidity
    client = ClientProfile(
        client_id="CLI-998822",
        full_name="Dr. Alireza Tehrani",
        liquidity_capital=50000.0,  # $50,000 USD initial liquidity
        risk_tolerance_score=0,     # Will be evaluated by psychometric test
        subscription_active=True,
        currency="USD",
    )
    platform.register_client(client)
    print(f"\n[1. Client Onboarding] Registered: {client.full_name} | Capital: ${client.liquidity_capital:,.2f}")

    # 2. Simulate Psychometric Risk Assessment Test Answers
    # Answers range from 1 to 10 based on the 4 sensitive core questions
    test_answers = [8, 7, 8, 9]  # High growth / aggressive risk profile
    evaluated_score = platform.evaluate_risk_profile(test_answers)
    client.risk_tolerance_score = evaluated_score
    print(f"[2. Risk Profiling] Psychometric Test Evaluated Risk Score: {evaluated_score}/10 (Aggressive/Growth)")

    # 3. Generate Tailored Multi-Asset Portfolio & Rebalancing Plan
    try:
        portfolio = platform.generate_tailored_portfolio(client.client_id)
        print(f"\n[3. Robo-Advisor Portfolio Generation] Tailored Asset Allocation for {client.full_name}:")
        print("-" * 65)
        print(f"{'Asset Symbol':<15} | {'Target Weight':<15} | {'Action':<10} | {'Amount ($)':<12}")
        print("-" * 65)
        for item in portfolio:
            print(f"{item.symbol:<15} | {item.target_weight_pct:>12.1f}% | {item.recommended_action:<10} | ${item.adjustment_amount:>10,.2f}")
        print("-" * 65)
        print("[SUCCESS] Data securely encrypted. Portfolio rebalancing recommendations generated successfully.")
    except Exception as e:
        print(f"[ERROR] Portfolio generation failed: {e}")

    print("\n==================================================")
    print("   END OF DEMO - SYSTEM READY FOR LIVE DEPLOYMENT ")
    print("==================================================")


if __name__ == "__main__":
    run_demo_presentation()
