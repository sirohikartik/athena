import ollama

def ask(prompt: str, model: str = "gpt-oss:20b-cloud", stream: bool = True):
    try:
        if not stream:
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]

        # streaming mode
        stream_resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )


        for chunk in stream_resp:
            token = chunk["message"]["content"]
            print(token, end="", flush=True)


        print()
        return "-"*100

    except Exception as e:
        return f"Error: {e}"
