from ..models.entities import Portfolio

from ..models.value_objects import (
    Money,
    Exposure,
    RiskScore,
    DiversificationRatio,
    PortfolioAnalyticsSnapshot,
)



class PortfolioAnalyticsService:
    """
    Domain service responsible for
    portfolio analytics.

    Responsibilities:

    - Calculate portfolio value
    - Calculate exposure
    - Calculate risk score
    - Calculate diversification
    - Generate analytics snapshot

    Keeps analytical logic outside
    aggregate entities.
    """



    def total_value(
        self,
        portfolio: Portfolio,
    ) -> Money:
        """
        Return total portfolio market value.
        """

        return (
            portfolio
            .holdings
            .total_market_value()
        )




    def exposure(
        self,
        portfolio: Portfolio,
    ) -> Exposure:
        """
        Return portfolio exposure.
        """

        return (
            portfolio
            .holdings
            .total_exposure()
        )




    def risk_score(
        self,
        portfolio: Portfolio,
    ) -> RiskScore:
        """
        Return portfolio risk score.
        """

        return (
            portfolio
            .holdings
            .risk_score()
        )




    def diversification(
        self,
        portfolio: Portfolio,
    ) -> DiversificationRatio:
        """
        Return diversification ratio.
        """

        return (
            portfolio
            .holdings
            .diversification_ratio()
        )




    def snapshot(
        self,
        portfolio: Portfolio,
    ) -> PortfolioAnalyticsSnapshot:
        """
        Generate immutable portfolio analytics snapshot.

        Used for:

        - Dashboard
        - Reporting
        - AI Risk Engine
        - Monitoring
        """


        return PortfolioAnalyticsSnapshot(

            total_value=self.total_value(
                portfolio
            ),

            exposure=self.exposure(
                portfolio
            ),

            risk_score=self.risk_score(
                portfolio
            ),

            diversification=self.diversification(
                portfolio
            ),

        )