from groq import Groq

from core.config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)


def generate_response(message: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Groq returned an empty response")

    return content