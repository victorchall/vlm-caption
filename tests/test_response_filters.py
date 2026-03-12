import pytest
from response_filters import filter_thinking, filter_caption, filter_ascii, remove_base64_image


class TestFilterThinking:
    def test_removes_complete_think_block(self):
        text = "<think>Some reasoning here</think>\n\nActual output."
        assert filter_thinking(text) == "Actual output."

    def test_removes_multiline_think_block(self):
        text = "<think>\nLine 1\nLine 2\nLine 3\n</think>\n\nActual output."
        assert filter_thinking(text) == "Actual output."

    def test_handles_missing_opening_think_tag(self):
        """vLLM strips the opening <think> but leaves closing </think>"""
        text = "The user wants a caption.\nLet me think...\n</think>\n\nActual output."
        assert filter_thinking(text) == "Actual output."

    def test_no_thinking_returns_unchanged(self):
        text = "Just a normal caption with no thinking."
        assert filter_thinking(text) == "Just a normal caption with no thinking."

    def test_empty_think_block(self):
        text = "<think></think>\nCaption."
        assert filter_thinking(text) == "Caption."

    def test_strips_whitespace(self):
        text = "  \n<think>thoughts</think>\n\n  Actual output.  \n"
        assert filter_thinking(text) == "Actual output."

    def test_empty_string(self):
        assert filter_thinking("") == ""

    def test_only_thinking_no_output(self):
        text = "Some reasoning\n</think>"
        assert filter_thinking(text) == ""

    def test_preserves_think_word_in_normal_text(self):
        text = "I think this is a good caption."
        assert filter_thinking(text) == "I think this is a good caption."


class TestFilterCaption:
    def test_removes_begin_box_token(self):
        assert filter_caption("Hello<|begin_of_box|> world") == "Hello world"

    def test_removes_end_box_token(self):
        assert filter_caption("Hello<|end_of_box|> world") == "Hello world"

    def test_removes_both_box_tokens(self):
        text = "<|begin_of_box|>content<|end_of_box|>"
        assert filter_caption(text) == "content"

    def test_no_tokens_returns_unchanged(self):
        text = "Normal caption text."
        assert filter_caption(text) == "Normal caption text."

    def test_multiple_occurrences(self):
        text = "<|begin_of_box|>a<|end_of_box|> <|begin_of_box|>b<|end_of_box|>"
        assert filter_caption(text) == "a b"


class TestFilterAscii:
    def test_ascii_unchanged(self):
        assert filter_ascii("Hello world") == "Hello world"

    def test_replaces_non_ascii(self):
        assert filter_ascii("caf\u00e9") == "caf?"

    def test_empty_string(self):
        assert filter_ascii("") == ""

    def test_all_non_ascii(self):
        assert filter_ascii("\u00e9\u00e8\u00ea") == "???"

    def test_preserves_printable_ascii(self):
        text = "ABCxyz 012 !@#$%"
        assert filter_ascii(text) == text


class TestRemoveBase64Image:
    def test_removes_base64_from_image_url(self):
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": "Describe this"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQ..."}}
            ]}
        ]
        result = remove_base64_image(messages)
        assert result[0]["content"][1]["image_url"]["url"] == "...removed..."

    def test_preserves_text_content(self):
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": "Hello"}
            ]}
        ]
        result = remove_base64_image(messages)
        assert result[0]["content"][0]["text"] == "Hello"

    def test_handles_string_content(self):
        messages = [{"role": "system", "content": "You are helpful."}]
        result = remove_base64_image(messages)
        assert result[0]["content"] == "You are helpful."

    def test_handles_empty_messages(self):
        assert remove_base64_image([]) == []
