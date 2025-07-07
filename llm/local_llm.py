import subprocess

def query_llm(prompt: str) -> str:
    """
    Runs the Phi model via Ollama and returns its response.
    Assumes 'phi' model has been pulled with `ollama pull phi`.
    """
    try:
        result = subprocess.run(
            ['ollama', 'run', 'phi'],
            input=prompt.encode('utf-8'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )
        output = result.stdout.decode('utf-8')
        return output.strip()
    except subprocess.TimeoutExpired:
        return "The model took too long to respond."
    except Exception as e:
        return f"Error during model execution: {e}"
