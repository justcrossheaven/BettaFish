"""Tests for engine prompt modules loaded directly from file paths (avoids package side effects)."""

import importlib.util
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, rel_path: str):
    path = PROJECT_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


insight = _load_module("insight_prompts", "InsightEngine/prompts/prompts.py")
media = _load_module("media_prompts", "MediaEngine/prompts/prompts.py")
query = _load_module("query_prompts", "QueryEngine/prompts/prompts.py")


class TestPromptModules:
    def test_modules_load(self):
        assert hasattr(insight, "SYSTEM_PROMPT_REPORT_STRUCTURE")
        assert hasattr(media, "SYSTEM_PROMPT_REPORT_STRUCTURE")
        assert hasattr(query, "SYSTEM_PROMPT_REPORT_STRUCTURE")

    def test_required_system_prompts_exist(self):
        required = [
            "SYSTEM_PROMPT_REPORT_STRUCTURE",
            "SYSTEM_PROMPT_FIRST_SEARCH",
            "SYSTEM_PROMPT_FIRST_SUMMARY",
            "SYSTEM_PROMPT_REFLECTION",
            "SYSTEM_PROMPT_REFLECTION_SUMMARY",
            "SYSTEM_PROMPT_REPORT_FORMATTING",
        ]
        for mod in [insight, media, query]:
            for name in required:
                assert hasattr(mod, name)
                assert isinstance(getattr(mod, name), str)
                assert len(getattr(mod, name)) > 0

    def test_schemas_are_json_serializable(self):
        schemas = [
            insight.output_schema_report_structure,
            insight.output_schema_first_search,
            insight.output_schema_first_summary,
            media.output_schema_report_structure,
            media.output_schema_first_search,
            media.output_schema_first_summary,
            query.output_schema_report_structure,
            query.output_schema_first_search,
            query.output_schema_first_summary,
            query.output_schema_reflection,
        ]
        for schema in schemas:
            assert isinstance(schema, dict)
            assert isinstance(json.loads(json.dumps(schema)), dict)

    def test_report_structure_schema_shape(self):
        for mod in [insight, media, query]:
            schema = mod.output_schema_report_structure
            assert schema["type"] == "array"
            assert schema["items"]["type"] == "object"

    def test_key_prompt_content(self):
        assert "sentiment" in insight.SYSTEM_PROMPT_REPORT_STRUCTURE.lower() or "narrative" in insight.SYSTEM_PROMPT_REPORT_STRUCTURE.lower()
        assert "visual" in media.SYSTEM_PROMPT_REPORT_STRUCTURE.lower() or "chart" in media.SYSTEM_PROMPT_REPORT_STRUCTURE.lower()
        assert "MARKET ANCHOR" in query.SYSTEM_PROMPT_FIRST_SEARCH or "{current_date}" in query.SYSTEM_PROMPT_FIRST_SEARCH
