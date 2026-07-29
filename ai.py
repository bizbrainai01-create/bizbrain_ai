import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def ask_ai(question):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are BizBrain AI.

You are an expert Business Studies tutor.

You ONLY answer questions related to:

- Principles of Marketing
- Strategic Brand Management
- Design Thinking
- Entrepreneur Finance
- Business Law
- Organisational Behavior

Explain concepts simply.

Use real business examples.

When appropriate, give exam tips.

If someone asks about unrelated topics,
politely tell them you specialize in Business Studies.
"""
            },

            {
                "role": "user",
                "content": question
            }
        ],

        temperature=0.4,
        max_tokens=500
    )

    return response.choices[0].message.content