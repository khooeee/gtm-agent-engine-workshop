import os
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
import gtm_agent.gtm_agent as agent_module


class FakeAgent:
    def __init__(self):
        self.invocation = None

    def invoke(self, inputs, *, config):
        self.invocation = {"inputs": inputs, "config": config}
        return {"messages": [SimpleNamespace(content="done")]}


def test_scoring_and_update_requests_receive_resolved_rep(monkeypatch):
    rep = {"rep_id": "rep_rgarcia", "name": "Rosa Garcia", "email": "rosa@example.com"}
    created = []

    def create_agent(resolved_rep):
        fake_agent = FakeAgent()
        created.append((resolved_rep, fake_agent))
        return fake_agent

    monkeypatch.setattr(data_service, "get_rep", lambda user_id: rep)
    monkeypatch.setattr(agent_module, "_create_agent", create_agent)

    for request in (
        "score LEAD-x against OFFER-y",
        "add Terraform to LEAD-39002's tech stack, then score them against OFFER-10004",
    ):
        result = agent_module.run_agent(request, user_id=rep["rep_id"])
        resolved_rep, fake_agent = created[-1]
        assert resolved_rep is rep
        assert fake_agent.invocation["config"]["metadata"]["rep"] is rep
        assert agent_module.build_system_prompt(resolved_rep).endswith(
            "- Name: Rosa Garcia\n- Email: rosa@example.com\n- Rep ID: rep_rgarcia"
        )
        assert result["reply"] == "done"
