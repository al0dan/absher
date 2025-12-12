"""
AI Service for Contract Generation
Supports: ALLaM (SDAIA's sovereign Arabic AI), Groq, and fallback templates.

ALLaM Access Options:
1. Hugging Face Inference API (Free tier available)
2. Azure AI Studio (Requires Azure subscription)
3. Groq API (Fast inference, may not have ALLaM directly)
"""
import os
import requests
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# API Keys
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
KIMI_API_KEY = os.getenv('KIMI_API_KEY')

# ALLaM-2-7B is available directly on Groq (SDAIA's sovereign Arabic AI)
ALLAM_MODEL_GROQ = "allam-2-7b"  # SDAIA ALLaM on Groq
ALLAM_MODEL_HF = "sdaia/allam-1-7b-instruct"  # HuggingFace backup
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"  # Fallback if ALLaM fails


def generate_with_allam_hf(prompt_system: str, prompt_user: str) -> str:
    """Generate contract using ALLaM via Hugging Face Inference API."""
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY not set")
    
    # Format prompt for instruction-tuned model
    full_prompt = f"""<s>[INST] <<SYS>>
{prompt_system}
<</SYS>>

{prompt_user} [/INST]"""
    
    start_time = time.time()
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{ALLAM_MODEL}",
        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
        json={
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 2000,
                "temperature": 0.2,
                "do_sample": True,
                "return_full_text": False
            }
        },
        timeout=60  # HF inference can be slow
    )
    response.raise_for_status()
    
    duration = time.time() - start_time
    result = response.json()
    
    if isinstance(result, list) and len(result) > 0:
        generated_text = result[0].get('generated_text', '')
        logger.info(f"ALLaM (HuggingFace) generation successful in {duration:.2f}s")
        return generated_text
    
    raise ValueError(f"Unexpected response format: {result}")


def clean_ai_output(text: str) -> str:
    """
    Aggressively clean AI-generated contract text.
    ALLaM-2-7B (7B params) tends to repeat signature blocks - we truncate after the FIRST one.
    """
    if not text:
        return text
    
    # FIRST: Find the FIRST occurrence of signature/ending patterns and CUT there
    first_end_markers = [
        "والله ولي التوفيق",
        "توقيع الطرف الأول:",
        "توقيع المورد:",
        "الممثل المعتمد لشركة",
        "[اسم الممثل المعتمد",
        "تم إبرام هذا العقد في مدينة",
        "تم التوقيع على هذا العقد"
    ]
    
    best_cut_pos = len(text)
    
    for marker in first_end_markers:
        pos = text.find(marker)
        if pos != -1:
            # Find end of this section (next double newline or reasonable length after marker)
            after_marker = pos + len(marker)
            next_para = text.find('\n\n', after_marker)
            
            # For "والله ولي التوفيق", include a short signature section after
            if marker == "والله ولي التوفيق":
                # Allow up to 500 chars after for signatures, then cut
                cut_point = min(after_marker + 500, next_para if next_para != -1 else after_marker + 500)
            else:
                # For other markers, include the line and one more paragraph
                cut_point = next_para if next_para != -1 else after_marker + 200
            
            if cut_point < best_cut_pos:
                best_cut_pos = cut_point
    
    # Cut at the best position found
    if best_cut_pos < len(text):
        text = text[:best_cut_pos].strip()
    
    # SECOND: Remove duplicate lines (ALLaM likes to repeat)
    lines = text.split('\n')
    unique_lines = []
    seen = set()
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            unique_lines.append(line)
            continue
        
        # Skip exact duplicates
        if stripped in seen:
            continue
        
        seen.add(stripped)
        unique_lines.append(line)
    
    text = '\n'.join(unique_lines).strip()
    
    # THIRD: Remove trailing garbage (lines ending with : or [ )
    lines = text.split('\n')
    while lines and (lines[-1].strip().endswith(':') or lines[-1].strip().endswith('[')):
        lines.pop()
    
    return '\n'.join(lines).strip()


