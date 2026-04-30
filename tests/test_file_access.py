import asyncio
import json
import os

import pytest

from file_utils.file_access import (
    OUTPUT_FORMAT_JSONL,
    OUTPUT_FORMAT_TXT,
    caption_exists,
    concat_prompts,
    save_caption,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


class TestConcatPrompts:
    def test_joins_with_double_newline(self):
        assert concat_prompts(["a", "b", "c"]) == "a\n\nb\n\nc"

    def test_single_prompt(self):
        assert concat_prompts(["only"]) == "only"

    def test_empty_list(self):
        assert concat_prompts([]) == ""


class TestSaveCaptionTxt:
    def test_writes_txt_sidecar(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")  # placeholder

        _run(save_caption(
            file_path=str(image),
            caption_text="a cat",
            debug_info="",
            output_format=OUTPUT_FORMAT_TXT,
        ))

        txt = tmp_path / "img.txt"
        assert txt.exists()
        assert txt.read_text(encoding="utf-8") == "a cat"

    def test_overwrites_existing_txt(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        (tmp_path / "img.txt").write_text("old", encoding="utf-8")

        _run(save_caption(
            file_path=str(image),
            caption_text="new",
            debug_info="",
            output_format=OUTPUT_FORMAT_TXT,
        ))

        assert (tmp_path / "img.txt").read_text(encoding="utf-8") == "new"


class TestSaveCaptionJsonl:
    def test_appends_one_entry_per_call(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        prompt = concat_prompts(["describe", "summarize"])

        _run(save_caption(
            file_path=str(image),
            caption_text="caption-A",
            debug_info="",
            output_format=OUTPUT_FORMAT_JSONL,
            model="model-X",
            concat_prompt=prompt,
        ))
        _run(save_caption(
            file_path=str(image),
            caption_text="caption-B",
            debug_info="",
            output_format=OUTPUT_FORMAT_JSONL,
            model="model-Y",
            concat_prompt=prompt,
        ))

        jsonl = tmp_path / "img.jsonl"
        assert jsonl.exists()
        lines = [l for l in jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 2
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first == {"text": "caption-A", "model": "model-X", "prompt": prompt}
        assert second == {"text": "caption-B", "model": "model-Y", "prompt": prompt}

    def test_does_not_create_txt_in_jsonl_mode(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")

        _run(save_caption(
            file_path=str(image),
            caption_text="x",
            debug_info="",
            output_format=OUTPUT_FORMAT_JSONL,
            model="m",
            concat_prompt="p",
        ))

        assert not (tmp_path / "img.txt").exists()
        assert (tmp_path / "img.jsonl").exists()


class TestCaptionExistsTxt:
    def test_true_when_txt_present(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        (tmp_path / "img.txt").write_text("hi", encoding="utf-8")

        assert caption_exists(str(image), OUTPUT_FORMAT_TXT) is True

    def test_false_when_txt_absent(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        assert caption_exists(str(image), OUTPUT_FORMAT_TXT) is False


class TestCaptionExistsJsonl:
    def _seed(self, tmp_path, entries):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        jsonl = tmp_path / "img.jsonl"
        with open(jsonl, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return str(image)

    def test_false_when_jsonl_absent(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        assert caption_exists(str(image), OUTPUT_FORMAT_JSONL, model="m", concat_prompt="p") is False

    def test_true_on_exact_model_and_prompt_match(self, tmp_path):
        image_path = self._seed(tmp_path, [
            {"text": "x", "model": "m1", "prompt": "p1"},
            {"text": "y", "model": "m2", "prompt": "p2"},
        ])
        assert caption_exists(image_path, OUTPUT_FORMAT_JSONL, model="m2", concat_prompt="p2") is True

    def test_false_when_model_differs(self, tmp_path):
        image_path = self._seed(tmp_path, [
            {"text": "x", "model": "m1", "prompt": "p1"},
        ])
        assert caption_exists(image_path, OUTPUT_FORMAT_JSONL, model="other", concat_prompt="p1") is False

    def test_false_when_prompt_differs(self, tmp_path):
        image_path = self._seed(tmp_path, [
            {"text": "x", "model": "m1", "prompt": "p1"},
        ])
        assert caption_exists(image_path, OUTPUT_FORMAT_JSONL, model="m1", concat_prompt="other") is False

    def test_skips_blank_and_malformed_lines(self, tmp_path):
        image = tmp_path / "img.jpg"
        image.write_bytes(b"\x00")
        jsonl = tmp_path / "img.jsonl"
        jsonl.write_text(
            "\n"
            "not json at all\n"
            + json.dumps({"text": "x", "model": "m1", "prompt": "p1"}) + "\n",
            encoding="utf-8",
        )
        assert caption_exists(str(image), OUTPUT_FORMAT_JSONL, model="m1", concat_prompt="p1") is True
        assert caption_exists(str(image), OUTPUT_FORMAT_JSONL, model="m1", concat_prompt="missing") is False
