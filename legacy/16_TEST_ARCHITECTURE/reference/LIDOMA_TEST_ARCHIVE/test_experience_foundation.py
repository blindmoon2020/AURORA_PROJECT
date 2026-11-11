from lidoma_engines.experience import DecisionExperience


def test_decision_experience_creation():

    experience = DecisionExperience(
        experience_id="experience.alpha",
        decision_id="decision.alpha",
        outcome="success",
        lessons={
            "pattern": "high_confidence"
        },
    )

    assert experience.experience_id == (
        "experience.alpha"
    )

    assert experience.decision_id == (
        "decision.alpha"
    )

    assert experience.lessons["pattern"] == (
        "high_confidence"
    )


def test_experience_validation():

    try:
        DecisionExperience(
            experience_id="",
            decision_id="decision.alpha",
            outcome="success",
        )

        assert False

    except ValueError:
        assert True