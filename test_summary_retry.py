from rules.summary_retry import run_summary_retry_rules
import asyncio
import inspect

class FakeDelta:
    def __init__(self, content):
        self.content = content

class FakeChoice:
    def __init__(self, content_chunk):
        self.delta = FakeDelta(content_chunk)

class FakeUsage:
    def __init__(self, completion_tokens=7, prompt_tokens=11):
        self.completion_tokens = completion_tokens
        self.prompt_tokens = prompt_tokens

class FakeEvent:
    def __init__(self, choices, usage=None):
        self.choices = choices
        self.usage = usage

class AsyncStreamFake:
    def __init__(self, chunks):
        self._chunks = chunks
        self._index = 0
        self._sent_usage = False # Flag to send the usage stats once at the end

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(0.001)        
        if self._index < len(self._chunks):
            chunk_text = self._chunks[self._index]
            self._index += 1
            return FakeEvent(choices=[FakeChoice(content_chunk=chunk_text)])

        elif not self._sent_usage:
            self._sent_usage = True
            usage = FakeUsage(completion_tokens=7, prompt_tokens=11)
            return FakeEvent(choices=[], usage=usage)
        else:
            raise StopAsyncIteration

class FakeCompletions:
    def __init__(self, completions):
        self.completions = completions

    async def create(self, **kwargs):
        return AsyncStreamFake(self.completions)

class FakeChat:
    def __init__(self, completions):
        self.completions = FakeCompletions(completions)
    
class FakeClient:
    def __init__(self, completions = ["foo", "bar"]):
        self.chat = FakeChat(completions)
        self.chat.completions

MESSAGES = []
BAD_PHRASE1 = "bad phrase1"
BAD_PHRASE2 = "bad phrase2"
GOOD_PHRASE1 = "good phrase1"
GOOD_PHRASE2 = "good phrase2"
MINIMUM_CONFIG = {
    "model": "foo",
    "retry_rules": [
        {
            "rule_name": "my_rejection",
            "phrases": [
                BAD_PHRASE1,
                BAD_PHRASE2
            ],
            "rejection_note": "Bad phrases found: [phrases]"
        }
    ]
}

async def test_when_empty_config_then_does_not_crash():
    try:
        client_fake = FakeClient()
        result = await run_summary_retry_rules(client_fake, {}, MESSAGES, "", 0, 0) # type: ignore
        print(f"  -- result: {result}")
        return True
    except Exception as ex:
        print(ex)
        return False

async def test_run_summary_retry_rules_retries_minimum_config_with_match():
    try:
        client_fake = FakeClient()
        result = await run_summary_retry_rules(client_fake, MINIMUM_CONFIG, MESSAGES, BAD_PHRASE1, 0, 0) # type: ignore
        print(f"  -- result: {result}")
        assert BAD_PHRASE1 not in result
        return True
    except Exception as ex:
        print(ex)
        return False

async def test_when_no_bad_phrase_returns_original():
    try:
        client_result = "foo bar"
        client_fake = FakeClient(client_result)

        result, _, _ = await run_summary_retry_rules(client_fake, MINIMUM_CONFIG, MESSAGES, GOOD_PHRASE1, 0, 0) # type: ignore

        print(f"  -- result: {result}")
        assert result == GOOD_PHRASE1
        return True
    except Exception as ex:
        print(ex)
        return False
    
async def test_when_bad_phrases_then_returns_corrected_from_client():
    try:
        client_result = "foo bar"
        client_fake = FakeClient(client_result)
        fake_summary_result = f"{BAD_PHRASE1} {BAD_PHRASE2}"
        MINIMUM_CONFIG["retry_rules"][0]["phrases"] = [BAD_PHRASE1, BAD_PHRASE2]

        result, _, _ = await run_summary_retry_rules(client_fake, MINIMUM_CONFIG, MESSAGES, fake_summary_result, 0, 0) # type: ignore

        print(f"  -- result: {result}")
        assert result == client_result
        return True
    except Exception as ex:
        print(ex)
        return False

async def test_when_failure_to_correct_then_returns_original():
    try:
        client_fake = FakeClient([BAD_PHRASE1,BAD_PHRASE2])
        from rules.summary_retry import run_summary_retry_rules
        fake_summary_result = f"{BAD_PHRASE1} {BAD_PHRASE2}"
        MINIMUM_CONFIG["retry_rules"][0]["phrases"] = [BAD_PHRASE1, BAD_PHRASE2]

        result, _, _ = await run_summary_retry_rules(client_fake, MINIMUM_CONFIG, MESSAGES, fake_summary_result, 0, 0) # type: ignore

        print(f"  -- result: {result}")
        assert result == fake_summary_result
        return True
    except Exception as ex:
        print(ex)
        return False

async def main():
    print("🔧 Running hints system tests...\n")

    test_functions = []
    for name, func in globals().items():
        if name.startswith("test_") and inspect.iscoroutinefunction(func):
            test_functions.append(func)
    
    if not test_functions:
        print("🤔 No tests found. Make sure your async test functions are named with a 'test_' prefix.")
        return

    test_results = []
    passed_count = 0
    failed_count = 0

    for test_func in test_functions:
        print(f"▶️  Running: {test_func.__name__}")
        try:
            result = await test_func()
            test_results.append(result)

            if result:
                print(f"✅ PASSED: {test_func.__name__}\n")
                passed_count += 1
            else:
                print(f"❌ FAILED: {test_func.__name__}\n")
                failed_count += 1

        except Exception as e:
            print(f"💥 ERROR in {test_func.__name__}: {e}\n")
            test_results.append(False)
            failed_count += 1
    print("------- Test Summary -------")
    print(f"Total tests run: {len(test_functions)}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print("--------------------------\n")

    if all(test_results):
        print("🎉 All tests passed! The rejection/retry system is working correctly.")
    else:
        print("❌ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())