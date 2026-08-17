"""
LLM Router

Responsibilities
----------------
Classify whether a user query requires knowledge base retrieval.

Returns only one of:

- GENERAL
- KNOWLEDGE
"""

from __future__ import annotations

from openai import OpenAI

from app.config.settings import settings


class Router:
    """
    LLM-based intent router.
    """

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        self.model = settings.OPENAI_CHAT_MODEL

        self.system_prompt = """
You are an intent classifier.

Your task is ONLY to classify the user's query.

Return EXACTLY one word.

GENERAL
or
KNOWLEDGE

GENERAL:
- Greetings
- Small talk
- Identity questions
- Capability questions
- Thank you
- Goodbye

KNOWLEDGE:
- Any question requiring information from the provided 3GPP telecom documentation.
- Technical telecom questions.
- Follow-up questions about previous telecom answers.

Never explain.

Never answer the question.

Return only GENERAL or KNOWLEDGE.
"""

    # ---------------------------------------------------------

    def route(
        self,
        query: str,
    ) -> str:
        """
        Returns:
            GENERAL
            KNOWLEDGE
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
        )

        decision = (
            response.choices[0]
            .message.content.strip()
            .upper()
        )

        if not decision or decision not in {
            "GENERAL",
            "KNOWLEDGE",
        }:
            return "GENERAL"

        return decision