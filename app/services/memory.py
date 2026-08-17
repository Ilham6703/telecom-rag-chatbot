"""
Conversation Memory

Responsibilities
----------------
- Store recent conversation
- Return conversation history
- Keep only the latest N messages

Does NOT:
- Store long-term memory
- Rewrite queries
- Summarize conversations
"""

from collections import deque


class ConversationMemory:
    """
    Short-term conversation memory.
    """

    def __init__(self, max_messages: int = 15):

        self.history = deque(maxlen=max_messages)

    # ---------------------------------------------------------

    def add_user_message(
        self,
        message: str,
    ) -> None:

        self.history.append(
            {
                "role": "user",
                "content": message,
            }
        )

    # ---------------------------------------------------------

    def add_assistant_message(
        self,
        message: str,
    ) -> None:

        self.history.append(
            {
                "role": "assistant",
                "content": message,
            }
        )

    # ---------------------------------------------------------

    def get_history(self) -> list[dict]:

        return list(self.history)

    # ---------------------------------------------------------

    def clear(self) -> None:

        self.history.clear()