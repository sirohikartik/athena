from utils import model

SYSTEM_PROMPT = """You are Athena, a precise and knowledgeable AI assistant.

You will be given:
- CONTEXT: Fresh information retrieved from the web for the current question.
- HISTORY: A summary of what the user has asked before (may be empty).
- QUESTION: The user's current question.

Rules:
- Answer using the CONTEXT as your primary source of truth.
- Use HISTORY only if it helps clarify the current question.
- Give a clear, direct, well-structured answer.
- Do not say "the context states" or "based on the provided text" — answer as yourself.
- Do not say you lack information if the CONTEXT clearly contains it.
- If the CONTEXT genuinely does not cover the question, say so briefly and share what you do know.
- Never hallucinate facts.
"""


def agent(context: str, question: str, history: str = "", model_name: str = model.DEFAULT_MODEL) -> str:
    history_block = f"HISTORY:\n{history.strip()}\n\n" if history.strip() else ""

    prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"{history_block}"
        f"CONTEXT:\n{context.strip()}\n\n"
        f"QUESTION:\n{question.strip()}\n\n"
        f"ANSWER:"
    )

    return model.ask(prompt, model_name)
