import json
import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile, get_prospect


class SensitiveProspectDataTest(unittest.TestCase):
    def setUp(self):
        self.prospect_id = "TEST-SENSITIVE-PROSPECT"
        self.record = {
            "name": "Test Prospect",
            "email": "test@example.com",
            "disqualified": False,
            "annual_revenue": 42_000_000,
            "enrichment_source": "Test enrichment",
            "segment": "Enterprise",
            "engagement_history": [],
            "account_details": [],
            "tech_stack": ["Kafka"],
            "billing_qualification": {
                "tax_id": "123-45-6789",
                "card_on_file": "4111111111111111",
                "date_of_birth": "1990-01-01",
                "credit_check_ref": "EXPN-TEST",
            },
        }
        data_service.PROSPECTS[self.prospect_id] = self.record

    def tearDown(self):
        data_service.PROSPECTS.pop(self.prospect_id, None)
        data_service._PROFILES.pop(self.prospect_id, None)

    def test_prospect_tools_exclude_billing_data(self):
        contact = get_prospect.invoke({"prospect_id": self.prospect_id})
        profile = build_prospect_profile.invoke({"prospect_id": self.prospect_id})
        serialized = json.dumps({"contact": contact, "profile": profile})

        for sensitive_field in (
            "tax_id",
            "card_on_file",
            "date_of_birth",
            "credit_check_ref",
            "billing_qualification",
        ):
            self.assertNotIn(sensitive_field, serialized)
        self.assertEqual(contact["prospect"]["name"], self.record["name"])
        self.assertEqual(contact["prospect"]["email"], self.record["email"])
        self.assertEqual(
            profile["prospect_profile"]["annual_revenue"],
            self.record["annual_revenue"],
        )


if __name__ == "__main__":
    unittest.main()
