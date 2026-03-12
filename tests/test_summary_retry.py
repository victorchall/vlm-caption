import pytest
import asyncio
from rules.summary_retry import run_summary_retry_rules


# --- Fake streaming client for testing without a real API ---

class _FakeEvent:
    def __init__(self, content=None, usage=None):
        self.choices = [type('C', (), {'delta': type('D', (), {'content': content})()})()] if content is not None else []
        self.usage = usage

class _FakeStream:
    """Async iterator that yields chunks then a usage event."""
    def __init__(self, chunks):
        self._items = [_FakeEvent(content=c) for c in chunks]
        self._items.append(_FakeEvent(usage=type('U', (), {'completion_tokens': 7, 'prompt_tokens': 11})()))
        self._idx = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._idx]
        self._idx += 1
        return item

class FakeClient:
    """Mimics openai.AsyncClient with a canned streaming response."""
    def __init__(self, response_chunks):
        self.chat = type('Chat', (), {
            'completions': type('Comp', (), {
                'create': self._create
            })()
        })()
        self._chunks = response_chunks

    async def _create(self, **kwargs):
        return _FakeStream(self._chunks)


RETRY_CONFIG = {
    "model": "test-model",
    "retry_rules": [
        {
            "rule_name": "test_rejection",
            "phrases": ["bad phrase", "another bad"],
            "rejection_note": "Please remove: [phrases]"
        }
    ]
}

NO_RULES_CONFIG = {"model": "test-model"}


class TestSummaryRetryRules:
    @pytest.mark.asyncio
    async def test_no_rules_returns_original(self):
        client = FakeClient(["whatever"])
        result, ct, pt = await run_summary_retry_rules(
            client, NO_RULES_CONFIG, [], "original text", 0, 0
        )
        assert result == "original text"

    @pytest.mark.asyncio
    async def test_clean_summary_returns_original(self):
        client = FakeClient(["whatever"])
        result, _, _ = await run_summary_retry_rules(
            client, RETRY_CONFIG, [], "perfectly fine summary", 0, 0
        )
        assert result == "perfectly fine summary"

    @pytest.mark.asyncio
    async def test_bad_phrase_triggers_retry_and_returns_corrected(self):
        client = FakeClient(["corrected ", "response"])
        result, _, _ = await run_summary_retry_rules(
            client, RETRY_CONFIG, [], "this has bad phrase in it", 0, 0
        )
        assert result == "corrected response"
        assert "bad phrase" not in result

    @pytest.mark.asyncio
    async def test_retry_still_bad_returns_original(self):
        """When the retry response still contains bad phrases, return the original."""
        client = FakeClient(["still has ", "bad phrase"])
        original = "original with bad phrase"
        result, _, _ = await run_summary_retry_rules(
            client, RETRY_CONFIG, [], original, 0, 0
        )
        assert result == original

    @pytest.mark.asyncio
    async def test_retry_strips_thinking_from_response(self):
        """Thinking blocks in the retry response should be filtered out."""
        client = FakeClient(["reasoning\n</think>\n\ncorrected ", "response"])
        result, _, _ = await run_summary_retry_rules(
            client, RETRY_CONFIG, [], "this has bad phrase", 0, 0
        )
        assert "</think>" not in result
        assert result == "corrected response"

    @pytest.mark.asyncio
    async def test_token_usage_accumulated(self):
        client = FakeClient(["fixed"])
        _, ct, pt = await run_summary_retry_rules(
            client, RETRY_CONFIG, [], "bad phrase here", 10, 20
        )
        assert ct == 10 + 7  # initial + fake usage
        assert pt == 20 + 11

    @pytest.mark.asyncio
    async def test_empty_config_does_not_crash(self):
        client = FakeClient(["whatever"])
        result, ct, pt = await run_summary_retry_rules(
            client, {}, [], "some text", 0, 0
        )
        assert result == "some text"
