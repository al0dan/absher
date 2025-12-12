# عقود | Uqood
> **AI-Powered Arabic Contract Management Platform**

<div align="center">

![Vision 2030](https://img.shields.io/badge/Vision%202030-Aligned-00a651?style=for-the-badge)
![Saudi Arabia](https://img.shields.io/badge/Made%20in-Saudi%20Arabia-006c35?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white)

**The first Arabic-native contract platform powered by Saudi Sovereign AI (ALLaM)**

[🚀 Live Demo](#demo) · [📖 Documentation](#features) · [🔧 Installation](#installation)

</div>

---

## ✨ Features

### 🤖 AI Contract Generation
- **ALLaM-2-7B Integration** - SDAIA's sovereign Arabic AI via Groq
- Generates legally compliant Arabic contracts in seconds
- Supports 4 contract types: Supply, Service, NDA, Rental
- References Saudi Civil Transactions Law (م/191)

### 🏢 Government API Integration
- **Wathq API** - Real-time Commercial Registration (CR) verification
- Auto-fill company data from Ministry of Commerce
- **Nafath Ready** - National Single Sign-On (simulation mode)
- **ZATCA Compatible** - E-invoicing XML generation

### 📝 Contract Types
| Type | Arabic | Use Case |
|------|--------|----------|
| 📦 Supply | عقد توريد | Product delivery |
| 🛠️ Service | عقد خدمات | Consulting, maintenance |
| 🔒 NDA | اتفاقية عدم إفصاح | Confidentiality |
| 🏠 Rental | عقد إيجار | Equipment, property |

### 🎨 Arabic-First Design
- Full RTL support with professional Arabic typography
- Absher-inspired UI/UX
- Mobile-responsive design
- PDF generation with Arabic fonts

---

## 🛠️ Tech Stack

- **Backend**: Flask + SQLAlchemy
- **AI**: Groq API (ALLaM-2-7B, Llama 3.3)
- **Frontend**: Jinja2 + Vanilla CSS
- **APIs**: Wathq, Nafath (sim), ZATCA (sim)
- **PDF**: WeasyPrint

---

## 🚀 Installation

### Prerequisites
- Python 3.11+
- pip

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/uqood-platform.git
cd uqood-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

Visit `http://localhost:5000` 🎉

### Demo Credentials
| Username | Password | Company |
|----------|----------|---------|
| almarai | almarai123 | شركة المراعي |
| stc | stc123 | الاتصالات السعودية |
| demo | demo | شركة التقنية المتقدمة |

---

## 🔑 Environment Variables

```bash
# Required
FLASK_SECRET_KEY=your-secret-key
GROQ_API_KEY=gsk_xxx          # Get from console.groq.com

# Optional - Government APIs
WATHQ_API_KEY=xxx             # Get from developer.wathq.sa
WATHQ_SANDBOX=false           # true for sandbox

# Optional - Other AI Providers
KIMI_API_KEY=xxx              # Moonshot AI fallback
```

---

## 📁 Project Structure

```
uqood-platform/
├── app.py                 # Flask application factory
├── models.py              # Database models
├── routes/
│   ├── auth.py           # Authentication routes
│   ├── contracts.py      # Contract CRUD + API
│   └── main.py           # Landing pages
├── services/
│   ├── ai_service.py     # ALLaM/Groq integration
│   ├── wathq_service.py  # CR verification
│   ├── nafath_service.py # National SSO
│   └── zatca_service.py  # E-invoicing
├── templates/             # Jinja2 HTML templates
├── css/                   # Stylesheets
└── img/                   # Assets
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contract` | POST | Create AI-generated contract |
| `/api/contract/<id>/sign` | POST | Sign contract |
| `/api/lookup/cr` | POST | Verify Commercial Registration |
| `/api/validate/vat` | POST | Validate VAT number |
| `/health` | GET | Health check |

---

## 🎯 Vision 2030 Alignment

This project supports Saudi Vision 2030 goals:
- **Digital Transformation** - Paperless contract management
- **SME Empowerment** - Accessible legal automation
- **Sovereign AI** - Using Saudi's ALLaM model
- **E-Government** - Integration with Wathq, Nafath, ZATCA

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- **SDAIA** - ALLaM Arabic AI Model
- **Ministry of Commerce** - Wathq API
- **Absher** - Design inspiration

---

<div align="center">

**Built with ❤️ in Saudi Arabia**

عقود | Uqood - إدارة العقود بالذكاء الاصطناعي

</div>
