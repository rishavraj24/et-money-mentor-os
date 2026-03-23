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
# 📦 2. CLEAN DATA MODELS (Pydantic)
# ==========================================
class HealthReq(BaseModel): 
    q1: int; q2: int; q3: int; q4: int; q5: int; q6: int

class TaxReq(BaseModel): 
    salary: float; hra: float; sec80c: float; sec80d: float; risk: str; liquidity: str

class CoupleReq(BaseModel): 
    p1_inc: float; p2_inc: float; p1_nw: float; p2_nw: float; rent: float; p1_nps: bool; p2_nps: bool

class EventReq(BaseModel): 
    event: str; amount: float; tax_bracket: int; risk: str; years: int; portfolio: float; goal: str

class PortReq(BaseModel): 
    portfolio_value: float

class FireReq(BaseModel): 
    age: int; income: float; retire_age: int; expenses: float; corpus: float; goals: str; life_expectancy: int; step_up_pct: float

class TranslateReq(BaseModel): 
    text: str; language: str

# ==========================================
# 🧠 3. THE IMMORTAL MODEL SELECTOR
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
        lang_rule = f"Write the ENTIRE response strictly in {language.upper()} using its NATIVE SCRIPT. Keep the tone professional yet accessible."
    else:
        lang_rule = f"Write the ENTIRE response strictly in {language.upper()} with institutional clarity."

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
    if req.language.lower() == "english":
        return {"translated_text": req.text}
        
    lang_rule = req.language if req.language.lower() != "hinglish" else "Hinglish (Conversational Hindi written in Roman/English alphabet)"
        
    prompt = f"""
    You are an expert financial translator and localization specialist. Translate the following institutional wealth report into {lang_rule}.
    CRITICAL RULES:
    1. Preserve ALL Markdown formatting exactly (### headers, **bold text**, bullet points, emojis).
    2. DO NOT change any mathematical values, percentages, or underlying meanings.
    3. Ensure complex financial terminology (e.g., CAGR, XIRR, Expense Ratio) is accurately represented or explained in the target language.
    
    REPORT TO TRANSLATE:
    {req.text}
    """
    
    for m_name in get_high_quota_models():
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt, safety_settings=safe_config)
            return {"translated_text": response.text}
        except Exception:
            continue
    return {"translated_text": req.text + "\n\n*(Translation failed due to server load. Please try again.)*"}

