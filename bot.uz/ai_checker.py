import json
import httpx
import logging
from typing import Dict

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = """Sen tajribali o'qituvchisan. O'quvchining uy ishini tekshirib, adolatli baho ber.

Vazifa: {task}
O'quvchi: {student_name}
Uy ishi: {homework}

Faqat quyidagi JSON formatda javob ber (boshqa hech narsa yozma, hech qanday markdown yo'q):
{{
  "score": 75,
  "feedback": "Umumiy baho: 2-3 jumlada asosiy fikr",
  "strengths": "• Birinchi yaxshi joy\\n• Ikkinchi yaxshi joy",
  "weaknesses": "• Birinchi kamchilik\\n• Ikkinchi kamchilik va tavsiya"
}}

Baholash mezonlari (har biri 25 ball):
1. To'liqlik — Vazifa to'liq bajarilganmi?
2. To'g'rilik — Javob to'g'ri va aniqmi?
3. Tushunish — Mavzuni tushunganmi?
4. Sifat — Yozish sifati, ijodiylik"""

class AIChecker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    async def check_homework(
        self,
        task: str,
        homework: str,
        student_name: str,
        custom_prompt: str = None
    ) -> Dict:
        prompt_template = custom_prompt if custom_prompt else DEFAULT_PROMPT
        
        # Agar custom prompt da {task} placeholder bo'lsa ishlatamiz
        if "{task}" in prompt_template and "{homework}" in prompt_template:
            full_prompt = prompt_template.format(
                task=task,
                homework=homework,
                student_name=student_name
            )
        else:
            # Custom prompt ni prefix sifatida ishlatamiz
            full_prompt = f"""{custom_prompt}

Vazifa: {task}
O'quvchi: {student_name}
Uy ishi: {homework}

Faqat JSON formatda javob ber:
{{"score": 0-100, "feedback": "...", "strengths": "...", "weaknesses": "..."}}"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"API xatosi: {response.status_code} — {response.text}")
                raise Exception(f"API xatosi: {response.status_code}")
            
            data = response.json()
            text = data['content'][0]['text'].strip()
            
            # JSON ni tozalash
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            
            # Tekshirish va standartlashtirish
            score = max(0, min(100, int(result.get('score', 50))))
            
            return {
                "score": score,
                "feedback": result.get('feedback', 'Baho berilmadi'),
                "strengths": result.get('strengths', 'Aniqlanmadi'),
                "weaknesses": result.get('weaknesses', 'Aniqlanmadi')
            }