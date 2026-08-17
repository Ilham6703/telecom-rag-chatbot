"""
Chat Service

Responsibilities
----------------
- Orchestrate the chatbot pipeline
- Route the request
- Retrieve knowledge when required
- Build prompts
- Call the LLM
- Update conversation memory

Does NOT:
- Parse documents
- Generate embeddings
- Store vectors
"""

from pathlib import Path

from app.services.router import Router
from app.services.memory import ConversationMemory
from app.services.llm import LLMService
from app.retrieval.retriever import HybridRetriever
from app.config.settings import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_MEMORIES: dict[str, ConversationMemory] = {}


class ChatService:

    def __init__(self, session_id: str | None = None):

        self.session_id = session_id or "default-session"

        self.router = Router()

        if self.session_id not in SESSION_MEMORIES:
            SESSION_MEMORIES[self.session_id] = ConversationMemory()

        self.memory = SESSION_MEMORIES[self.session_id]

        self.retriever = HybridRetriever()

        self.llm = LLMService()

        self.system_prompt = (
            PROJECT_ROOT
            / "prompts"
            / "system_prompt.txt"
        ).read_text(encoding="utf-8")

    # ---------------------------------------------------------

    def chat(
        self,
        user_query: str,
    ) -> str:
        """
        Main chatbot entry point.
        """

        route = self.router.route(user_query)

        history = self.memory.get_history()

        # -----------------------------------------------------
        # GENERAL CHAT
        # -----------------------------------------------------

        if route == "GENERAL":

            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt,
                }
            ]

            messages.extend(history)

            messages.append(
                {
                    "role": "user",
                    "content": user_query,
                }
            )

            response = self.llm.generate(messages)

        # -----------------------------------------------------
        # KNOWLEDGE QUERY
        # -----------------------------------------------------

        else:

            retrieved_chunks = self.retriever.retrieve(
                user_query
            )

            if not retrieved_chunks:
                response = (
                    "I could not find relevant information in the provided 3GPP documentation."
                )

            else:
                context = "\n\n".join(
                    chunk["text"]
                    for chunk in retrieved_chunks
                )

                messages = [
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    }
                ]

                messages.extend(history)

                messages.append(
                    {
                        "role": "user",
                        "content": f"""
Answer ONLY using the retrieved knowledge.

Question:
{user_query}

Retrieved Context:
{context}
""",
                    }
                )

                response = self.llm.generate(messages)

        # -----------------------------------------------------
        # Update Memory
        # -----------------------------------------------------

        self.memory.add_user_message(user_query)

        self.memory.add_assistant_message(response)

        return response

    def chat_stream(self, user_query: str):
        """Stream chunks for the response while updating memory only after completion."""

        route = self.router.route(user_query)
        history = self.memory.get_history()
        full_response: list[str] = []

        if route == "GENERAL":
            messages = [
                {"role": "system", "content": self.system_prompt},
            ]
            messages.extend(history)
            messages.append({"role": "user", "content": user_query})
            generator = self.llm.generate_stream(messages)
        else:
            retrieved_chunks = self.retriever.retrieve(user_query)
            if not retrieved_chunks:
                message = "I could not find relevant information in the provided 3GPP documentation."
                yield message
                self.memory.add_user_message(user_query)
                self.memory.add_assistant_message(message)
                return

            context = "\n\n".join(chunk["text"] for chunk in retrieved_chunks)
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(history)
            messages.append(
                {
                    "role": "user",
                    "content": f"""
Answer ONLY using the retrieved knowledge.

Question:
{user_query}

Retrieved Context:
{context}
""",
                }
            )
            generator = self.llm.generate_stream(messages)

        for chunk in generator:
            full_response.append(chunk)
            yield chunk

        self.memory.add_user_message(user_query)
        self.memory.add_assistant_message("".join(full_response).strip())