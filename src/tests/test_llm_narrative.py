"""Tests for optional LLM-backed narrative synthesis."""

from src.synthesis.llm_client import LLMClient, LLMGenerationError
from src.synthesis.narrative_generator import NarrativeGenerator


SAMPLE_VERIFIED_CLAIM = {
    "claim": "Officials said ceasefire talks resumed on Monday.",
    "claim_type": "factual_claim",
    "verification_status": "needs_verification",
    "credibility_score": 0.72,
    "evidence": [
        {
            "title": "Ceasefire talks resume",
            "source": "Reuters",
            "url": "https://example.test/ceasefire",
            "snippet": "Diplomats reported talks resumed after a short pause.",
            "credibility_score": 0.9,
        }
    ],
}


def test_narrative_generator_uses_llm_when_available():
    class FakeLLMClient:
        model = "fake-model"
        provider = "openai_responses"

        def generate(self, *, system_prompt, user_prompt):
            assert "Do not add new facts" in system_prompt
            assert "Officials said ceasefire talks resumed" in user_prompt
            assert "[1] Reuters" in user_prompt
            return "Evidence indicates talks resumed, but independent confirmation remains limited. [1]"

    generator = NarrativeGenerator(use_llm=True, llm_client=FakeLLMClient())
    narrative = generator.generate_counter_narrative(SAMPLE_VERIFIED_CLAIM, tone="analytical")

    assert narrative["generation_backend"] == "llm"
    assert narrative["llm_model"] == "fake-model"
    assert narrative["counter_narrative"].startswith("Assessment:")
    assert "independent confirmation remains limited" in narrative["counter_narrative"]


def test_narrative_generator_falls_back_when_llm_fails():
    class FailingLLMClient:
        model = "fake-model"
        provider = "openai_responses"

        def generate(self, **_kwargs):
            raise LLMGenerationError("test failure")

    generator = NarrativeGenerator(use_llm=True, llm_client=FailingLLMClient())
    narrative = generator.generate_counter_narrative(SAMPLE_VERIFIED_CLAIM, tone="public")

    assert narrative["generation_backend"] == "template_fallback"
    assert narrative["llm_error"] == "test failure"
    assert narrative["counter_narrative"].startswith("What this means:")
    assert "After reviewing 1 sources" in narrative["counter_narrative"]


def test_llm_client_responses_api_payload_and_text_extraction():
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"output_text": "Generated narrative from Responses API."}

    class FakeSession:
        def post(self, url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

    client = LLMClient(
        api_key="test-key",
        api_base="https://api.example.test/v1",
        provider="openai_responses",
        model="test-model",
        session=FakeSession(),
    )

    output = client.generate(system_prompt="system", user_prompt="user")

    assert output == "Generated narrative from Responses API."
    assert captured["url"] == "https://api.example.test/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "test-model"
    assert captured["json"]["instructions"] == "system"
    assert captured["json"]["input"] == "user"

