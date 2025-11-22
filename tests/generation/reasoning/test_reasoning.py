"""Tests for chain-of-thought reasoning module.

v0.3.7b: Test reasoning parser, generator, and integration.
"""

import pytest

from src.generation.reasoning import (
    ReasoningMode,
    ReasoningStep,
    ValidationFlag,
    ReasonedResponse,
    ReasoningParser,
    build_reasoning_prompt,
)


class TestReasoningTypes:
    """Test reasoning data types."""

    def test_reasoning_mode_enum(self):
        """Test ReasoningMode enum values."""
        assert ReasoningMode.NONE.value == "none"
        assert ReasoningMode.BASIC.value == "basic"
        assert ReasoningMode.STRUCTURED.value == "structured"
        assert ReasoningMode.CHAIN.value == "chain"

    def test_reasoning_step_creation(self):
        """Test ReasoningStep dataclass."""
        step = ReasoningStep(
            step_number=1,
            thought="Understanding the query",
            action="understand",
            confidence=0.95,
            evidence=[1, 2]
        )

        assert step.step_number == 1
        assert step.action == "understand"
        assert step.confidence == 0.95
        assert step.evidence == [1, 2]

    def test_validation_flag_creation(self):
        """Test ValidationFlag dataclass."""
        flag = ValidationFlag(
            type="contradiction",
            description="Sources disagree",
            severity="high",
            step_numbers=[2, 3]
        )

        assert flag.type == "contradiction"
        assert flag.severity == "high"
        assert len(flag.step_numbers) == 2

    def test_reasoned_response_has_critical_issues(self):
        """Test has_critical_issues method."""
        response = ReasonedResponse(
            answer="Test answer",
            citations=["[1]"],
            reasoning_steps=[],
            validation_flags=[
                ValidationFlag("test", "Test issue", "high", [])
            ],
            overall_confidence=0.5,
            mode=ReasoningMode.BASIC,
            raw_response=""
        )

        assert response.has_critical_issues() is True

    def test_reasoned_response_get_step_by_action(self):
        """Test get_step_by_action method."""
        steps = [
            ReasoningStep(1, "Understanding", "understand", 1.0),
            ReasoningStep(2, "Analyzing", "analyze", 0.9)
        ]

        response = ReasonedResponse(
            answer="Test",
            citations=[],
            reasoning_steps=steps,
            validation_flags=[],
            overall_confidence=0.95,
            mode=ReasoningMode.BASIC,
            raw_response=""
        )

        understand_step = response.get_step_by_action("understand")
        assert understand_step is not None
        assert understand_step.step_number == 1

        missing_step = response.get_step_by_action("synthesize")
        assert missing_step is None


class TestReasoningParser:
    """Test reasoning parser functionality."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return ReasoningParser()

    def test_parse_direct_answer(self, parser):
        """Test parsing response with no reasoning."""
        raw_response = "Machine learning is a subset of AI that focuses on learning from data."

        response = parser.parse_response(raw_response, ReasoningMode.NONE)

        assert response.mode == ReasoningMode.NONE
        assert response.answer == raw_response
        assert len(response.reasoning_steps) == 0
        assert response.overall_confidence == 0.5

    def test_parse_basic_reasoning(self, parser):
        """Test parsing basic reasoning format."""
        raw_response = """
<reasoning>
1. The question asks about machine learning
2. I have information from sources [1] and [2]
3. Both sources agree on the definition
4. Therefore, I can provide a confident answer
</reasoning>

<answer>
Machine learning is a subset of AI [1][2].
</answer>
"""

        response = parser.parse_response(raw_response, ReasoningMode.BASIC)

        assert response.mode == ReasoningMode.BASIC
        assert "Machine learning" in response.answer
        assert len(response.reasoning_steps) > 0
        assert len(response.citations) == 2

    def test_parse_structured_reasoning(self, parser):
        """Test parsing structured XML reasoning."""
        raw_response = """
<reasoning>
<step number="1" action="understand">
The question asks for a definition of ML.
</step>

<step number="2" action="retrieve" confidence="0.95">
Found relevant information in sources [1] and [2].
</step>

<step number="3" action="analyze" confidence="0.90">
Both sources provide consistent definitions.
</step>
</reasoning>

