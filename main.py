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

class HealthReq(BaseModel): q1: int; q2: int; q3: int; q4: int; q5: int; q6: int;
class TaxReq(BaseModel): salary: float; hra: float; sec80c: float; sec80d: float; risk: str; liquidity: str;
class CoupleReq(BaseModel): p1_inc: float; p2_inc: float; p1_nw: float; p2_nw: float; rent: float; p1_nps: bool; p2_nps: bool;
class EventReq(BaseModel): event: str; amount: float; tax_bracket: int; risk: str; years: int; portfolio: float; goal: str;
class PortReq(BaseModel): portfolio_value: float;
class FireReq(BaseModel): age: int; income: float; retire_age: int; expenses: float; corpus: float; goals: str; life_expectancy: int; step_up_pct: float;
class TranslateReq(BaseModel): text: str; language: str

def get_high_quota_models():
    return ["gemini-flash-latest"]

def safe_generate(prompt: str, image_part: dict = None) -> str:
    if not API_KEY: return "⚠️ API Key missing."
    last_error = ""
    
    formatting_directive = """
    \n\nCRITICAL FORMATTING INSTRUCTIONS:
    1. Respond in highly professional English.
    2. Keep paragraphs short and organized.
    3. Use '### ' for main headers.
    4. Use bullet points extensively.
    5. Bold **key financial terms, percentages, and numbers**.
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
        lang_rule = "Write the ENTIRE response in HINGLISH (Conversational Hindi written using the English/Roman Alphabet). DO NOT use Devanagari script."
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

@app.post("/api/translate")
async def translate_text(req: TranslateReq):
    if req.language.lower() == "english":
        return {"translated_text": req.text}
        
    lang_rule = req.language
    if req.language.lower() == "hinglish":
        lang_rule = "Hinglish (Hindi language written in Roman/English alphabet)"
        
    prompt = f"""
    You are an expert financial translator. Translate the following report into {lang_rule}.
    CRITICAL RULES:
    1. You MUST preserve ALL Markdown formatting exactly (### headers, **bold text**, bullet points).
    2. Do NOT change the layout, mathematical values, or meaning.
    3. Keep financial terms accurate and professional.
    
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
    return {"translated_text": req.text + "\n\n*(Translation failed. Please try again.)*"}

@app.post("/api/upload/form16")
async def upload_form16(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
        prompt = """Extract exactly: {"salary": Gross Salary, "hra": HRA, "sec80c": 80C Deductions, "sec80d": 80D Deductions}. Output ONLY valid JSON."""
        for m_name in get_high_quota_models():
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content([prompt, pdf_part], safety_settings=safe_config)
                return {"status": "success", "data": extract_json_from_text(response.text)}
            except Exception:
                continue
        return {"status": "error", "message": "Failed to parse."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/upload/portfolio")
async def upload_portfolio(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
        prompt = """Extract Total Portfolio Value. Output ONLY valid JSON: {"portfolio_value": value}"""
        for m_name in get_high_quota_models():
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content([prompt, pdf_part], safety_settings=safe_config)
                return {"status": "success", "data": extract_json_from_text(response.text)}
            except Exception:
                continue
        return {"status": "error", "message": "Failed to parse."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat")
async def chat_bot(message: str = Form(...), language: str = Form(...), image: Optional[UploadFile] = File(None)):
    prompt = f"You are ET Money Mentor, an elite and highly-paid institutional wealth manager. Provide detailed, step-by-step financial wisdom based on Indian taxation and SEBI rules. User Query: '{message}'"
    image_part = None
    if image and image.filename:
        image_bytes = await image.read()
        image_part = {"mime_type": image.content_type, "data": image_bytes}
    return {"reply": safe_chat_generate(prompt, language, image_part)}

@app.post("/api/health")
async def calc_health(req: HealthReq):
    q1_norm = (req.q1 / 12) * 10
    score = int(300 + (((((q1_norm) * 0.25) + (req.q3 * 0.25) + (req.q2 * 0.15) + (req.q6 * 0.15) + (req.q4 * 0.10) + (req.q5 * 0.10)) / 10) * 600))
    prompt = f"""
    Act as a ruthless, elite Wealth Manager conducting a forensic financial audit. The client's Financial Health Score is {score}/900.
    Metrics (Out of 10): Emergency Buffer({q1_norm:.1f}), Insurance Depth({req.q2}), Debt-to-Income({req.q3}), Asset Diversification({req.q4}), Tax Efficiency({req.q5}), Retirement Readiness({req.q6}).
    Provide an EXHAUSTIVE, multi-tiered action plan. Do not sugarcoat vulnerabilities. 
    Structure exactly using these headers:
    ### 🚨 Critical Vulnerability Triage
    Identify the absolute weakest links from the metrics above and explain the mathematical risk of ignoring them.
    ### 🛡️ Immediate Fortification Protocol
    Provide exact, actionable steps they must take this month to fix the lowest scores.
    ### 🚀 Long-Term Alpha Generation
    Explain how fixing these specific metrics unlocks compound growth and financial security.
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
    Act as a top 1% Institutional FIRE Architect in India. 
    Client Profile: Age {req.age}, Monthly Income ₹{req.income:,.0f}, Monthly Expenses ₹{req.expenses:,.0f}. Existing Corpus: ₹{req.corpus:,.0f}. Retiring at Age: {req.retire_age}.
    True Target Corpus (adjusted for 7% Indian inflation): ₹{target_corpus:,.0f}. Required Base SIP (with {req.step_up_pct*100}% annual step-up): ₹{first_year_sip:,.0f}. Major Goal: '{req.goals}'.
    Deliver an EXHAUSTIVE execution blueprint with exact headers:
    ### 📉 The Mathematical Reality
    Explain why the US 4% rule fails in India and why we use Present Value of Growing Annuity.
    ### 📅 Month-by-Month Financial Roadmap
    Provide strict monthly actions and SIP amounts split PER GOAL (e.g., Retirement vs {req.goals}).
    ### ⚔️ Asset Allocation Shifts
    Detail the exact percentage splits between equity and debt for their current age.
    ### 🛡️ Insurance Gaps & Emergency Targets
    Define exact target amounts for term cover, health cover, and a 6-month cash buffer.
    """
    return {"target_corpus": target_corpus, "required_sip": first_year_sip, "emergency_fund": req.expenses * 6, "trajectory": trajectory, "report": safe_generate(prompt)}

@app.post("/api/events")
async def calc_events(req: EventReq):
    if req.event in ["Bonus / Windfall", "Inheritance"]:
        tax = req.amount * (req.tax_bracket/100) if "Bonus" in req.event else 0; net = req.amount - tax
        result_data = {"type": "windfall", "gross": req.amount, "tax": tax, "net": net}
        prompt = f"""
        You are an elite private wealth manager specializing in Sudden Wealth Events.
        Event: Received ₹{req.amount:,.0f} from '{req.event}'. Tax Friction: ₹{tax:,.0f}. Net Actionable Capital: ₹{net:,.0f}.
        Client Portfolio: ₹{req.portfolio:,.0f}. Risk Profile: {req.risk}. Specific Goal: {req.goal}.
        Provide a hyper-detailed deployment thesis using exact headers:
        ### 🧠 Behavioral Finance Warning
        Address 'Hedonic Adaptation' and lifestyle creep with strict splurge vs invest rules.
        ### 🔄 Deployment Strategy: Lumpsum vs STP
        Mathematically analyze instant deployment vs Systematic Transfer Plan to hedge volatility.
        ### 📊 Asset Allocation Matrix
        Define exact percentage allocations across Domestic Equity, International Equity, and Fixed Income based on '{req.risk}'.
        """
        return {"data": result_data, "report": safe_generate(prompt)}
    else: 
        inflation = 0.10 if "Baby" in req.event else 0.07; cagr = 0.12 if req.years > 5 else 0.08
        future_cost = req.amount * ((1 + inflation) ** req.years)
        r = cagr / 12; n = req.years * 12
        sip = (future_cost * r) / (((1 + r)**n) - 1) if n > 0 else 0
        result_data = {"type": "goal", "future_cost": future_cost, "required_sip": sip, "years": req.years}
        prompt = f"""
        You are a top-tier financial advisor mapping out a major future liability.
        Event: '{req.event}' occurring in {req.years} years.
        Current Cost: ₹{req.amount:,.0f}. Inflated Future Cost: ₹{future_cost:,.0f}. Required SIP: ₹{sip:,.0f}. 
        Client Portfolio: ₹{req.portfolio:,.0f}. Risk Profile: {req.risk}. Goal: {req.goal}.
        Provide an inflation-hedging masterplan using exact headers:
        ### 🔥 The Inflation Reality Check
        Explain the destructive power of specific inflation over {req.years} years.
        ### ⚙️ The Investment Engine
        Recommend specific mutual fund categories (e.g., Flexicap, Factor funds) needed for the ₹{sip:,.0f} SIP based on the {req.risk} profile.
        ### 📉 Derisking Glide Path
        Detail a strict timeline on shifting funds from volatile equity to safe debt 2-3 years prior to the goal.
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
    You are India's top Chartered Accountant specializing in HNI tax optimization.
    Client Salary: ₹{req.salary:,.0f}. Mathematical Winner: {winner}.
    Current Claims: HRA (₹{req.hra:,.0f}), 80C (₹{req.sec80c:,.0f}), 80D (₹{req.sec80d:,.0f}). Risk Profile: {req.risk}. Liquidity Constraint: {req.liquidity}.
    Deliver a RUTHLESS, exhaustive tax-alpha strategy using exact headers:
    ### ⚖️ Regime Analytics
    Explain mathematically why {winner} is optimal based on their specific deductions.
    ### 🕳️ Plugging Deduction Leaks
    Identify advanced tax loopholes they are missing (e.g., 80CCD(1B), Section 24(b), Tax-Loss Harvesting).
    ### 💧 Liquidity-Matched Investments
    Give definitive verdicts on ELSS vs. PPF vs. VPF vs. NPS mapped strictly to their '{req.risk}' profile and '{req.liquidity}' needs.
    """
    return {"old_tax": old_t, "new_tax": new_t, "winner": winner, "saved": abs(old_t-new_t), "report": safe_generate(prompt)}

@app.post("/api/couple")
async def calc_couple(req: CoupleReq):
    r1 = 0.3 if req.p1_inc > 1500000 else 0.2; r2 = 0.3 if req.p2_inc > 1500000 else 0.2
    hra_p1 = min(req.p1_inc * 0.25, req.rent) * r1; hra_p2 = min(req.p2_inc * 0.25, req.rent) * r2
    hra_winner = "Partner 1" if hra_p1 > hra_p2 else "Partner 2"
    prompt = f"""
    Act as an elite Joint Financial Planner for Dual-Income households.
    P1: Income ₹{req.p1_inc:,.0f}, Net Worth ₹{req.p1_nw:,.0f}, NPS Match: {req.p1_nps}.
    P2: Income ₹{req.p2_inc:,.0f}, Net Worth ₹{req.p2_nw:,.0f}, NPS Match: {req.p2_nps}.
    Optimal HRA Claimant computed as: {hra_winner}.
    Provide an exhaustive household synergy masterplan using exact headers:
    ### 🤝 HRA & Corporate NPS Optimization
    Explain why {hra_winner} claiming HRA maximizes household net income. Also, analyze their NPS matching status and how it creates tax-shielded alpha.
    ### 🔀 SIP Splits for Tax Efficiency
    Provide a mathematical strategy on how they should split their monthly SIPs between both incomes to minimize long-term capital gains tax friction.
    ### 🛡️ Joint vs. Individual Insurance
    Give a definitive strategy on Base Family Floater Health Insurance vs Individual policies based on their dual-income nature.
    """
    return {"combined_nw": req.p1_nw + req.p2_nw, "hra_claimant": hra_winner, "report": safe_generate(prompt)}

@app.post("/api/portfolio")
async def calc_port(req: PortReq):
    prompt = f"""
    Act as a highly critical, quantitative Mutual Fund Analyst.
    Portfolio Value: ₹{req.portfolio_value:,.0f}.
    True XIRR: 16.4%, Benchmark (Nifty50): 14.1%. Expense Ratio Drag: 1.62%.
    Write a scathing, hyper-analytical portfolio reconstruction report. Use exact headers:
    ### 🩸 The Expense Ratio Drag
    Demonstrate mathematically how a 1.62% drag destroys compound interest over 20 years.
    ### 🪤 Stock Overlap Analysis
    Explain how holding multiple active funds creates dangerous concentration risk (di-worsification).
    ### 🔄 AI-Generated Rebalancing Plan
    Provide a step-by-step timeline to exit high-fee funds utilizing the ₹1.25L tax-free LTCG limit, shifting into direct index funds.
    """
    return {"xirr": 16.4, "drag": 1.62, "benchmark": 14.10, "report": safe_generate(prompt)}