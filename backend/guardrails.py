import re
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from models import ModerationResult
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    GuardrailFunctionOutput,
    InputGuardrail,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

load_dotenv(override=True)

# Patterns for detecting sensitive information
SENSITIVE_PATTERNS = {
    "api_key": r"(?i)(api[_-]?key|apikey)[\s:=]+['\"]?([a-zA-Z0-9_\-]{20,})",
    "password": r"(?i)(password|passwd|pwd)[\s:=]+['\"]?([^\s\"']{6,})",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
}

# Harmful content keywords (basic implementation)
HARMFUL_KEYWORDS = [
    "hack",
    "exploit",
    "illegal",
    "bomb",
    "weapon",
    "steal",
    "pirate",
    "crack password",
    "bypass security",
]


class GuardrailsManager:
    """
    Manages all guardrails for the AI assistant.

    This class checks user input and AI output for:
    1. Harmful content (hate speech, violence, illegal activities)
    2. Sensitive data (API keys, passwords, SSNs, credit cards)
    3. Token limits to prevent excessive API usage
    """

    def __init__(
        self,
        moderation_agent: Agent,
        max_tokens: int = 400,
    ):
        """
        Initialize the guardrails manager.

        Args:
            max_tokens: Maximum tokens allowed per request (default: 400)
        """
        self.max_tokens = max_tokens

        self.moderation_agent = moderation_agent

    def check_sensitive_data(self, text: str) -> dict[str, Any]:
        """
        Check if text contains sensitive information like API keys, passwords, etc.

        Args:
            text: The text to check

        Returns:
            Dict with 'found' (bool) and 'types' (list of detected sensitive data types)
        """
        found_types = []

        for data_type, pattern in SENSITIVE_PATTERNS.items():
            if re.search(pattern, text):
                found_types.append(data_type)

        return {"found": len(found_types) > 0, "types": found_types}

    def check_harmful_content(self, text: str) -> dict[str, Any]:
        """
        Basic keyword-based check for potentially harmful requests.

        Args:
            text: The text to check

        Returns:
            Dict with 'is_harmful' (bool) and 'matched_keywords' (list)
        """
        text_lower = text.lower()
        matched = [kw for kw in HARMFUL_KEYWORDS if kw in text_lower]

        return {"is_harmful": len(matched) > 0, "matched_keywords": matched}

    async def moderate_content(
        self, text: str, context: str = "user_input"
    ) -> ModerationResult:
        """
        Use LLM to moderate content for safety.

        This is more sophisticated than keyword matching and can understand context.

        Args:
            text: The content to moderate
            context: Either 'user_input' or 'ai_output'

        Returns:
            ModerationResult indicating if content is safe
        """

        token_limit_check = self.check_token_limit(text)

        if not token_limit_check["within_limit"]:
            return ModerationResult(
                is_safe=False,
                reason=f"Your input is above the limit of {self.max_tokens} words!",
                category="token_limit",
            )
        # First, check basic patterns
        sensitive_check = self.check_sensitive_data(text)
        if sensitive_check["found"]:
            return ModerationResult(
                is_safe=False,
                reason=f"Contains sensitive data: {', '.join(sensitive_check['types'])}",
                category="sensitive_data",
            )

        harmful_check = self.check_harmful_content(text)
        if harmful_check["is_harmful"]:
            return ModerationResult(
                is_safe=False,
                reason=f"Contains potentially harmful keywords: {', '.join(harmful_check['matched_keywords'])}",
                category="harmful_content",
            )

        prompt = f"""Analyze this {context} for safety concerns:
                {text}
                Respond with whether it's safe to process."""

        result = await Runner.run(self.moderation_agent, prompt)
        if isinstance(result.final_output, str):
            return ModerationResult.model_validate_json(result.final_output)
        return ModerationResult.model_validate(result.final_output)

    def check_token_limit(self, text: str) -> dict[str, Any]:
        """
        Rough estimate of token count (4 chars ≈ 1 token).

        Args:
            text: The text to check

        Returns:
            Dict with 'within_limit' (bool) and 'estimated_tokens' (int)
        """
        estimated_tokens = len(text) // 4

        return {
            "within_limit": estimated_tokens <= self.max_tokens,
            "estimated_tokens": estimated_tokens,
            "max_tokens": self.max_tokens,
        }


def get_digital_twin_agent_guardrails(
    input_moderation_agent: Agent,
) -> list[InputGuardrail[Any]]:

    @input_guardrail(run_in_parallel=False)
    async def input_moderation_guardrail(
        ctx: RunContextWrapper[None],
        agent: Agent,
        input: str | list[TResponseInputItem],
    ) -> GuardrailFunctionOutput:
        moderation_input = str(
            input if isinstance(input, str) else input[-1].get("content", "")
        )
        if not moderation_input:
            raise ValueError("Input moderation received no message to evaluate")

        guardrails_manager = GuardrailsManager(input_moderation_agent)

        moderation_result = await guardrails_manager.moderate_content(
            moderation_input, context="user_input"
        )
        return GuardrailFunctionOutput(
            output_info=moderation_result,
            tripwire_triggered=(not moderation_result.is_safe),
        )

    return [input_moderation_guardrail]
