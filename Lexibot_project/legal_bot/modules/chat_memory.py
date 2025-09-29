class ChatMemory:
    """Simple conversation memory storing previous QA pairs."""
    def __init__(self, max_history=5):
        self.history = []
        self.max_history = max_history

    def add(self, question, answer):
        self.history.append({"question": question, "answer": answer})
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_context(self):
        """Return concatenated previous conversation as context."""
        context = ""
        for qa in self.history:
            context += f"Q: {qa['question']}\nA: {qa['answer']}\n"
        return context
