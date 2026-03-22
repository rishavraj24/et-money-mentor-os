# 🚀 ET Money Mentor OS

**The Institutional-Grade Retail Wealth Operating System powered by Gemini 1.5 Flash.**

![ET Money Mentor](https://img.shields.io/badge/Status-Hackathon_Ready-success?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Gemini AI](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google)
![Vanilla JS](https://img.shields.io/badge/Vanilla_JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

---

## ⚠️ The Problem Statement

95% of Indians do not have a structured financial plan.  
Financial advisors charge ₹25,000+ annually, making quality advice accessible only to HNIs.

Retail investors face:
- Generic advice
- Fragmented tools
- No personalization

---

## 💡 The Solution

**ET Money Mentor OS** is an AI-powered personal finance operating system that transforms confused savers into confident investors.

It delivers:
- Hyper-personalized financial strategies
- Institutional-grade insights
- AI-driven decision making

---

## ✨ Core Modules (Financial Engine)

### 🔥 FIRE Path Planner
- Inflation-adjusted corpus calculation
- PVGA-based approach (not outdated 4% rule)
- Month-by-month wealth roadmap

### 🏥 Money Health Score
- 6-dimension financial analysis:
  - Emergency
  - Insurance
  - Debt
  - Diversification
  - Tax
  - Retirement
- Generates vulnerability report

### 🎉 Life Event Advisor
- Marriage / Baby / Windfall planning
- SIP calculations
- Behavioral finance alerts

### 🧙‍♂️ Tax Wizard
- AI OCR for Form 16
- Old vs New regime comparison
- Detects deduction leaks

### 👩‍❤️‍👨 Couple's Planner
- Joint tax optimization
- HRA + NPS strategies
- SIP allocation optimization

### 📈 MF Portfolio X-Ray
- Upload CAMS/KFintech statement
- Detect:
  - Expense ratio drag
  - Portfolio overlap
- Smart rebalancing plan

---

## 🛠️ God-Tier Features

- 👁️ Vision-enabled AI Chat
- 💾 Persistent Memory (LocalStorage)
- 🌍 Multi-language translation
- 🎙️ Speech-to-text & text-to-speech
- 📄 Native PDF export

---

## ⚙️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic  
- **AI Engine:** Gemini 1.5 Flash  
- **Frontend:** HTML, CSS, Vanilla JS  
- **Charts:** Chart.js  
- **PDF:** html2pdf.js  

---

## 🚀 Setup Instructions (One Shot Setup)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/et-money-mentor.git
cd et-money-mentor
```

## 2. Create virtual environment
python -m venv venv

## 3. Activate venv
### Windows:
venv\Scripts\activate

### Mac/Linux:
# source venv/bin/activate

## 4. Install dependencies
pip install fastapi uvicorn google-generativeai pydantic python-dotenv python-multipart

## 5. Create .env file
echo GEMINI_API_KEY=your_api_key_here > .env

## 6. Run server
uvicorn main:app --reload

## 7. Environment Variables
GEMINI_API_KEY=your_api_key_here

## 8. Future Enhancements
**Broker integrations
**Real-time market insights
**Mobile app
**Advanced tax simulations

## Built for the ET Money Hackathon 2026