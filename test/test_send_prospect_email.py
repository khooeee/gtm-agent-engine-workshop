import os
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
from gtm_agent.gtm_agent import send_prospect_email


def runtime():
    return SimpleNamespace(config={"metadata": {"user_id": "rep_rgarcia"}})


def prospect(prospect_id):
    return {
        "prospect_id": prospect_id,
        "name": "Test Prospect",
        "email": "prospect@example.com",
    }


def test_disqualified_prospect_is_blocked(monkeypatch):
    sent = False

    def get_record(prospect_id):
        assert prospect_id == "LEAD-BLOCKED"
        return {"disqualified": True}

    def fail_if_sent(*args, **kwargs):
        nonlocal sent
        sent = True

    monkeypatch.setattr(data_service, "get_prospect_record", get_record)
    monkeypatch.setattr("gtm_agent.gtm_agent.uuid.uuid4", fail_if_sent)

    result = send_prospect_email.func(prospect("LEAD-BLOCKED"), "Subject", "Body", runtime())

    assert result == {"status": "blocked", "reason": "prospect is disqualified"}
    assert not sent


def test_qualified_prospect_is_sent(monkeypatch):
    monkeypatch.setattr(data_service, "get_prospect_record", lambda prospect_id: {"disqualified": False})

    result = send_prospect_email.func(prospect("LEAD-QUALIFIED"), "Subject", "Body", runtime())

    assert result["status"] == "sent"
    assert result["to"] == "prospect@example.com"
