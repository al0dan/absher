"""
PDF Service using WeasyPrint
Generates Arabic PDFs with proper BiDi support and text selectability.
"""
import os
import base64
import logging

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)

def get_image_base64(path):
    """Read image file and convert to base64 data URI"""
    try:
        # Resolve path relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, path.lstrip('/'))
        
        with open(full_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        mime = "image/png"
        if path.endswith(".svg"):
            mime = "image/svg+xml"
        elif path.endswith(".jpg") or path.endswith(".jpeg"):
            mime = "image/jpeg"
            
        return f"data:{mime};base64,{encoded_string}"
    except Exception as e:
        logger.error(f"Failed to load image {path}: {e}")
        return ""

def generate_pdf_from_html(html_content: str, output_path: str = None) -> bytes:
    """
    Generate a PDF from HTML content using WeasyPrint.
    """
    if not WEASYPRINT_AVAILABLE:
        logger.error("WeasyPrint not available")
        raise ImportError("WeasyPrint is required for PDF generation")
    
    try:
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"PDF saved to {output_path}")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise


def generate_contract_pdf(contract_data: dict) -> bytes:
    """
    Generate a contract PDF with proper Absher styling.
    """
    # Load images as base64
    logo_absher = get_image_base64("img/Absher_Business_logo.svg")
    logo_vision = get_image_base64("img/vission-logo.png")
    logo_moi = get_image_base64("img/moi-logo.svg")
    
    html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        /* Use system fonts with Arabic fallback - more reliable for PDF */
        @page {{
            size: A4;
            margin: 15mm;
        }}
        
        :root {{
            --business-theme-color: #3D80C1;
            --absher-green: #008850;
        }}

        * {{
            font-family: 'Noto Sans Arabic', 'Segoe UI', 'Arial', 'Tahoma', sans-serif;
            box-sizing: border-box;
        }}
        
        body {{
            margin: 0;
            padding: 20px;
            direction: rtl;
            color: #333;
        }}
        
        .pdf-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--business-theme-color);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        
        .header-logo-group {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .contract-title {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .contract-title h1 {{
            color: var(--business-theme-color);
            margin: 0;
            font-size: 20px;
        }}
        
        .contract-id {{
            background: #e3f2fd;
            color: #1565c0;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            display: inline-block;
            margin-top: 5px;
            font-weight: bold;
        }}
        
        .parties-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .party-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-right: 3px solid var(--business-theme-color);
            border-radius: 6px;
            padding: 10px 15px;
        }}
        
        .party-title {{
            color: #555;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 11px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 4px;
        }}
        
        .party-info {{
            margin: 3px 0;
            font-size: 11px;
            line-height: 1.4;
        }}
        
        .party-name {{
            color: var(--business-theme-color);
            font-weight: bold;
            font-size: 12px;
            margin-bottom: 4px;
        }}
        
        .contract-body {{
            background: linear-gradient(to bottom, #fefefe, #f9f9f9);
            padding: 20px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            border-right: 3px solid var(--business-theme-color);
            font-size: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            text-align: justify;
            margin-bottom: 30px;
        }}
        
        .signatures-section {{
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
        }}
        
        .signature-block {{
            width: 45%;
            text-align: center;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            background: #fff;
        }}
        
        .signature-img {{
            max-width: 120px;
            height: 50px;
            margin: 5px auto;
            object-fit: contain;
        }}
        
        .pdf-footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 9px;
            color: #999;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="pdf-header">
        <div class="header-logo-group">
            <img src="{logo_absher}" alt="Absher" style="height: 55px;">
            <div>
                <div style="font-size: 16px; font-weight: 700; color: #3D80C1;">أبشر أعمال</div>
                <div style="font-size: 10px; color: #666;">منصة عقود - وزارة الداخلية</div>
            </div>
        </div>
        <div class="header-logo-group">
            <img src="{logo_vision}" alt="Vision 2030" style="height: 40px;">
            <img src="{logo_moi}" alt="MOI" style="height: 40px;">
        </div>
    </div>
    
    <div class="contract-title">
        <h1>وثيقة عقد توريد</h1>
        <div class="contract-id">#{contract_data.get('id', 'N/A')}</div>
    </div>
    
    <div class="parties-grid">
        <div class="party-card">
            <div class="party-title">الطرف الأول (المورد)</div>
            <div class="party-name">{contract_data.get('supplier', 'N/A')}</div>
            <div class="party-info"><strong>السجل التجاري:</strong> {contract_data.get('supplier_cr', 'N/A')}</div>
            <div class="party-info"><strong>الرقم الضريبي:</strong> {contract_data.get('supplier_vat', 'N/A')}</div>
        </div>
        
        <div class="party-card">
            <div class="party-title">الطرف الثاني (المشتري)</div>
            <div class="party-name">{contract_data.get('buyer', 'N/A')}</div>
            <div class="party-info"><strong>السجل التجاري:</strong> {contract_data.get('buyer_cr', 'N/A')}</div>
            <div class="party-info"><strong>الرقم الضريبي:</strong> {contract_data.get('buyer_vat', 'N/A')}</div>
        </div>
    </div>
    
    <div class="contract-body">{contract_data.get('contract_text', 'لا يوجد نص محدد للعقد.')}</div>
    
    <div class="signatures-section">
        <div class="signature-block">
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 11px;">توقيع المورد</div>
            {'<img src="' + contract_data.get('supplier_signature', '') + '" class="signature-img">' if contract_data.get('supplier_signature') else '<div style="height:50px; color: #ccc;">(لم يتم التوقيع)</div>'}
            <div style="font-size: 11px;">{contract_data.get('supplier_name', '')}</div>
        </div>
        
        <div class="signature-block">
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 11px;">توقيع المشتري</div>
            {'<img src="' + contract_data.get('buyer_signature', '') + '" class="signature-img">' if contract_data.get('buyer_signature') else '<div style="height:50px; color: #ccc;">(لم يتم التوقيع)</div>'}
            <div style="font-size: 11px;">{contract_data.get('buyer_name', '')}</div>
        </div>
    </div>
    
    <div class="pdf-footer">
        <p>تم إنشاء هذه الوثيقة آلياً عبر منصة أبشر أعمال - جميع الحقوق محفوظة لوزارة الداخلية</p>
        <p>تاريخ الإنشاء: {contract_data.get('created_at', '2025')}</p>
    </div>
</body>
</html>'''
    
    return generate_pdf_from_html(html)
