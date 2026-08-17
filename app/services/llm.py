"""
LLM Service

Responsibilities
----------------
- Communicate with GPT-4o
- Generate grounded responses

Does NOT:
- Retrieve documents
- Manage memory
- Route requests
- Load prompts
"""

from __future__ import annotations

from collections.abc import Iterator

from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI

from app.config.settings import settings


class LLMService:
    """
    Wrapper around OpenAI Chat Completions API.
    """

    def __init__(self):

        self.client = wrap_openai(
            OpenAI(
                api_key=settings.OPENAI_API_KEY
            )
        )

        self.model = settings.OPENAI_CHAT_MODEL

    # ---------------------------------------------------------

    @traceable(name="LLMService.generate")
    def generate(
        self,
        messages: list[dict],
    ) -> str:
        """
        Generate a response from GPT-4o.

        Parameters
        ----------
        messages : list[dict]
            Standard OpenAI chat messages.

        Returns
        -------
        str
            Assistant response.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=messages,
        )

        return response.choices[0].message.content.strip()

    def generate_stream(
        self,
        messages: list[dict],
    ) -> Iterator[str]:
        """Stream the model response as it is generated."""

        stream = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta