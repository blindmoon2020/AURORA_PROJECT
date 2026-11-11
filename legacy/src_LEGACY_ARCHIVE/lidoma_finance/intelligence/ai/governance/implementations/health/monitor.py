from ...health import ProviderHealth


class ProviderHealthMonitor:
    """
    Runtime health monitor for AI providers.

    Responsibilities:

    - Create provider health status
    - Validate runtime latency
    - Provide health state objects
    """


    def create_status(
        self,
        provider_id: str,
        available: bool,
        latency_ms: float,
    ) -> ProviderHealth:

        if not provider_id:

            raise ValueError(
                "provider_id required"
            )


        if latency_ms < 0:

            raise ValueError(
                "latency cannot be negative"
            )


        return ProviderHealth(

            provider_id=provider_id,

            available=available,

            latency_ms=latency_ms,

        )