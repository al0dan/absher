import os
import requests
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# AI Configuration: ALLaM via Groq (primary), Kimi (fallback)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
KIMI_API_KEY = os.getenv('KIMI_API_KEY')
AI_MODEL = os.getenv('AI_MODEL', 'allam-2-7b')

def generate_contract_ai(supplier, buyer, items, price):
    prompt_system = 'أنت محامي سعودي متخصص. أنشئ عقد توريد رسمي وقانوني حسب الأنظمة السعودية. ابدأ بـ بسم الله الرحمن الرحيم.'
    prompt_user = f'عقد توريد بين {supplier} (مورد) و {buyer} (مشتري) لتوريد: {items} بقيمة {price} ريال.'
    
    # Try ALLaM via Groq first (Sovereign AI)
    if GROQ_API_KEY:
        try:
            start_time = time.time()
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': AI_MODEL,
                    'messages': [
                        {'role': 'system', 'content': prompt_system},
                        {'role': 'user', 'content': prompt_user}
                    ],
                    'temperature': 0.2,
                    'max_tokens': 2000
                },
                timeout=15
            )
            response.raise_for_status()
            duration = time.time() - start_time
            logger.info(f"ALLaM Generation successful in {duration:.2f}s")
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"ALLaM/Groq failed: {e}. Trying Kimi fallback.")
    
    # Fallback to Kimi
    if KIMI_API_KEY:
        try:
            start_time = time.time()
            response = requests.post(
                'https://api.moonshot.cn/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {KIMI_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'moonshot-v1-8k',
                    'messages': [
                        {'role': 'system', 'content': prompt_system},
                        {'role': 'user', 'content': prompt_user}
                    ],
                    'temperature': 0.2,
                    'max_tokens': 2000
                },
                timeout=10
            )
            response.raise_for_status()
            duration = time.time() - start_time
            logger.info(f"Kimi Generation successful in {duration:.2f}s")
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"Kimi failed: {e}. Using template.")
    
    logger.info("No AI available, using template.")
    return f'''بسم الله الرحمن الرحيم

عقد توريد (نموذج قياسي)

تم الاتفاق في {datetime.now().strftime('%Y/%m/%d')} بين:
الطرف الأول (المورد): {supplier}
الطرف الثاني (المشتري): {buyer}

البند الأول: يلتزم الطرف الأول بتوريد:
{items}
وفقاً للمواصفات القياسية.

البند الثاني: القيمة الإجمالية للعقد {price} ريال سعودي، تدفع عند الاستلام.

البند الثالث: يخضع هذا العقد للأنظمة المعمول بها في المملكة العربية السعودية.

البند الرابع: يعتبر هذا العقد ساري المفعول بمجرد توقيع الطرفين إلكترونياً عبر منصة أبشر أعمال.
'''