def generate_with_groq(prompt_system: str, prompt_user: str) -> str:
    """Generate contract using Groq API with ALLaM-2-7B (SDAIA's Sovereign Arabic AI)."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    
    # ONLY USE ALLAM - SDAIA's Sovereign Arabic AI (Required for Hackathon)
    # NO FALLBACK - If ALLaM fails, we want to know immediately
    candidate_models = ["allam-2-7b"]
    
    logger.info("🇸🇦 Using ALLaM-2-7B (SDAIA Sovereign Arabic AI) for contract generation")
    
    start_time = time.time()
    
    for model in candidate_models:
        try:
            logger.info(f"Attempting Groq generation with model: {model}")
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': prompt_system},
                        {'role': 'user', 'content': prompt_user}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 1500,  # Reduced to prevent ALLaM repetition
                    'stop': ['###', '---END---', 'شهادة المنشأ:', 'شهادة التأمين:', 'بسم الله الرحمن الرحيم\nتم التوقيع']
                },
                timeout=30  # Increased timeout for larger responses
            )
            response.raise_for_status()
            
            duration = time.time() - start_time
            raw_result = response.json()['choices'][0]['message']['content']
            cleaned_result = clean_ai_output(raw_result)
            
            logger.info(f"Groq generation successful with {model} in {duration:.2f}s (raw: {len(raw_result)}, cleaned: {len(cleaned_result)} chars)")
            return cleaned_result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Model {model} not found on Groq, trying next...")
                continue
            logger.warning(f"Groq error with {model}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Groq attempt failed for {model}: {e}")
            continue

    raise ValueError("All Groq models failed")


def generate_with_kimi(prompt_system: str, prompt_user: str) -> str:
    """Generate contract using Kimi (Moonshot) API."""
    if not KIMI_API_KEY:
        raise ValueError("KIMI_API_KEY not set")
    
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
        timeout=30
    )
    response.raise_for_status()
    
    duration = time.time() - start_time
    logger.info(f"Kimi generation successful in {duration:.2f}s")
    return response.json()['choices'][0]['message']['content']


def get_template_contract(supplier: str, buyer: str, items: str, price: str) -> str:
    """Return a template contract when AI is unavailable."""
    return f'''بسم الله الرحمن الرحيم

عقد توريد

تم الاتفاق في {datetime.now().strftime('%Y/%m/%d')} بين:

الطرف الأول (المورد): {supplier}
الطرف الثاني (المشتري): {buyer}

البند الأول - موضوع العقد:
يلتزم الطرف الأول بتوريد المواد التالية:
{items}
وفقاً للمواصفات والمعايير القياسية المعتمدة.

البند الثاني - القيمة:
القيمة الإجمالية للعقد: {price} ريال سعودي
تُدفع عند استلام البضائع والتحقق من مطابقتها للمواصفات.

البند الثالث - مدة التوريد:
يلتزم الطرف الأول بالتوريد خلال المدة المتفق عليها.

البند الرابع - الضمانات:
يضمن الطرف الأول جودة المنتجات لمدة سنة من تاريخ التسليم.

البند الخامس - القانون الواجب التطبيق:
يخضع هذا العقد لأحكام نظام المعاملات المدنية السعودي الصادر بالمرسوم الملكي رقم م/191.

البند السادس - فض النزاعات:
في حال نشوء أي خلاف، يتم اللجوء أولاً للتسوية الودية، وإلا فالمحاكم السعودية المختصة.

تحرر هذا العقد من نسختين لكل طرف نسخة للعمل بموجبها.
'''


def generate_contract_ai(supplier: str, buyer: str, items: str, price: str, contract_type: str = 'supply') -> str:
    """
    Generate an Arabic legal contract using AI.
    
    Priority:
    1. ALLaM-2-7B (SDAIA's sovereign AI)
    2. Llama 3.3 (Fallback)
    
    Contract Types:
    - supply (توريد)
    - nda (عدم إفصاح)
    - service (خدمات)
    - rental (إيجار)
    """
    
    # Base system prompt for Saudi legal context
    system_base = '''أنت محامي سعودي خبير متخصص في صياغة العقود التجارية.
مهمتك إنشاء عقد رسمي وقانوني يتوافق مع:
- نظام المعاملات المدنية السعودي (المرسوم الملكي م/191)
- أحكام الشريعة الإسلامية

تعليمات مهمة:
- ابدأ العقد بـ "بسم الله الرحمن الرحيم"
- اكتب بلغة عربية فصحى رسمية.
- اكتب العقد بشكل منظم في مواد مرقمة.
- انتهِ العقد بجملة "والله ولي التوفيق" ثم التواقيع فقط.
- لا تكتب أي شيء بعد قسم التواقيع.
- لا تذكر "شهادات" أو حقول فارغة بعد العقد.
'''

    # Specific instructions by type
    if contract_type == 'nda':
        prompt_system = system_base + '''
النوع: اتفاقية عدم إفصاح (NDA)
ركز على:
- تعريف المعلومات السرية بدقة.
- التزامات الطرف المتلقي.
- الاستثناءات من السرية.
- مدة السرية (عادة 3-5 سنوات).
- العقوبات والتعويض في حال الإخلال.'''
        
        prompt_user = f'''أنشئ اتفاقية عدم إفصاح بين:
- الطرف المفصح: {supplier}
- الطرف المتلقي: {buyer}
- نطاق المعلومات السرية: {items}
- مدة الاتفاقية: {price} سنوات (أو المدة المذكورة)

اكتب اتفاقية محكمة تحمي أسرار العمل.'''

    elif contract_type == 'service':
        prompt_system = system_base + '''
النوع: عقد تقديم خدمات
ركز على:
- نطاق الخدمات بوضوح.
- الجدول الزمني للتنفيذ.
- معايير الجودة والأداء.
- آلية الدفع والاستلام.
- الملكية الفكرية للمخرجات.'''
        
        prompt_user = f'''أنشئ عقد تقديم خدمات بين:
- مقدم الخدمة: {supplier}
- العميل: {buyer}
- تفاصيل الخدمات: {items}
- قيمة العقد: {price} ريال سعودي

اكتب عقداً يضمن حقوق الطرفين ووضوح المخرجات.'''

    elif contract_type == 'rental':
        prompt_system = system_base + '''
النوع: عقد إيجار (معدات أو عقار تجاري)
ركز على:
- وصف العين المؤجرة.
- مدة الإيجار وشروط التجديد.
- قيمة الإيجار وطريقة السداد.
- التزامات الصيانة والتشغيل.
- حالة العين عند الإعادة.'''
        
        prompt_user = f'''أنشئ عقد إيجار بين:
- المؤجر: {supplier}
- المستأجر: {buyer}
- وصف العين المؤجرة: {items}
- قيمة الإيجار السنوي/الشهري: {price} ريال سعودي

اكتب عقداً يحدد بوضوح التزامات الطرفين.'''

    else: # Default: Supply
        prompt_system = system_base + '''
النوع: عقد توريد بضائع
ركز على:
- مواصفات البضائع وجودتها.
- موعد ومكان التسليم.
- شروط الفحص والقبول.
- الضمانات (عيوب التصنيع).'''
        
        prompt_user = f'''أنشئ عقد توريد رسمي بين:
- المورد: {supplier}
- المشتري: {buyer}
- المواد المطلوبة: {items}
- القيمة الإجمالية: {price} ريال سعودي

اكتب عقداً شاملاً يحمي حقوق الطرفين.'''

    # Try providers in order
    providers = [
        ('Groq', lambda: generate_with_groq(prompt_system, prompt_user)),
        ('Kimi', lambda: generate_with_kimi(prompt_system, prompt_user)),
    ]
    
    for name, generator in providers:
        try:
            result = generator()
            if result and len(result) > 100:  # Sanity check
                return result
        except Exception as e:
            logger.warning(f"{name} failed: {e}")
            continue
    
    # All providers failed, use template
    logger.info("All AI providers failed, using template")
    return get_template_contract(supplier, buyer, items, price)
