import os
from litellm import completion

# Ensure GEMINI API key exists
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY not set in environment!")

LLM_MODEL = "gemini-1.5-flash"

def llm_call(prompt):
    response = completion(
        model=LLM_MODEL,
        api_key=GEMINI_KEY,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]
