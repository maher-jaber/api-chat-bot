# session_store.py
from collections import defaultdict, deque

class SessionMemoryStore:
    def __init__(self, max_memory=10):
        self.sessions = defaultdict(lambda: deque(maxlen=max_memory))

    def get_history(self, session_id):
        return list(self.sessions[session_id])

    def add_message(self, session_id, user_msg, bot_msg):
        self.sessions[session_id].append({"user": user_msg, "bot": bot_msg})