@app.post("/api/upload/form16")
async def upload_form16(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
        prompt = """Perform high-precision OCR on this tax document. Extract exactly these 4 values: {"salary": Gross Salary, "hra": HRA exemption, "sec80c": 80C Deductions, "sec80d": 80D Deductions}. Return ONLY a valid JSON object. No markdown, no extra text."""
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
    prompt = f"Act as ET Money Mentor, an elite, highly-paid institutional wealth manager. The user is asking: '{message}'. Provide detailed, step-by-step financial wisdom based on Indian taxation (Income Tax Act) and SEBI regulations. Be insightful, authoritative, and deeply analytical."
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
    Act as a forensic financial auditor. The client's Algorithmic Financial Health Score is {score}/900.
    Granular Metrics (Out of 10): 
    - Emergency Liquidity Buffer: {q1_norm:.1f}/10
    - Insurance/Risk Depth: {req.q2}/10
    - Debt-to-Income Optimization: {req.q3}/10
    - Asset Diversification: {req.q4}/10
    - Tax Shield Efficiency: {req.q5}/10
    - Retirement Glide-Path Readiness: {req.q6}/10

    Deliver a brutally honest, EXHAUSTIVE diagnostic report. Use exact headers:
    ### 🚨 Critical Vulnerability Triage
    Identify the absolute weakest links (lowest scores). Explain the cascading mathematical risk (e.g., how low insurance wipes out compounding, or how bad debt destroys wealth velocity). Do not sugarcoat it.
    ### 🛡️ 30-Day Fortification Protocol
    Provide a strict, prioritized checklist of exact, actionable steps they MUST execute this month to plug the leaks. Name specific asset classes (e.g., Liquid Funds, Arbitrage) where relevant.
    ### 🚀 Long-Term Alpha Generation Blueprint
    Explain the 'Compounding Flywheel' effect. How will fixing these specific metrics today unlock exponential net-worth growth over the next decade?
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
    Act as a top 1% Institutional FIRE (Financial Independence, Retire Early) Architect in India. 
    Client Telemetry: Age {req.age}, Monthly Income ₹{req.income:,.0f}, Monthly Lifestyle Expense ₹{req.expenses:,.0f}. Existing Corpus: ₹{req.corpus:,.0f}. Target Retirement Age: {req.retire_age}.
    Mathematical Reality (Adjusted for 7% Indian CPI Inflation): 
    - True Target Corpus Required: ₹{target_corpus:,.0f}
    - Required Base Monthly SIP (with {req.step_up_pct*100}% annual step-up): ₹{first_year_sip:,.0f}.
    - Major Goal Specified: '{req.goals}'.
    
    Deliver an EXHAUSTIVE, uncompromising execution blueprint using exact headers:
    ### 📉 The Mathematical Reality & Sequence of Returns
    Explain why standard US models (like the 4% rule) fail in India. Detail how you used the 'Present Value of a Growing Annuity' to calculate their ₹{target_corpus:,.0f} corpus, factoring in 7% inflation and 9% post-retirement yield.
    ### 📅 Granular Deployment Roadmap
    Provide strict asset-allocation directives. Break down the ₹{first_year_sip:,.0f} SIP into a Multi-Cap/Index strategy to achieve the 12% pre-retirement CAGR.
    ### ⚔️ Tactical De-Risking & Glide Path
    Explain exactly how the client must shift assets from volatile Equity to Fixed Income/Debt 3 years before age {req.retire_age} to prevent 'Sequence of Returns Risk' (SORR).
    ### 🛡️ The Absolute Defense Layer
    Define exact, non-negotiable target amounts for Term Insurance (Human Life Value method), base Family Floater Health cover, and a 6-to-12 month liquid cash buffer.
    """
    return {"target_corpus": target_corpus, "required_sip": first_year_sip, "emergency_fund": req.expenses * 6, "trajectory": trajectory, "report": safe_generate(prompt)}

@app.post("/api/events")
async def calc_events(req: EventReq):
    if req.event in ["Bonus / Windfall", "Inheritance"]:
        tax = req.amount * (req.tax_bracket/100) if "Bonus" in req.event else 0; net = req.amount - tax
        result_data = {"type": "windfall", "gross": req.amount, "tax": tax, "net": net}
        prompt = f"""
        Act as an elite Private Wealth Manager specializing in Sudden Wealth Events.
        Event Analysis: Client received a gross windfall of ₹{req.amount:,.0f} from '{req.event}'. 
        Tax Friction Deduction: ₹{tax:,.0f}. 
        Net Actionable Capital to deploy: ₹{net:,.0f}.
        Client Context: Existing Portfolio ₹{req.portfolio:,.0f}, Risk Tolerance: '{req.risk}', Target Goal: '{req.goal}'.
        
        Provide a hyper-detailed deployment thesis using exact headers:
        ### 🧠 Behavioral Defense Mechanism
        Address the psychological danger of 'Hedonic Adaptation' and lifestyle creep. Establish strict boundaries (e.g., the 10% splurge rule vs 90% capital deployment).
        ### 🔄 Deployment Strategy: Lumpsum vs. Systematic Transfer Plan (STP)
        Mathematically and psychologically analyze if they should deploy the ₹{net:,.0f} instantly or use a 6-12 month STP through a Liquid Fund to hedge against current market valuations and volatility.
        ### 📊 Tactical Asset Allocation Matrix
        Construct a precise percentage-based portfolio split across Domestic Equities, International Equities, and Fixed Income/Gold, strictly mapping to their '{req.risk}' profile.
        """
        return {"data": result_data, "report": safe_generate(prompt)}
    else: 
        inflation = 0.10 if "Baby" in req.event else 0.07; cagr = 0.12 if req.years > 5 else 0.08
        future_cost = req.amount * ((1 + inflation) ** req.years)
        r = cagr / 12; n = req.years * 12
        sip = (future_cost * r) / (((1 + r)**n) - 1) if n > 0 else 0
        result_data = {"type": "goal", "future_cost": future_cost, "required_sip": sip, "years": req.years}
        prompt = f"""
        Act as a top-tier institutional financial advisor mapping out a major future liability.
        Liability Analysis: Planning for '{req.event}' occurring in exactly {req.years} years.
        Current Baseline Cost: ₹{req.amount:,.0f}. 
        Inflated Future Cost (assuming {inflation*100}% sector-specific inflation): ₹{future_cost:,.0f}. 
        Required Monthly SIP Engine: ₹{sip:,.0f}. 
        Client Risk Profile: {req.risk}. Goal: {req.goal}.
        
        Provide an uncompromising, inflation-hedging masterplan using exact headers:
        ### 🔥 The Inflation Reality Check
        Explain the destructive, compounding power of {inflation*100}% inflation over {req.years} years, proving why keeping this money in a savings account guarantees failure.
        ### ⚙️ The Investment Engine Construction
        Recommend the exact Mutual Fund categories (e.g., Nifty 50 Index, Flexicap, Midcap) needed to absorb the ₹{sip:,.0f} SIP and generate the required CAGR, factoring in their '{req.risk}' tolerance.
        ### 📉 Derisking Glide Path (The Exit Strategy)
        Detail a strict timeline on shifting funds from volatile equities to safe, ultra-short-duration debt funds 18-24 months prior to the event to secure the corpus from sudden market crashes.
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
    Act as India's premier Chartered Accountant specializing in HNI (High Net-Worth Individual) tax alpha optimization.
    Client Financials: Base Salary ₹{req.salary:,.0f}. 
    Mathematical Winner: {winner} (Old Tax: ₹{old_t:,.0f} vs New Tax: ₹{new_t:,.0f}).
    Current Capital Claimed: HRA (₹{req.hra:,.0f}), 80C (₹{req.sec80c:,.0f}), 80D (₹{req.sec80d:,.0f}). 
    Risk Profile: {req.risk}. Liquidity Constraint: {req.liquidity}.
    
    Deliver a RUTHLESS, exhaustive tax-alpha strategy using exact headers:
    ### ⚖️ Regime Analytics & Breakeven Point
    Explain mathematically exactly why {winner} is optimal based on their specific deduction velocity. What extra deductions would they need to flip the outcome?
    ### 🕳️ Plugging Deduction Leaks (Advanced Exemptions)
    Identify high-level tax loopholes they are likely missing. Specifically address Section 80CCD(1B) (NPS Tier-1), Section 24(b) (Home Loan Interest), and the utilization of the ₹1.25 Lakh Tax-Free Long Term Capital Gains (LTCG) limit via Tax-Loss Harvesting.
    ### 💧 Liquidity-Matched Instrument Selection
    Give definitive, uncompromising verdicts on the best tax-saving instruments (ELSS vs. PPF vs. VPF) mapped strictly to their '{req.risk}' profile and '{req.liquidity}' constraints. Do not give generic advice; choose a path for them.
    """
    return {"old_tax": old_t, "new_tax": new_t, "winner": winner, "saved": abs(old_t-new_t), "report": safe_generate(prompt)}

@app.post("/api/couple")
async def calc_couple(req: CoupleReq):
    r1 = 0.3 if req.p1_inc > 1500000 else 0.2; r2 = 0.3 if req.p2_inc > 1500000 else 0.2
    hra_p1 = min(req.p1_inc * 0.25, req.rent) * r1; hra_p2 = min(req.p2_inc * 0.25, req.rent) * r2
    hra_winner = "Partner 1" if hra_p1 > hra_p2 else "Partner 2"
    prompt = f"""
    Act as an elite Joint Financial Planner for high-earning Dual-Income No-Kids (DINK) / Dual-Income households.
    Partner 1: Income ₹{req.p1_inc:,.0f}, Net Worth ₹{req.p1_nw:,.0f}, Corporate NPS Match: {req.p1_nps}.
    Partner 2: Income ₹{req.p2_inc:,.0f}, Net Worth ₹{req.p2_nw:,.0f}, Corporate NPS Match: {req.p2_nps}.
    Algorithmic HRA Claimant Optimization: {hra_winner} should claim the rent.
    
    Provide an exhaustive, legally sound household synergy masterplan using exact headers:
    ### 🤝 Rent Structuring & Corporate NPS Optimization
    Explain the mathematics behind why {hra_winner} claiming HRA maximizes total household post-tax income. Deep-dive into their Corporate NPS status—how 10% of basic salary matched by an employer bypasses the new regime completely, acting as pure 'Tax-Shielded Alpha'.
    ### 🔀 SIP Splitting & Capital Gains Engineering
    Provide a master strategy on how they should disproportionately split their monthly SIPs between both PAN cards to utilize two separate ₹1.25 Lakh tax-free LTCG limits every single year, preventing massive future tax friction.
    ### 🛡️ Unified Insurance Architecture
    Give a definitive structural strategy on why they must establish a high-cover Base Family Floater Health Insurance policy combined with a Super Top-Up, rather than relying solely on fragile corporate covers.
    """
    return {"combined_nw": req.p1_nw + req.p2_nw, "hra_claimant": hra_winner, "report": safe_generate(prompt)}

@app.post("/api/portfolio")
async def upload_portfolio(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
        
        # 1. BULLETPROOF EXTRACTION PROMPT
        extraction_prompt = """
        Perform a deep forensic analysis of this mutual fund/stock portfolio statement. 
        Extract the actual mathematical values from the document. 
        If 'expense ratio' or 'benchmark' is not explicitly written, estimate a realistic number based on the specific active funds listed in the document.
        
        CRITICAL: Return ONLY a valid JSON object. Do not include any markdown formatting or extra text.
        The values MUST be pure numbers (no commas, no percentage signs).
        
        Example Format:
        {
            "portfolio_value": 4560000.0,
            "invested_amount": 2850000.0,
            "xirr": 18.2,
            "benchmark": 14.5,
            "expense_ratio": 1.45
        }
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

        # SAFE FLOAT CONVERTER: Removes commas, %, strings, and safely converts to float
        def to_float(val):
            try:
                clean_str = re.sub(r'[^\d.]', '', str(val))
                return float(clean_str) if clean_str else 0.0
            except:
                return 0.0

        # 2. ASSIGN REAL VARIABLES SAFELY
        port_val = to_float(extracted_data.get("portfolio_value", 0))
        xirr = to_float(extracted_data.get("xirr", 0))
        benchmark = to_float(extracted_data.get("benchmark", 0))
        drag = to_float(extracted_data.get("expense_ratio", 0))

        # 3. DYNAMIC REPORT GENERATION
        report_prompt = f"""
        Act as a highly critical, quantitative Mutual Fund Analyst.
        Total Portfolio Assessed Value: ₹{port_val:,.0f}.
        True XIRR: {xirr}%, Benchmark (Nifty50): {benchmark}%. Current Active Expense Ratio Drag: {drag}%.
        
        Write a scathing, hyper-analytical portfolio reconstruction report designed to shock the client into action. Use exact headers:
        ### 🩸 The Expense Ratio Hemorrhage
        Demonstrate mathematically how a {drag}% drag destroys exponential compound interest over 20 years compared to a cheap index fund.
        ### 🪤 Stock Overlap Analysis
        Explain how holding multiple active funds creates dangerous concentration risk (di-worsification).
        ### 🔄 AI-Generated Rebalancing Plan
        Provide a step-by-step timeline to exit high-fee funds utilizing the ₹1.25L tax-free LTCG limit, shifting into direct index funds.
        """
        
        # 4. RETURN THE REAL DATA
        return {
            "status": "success", 
            "xirr": xirr, 
            "drag": drag, 
            "benchmark": benchmark, 
            "report": safe_generate(report_prompt)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}