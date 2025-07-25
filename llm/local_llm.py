import subprocess

OLLAMA_PATH = r"C:\Users\jammy\AppData\Local\Programs\Ollama\ollama.exe"
MODEL_NAME = 'mistral'

def query_llm(prompt: str) -> str:
    try:
        result = subprocess.run(
            [OLLAMA_PATH, 'run', MODEL_NAME],
            input=prompt.encode('utf-8'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10000
        )
        output = result.stdout.decode('utf-8')
        return output.strip()
    except subprocess.TimeoutExpired:
        return "The model took too long to respond."
    except Exception as e:
        return f"Error during model execution: {e}"
