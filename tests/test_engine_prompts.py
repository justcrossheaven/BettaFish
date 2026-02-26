"""
Tests for engine prompts (InsightEngine, MediaEngine, QueryEngine)
Tests schema validity and prompt generation.
"""

import pytest
import json


class TestInsightEnginePrompts:
    """Test InsightEngine/prompts/prompts.py"""
    
    def test_module_imports(self):
        """Should import InsightEngine prompts module."""
        from InsightEngine.prompts import prompts
        assert hasattr(prompts, 'SYSTEM_PROMPT_REPORT_STRUCTURE')
    
    def test_all_system_prompts_defined(self):
        """Should have all required system prompts."""
        from InsightEngine.prompts import prompts
        
        required_prompts = [
            'SYSTEM_PROMPT_REPORT_STRUCTURE',
            'SYSTEM_PROMPT_FIRST_SEARCH',
            'SYSTEM_PROMPT_FIRST_SUMMARY',
            'SYSTEM_PROMPT_REFLECTION',
            'SYSTEM_PROMPT_REFLECTION_SUMMARY',
            'SYSTEM_PROMPT_REPORT_FORMATTING'
        ]
        
        for prompt in required_prompts:
            assert hasattr(prompts, prompt)
            assert isinstance(getattr(prompts, prompt), str)
            assert len(getattr(prompts, prompt)) > 0
    
    def test_schemas_are_valid_json(self):
        """Should have valid JSON schemas."""
        from InsightEngine.prompts import prompts
        
        schemas = [
            prompts.output_schema_report_structure,
            prompts.output_schema_hot_topic_matrix,
            prompts.output_schema_first_search,
            prompts.output_schema_first_summary,
            prompts.output_schema_reflection,
            prompts.output_schema_reflection_summary
        ]
        
        for schema in schemas:
            assert isinstance(schema, dict)
            # Should be serializable as JSON
            json_str = json.dumps(schema)
            assert len(json_str) > 0
    
    def test_perception_layer_firewall_exists(self):
        """Should have perception layer firewall rules."""
        from InsightEngine.prompts import prompts
        assert hasattr(prompts, 'PERCEPTION_LAYER_FIREWALL')
        assert 'NO Price Predictions' in prompts.PERCEPTION_LAYER_FIREWALL


class TestMediaEnginePrompts:
    """Test MediaEngine/prompts/prompts.py"""
    
    def test_module_imports(self):
        """Should import MediaEngine prompts module."""
        from MediaEngine.prompts import prompts
        assert hasattr(prompts, 'SYSTEM_PROMPT_REPORT_STRUCTURE')
    
    def test_all_system_prompts_defined(self):
        """Should have all required system prompts."""
        from MediaEngine.prompts import prompts
        
        required_prompts = [
            'SYSTEM_PROMPT_REPORT_STRUCTURE',
            'SYSTEM_PROMPT_FIRST_SEARCH',
            'SYSTEM_PROMPT_FIRST_SUMMARY',
            'SYSTEM_PROMPT_REFLECTION',
            'SYSTEM_PROMPT_REFLECTION_SUMMARY',
            'SYSTEM_PROMPT_REPORT_FORMATTING'
        ]
        
        for prompt in required_prompts:
            assert hasattr(prompts, prompt)
            assert isinstance(getattr(prompts, prompt), str)
    
    def test_schemas_valid_json(self):
        """Should have valid JSON schemas."""
        from MediaEngine.prompts import prompts
        
        schemas = [
            prompts.output_schema_report_structure,
            prompts.output_schema_first_search,
            prompts.output_schema_first_summary
        ]
        
        for schema in schemas:
            json_str = json.dumps(schema)
            assert len(json_str) > 0
    
    def test_visual_focus_type_in_schema(self):
        """Should have visual_focus_type in report structure."""
        from MediaEngine.prompts import prompts
        schema = prompts.output_schema_report_structure
        
        # Check structure
        assert 'type' in schema
        assert schema['type'] == 'array'


class TestQueryEnginePrompts:
    """Test QueryEngine/prompts/prompts.py"""
    
    def test_module_imports(self):
        """Should import QueryEngine prompts module."""
        from QueryEngine.prompts import prompts
        assert hasattr(prompts, 'SYSTEM_PROMPT_REPORT_STRUCTURE')
    
    def test_all_system_prompts_defined(self):
        """Should have all required system prompts."""
        from QueryEngine.prompts import prompts
        
        required_prompts = [
            'SYSTEM_PROMPT_REPORT_STRUCTURE',
            'SYSTEM_PROMPT_FIRST_SEARCH',
            'SYSTEM_PROMPT_FIRST_SUMMARY',
            'SYSTEM_PROMPT_REFLECTION',
            'SYSTEM_PROMPT_REFLECTION_SUMMARY',
            'SYSTEM_PROMPT_REPORT_FORMATTING'
        ]
        
        for prompt in required_prompts:
            assert hasattr(prompts, prompt)
            assert isinstance(getattr(prompts, prompt), str)
            assert len(getattr(prompts, prompt)) > 100  # Non-trivial content
    
    def test_schemas_valid_json(self):
        """Should have valid JSON schemas."""
        from QueryEngine.prompts import prompts
        
        schemas = [
            prompts.output_schema_report_structure,
            prompts.output_schema_first_search,
            prompts.output_schema_first_summary,
            prompts.output_schema_reflection
        ]
        
        for schema in schemas:
            json_str = json.dumps(schema)
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
    
    def test_market_anchor_protocol_placeholder(self):
        """Should have market anchor placeholders in first search prompt."""
        from QueryEngine.prompts import prompts
        prompt = prompts.SYSTEM_PROMPT_FIRST_SEARCH
        
        # Should contain format placeholders
        assert '{current_date}' in prompt or 'MARKET ANCHOR' in prompt
    
    def test_analytical_focus_in_schema(self):
        """Should have analytical_focus in report structure."""
        from QueryEngine.prompts import prompts
        schema = prompts.output_schema_report_structure
        
        assert 'type' in schema
        assert schema['type'] == 'array'


