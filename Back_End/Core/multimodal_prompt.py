import json
import os

from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

_groq_api_key = os.getenv("GROQ_API_KEY")
_groq_model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
_groq_client = None


def _get_groq_client():
    global _groq_client

    if not _groq_api_key:
        raise RuntimeError("Thiếu GROQ_API_KEY trong .env.")

    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=_groq_api_key)

    return _groq_client


class MultimodalPromptTransformer:
    def __init__(self):
        self.model_name = _groq_model_name

    async def transform(self, text_prompt: str, image_url: str) -> dict:
        prompt = (text_prompt or "").strip()
        image = (image_url or "").strip()

        if not prompt:
            raise ValueError("Text prompt is required.")
        if not image:
            raise ValueError("Image URL is required.")

        system_prompt = """
        You transform a Vietnamese user's text + food/menu image into a concise Vietnamese text prompt for a restaurant recommendation pipeline.

        Return ONLY valid JSON:
        {
          "transformed_prompt": "...",
          "image_summary": "...",
          "confidence": 0.0
        }

        Rules:
        - The transformed_prompt will be passed to routing/search. It must be useful, concise, and in Vietnamese.
        - Preserve and combine BOTH information sources: the user's text prompt and the image content. The text prompt defines the user's intent; the image adds dish/menu/store evidence. If they conflict, keep the user's intent and mention the image finding cautiously.
        - Do not answer the user directly.
        - If the image is a menu: extract the most relevant readable dish/drink names and include them in the prompt. Do not list too many items; keep 5-12 clear items maximum.
        - If the user asks "Tôi nên ăn món nào" with a menu image, transform into: "Tôi nên ăn món nào trong những món trong menu sau đây: ..."
        - If the image is a dish: identify the most likely dish/drink. If uncertain, mention "có vẻ là". Transform search intent into: "Tôi muốn ăn món ...".
        - When a recognized dish clearly implies a restaurant venue type, add that type naturally to transformed_prompt, but ONLY choose from this allowed list: "Quán Việt", "Quán Chay", "Quán Thái", "Quán nước", "Quán Nhật", "Quán Âu", "Tiệm bánh".
        - Do NOT force a venue type. Leave type unstated if the dish/menu is ambiguous or no allowed type fits confidently.
        - Venue type examples:
          * bánh gato, bánh kem, croissant, bánh ngọt -> "Tiệm bánh"
          * mì Ý, pizza, pasta, steak, burger kiểu Âu -> "Quán Âu"
          * sushi, sashimi, ramen, udon, takoyaki -> "Quán Nhật"
          * pad Thái, tom yum, som tam -> "Quán Thái"
          * phở, bún bò, cơm tấm, bánh mì, bún chả -> "Quán Việt"
          * trà sữa, cà phê, nước ép, sinh tố, đồ uống -> "Quán nước"
          * món chay rõ ràng, cơm chay, bún chay, lẩu chay -> "Quán Chay"
        - Format examples for transformed_prompt:
          * User asks "Tìm quán ăn có món này", image is bánh gato -> "Tôi muốn ăn bánh gato ở Tiệm bánh."
          * User asks "Tìm quán ăn có món này", image is mì Ý -> "Tôi muốn ăn mì Ý ở Quán Âu."
          * User asks "Tối nay ăn món này", image is sushi -> "Tối nay tôi muốn ăn sushi ở Quán Nhật."
          * User asks "Tôi nên ăn món nào", image is a menu -> "Tôi nên ăn món nào trong những món trong menu sau đây: ..."
        - If the image is a restaurant/storefront/ambience: describe visible cuisine, allowed venue type if clear, vibe, and constraints briefly.
        - If OCR/recognition is uncertain, keep confidence lower and use cautious wording. Do not invent exact dish names that are not visible or likely.
        - Do not include markdown. Do not include beta warnings in transformed_prompt.
        """

        user_text = f"""
        User text prompt: {prompt}

        Analyze the attached image and produce the transformed prompt.
        """

        completion = await _get_groq_client().chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": image}},
                    ],
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw_content = completion.choices[0].message.content or "{}"
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError:
            data = {
                "transformed_prompt": f"{prompt}. Dựa thêm trên nội dung ảnh: {raw_content[:500]}",
                "image_summary": raw_content[:500],
                "confidence": 0.4,
            }
        transformed_prompt = str(data.get("transformed_prompt") or "").strip()

        if not transformed_prompt:
            transformed_prompt = prompt

        return {
            "transformed_prompt": transformed_prompt,
            "image_summary": str(data.get("image_summary") or "").strip(),
            "confidence": data.get("confidence"),
        }