<answer>
Machine learning (ML) is defined as... [1][2]
</answer>
"""

        response = parser.parse_response(raw_response, ReasoningMode.STRUCTURED)

        assert response.mode == ReasoningMode.STRUCTURED
        assert len(response.reasoning_steps) == 3
        assert response.reasoning_steps[0].action == "understand"
        assert response.reasoning_steps[1].confidence == 0.95
        assert response.overall_confidence > 0

    def test_extract_citations(self, parser):
        """Test citation extraction."""
        text = "According to source [1], ML is important. Source [2] agrees, and [3] provides examples."

        citations = parser._extract_citations(text)

        assert len(citations) == 3
        assert "[1]" in citations
        assert "[2]" in citations
        assert "[3]" in citations

    def test_detect_contradiction(self, parser):
        """Test contradiction detection."""
        steps = [
            ReasoningStep(
                1,
                "Source [1] says X is true, however source [2] contradicts this.",
                "analyze",
                0.8
            )
        ]

        flags = parser._detect_contradictions(steps)

        assert len(flags) > 0
        assert flags[0].type == "contradiction"

    def test_detect_uncertainty(self, parser):
        """Test uncertainty detection."""
        steps = [
            ReasoningStep(
                1,
                "I'm not sure about this answer based on the sources.",
                "analyze",
                0.5
            )
        ]
        answer = "The answer is uncertain."

        flags = parser._detect_uncertainty(steps, answer)

        assert len(flags) > 0
        assert any(f.type == "uncertainty" for f in flags)

    def test_confidence_calculation(self, parser):
        """Test overall confidence calculation."""
        steps = [
            ReasoningStep(1, "High confidence step", "understand", 0.9),
            ReasoningStep(2, "Lower confidence step", "analyze", 0.7),
            ReasoningStep(3, "Medium confidence step", "conclude", 0.8)
        ]
        flags = []  # No validation issues

        confidence = parser._calculate_confidence(steps, flags)

        assert 0.7 <= confidence <= 0.9  # Should be average
        assert isinstance(confidence, float)

    def test_confidence_with_penalties(self, parser):
        """Test confidence calculation with validation penalties."""
        steps = [
            ReasoningStep(1, "Step", "analyze", 0.9)
        ]
        flags = [
            ValidationFlag("test", "High severity issue", "high", [1])
        ]

        confidence = parser._calculate_confidence(steps, flags)

        assert confidence < 0.9  # Should be penalised


class TestReasoningPrompts:
    """Test reasoning prompt generation."""

    def test_build_basic_prompt(self):
        """Test building basic reasoning prompt."""
        from dataclasses import dataclass

        @dataclass
        class MockChunk:
            content: str
            metadata: dict

        chunks = [
            MockChunk("ML is about learning from data", {"source": "paper.pdf", "page": 1}),
            MockChunk("Neural networks are ML models", {"source": "book.pdf", "page": 42})
        ]

        prompt = build_reasoning_prompt(
            query="What is machine learning?",
            chunks=chunks,
            mode=ReasoningMode.BASIC
        )

        assert "What is machine learning?" in prompt
        assert "[1]" in prompt
        assert "[2]" in prompt
        assert "ML is about learning" in prompt
        assert "<reasoning>" in prompt
        assert "<answer>" in prompt

    def test_build_structured_prompt(self):
        """Test building structured reasoning prompt."""
        from dataclasses import dataclass

        @dataclass
        class MockChunk:
            content: str
            metadata: dict

        chunks = [MockChunk("Test content", {"source": "test.pdf"})]

        prompt = build_reasoning_prompt(
            "Test query",
            chunks,
            ReasoningMode.STRUCTURED
        )

        assert "step number=" in prompt
        assert "action=" in prompt
        assert "confidence=" in prompt

    def test_build_chain_prompt(self):
        """Test building full chain-of-thought prompt."""
        from dataclasses import dataclass

        @dataclass
        class MockChunk:
            content: str
            metadata: dict

        chunks = [MockChunk("Test", {"source": "test.pdf"})]

        prompt = build_reasoning_prompt(
            "Test query",
            chunks,
            ReasoningMode.CHAIN
        )

        assert "chain_of_thought" in prompt
        assert "Understanding the Query" in prompt
        assert "Evidence Gathering" in prompt
        assert "Confidence Assessment" in prompt


class TestReasoningIntegration:
    """Integration tests for reasoning module."""

    def test_end_to_end_parsing(self):
        """Test complete parse workflow."""
        parser = ReasoningParser()

        # Simulate LLM response
        llm_response = """
<reasoning>
1. Question asks about ML
2. Found info in [1] and [2]
3. Sources agree on definition
</reasoning>

<answer>
Machine learning is defined in sources [1] and [2] as...
</answer>
"""

        response = parser.parse_response(llm_response, ReasoningMode.BASIC)

        # Verify complete response
        assert response.answer is not None
        assert len(response.citations) == 2
        assert len(response.reasoning_steps) >= 1
        assert 0.0 <= response.overall_confidence <= 1.0
        assert response.mode == ReasoningMode.BASIC

    def test_fallback_to_direct_answer(self):
        """Test fallback when no reasoning markers found."""
        parser = ReasoningParser()

        # Response without reasoning tags
        response_text = "This is just a direct answer without any reasoning tags."

        response = parser.parse_response(response_text, ReasoningMode.BASIC)

        # Should still parse successfully
        assert response.answer == response_text
        assert len(response.reasoning_steps) >= 0  # May have minimal parsing