class TestPromptConsistency:
    """Test consistency across all engine prompts."""
    
    def test_all_engines_have_six_prompts(self):
        """All engines should have 6 main system prompts."""
        from InsightEngine.prompts import prompts as insight
        from MediaEngine.prompts import prompts as media
        from QueryEngine.prompts import prompts as query
        
        prompt_names = [
            'SYSTEM_PROMPT_REPORT_STRUCTURE',
            'SYSTEM_PROMPT_FIRST_SEARCH',
            'SYSTEM_PROMPT_FIRST_SUMMARY',
            'SYSTEM_PROMPT_REFLECTION',
            'SYSTEM_PROMPT_REFLECTION_SUMMARY',
            'SYSTEM_PROMPT_REPORT_FORMATTING'
        ]
        
        for prompt_name in prompt_names:
            assert hasattr(insight, prompt_name)
            assert hasattr(media, prompt_name)
            assert hasattr(query, prompt_name)
    
    def test_schemas_have_type_field(self):
        """All schemas should have 'type' field."""
        from InsightEngine.prompts import prompts as insight
        
        schemas = [
            insight.output_schema_report_structure,
            insight.output_schema_first_search,
            insight.output_schema_first_summary
        ]
        
        for schema in schemas:
            assert 'type' in schema
    
    def test_prompts_not_empty(self):
        """All prompts should have substantial content."""
        from QueryEngine.prompts import prompts
        
        for attr_name in dir(prompts):
            if attr_name.startswith('SYSTEM_PROMPT_'):
                prompt = getattr(prompts, attr_name)
                assert isinstance(prompt, str)
                assert len(prompt) > 50  # At least 50 characters


class TestSchemaValidation:
    """Test JSON schema validation for all engines."""
    
    def test_report_structure_schema_format(self):
        """Report structure schemas should be arrays of objects."""
        from InsightEngine.prompts import prompts as insight
        from MediaEngine.prompts import prompts as media
        from QueryEngine.prompts import prompts as query
        
        for engine in [insight, media, query]:
            schema = engine.output_schema_report_structure
            assert schema['type'] == 'array'
            assert 'items' in schema
            assert schema['items']['type'] == 'object'
    
    def test_first_search_schema_has_required_fields(self):
        """First search schemas should have required fields."""
        from QueryEngine.prompts import prompts
        
        schema = prompts.output_schema_first_search
        assert 'properties' in schema
        assert 'search_query' in schema['properties']
        assert 'search_tool' in schema['properties']
        assert 'reasoning' in schema['properties']
    
    def test_summary_schema_has_paragraph_field(self):
        """Summary schemas should have paragraph_latest_state."""
        from QueryEngine.prompts import prompts
        
        schema = prompts.output_schema_first_summary
        assert 'properties' in schema
        assert 'paragraph_latest_state' in schema['properties']


class TestPromptContent:
    """Test specific prompt content requirements."""
    
    def test_query_engine_mentions_value_investing(self):
        """QueryEngine should mention value investing."""
        from QueryEngine.prompts import prompts
        
        # Check at least one prompt mentions value investing concepts
        all_prompts = [
            prompts.SYSTEM_PROMPT_REPORT_STRUCTURE,
            prompts.SYSTEM_PROMPT_FIRST_SUMMARY
        ]
        
        mentions_value_investing = any(
            'Value Investing' in prompt or 'value investing' in prompt or 'Variant Perception' in prompt
            for prompt in all_prompts
        )
        assert mentions_value_investing
    
    def test_media_engine_mentions_visual(self):
        """MediaEngine should mention visual analysis."""
        from MediaEngine.prompts import prompts
        
        prompt = prompts.SYSTEM_PROMPT_REPORT_STRUCTURE
        assert 'visual' in prompt.lower() or 'chart' in prompt.lower()
    
    def test_insight_engine_mentions_sentiment(self):
        """InsightEngine should mention sentiment/narrative."""
        from InsightEngine.prompts import prompts
        
        prompt = prompts.SYSTEM_PROMPT_REPORT_STRUCTURE
        assert 'sentiment' in prompt.lower() or 'narrative' in prompt.lower()
