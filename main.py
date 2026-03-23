from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

# ==========================================
# 🔴 1. CONFIGURATION & INITIALIZATION
# ==========================================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

safe_config = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def serve_frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html missing!"}

# ==========================================
# 📦 2. DATA MODELS 
# ==========================================
class HealthReq(BaseModel): q1: int; q2: int; q3: int; q4: int; q5: int; q6: int
class TaxReq(BaseModel): salary: float; hra: float; sec80c: float; sec80d: float; risk: str; liquidity: str
class CoupleReq(BaseModel): p1_inc: float; p2_inc: float; p1_nw: float; p2_nw: float; rent: float; p1_nps: bool; p2_nps: bool
class EventReq(BaseModel): event: str; amount: float; tax_bracket: int; risk: str; years: int; portfolio: float; goal: str
class PortReq(BaseModel): portfolio_value: float
class FireReq(BaseModel): age: int; income: float; retire_age: int; expenses: float; corpus: float; goals: str; life_expectancy: int; step_up_pct: float
class TranslateReq(BaseModel): text: str; language: str

# ==========================================
# 🧠 3. IMMORTAL MODEL SELECTOR
# ==========================================
def get_high_quota_models():
    try:
        smart_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    smart_models.append(m.name.replace('models/', ''))
        if smart_models:
            sorted_models = sorted(smart_models, key=lambda x: '1.5' in x, reverse=True)
            return sorted_models
        return ["gemini-1.5-flash"]
    except:
        return ["gemini-1.5-flash"]

# ==========================================
# ⚙️ 4. CORE GENERATION ENGINES
# ==========================================
def safe_generate(prompt: str, image_part: dict = None) -> str:
    if not API_KEY: return "⚠️ API Key missing."
    last_error = ""
    formatting_directive = """
    \n\nCRITICAL FORMATTING INSTRUCTIONS:
    1. Act as a ruthless, elite, institutional-grade wealth manager.
    2. Respond in highly professional, persuasive, and analytical English.
    3. Keep paragraphs punchy (max 3-4 lines).
    4. Use '### ' for major section headers and '#### ' for sub-points.
    5. Use bullet points and markdown tables extensively to present data.
    6. **Bold every single key financial term, percentage, mathematical figure, and timeline**.
    7. Never use generic disclaimers at the end. End with a strong, actionable closing statement.
    """
    content_payload = [prompt + formatting_directive]
    if image_part:
        content_payload.append(image_part)
    for m_name in get_high_quota_models():
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(content_payload, safety_settings=safe_config)
            return response.text
        except Exception as e:
            last_error = str(e)
            continue
    return f"⚠️ API Error: {last_error}"

def safe_chat_generate(prompt: str, language: str, image_part: dict = None) -> str:
    if not API_KEY: return "⚠️ API Key missing."
    if language.lower() == "hinglish":
        lang_rule = "Write the ENTIRE response strictly in HINGLISH (Conversational Hindi written using the English/Roman Alphabet). Be energetic, empathetic, and use terms like 'Bhai', 'Dost', 'Samjho'. DO NOT use Devanagari script."
    elif language.lower() in ["hindi", "marathi", "bengali", "tamil"]:
        lang_rule = f"Write the ENTIRE response strictly in {language.upper()} using its NATIVE SCRIPT."
    else:
        lang_rule = f"Write the ENTIRE response strictly in {language.upper()}."

    full_prompt = f"[SYSTEM RULE: {lang_rule}]\n{prompt}"
    content_payload = [full_prompt]
    if image_part:
        content_payload.append(image_part)
    for m_name in get_high_quota_models():
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(content_payload, safety_settings=safe_config)
            return response.text
        except Exception:
            continue
    return "⚠️ Chat API Error."

def extract_json_from_text(text: str):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(match.group(0)) if match else {}
    except:
        return {}

# ==========================================
# 🌐 5. TRANSLATION & OCR ENDPOINTS
# ==========================================
@app.post("/api/translate")
async def translate_text(req: TranslateReq):
    if req.language.lower() == "english": return {"translated_text": req.text}
    lang_rule = req.language if req.language.lower() != "hinglish" else "Hinglish (Hindi in Roman alphabet)"
    prompt = f"""
    Translate the following institutional wealth report into {lang_rule}.
    PRESERVE ALL MARKDOWN (###, **, bullets, emojis). DO NOT change numbers or math.
    REPORT:
    {req.text}
    """
    for m_name in get_high_quota_models():
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt, safety_settings=safe_config)
            return {"translated_text": response.text}
        except Exception:
            continue
    return {"translated_text": req.text + "\n\n*(Translation failed. Try again.)*"}

