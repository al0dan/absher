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

# ALLaM-2-7B is available directly on Groq (SDAIA's sovereign Arabic AI)
ALLAM_MODEL_GROQ = "allam-2-7b"  # SDAIA ALLaM on Groq
ALLAM_MODEL_HF = "sdaia/allam-1-7b-instruct"  # HuggingFace backup
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"  # Fallback if ALLaM fails


def _get_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def generate_with_allam_hf(prompt_system: str, prompt_user: str) -> str:
    """Generate contract using ALLaM via Hugging Face Inference API."""
    huggingface_api_key = _get_env('HUGGINGFACE_API_KEY')
    if not huggingface_api_key:
        raise ValueError("HUGGINGFACE_API_KEY not set")
    
    # Format prompt for instruction-tuned model
    full_prompt = f"""<s>[INST] <<SYS>>
{prompt_system}
<</SYS>>

{prompt_user} [/INST]"""
    
    start_time = time.time()
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{ALLAM_MODEL_HF}",
        headers={"Authorization": f"Bearer {huggingface_api_key}"},
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
    Clean AI-generated contract text for ALLaM-2-7B.
    Handles repetition, truncates at proper endings, removes garbage.
    """
    if not text:
        return text

    # Step 1: Remove common AI artifacts
    artifacts = [
        '**', '```', '---', '###', '___',
        '[ملاحظة]', '[ملاحظات]', '[نهاية العقد]',
        'ملاحظة:', 'ملاحظات:', 'المرفقات:',
        'شهادة المنشأ:', 'شهادة التأمين:',
    ]
    for artifact in artifacts:
        text = text.replace(artifact, '')

    # Step 2: Find the FIRST proper ending and cut there
    end_markers = [
        ("والله ولي التوفيق", 300),  # marker, chars to include after
        ("تحرر هذا العقد من نسختين", 150),
        ("توقيع الطرف الأول", 200),
        ("التوقيعات:", 200),
        ("الطرف الأول:", 250),  # Signature section start
    ]

    best_cut = len(text)
    for marker, extra in end_markers:
        pos = text.find(marker)
        if pos != -1:
            cut_point = min(pos + len(marker) + extra, len(text))
            if cut_point < best_cut:
                best_cut = cut_point

    text = text[:best_cut].strip()

    # Step 3: Remove duplicate consecutive lines (ALLaM repetition)
    lines = text.split('\n')
    cleaned_lines = []
    prev_line = None

    for line in lines:
        stripped = line.strip()

        # Allow empty lines
        if not stripped:
            if prev_line != '':
                cleaned_lines.append('')
            prev_line = ''
            continue

        # Skip if exact duplicate of previous non-empty line
        if stripped == prev_line:
            continue

        cleaned_lines.append(line)
        prev_line = stripped

    text = '\n'.join(cleaned_lines)

    # Step 4: Remove duplicate paragraphs (longer repetitions)
    paragraphs = text.split('\n\n')
    seen_paras = set()
    unique_paras = []

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue
        # Use first 50 chars as fingerprint
        fingerprint = para_clean[:50]
        if fingerprint in seen_paras:
            continue
        seen_paras.add(fingerprint)
        unique_paras.append(para)

    text = '\n\n'.join(unique_paras)

    # Step 5: Remove trailing incomplete lines
    lines = text.split('\n')
    while lines:
        last = lines[-1].strip()
        if last.endswith(':') or last.endswith('[') or last.endswith('(') or last == '':
            lines.pop()
        else:
            break

    return '\n'.join(lines).strip()


def generate_with_groq(prompt_system: str, prompt_user: str) -> str:
    """Generate contract using Groq API with ALLaM-2-7B (SDAIA's Sovereign Arabic AI)."""
    groq_api_key = _get_env('GROQ_API_KEY')
    
    # Debug logging
    logger.info(f"🔑 GROQ_API_KEY loaded: {'Yes' if groq_api_key else 'No'} (length: {len(groq_api_key) if groq_api_key else 0})")
    
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not set")

    # ONLY USE ALLAM - SDAIA's Sovereign Arabic AI (Required for Hackathon)
    candidate_models = ["allam-2-7b"]

    logger.info("🇸🇦 Using ALLaM-2-7B (SDAIA Sovereign Arabic AI) for contract generation")

    start_time = time.time()

    for model in candidate_models:
        try:
            logger.info(f"Attempting Groq generation with model: {model}")
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {groq_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': prompt_system},
                        {'role': 'user', 'content': prompt_user}
                    ],
                    'temperature': 0.2,  # Lower for more deterministic output
                    'max_tokens': 1000,  # Reduced to prevent repetition
                    'top_p': 0.9,
                    'stop': [
                        '###',
                        '---',
                        'ملاحظة:',
                        'ملاحظات:',
                        'شهادة المنشأ',
                        'شهادة التأمين',
                        'المرفقات:',
                        'نموذج',
                        '**',
                        'بسم الله الرحمن الرحيم\n\nبسم'  # Prevent restart
                    ]
                },
                timeout=45
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
    kimi_api_key = _get_env('KIMI_API_KEY')
    if not kimi_api_key:
        raise ValueError("KIMI_API_KEY not set")
    
    start_time = time.time()
    response = requests.post(
        'https://api.moonshot.cn/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {kimi_api_key}',
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
    context = _extract_contract_context(items)

    scope = context.get('scope') or ''
    start_date = context.get('start_date')
    duration = context.get('duration')
    payment_terms = context.get('payment_terms')
    extra_clauses = context.get('extra_clauses')

    duration_text = "يلتزم الطرف الأول بالتوريد خلال المدة المتفق عليها."
    if start_date and duration:
        duration_text = f"تبدأ مدة العقد من تاريخ {start_date} ولمدة {duration}، ويلتزم الطرف الأول بالتوريد خلال هذه المدة."
    elif start_date:
        duration_text = f"تبدأ مدة العقد من تاريخ {start_date}، ويلتزم الطرف الأول بالتوريد خلال المدة المتفق عليها."
    elif duration:
        duration_text = f"مدة العقد: {duration}، ويلتزم الطرف الأول بالتوريد خلال هذه المدة."

    payment_text = "تُدفع عند استلام البضائع والتحقق من مطابقتها للمواصفات."
    if payment_terms:
        payment_text = f"تُدفع وفقاً لشروط الدفع المتفق عليها: {payment_terms}."

    extra_section = ""
    if extra_clauses:
        extra_section = f"""

البند السابع - بنود إضافية:
يتفق الطرفان على تضمين البنود الإضافية التالية: {extra_clauses}.
"""

    return f'''بسم الله الرحمن الرحيم

عقد توريد

تم الاتفاق في {datetime.now().strftime('%Y/%m/%d')} بين:

الطرف الأول (المورد): {supplier}
الطرف الثاني (المشتري): {buyer}

البند الأول - موضوع العقد:
يلتزم الطرف الأول بتوريد المواد التالية:
{scope}
وفقاً للمواصفات والمعايير القياسية المعتمدة.

البند الثاني - القيمة:
القيمة الإجمالية للعقد: {price} ريال سعودي
{payment_text}

البند الثالث - مدة التوريد:
{duration_text}

البند الرابع - الضمانات:
يضمن الطرف الأول جودة المنتجات لمدة سنة من تاريخ التسليم.

البند الخامس - القانون الواجب التطبيق:
يخضع هذا العقد لأحكام نظام المعاملات المدنية السعودي الصادر بالمرسوم الملكي رقم م/191.

البند السادس - فض النزاعات:
في حال نشوء أي خلاف، يتم اللجوء أولاً للتسوية الودية، وإلا فالمحاكم السعودية المختصة.{extra_section}

تحرر هذا العقد من نسختين لكل طرف نسخة للعمل بموجبها.
'''


def _extract_contract_context(items: str) -> dict:
    """
    Extract structured context from the UI-packed `items` field.

    Frontend sometimes appends:
    - [ملاحظات AI]: ...
    - --- التفاصيل التعاقدية ---
      تاريخ البداية: ...
      المدة: ...
      شروط الدفع: ...
      البنود الإضافية المطلوبة: ...
    """
    context = {
        'scope': (items or '').strip(),
        'ai_notes': None,
        'start_date': None,
        'duration': None,
        'payment_terms': None,
        'extra_clauses': None,
    }

    if not items or not isinstance(items, str):
        return context

    text = items.strip()

    # Optional AI notes line (expected as first line)
    first_line, *rest = text.splitlines()
    if first_line.strip().startswith('[ملاحظات AI]:'):
        context['ai_notes'] = first_line.split(':', 1)[1].strip() if ':' in first_line else None
        text = '\n'.join(rest).lstrip()

    marker = '--- التفاصيل التعاقدية ---'
    if marker not in text:
        context['scope'] = text.strip()
        return context

    before, after = text.split(marker, 1)
    context['scope'] = before.strip()

    for raw_line in after.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('تاريخ البداية:'):
            context['start_date'] = line.split(':', 1)[1].strip()
        elif line.startswith('المدة:'):
            context['duration'] = line.split(':', 1)[1].strip()
        elif line.startswith('شروط الدفع:'):
            context['payment_terms'] = line.split(':', 1)[1].strip()
        elif line.startswith('البنود الإضافية المطلوبة:'):
            context['extra_clauses'] = line.split(':', 1)[1].strip()

    return context


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
    context = _extract_contract_context(items)

    # Base system prompt for Saudi legal context - tuned for concise, Absher-style output
    system_base = '''أنت محامي سعودي. اكتب عقداً عربياً رسمياً مختصراً ومنظماً بصياغة حكومية واضحة.

تنسيق الإخراج:
- لا تستخدم Markdown ولا عناوين ### ولا علامات ``` ولا فواصل زخرفية.
- ابدأ بـ "بسم الله الرحمن الرحيم" ثم عنوان العقد في سطر مستقل.
- بعد التمهيد، اكتب 6–8 مواد مرقمة بصيغة "المادة (1): ...".
- كل مادة جملة أو جملتين فقط، بدون تكرار.
- اذكر البيانات المتفق عليها (البضائع/النطاق، المدة، تاريخ البداية، الدفع) ضمن المواد بشكل طبيعي.
- إذا طُلبت بنود إضافية (مثل الشرط الجزائي أو القوة القاهرة) فخصص لها مادة واضحة.
- اختم بـ "والله ولي التوفيق" ثم "التوقيعات:" وخانتين للتوقيع للطرفين.

قيود:
- لا تذكر عبارات مثل "[ملاحظات AI]" أو "--- التفاصيل التعاقدية ---" ولا تنسخها حرفياً.
- لا تكتب شهادات أو مرفقات أو ملاحظات ختامية خارج نطاق العقد.

المرجع القانوني: نظام المعاملات المدنية السعودي (م/191)
'''

    # Specific instructions by type - CONCISE FOR ALLAM
    if contract_type == 'nda':
        prompt_system = system_base + '\nالنوع: اتفاقية عدم إفصاح. المواد: تعريف السرية، الالتزامات، الاستثناءات، المدة، الجزاءات.'

        prompt_user = f'''اتفاقية عدم إفصاح:
الطرف المفصح: {supplier}
الطرف المتلقي: {buyer}
النطاق: {context["scope"]}'''

        if context.get('duration'):
            prompt_user += f'\nالمدة: {context["duration"]}'
        else:
            prompt_user += f'\nالمدة: {price} سنة'

        if context.get('extra_clauses'):
            prompt_user += f'\nبنود إضافية مطلوبة: {context["extra_clauses"]}'
        if context.get('ai_notes'):
            prompt_user += f'\nملاحظات: {context["ai_notes"]}'

    elif contract_type == 'service':
        prompt_system = system_base + '\nالنوع: عقد خدمات. المواد: نطاق العمل، المدة، القيمة، الدفع، الجودة، الإنهاء.'

        prompt_user = f'''عقد خدمات:
مقدم الخدمة: {supplier}
العميل: {buyer}
الخدمات/النطاق: {context["scope"]}
القيمة: {price} ريال'''

        if context.get('start_date'):
            prompt_user += f'\nتاريخ البداية: {context["start_date"]}'
        if context.get('duration'):
            prompt_user += f'\nالمدة: {context["duration"]}'
        if context.get('payment_terms'):
            prompt_user += f'\nشروط الدفع: {context["payment_terms"]}'
        if context.get('extra_clauses'):
            prompt_user += f'\nبنود إضافية مطلوبة: {context["extra_clauses"]}'
        if context.get('ai_notes'):
            prompt_user += f'\nملاحظات: {context["ai_notes"]}'

    elif contract_type == 'rental':
        prompt_system = system_base + '\nالنوع: عقد إيجار. المواد: وصف العين، المدة، القيمة، الصيانة، الإخلاء.'

        prompt_user = f'''عقد إيجار:
المؤجر: {supplier}
المستأجر: {buyer}
وصف العين/النطاق: {context["scope"]}
الأجرة: {price} ريال'''

        if context.get('start_date'):
            prompt_user += f'\nتاريخ البداية: {context["start_date"]}'
        if context.get('duration'):
            prompt_user += f'\nالمدة: {context["duration"]}'
        if context.get('payment_terms'):
            prompt_user += f'\nشروط الدفع: {context["payment_terms"]}'
        if context.get('extra_clauses'):
            prompt_user += f'\nبنود إضافية مطلوبة: {context["extra_clauses"]}'
        if context.get('ai_notes'):
            prompt_user += f'\nملاحظات: {context["ai_notes"]}'

    else:  # Default: Supply
        prompt_system = system_base + '\nالنوع: عقد توريد. المواد: البضائع، الكمية، السعر، التسليم، الضمان، الجزاءات.'

        prompt_user = f'''عقد توريد:
المورد: {supplier}
المشتري: {buyer}
البضائع/نطاق التوريد: {context["scope"]}
القيمة: {price} ريال'''

        if context.get('start_date'):
            prompt_user += f'\nتاريخ البداية: {context["start_date"]}'
        if context.get('duration'):
            prompt_user += f'\nالمدة: {context["duration"]}'
        if context.get('payment_terms'):
            prompt_user += f'\nشروط الدفع: {context["payment_terms"]}'
        if context.get('extra_clauses'):
            prompt_user += f'\nبنود إضافية مطلوبة: {context["extra_clauses"]}'
        if context.get('ai_notes'):
            prompt_user += f'\nملاحظات: {context["ai_notes"]}'

    # Try providers in order
    providers = [
        ('Groq', lambda: generate_with_groq(prompt_system, prompt_user)),
        ('ALLaM (HuggingFace)', lambda: generate_with_allam_hf(prompt_system, prompt_user)),
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
