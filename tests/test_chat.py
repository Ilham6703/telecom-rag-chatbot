from app.services.chat import ChatService


def test_session_memory_persists_within_same_session():
    session_a = "session-1"

    first = ChatService(session_id=session_a)
    first.memory.add_user_message("ok my name is ilham")
    first.memory.add_assistant_message("Hello Ilham! How can I assist you today?")

    second = ChatService(session_id=session_a)
    history = second.memory.get_history()

    assert history[-2:] == [
        {"role": "user", "content": "ok my name is ilham"},
        {"role": "assistant", "content": "Hello Ilham! How can I assist you today?"},
    ]


def test_session_memory_is_isolated_between_sessions():
    session_a = "session-1"
    session_b = "session-2"

    first = ChatService(session_id=session_a)
    first.memory.add_user_message("ok my name is ilham")
    first.memory.add_assistant_message("Hello Ilham! How can I assist you today?")

    other = ChatService(session_id=session_b)
    history = other.memory.get_history()

    assert history == []