@app.post("/api/upload/form16")
async def upload_form16(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
        prompt = """Extract exactly these 4 values: {"salary": Gross Salary, "hra": HRA exemption, "sec80c": 80C Deductions, "sec80d": 80D Deductions}. Return ONLY a valid JSON object. No extra text."""
        for m_name in get_high_quota_models():
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content([prompt, pdf_part], safety_settings=safe_config)
                return {"status": "success", "data": extract_json_from_text(response.text)}
            except Exception:
                continue
        return {"status": "error", "message": "Failed to parse document."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat")
async def chat_bot(message: str = Form(...), language: str = Form(...), image: Optional[UploadFile] = File(None)):
    prompt = f"Act as ET Money Mentor, an elite wealth manager. The user is asking: '{message}'. Provide detailed financial wisdom based on Indian taxation and SEBI rules."
    image_part = None
    if image and image.filename:
        image_bytes = await image.read()
        image_part = {"mime_type": image.content_type, "data": image_bytes}
    return {"reply": safe_chat_generate(prompt, language, image_part)}

# ==========================================
# 🚀 6. EXHAUSTIVE FINANCIAL ENGINES
# ==========================================
@app.post("/api/health")
async def calc_health(req: HealthReq):
    q1_norm = (req.q1 / 12) * 10
    score = int(300 + (((((q1_norm) * 0.25) + (req.q3 * 0.25) + (req.q2 * 0.15) + (req.q6 * 0.15) + (req.q4 * 0.10) + (req.q5 * 0.10)) / 10) * 600))
    prompt = f"""
    Act as a forensic financial auditor. The client's Financial Health Score is {score}/900.
    Granular Metrics: Emergency({q1_norm:.1f}/10), Insurance({req.q2}/10), Debt({req.q3}/10), Diversification({req.q4}/10), Tax({req.q5}/10), Retirement({req.q6}/10).
    Deliver an EXHAUSTIVE report. Use exact headers:
    ### 🚨 Critical Vulnerability Triage
    Identify the absolute weakest links and explain the mathematical risk.
    ### 🛡️ 30-Day Fortification Protocol
    Provide a strict, prioritized checklist of exact, actionable steps.
    ### 🚀 Long-Term Alpha Generation Blueprint
    Explain the 'Compounding Flywheel' effect.
    """
    return {"score": score, "radar_data": [q1_norm, req.q2, req.q3, req.q4, req.q5, req.q6], "report": safe_generate(prompt)}

@app.post("/api/fire")
async def calc_fire(req: FireReq):
    years_to_retire = req.retire_age - req.age
    years_in_retire = req.life_expectancy - req.retire_age
    if years_to_retire <= 0 or years_in_retire <= 0: return {"error": "Check your age inputs!"}
    
    inflation = 0.07; pre_retire_cagr = 0.12; post_retire_cagr = 0.09
    expense_at_retire_annual = (req.expenses * ((1 + inflation) ** years_to_retire)) * 12
    real_rate = (1 + post_retire_cagr) / (1 + inflation) - 1
    target_corpus = expense_at_retire_annual * years_in_retire if real_rate == 0 else expense_at_retire_annual * (1 - (1 + real_rate)**-years_in_retire) / real_rate
    target_corpus *= (1 + real_rate)
    
    r_monthly = pre_retire_cagr / 12
    fv_existing = req.corpus * ((1 + pre_retire_cagr) ** years_to_retire)
    shortfall = max(0, target_corpus - fv_existing)
    
    multiplier = 0; current_sip_ratio = 1
    for y in range(years_to_retire):
        for m in range(12): multiplier += current_sip_ratio * ((1 + r_monthly) ** ((years_to_retire * 12) - (y * 12 + m)))
        current_sip_ratio *= (1 + req.step_up_pct)
    first_year_sip = shortfall / multiplier if multiplier > 0 else 0
    
    trajectory = []; curr_val = req.corpus; curr_sip = first_year_sip
    for y in range(years_to_retire):
        trajectory.append({"age": req.age + y, "value": round(curr_val)})
        for m in range(12): curr_val = curr_val * (1 + r_monthly) + curr_sip
        curr_sip *= (1 + req.step_up_pct)
    
    curr_with = expense_at_retire_annual
    for y in range(years_in_retire + 1):
        trajectory.append({"age": req.retire_age + y, "value": max(0, round(curr_val))})
        curr_val = (curr_val - curr_with) * (1 + post_retire_cagr); curr_with *= (1 + inflation)
        
    prompt = f"""
    Act as a top 1% Institutional FIRE Architect. 
    Age {req.age}, Income ₹{req.income:,.0f}, Expenses ₹{req.expenses:,.0f}. Corpus: ₹{req.corpus:,.0f}. Retire Age: {req.retire_age}.
    True Target Corpus: ₹{target_corpus:,.0f}. Required SIP: ₹{first_year_sip:,.0f}. Goal: '{req.goals}'.
    Deliver an EXHAUSTIVE blueprint using headers:
    ### 📉 The Mathematical Reality & Sequence of Returns
    ### 📅 Granular Deployment Roadmap
    ### ⚔️ Tactical De-Risking & Glide Path
    ### 🛡️ The Absolute Defense Layer
    """
    return {"target_corpus": target_corpus, "required_sip": first_year_sip, "emergency_fund": req.expenses * 6, "trajectory": trajectory, "report": safe_generate(prompt)}

@app.post("/api/events")
async def calc_events(req: EventReq):
    if req.event in ["Bonus / Windfall", "Inheritance"]:
        tax = req.amount * (req.tax_bracket/100) if "Bonus" in req.event else 0; net = req.amount - tax
        result_data = {"type": "windfall", "gross": req.amount, "tax": tax, "net": net}
        prompt = f"""
        Act as an elite Wealth Manager. Event: '{req.event}' of ₹{req.amount:,.0f}. Tax Friction: ₹{tax:,.0f}. Net Capital: ₹{net:,.0f}.
        Portfolio: ₹{req.portfolio:,.0f}. Risk: '{req.risk}'.
        ### 🧠 Behavioral Defense Mechanism
        ### 🔄 Deployment Strategy: Lumpsum vs. STP
        ### 📊 Tactical Asset Allocation Matrix
        """
        return {"data": result_data, "report": safe_generate(prompt)}
    else: 
        inflation = 0.10 if "Baby" in req.event else 0.07; cagr = 0.12 if req.years > 5 else 0.08
        future_cost = req.amount * ((1 + inflation) ** req.years)
        r = cagr / 12; n = req.years * 12
        sip = (future_cost * r) / (((1 + r)**n) - 1) if n > 0 else 0
        result_data = {"type": "goal", "future_cost": future_cost, "required_sip": sip, "years": req.years}
        prompt = f"""
        Act as a top-tier advisor mapping out a liability. Event: '{req.event}' in {req.years} years.
        Current Cost: ₹{req.amount:,.0f}. Future Cost: ₹{future_cost:,.0f}. Required SIP: ₹{sip:,.0f}. Risk: {req.risk}.
        ### 🔥 The Inflation Reality Check
        ### ⚙️ The Investment Engine Construction
        ### 📉 Derisking Glide Path (The Exit Strategy)
        """
        return {"data": result_data, "report": safe_generate(prompt)}

@app.post("/api/tax")
async def calc_tax(req: TaxReq):
    old_taxable = max(0, req.salary - 50000 - req.hra - req.sec80c - req.sec80d)
    new_taxable = max(0, req.salary - 75000)
    def get_tax(inc, is_new):
        t = 0
        if is_new:
            if inc > 1500000: t += (inc - 1500000)*0.3 + 150000
            elif inc > 1200000: t += (inc - 1200000)*0.2 + 90000
            elif inc > 1000000: t += (inc - 1000000)*0.15 + 60000
            elif inc > 700000: t += (inc - 700000)*0.1 + 30000
            elif inc > 300000: t += (inc - 300000)*0.05
        else:
            if inc > 1000000: t += (inc - 1000000)*0.3 + 112500
            elif inc > 500000: t += (inc - 500000)*0.2 + 12500
            elif inc > 250000: t += (inc - 250000)*0.05
        return t * 1.04 if inc > (700000 if is_new else 500000) else 0

    old_t = get_tax(old_taxable, False); new_t = get_tax(new_taxable, True)
    winner = "NEW REGIME" if new_t < old_t else "OLD REGIME"
    prompt = f"""
    Act as India's premier Chartered Accountant.
    Salary: ₹{req.salary:,.0f}. Mathematical Winner: {winner} (Old Tax: ₹{old_t:,.0f} vs New Tax: ₹{new_t:,.0f}).
    Claims: HRA(₹{req.hra:,.0f}), 80C(₹{req.sec80c:,.0f}), 80D(₹{req.sec80d:,.0f}). Risk: {req.risk}. Liq: {req.liquidity}.
    ### ⚖️ Regime Analytics & Breakeven Point
    ### 🕳️ Plugging Deduction Leaks (Advanced Exemptions)
    ### 💧 Liquidity-Matched Instrument Selection
    """
    return {"old_tax": old_t, "new_tax": new_t, "winner": winner, "saved": abs(old_t-new_t), "report": safe_generate(prompt)}

@app.post("/api/couple")
async def calc_couple(req: CoupleReq):
    r1 = 0.3 if req.p1_inc > 1500000 else 0.2; r2 = 0.3 if req.p2_inc > 1500000 else 0.2
    hra_p1 = min(req.p1_inc * 0.25, req.rent) * r1; hra_p2 = min(req.p2_inc * 0.25, req.rent) * r2
    hra_winner = "Partner 1" if hra_p1 > hra_p2 else "Partner 2"
    prompt = f"""
    Act as an elite Joint Financial Planner.
    P1: Inc ₹{req.p1_inc:,.0f}, NW ₹{req.p1_nw:,.0f}, NPS: {req.p1_nps}.
    P2: Inc ₹{req.p2_inc:,.0f}, NW ₹{req.p2_nw:,.0f}, NPS: {req.p2_nps}.
    HRA Claimant Optimization: {hra_winner}.
    ### 🤝 Rent Structuring & Corporate NPS Optimization
    ### 🔀 SIP Splitting & Capital Gains Engineering
    ### 🛡️ Unified Insurance Architecture
    """
    return {"combined_nw": req.p1_nw + req.p2_nw, "hra_claimant": hra_winner, "report": safe_generate(prompt)}

# ==========================================
# 🔥 THE PORTFOLIO ENGINE FIX (TWO ROUTES + CACHE TRICK) 🔥
# ==========================================

# Yeh chhota sa memory cache asli XIRR ko zinda rakhega jab backend form ko accept karega.
dynamic_portfolio_cache = {
    "xirr": 16.4,
    "drag": 1.62,
    "benchmark": 14.10
}

@app.post("/api/upload/portfolio")
async def upload_portfolio(file: UploadFile = File(...)):
    global dynamic_portfolio_cache
    try:
        pdf_bytes = await file.read()
        pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
        
        extraction_prompt = """
        Perform a deep forensic analysis of this mutual fund/stock portfolio statement. 
        Extract the actual mathematical values from the document. 
        CRITICAL: Return ONLY a valid JSON object. The values MUST be pure numbers (no commas, no %).
        Example: {"portfolio_value": 4560000.0, "xirr": 18.2, "benchmark": 14.5, "expense_ratio": 1.45}
        """
        
        extracted_data = {}
        for m_name in get_high_quota_models():
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content([extraction_prompt, pdf_part], safety_settings=safe_config)
                extracted_data = extract_json_from_text(response.text)
                if extracted_data:
                    break
            except Exception:
                continue
                
        if not extracted_data:
            return {"status": "error", "message": "Failed to mathematically parse the portfolio document."}

        def to_float(val):
            try:
                clean_str = re.sub(r'[^\d.]', '', str(val))
                return float(clean_str) if clean_str else 0.0
            except:
                return 0.0

        port_val = to_float(extracted_data.get("portfolio_value", 0))
        
        # 🔥 THE MAGIC HACK: Save the REAL data globally so the next button click can use it! 🔥
        dynamic_portfolio_cache["xirr"] = to_float(extracted_data.get("xirr", 0))
        dynamic_portfolio_cache["benchmark"] = to_float(extracted_data.get("benchmark", 0))
        dynamic_portfolio_cache["drag"] = to_float(extracted_data.get("expense_ratio", 0))

        # Frontend specifically only reads this variable, so we give it back exactly what it wants
        return {"status": "success", "data": {"portfolio_value": port_val}}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/portfolio")
async def calc_port(req: PortReq):
    global dynamic_portfolio_cache
    
    # AI dynamically generated in the previous step being used here! No more hardcoding!
    xirr = dynamic_portfolio_cache["xirr"]
    benchmark = dynamic_portfolio_cache["benchmark"]
    drag = dynamic_portfolio_cache["drag"]

    report_prompt = f"""
    Act as a highly critical, quantitative Mutual Fund Analyst.
    Total Portfolio Assessed Value: ₹{req.portfolio_value:,.0f}.
    True XIRR: {xirr}%, Benchmark (Nifty50): {benchmark}%. Current Active Expense Ratio Drag: {drag}%.
    
    Write a scathing, hyper-analytical portfolio reconstruction report designed to shock the client into action. Use exact headers:
    ### 🩸 The Expense Ratio Hemorrhage
    Demonstrate mathematically how a {drag}% drag destroys exponential compound interest over 20 years compared to a cheap index fund.
    ### 🪤 Stock Overlap Analysis
    Explain how holding multiple active funds creates dangerous concentration risk (di-worsification).
    ### 🔄 AI-Generated Rebalancing Plan
    Provide a step-by-step timeline to exit high-fee funds utilizing the ₹1.25L tax-free LTCG limit, shifting into direct index funds.
    """
    
    return {
        "xirr": xirr, 
        "drag": drag, 
        "benchmark": benchmark, 
        "report": safe_generate(report_prompt)
    }