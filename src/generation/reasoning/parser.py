"""
Parser for extracting reasoning from LLM responses.

v0.3.7b: Parse chain-of-thought reasoning with fallback strategies.
"""

import re

from src.generation.reasoning.types import (
    ReasonedResponse,
    ReasoningMode,
    ReasoningStep,
    ValidationFlag,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReasoningParser:
    """
    Parse reasoning and answers from LLM output.

    Supports multiple parsing strategies with fallbacks:
    1. XML-style tags (<reasoning>, <answer>)
    2. Markdown sections (## Understanding, ## Answer)
    3. Regex patterns (Step 1:, Step 2:)
    4. Direct text (no reasoning)

    Example:
        >>> parser = ReasoningParser()
        >>> response = parser.parse_response(
        ...     raw_response='<reasoning>Step 1...</reasoning><answer>ML is...</answer>',
        ...     mode=ReasoningMode.BASIC
        ... )
        >>> len(response.reasoning_steps)
        1
    """

    def __init__(self):
        """Initialise parser with compiled regex patterns."""
        # Compile regex patterns for performance
        self.xml_reasoning_pattern = re.compile(
            r'<reasoning>(.*?)</reasoning>',
            re.DOTALL | re.IGNORECASE
        )
        self.xml_answer_pattern = re.compile(
            r'<answer>(.*?)</answer>',
            re.DOTALL | re.IGNORECASE
        )
        self.chain_pattern = re.compile(
            r'<chain_of_thought>(.*?)</chain_of_thought>',
            re.DOTALL | re.IGNORECASE
        )
        self.step_pattern = re.compile(
            r'<step\s+number="(\d+)"\s+action="(\w+)"(?:\s+confidence="([\d.]+)")?>(.+?)</step>',
            re.DOTALL
        )
        self.numbered_step_pattern = re.compile(
            r'(?:^|\n)(\d+)[\.\)]\s+(.+?)(?=\n\d+[\.\)]|\n##|\Z)',
            re.DOTALL | re.MULTILINE
        )
        self.confidence_pattern = re.compile(
            r'confidence[:\s]+([\d.]+)',
            re.IGNORECASE
        )
        self.citation_pattern = re.compile(r'\[(\d+)\]')

    def parse_response(
        self,
        raw_response: str,
        mode: ReasoningMode
    ) -> ReasonedResponse:
        """
        Extract reasoning and answer from LLM response.

        Args:
            raw_response: Raw text from LLM
            mode: Reasoning mode that was used

        Returns:
            Parsed ReasonedResponse with reasoning steps and answer

        Example:
            >>> parser = ReasoningParser()
            >>> response = parser.parse_response(
            ...     '<reasoning>1. Understanding...</reasoning><answer>ML is...</answer>',
            ...     ReasoningMode.BASIC
            ... )
        """
        if mode == ReasoningMode.NONE:
            # No reasoning expected, entire response is the answer
            return self._parse_direct_answer(raw_response)

        # Try XML-style parsing first (most structured)
        reasoning_text, answer_text = self._extract_sections(raw_response)

        if not reasoning_text:
            # Fallback to regex patterns
            reasoning_text, answer_text = self._extract_with_regex(raw_response)

        if not reasoning_text:
            # No reasoning found, treat as direct answer
            logger.warning(f"No reasoning found for mode {mode}, using direct answer")
            return self._parse_direct_answer(raw_response)

        # Parse reasoning steps based on mode
        steps = self._parse_reasoning_steps(reasoning_text, mode)

        # Extract citations from answer
        citations = self._extract_citations(answer_text)

        # Validate reasoning
        flags = self._validate_reasoning(steps, answer_text)

        # Calculate overall confidence
        confidence = self._calculate_confidence(steps, flags)

        return ReasonedResponse(
            answer=answer_text.strip(),
            citations=citations,
            reasoning_steps=steps,
            validation_flags=flags,
            overall_confidence=confidence,
            mode=mode,
            raw_response=raw_response
        )

    def _parse_direct_answer(self, raw_response: str) -> ReasonedResponse:
        """
        Parse response with no reasoning (NONE mode).

        Args:
            raw_response: Raw LLM output

        Returns:
            ReasonedResponse with empty reasoning
        """
        citations = self._extract_citations(raw_response)

        return ReasonedResponse(
            answer=raw_response.strip(),
            citations=citations,
            reasoning_steps=[],
            validation_flags=[],
            overall_confidence=0.5,  # Neutral confidence when no reasoning
            mode=ReasoningMode.NONE,
            raw_response=raw_response
        )

    def _extract_sections(self, text: str) -> tuple[str | None, str]:
        """
        Extract reasoning and answer sections using XML-style tags.

        Args:
            text: Raw LLM response

        Returns:
            Tuple of (reasoning_text, answer_text)
        """
        # Try standard tags first
        reasoning_match = self.xml_reasoning_pattern.search(text)
        answer_match = self.xml_answer_pattern.search(text)

        # Try chain_of_thought tag if no reasoning found
        if not reasoning_match:
            reasoning_match = self.chain_pattern.search(text)

        reasoning = reasoning_match.group(1).strip() if reasoning_match else None
        answer = answer_match.group(1).strip() if answer_match else text

        return reasoning, answer

    def _extract_with_regex(self, text: str) -> tuple[str | None, str]:
        """
        Extract reasoning using regex patterns as fallback.

        Args:
            text: Raw LLM response

        Returns:
            Tuple of (reasoning_text, answer_text)
        """
        # Look for markdown-style sections
        sections = re.split(r'\n##\s+', text)

        reasoning_sections = []
        answer_section = text

        for section in sections:
            section_lower = section.lower()
            if any(keyword in section_lower for keyword in ['reasoning', 'thought', 'analysis']):
                reasoning_sections.append(section)
            elif 'answer' in section_lower:
                # Extract answer content after "Answer" heading
                answer_section = re.sub(r'^[^\n]+\n', '', section, count=1)

        reasoning = '\n\n'.join(reasoning_sections) if reasoning_sections else None
        return reasoning, answer_section.strip()

    def _parse_reasoning_steps(
        self,
        reasoning_text: str,
        mode: ReasoningMode
    ) -> list[ReasoningStep]:
        """
        Parse individual reasoning steps from reasoning text.

        Args:
            reasoning_text: Extracted reasoning section
            mode: Reasoning mode (affects parsing strategy)

        Returns:
            List of ReasoningStep objects
        """
        steps = []

        # Try XML-style step tags first (STRUCTURED mode)
        if mode == ReasoningMode.STRUCTURED:
            xml_steps = self.step_pattern.findall(reasoning_text)
            for number, action, confidence, thought in xml_steps:
                conf = float(confidence) if confidence else 1.0
                evidence = self._extract_evidence_from_text(thought)
                steps.append(ReasoningStep(
                    step_number=int(number),
                    thought=thought.strip(),
                    action=action,
                    confidence=conf,
                    evidence=evidence
                ))

        # Fallback to numbered list parsing
        if not steps:
            numbered_steps = self.numbered_step_pattern.findall(reasoning_text)
            for i, (number, thought) in enumerate(numbered_steps, start=1):
                action = self._infer_action_from_text(thought, i)
                confidence = self._extract_confidence_from_text(thought)
                evidence = self._extract_evidence_from_text(thought)

                steps.append(ReasoningStep(
                    step_number=int(number) if number.isdigit() else i,
                    thought=thought.strip(),
                    action=action,
                    confidence=confidence,
                    evidence=evidence
                ))

        # If still no steps, treat entire reasoning as one step
        if not steps:
            confidence = self._extract_confidence_from_text(reasoning_text)
            evidence = self._extract_evidence_from_text(reasoning_text)
            steps.append(ReasoningStep(
                step_number=1,
                thought=reasoning_text.strip(),
                action="analyze",
                confidence=confidence,
                evidence=evidence
            ))

        return steps

    def _infer_action_from_text(self, text: str, step_number: int) -> str:
        """
        Infer reasoning action type from text content.

        Args:
            text: Step text content
            step_number: Step number for heuristic

        Returns:
            Action type string
        """
        text_lower = text.lower()

        # Keyword-based inference
        if any(kw in text_lower for kw in ['understand', 'question', 'asking', 'identify']):
            return "understand"
        elif any(kw in text_lower for kw in ['retrieve', 'found', 'source', 'evidence']):
            return "retrieve"
        elif any(kw in text_lower for kw in ['analyze', 'examining', 'comparing', 'contradiction']):
            return "analyze"
        elif any(kw in text_lower for kw in ['combine', 'synthesize', 'integrate', 'together']):
            return "synthesize"
        elif any(kw in text_lower for kw in ['conclude', 'therefore', 'final', 'overall']):
            return "conclude"

        # Position-based heuristic
        if step_number == 1:
            return "understand"
        elif step_number <= 3:
            return "analyze"
        else:
            return "synthesize"

    def _extract_confidence_from_text(self, text: str) -> float:
        """
        Extract confidence score from text.

        Args:
            text: Text that may contain confidence statement

        Returns:
            Confidence value (0.0-1.0), defaults to 1.0 if not found
        """
        match = self.confidence_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 1.0

    def _extract_evidence_from_text(self, text: str) -> list[int]:
        """
        Extract citation numbers from text.

        Args:
            text: Text containing [1], [2], etc. citations

        Returns:
            List of citation indices
        """
        matches = self.citation_pattern.findall(text)
        return [int(m) for m in matches]

    def _extract_citations(self, text: str) -> list[str]:
        """
        Extract unique citation numbers from answer.

        Args:
            text: Answer text with [1], [2] style citations

        Returns:
            List of citation strings like "[1]", "[2]"
        """
        matches = self.citation_pattern.findall(text)
        unique_citations = sorted(set(int(m) for m in matches))
        return [f"[{c}]" for c in unique_citations]

    def _validate_reasoning(
        self,
        steps: list[ReasoningStep],
        answer: str
    ) -> list[ValidationFlag]:
        """
        Detect issues in reasoning process.

        Args:
            steps: Reasoning steps to validate
            answer: Final answer text

        Returns:
            List of validation flags for detected issues
        """
        flags = []

        # Check for contradictions
        flags.extend(self._detect_contradictions(steps))

        # Check for uncertainty markers
        flags.extend(self._detect_uncertainty(steps, answer))

        # Check for unsupported claims
        flags.extend(self._detect_unsupported_claims(steps, answer))

        # Check for low confidence steps
        flags.extend(self._detect_low_confidence(steps))

        return flags

    def _detect_contradictions(self, steps: list[ReasoningStep]) -> list[ValidationFlag]:
        """
        Detect contradictory statements in reasoning.

        Args:
            steps: Reasoning steps

        Returns:
            Validation flags for contradictions
        """
        flags = []

        # Look for explicit contradiction keywords
        contradiction_keywords = ['however', 'but', 'contradicts', 'disagrees', 'conflicts']

        for step in steps:
            text_lower = step.thought.lower()
            if any(kw in text_lower for kw in contradiction_keywords):
                flags.append(ValidationFlag(
                    type="contradiction",
                    description=f"Potential contradiction in step {step.step_number}",
                    severity="medium",
                    step_numbers=[step.step_number]
                ))

        return flags

    def _detect_uncertainty(
        self,
        steps: list[ReasoningStep],
        answer: str
    ) -> list[ValidationFlag]:
        """
        Detect uncertainty markers in reasoning or answer.

        Args:
            steps: Reasoning steps
            answer: Final answer

        Returns:
            Validation flags for uncertainty
        """
        flags = []

        uncertainty_markers = [
            'unclear', 'uncertain', 'not sure', 'possibly', 'might',
            'may be', 'perhaps', 'cannot determine', 'insufficient'
        ]

        # Check steps
        for step in steps:
            text_lower = step.thought.lower()
            if any(marker in text_lower for marker in uncertainty_markers):
                flags.append(ValidationFlag(
                    type="uncertainty",
                    description=f"Uncertainty expressed in step {step.step_number}",
                    severity="medium",
                    step_numbers=[step.step_number]
                ))

        # Check answer
        answer_lower = answer.lower()
        if any(marker in answer_lower for marker in uncertainty_markers):
            flags.append(ValidationFlag(
                type="uncertainty",
                description="Uncertainty expressed in final answer",
                severity="high",
                step_numbers=[]
            ))

        return flags

    def _detect_unsupported_claims(
        self,
        steps: list[ReasoningStep],
        answer: str
    ) -> list[ValidationFlag]:
        """
        Detect claims without supporting citations.

        Args:
            steps: Reasoning steps
            answer: Final answer

        Returns:
            Validation flags for unsupported claims
        """
        flags = []

        # Check if answer has any citations
        citations = self._extract_citations(answer)
        if not citations and len(answer) > 100:  # Non-trivial answer
            flags.append(ValidationFlag(
                type="missing_evidence",
                description="Answer lacks citations to support claims",
                severity="high",
                step_numbers=[]
            ))

        return flags

    def _detect_low_confidence(self, steps: list[ReasoningStep]) -> list[ValidationFlag]:
        """
        Detect steps with low confidence scores.

        Args:
            steps: Reasoning steps

        Returns:
            Validation flags for low confidence
        """
        flags = []

        for step in steps:
            if step.confidence < 0.5:
                flags.append(ValidationFlag(
                    type="low_confidence",
                    description=f"Step {step.step_number} has low confidence ({step.confidence:.2f})",
                    severity="medium",
                    step_numbers=[step.step_number]
                ))

        return flags

    def _calculate_confidence(
        self,
        steps: list[ReasoningStep],
        flags: list[ValidationFlag]
    ) -> float:
        """
        Calculate overall confidence from steps and validation.

        Args:
            steps: Reasoning steps with confidence scores
            flags: Validation flags detected

        Returns:
            Overall confidence score (0.0-1.0)
        """
        if not steps:
            return 0.5  # Neutral

        # Average confidence across steps
        avg_confidence = sum(s.confidence for s in steps) / len(steps)

        # Penalise for high-severity flags
        penalty = 0.0
        for flag in flags:
            if flag.severity == "high":
                penalty += 0.2
            elif flag.severity == "medium":
                penalty += 0.1

        # Apply penalty (min 0.0)
        final_confidence = max(0.0, avg_confidence - penalty)

        return round(final_confidence, 2)
