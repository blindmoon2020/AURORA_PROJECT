from uuid import UUID

from ..events import (
    PortfolioAnalyticsSnapshotCreatedEvent,
)

from ..models.value_objects import (
    PortfolioAnalyticsSnapshot,
)



class PortfolioEventFactory:
    """
    Factory responsible for creating
    portfolio domain events.

    Keeps event creation rules
    outside services.
    """



    @staticmethod
    def analytics_snapshot_created(
        portfolio_id: UUID,
        snapshot: PortfolioAnalyticsSnapshot,
    ) -> PortfolioAnalyticsSnapshotCreatedEvent:
        """
        Create analytics snapshot event.
        """


        return PortfolioAnalyticsSnapshotCreatedEvent(

            portfolio_id=portfolio_id,

            total_value=(
                snapshot
                .total_value
                .amount
            ),

            currency=(
                snapshot
                .total_value
                .currency
            ),

            exposure=(
                snapshot
                .exposure
                .value
            ),

            risk_score=(
                snapshot
                .risk_score
                .value
            ),

            diversification=(
                snapshot
                .diversification
                .value
            ),

        )