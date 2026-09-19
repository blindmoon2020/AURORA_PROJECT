from datetime import datetime, timezone

from lidoma_core.contracts import EventContract


def test_event_contract_creation():
    event = EventContract(
        event_id="EVT001",
        event_type="MARKET_UPDATE",
        timestamp=datetime.now(timezone.utc),
        source="DATA_ENGINE",
    )

    assert event.event_id == "EVT001"
    assert event.event_type == "MARKET_UPDATE"
    assert event.source == "DATA_ENGINE"
    assert event.version == "1.0"
