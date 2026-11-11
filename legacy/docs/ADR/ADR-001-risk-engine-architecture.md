# ADR-001: Risk Engine Architecture

Status: Accepted

Date:
2026-09-10


# Context

LIDOMA requires a deterministic, explainable and auditable
Risk Engine as the foundation of financial intelligence.

The Risk Engine must support:

- Portfolio risk calculation
- Risk metrics generation
- Future market data integration
- Event-driven communication
- Decision explainability
- Historical replay capability


# Decision

The Risk Engine will follow:

- Domain Driven Design (DDD)
- Event Driven Architecture (EDA)
- Pure calculation core
- Dependency inversion
- Infrastructure isolation


# Architecture Boundary


Portfolio Domain

        |

        v

Risk Engine Contract

        |

        v

Risk Calculation Pipeline

        |

        v

Risk Assessment

        |

        v

Risk Domain Event


# Core Rules


Risk Engine MUST:

- not depend on database
- not depend on external market providers
- produce deterministic outputs
- provide explainable metrics
- remain independently testable


# Risk Components


Initial implementation:

- Volatility
- Drawdown
- Correlation
- Exposure
- Risk Score


Future extensions:

- Historical VaR
- Parametric VaR
- Monte Carlo VaR
- CVaR
- Stress Testing


# Event Integration


Risk Engine emits:

- RiskAssessmentCreatedEvent
- RiskLimitBreachedEvent
- RiskSnapshotGeneratedEvent


# Non Goals


This phase does not implement:

- Market data adapters
- Database persistence
- API layer
- Authentication


# Consequences


Positive:

- Stable foundation for Phase 7
- Clear architecture boundary
- Easier testing
- Future scalability


Negative:

- Additional contracts before implementation
- More initial design work