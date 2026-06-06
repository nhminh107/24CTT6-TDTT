import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

_client = AsyncGroq(
    api_key=GROQ_API_KEY
)


class ChatBot(): 
    def __init__(self):
        self.client = _client
        self.routing_model_name = "llama-3.3-70b-versatile"

    async def routing(self, user_prompt):
        system_prompt = """
        You are a routing assistant for a food and health system. 
        Classify the user prompt into one of two intents: "QA" or "Search".
        - "QA": General questions about food, culinary culture, health, or the system itself.
        - "Search": Intent to find specific restaurants, food places, or eating recommendations.

        If the intent is "Search", you must also provide a field "isPoorInfo":
        - isPoorInfo = 1: If the prompt is too vague or lacks enough context to perform a meaningful search (e.g., just one or two words like "cay", "mặn", "đắt", "ngon" without any other intent).
        - isPoorInfo = 0: If the prompt has enough information to understand the basic requirement (e.g., "Tìm quán ăn sáng", "Ăn gì ở quận 1", "Quán phở gần đây").

        Return ONLY a JSON object in the following format:
        {
            "user_intent": "QA" | "Search",
            "isPoorInfo": 0 | 1  // Only included if user_intent is "Search"
        }
        """

        completion = await self.client.chat.completions.create(
            model=self.routing_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        return completion.choices[0].message.content

if __name__ == "__main__": 
    cb = ChatBot() 
    print(cb.routing("tìm quán ngon gần đây"))


