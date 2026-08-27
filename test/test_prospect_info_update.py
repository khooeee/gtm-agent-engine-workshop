import json
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
from gtm_agent import gtm_agent as agent_module


def test_update_persists_and_score_uses_updated_tech_stack(monkeypatch):
    prospect_id = "LEAD-39002"
    original_tech_stack = list(data_service.PROSPECTS[prospect_id]["tech_stack"])
    data_service._PROFILES.pop(prospect_id, None)
    try:
        initial_profile = agent_module.build_prospect_profile.invoke({"prospect_id": prospect_id})
        assert "Kafka" not in initial_profile["prospect_profile"]["tech_stack"]

        result = data_service.update_prospect_info(prospect_id, "Kafka")

        assert result["updated"] is True
        profile = agent_module.build_prospect_profile.invoke({"prospect_id": prospect_id})
        updated_tech_stack = profile["prospect_profile"]["tech_stack"]
        assert "Kafka" in updated_tech_stack

        captured = {}

        class FakeScoringModel:
            def invoke(self, messages):
                captured["profile"] = json.loads(
                    messages[1]["content"].split("\n\nProspect profile:\n", 1)[1]
                )
                return type("Result", (), {"model_dump": lambda self: {"score": 100}})()

        monkeypatch.setattr(agent_module, "_scoring_llm", FakeScoringModel())
        agent_module.score_prospect.invoke({
            "prospect_profile": profile["prospect_profile"],
            "offering": data_service.OFFERINGS["OFFER-10005"],
        })

        assert "Kafka" in captured["profile"]["tech_stack"]
    finally:
        data_service.PROSPECTS[prospect_id]["tech_stack"] = original_tech_stack
        data_service._PROFILES.pop(prospect_id, None)
