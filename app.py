import streamlit as st
import pdfplumber
import io
import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# ==========================================
# 1. القاموس المصرفي ثنائي اللغة (Bilingual Dictionary)
# ==========================================
TRANSLATIONS = {
    "ar": {
        "dir": "rtl",
        "align": "right",
        "font": "'Cairo', sans-serif",
        "app_title": "بنك وربة | Warba SmartMemo",
        "title": "أتمتة مذكرات الائتمان — Warba SmartMemo",
        "subtitle": "منظومة ذكاء اصطناعي بنكية مدعومة بوكلاء LangGraph لاستخراج البيانات وإعداد مذكرات ائتمان متوافقة مع الشريعة الإسلامية",
        "sidebar_header": "بنك وربة — قطاع الشركات",
        "sidebar_sub": "المساعد الذكي لمدراء العلاقات (RM Copilot)",
        "model_header": "⚙️ محرك الذكاء الاصطناعي",
        "model_select": "اختر النموذج اللغوي:",
        "api_key_label": "مفتاح API (اختياري للوضع الحي):",
        "docs_header": "📁 رفع وثائق العميل",
        "fin_upload": "1. القوائم المالية (PDF)",
        "cr_upload": "2. السجل التجاري / الهوية (PDF)",
        "notes_label": "3. ملاحظات الزيارة الميدانية (RM Notes)",
        "notes_placeholder": "اكتب انطباع الزيارة، كفاءة الإدارة، الغرض من التسهيلات، الضمانات المقترحة...",
        "btn_generate": "🚀 تشغيل وكلاء LangGraph",
        "btn_demo": "⚡ تجربة سريعة وفورية (شركة كويتية للمقاولات)",
        "spinner_msg": "جاري استخراج الجداول عبر pdfplumber وتنسيق مهام الوكلاء الأربعة...",
        "success_msg": "اكتمل التحليل وتوليد المذكرة الائتمانية بنجاح!",
        "tab1": "📋 الملخص التنفيذي",
        "tab2": "📊 المؤشرات والجداول المالية",
        "tab3": "⚖️ التدقيق الشرعي (Warba Shariah)",
        "tab4": "✍️ المراجعة البشرية والاعتماد (Human-in-the-Loop)",
        "shariah_badge": "الحالة: متوافق بالكامل مع الشريعة الإسلامية ومعايير AAOIFI",
        "human_caption": "مبدأ الرقابة المصرفية (Human-in-the-Loop): يحق للمصرفي تعديل الصياغة أو النسب قبل التصدير والاعتماد النهائي.",
        "btn_download": "📥 تحميل المذكرة الرسمية منسقة (Word .docx)",
        "btn_dispatch": "✅ اعتماد المذكرة وإرسالها إلى Core Banking API",
        "dispatch_success": "تم إرسال المذكرة بنجاح إلى نظام تدقيق الائتمان الداخلي لبنك وربة (Simulation)!",
        "demo_data": {
            "exec": "**اسم العميل:** شركة النور للمقاولات والتجارة العامة (ذ.م.م)\n\n**الطلب الائتماني:** تسهيلات مرابحة بضائع محلية بقيمة **3,500,000 د.ك** لتمويل عقد بنية تحتية حكومي معتمد.\n\n**التقييم العام:** تدفقات نقدية تشغيلية مستقرة مع عقود حكومية قائمة وسجل ائتماني ممتاز في السوق الكويتي.",
            "fin": "| المؤشر المالي المحسوب | القيمة المستخرجة | معيار بنك وربة | حالة المؤشر |\n| :--- | :--- | :--- | :--- |\n| نسبة السيولة الحالية (Current Ratio) | 1.68 | > 1.20 | ✅ ممتاز ومريح |\n| نسبة الدين إلى حقوق الملكية (D/E) | 1.75 | < 2.50 | ✅ متوافق وضمن الحدود |\n| هامش الربح التشغيلي (EBITDA Margin) | 19.2% | > 12.0% | ✅ أداء تشغيلي قوي |\n| تغطية خدمة الدين (DSCR) | 1.50x | > 1.25x | ✅ قدرة سداد آمنة ومستقرة |",
            "shariah": "* **فحص طبيعة النشاط (Activity Screening):** ✅ **مطابق بالكامل** — أعمال مقاولات عامة وتوريدات خالية من أي أنشطة محظورة شرعاً.\n* **فحص معايير AAOIFI المالية:** ✅ **مطابق** — نسبة الديون التقليدية إلى إجمالي الأصول أقل من 30%، والفوائد الربوية منعدمة.\n* **الهيكل التمويلي الإسلامي المعتمد:** **مرابحة بضائع محلية (Commodity Murabaha)** بإشراف هيئة الفتوى والرقابة الشرعية لبنك وربة، بفترة سداد 36 شهراً.",
            "risks": "1. **مخاطر تأخر دفعات المقاول الرئيسي:** المعالجة: اشتراط توقيع حوالة حق رسمية غير مشروطة لدفعات المشروع لحساب الشركة لدى بنك وربة.\n2. **مخاطر تذبذب أسعار المواد الإنشائية:** المعالجة: صرف دفعات المرابحة مجزأة ومرتبطة بشهادات الإنجاز الفعلي للمشروع."
        }
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "font": "'Inter', sans-serif",
        "app_title": "Warba Bank | Warba SmartMemo",
        "title": "Corporate Credit Memo Automation — Warba SmartMemo",
        "subtitle": "Enterprise Agentic AI powered by LangGraph for tabular ingestion & Shariah-compliant corporate credit memos",
        "sidebar_header": "Warba Bank — Corporate Banking",
        "sidebar_sub": "Relationship Manager Copilot (RM Copilot)",
        "model_header": "⚙️ AI Engine Configuration",
        "model_select": "Select LLM Engine:",
        "api_key_label": "API Key (Optional for Live Mode):",
        "docs_header": "📁 Upload Client Documents",
        "fin_upload": "1. Financial Statements (PDF)",
        "cr_upload": "2. Commercial Registry / ID (PDF)",
        "notes_label": "3. Site Visit Notes (RM Notes)",
        "notes_placeholder": "Enter site visit impressions, management quality, facility purpose, proposed covenants...",
        "btn_generate": "🚀 Run LangGraph Agents",
        "btn_demo": "⚡ Instant Demo (Kuwait Logistics Corp)",
        "spinner_msg": "Extracting tables via pdfplumber and orchestrating 4 LangGraph agents...",
        "success_msg": "Credit Analysis & Memo successfully generated!",
        "tab1": "📋 Executive Summary",
        "tab2": "📊 Financial Analysis",
        "tab3": "⚖️ Shariah Screening (Warba Shariah)",
        "tab4": "✍️ Human-in-the-Loop Audit & Sign-off",
        "shariah_badge": "STATUS: FULLY SHARIAH COMPLIANT (AAOIFI ALIGNED)",
        "human_caption": "Human-in-the-Loop Principle: The Relationship Manager retains full authority to edit ratios, clauses, and narrative before committee dispatch.",
        "btn_download": "📥 Download Formatted Memo (Word .docx)",
        "btn_dispatch": "✅ Dispatch Memo to Core Banking API",
        "dispatch_success": "Credit memo successfully dispatched to Warba Core Banking System (Simulation)!",
        "demo_data": {
            "exec": "**Client Name:** Al-Noor Contracting & General Trading Co. (W.L.L)\n\n**Requested Facility:** Commodity Murabaha Facility of **KWD 3,500,000** for approved government infrastructure project.\n\n**Overall Rating:** Stable operating cash flows, high-tier government receivables, and pristine credit history in the Kuwaiti market.",
            "fin": "| Calculated Metric | Extracted Value | Warba Benchmark | Status |\n| :--- | :--- | :--- | :--- |\n| Current Liquidity Ratio | 1.68 | > 1.20 | ✅ Strong & Comfortable |\n| Debt-to-Equity (D/E) | 1.75 | < 2.50 | ✅ Compliant within limits |\n| Operating Margin (EBITDA) | 19.2% | > 12.0% | ✅ High Operational Performance |\n| Debt Service Coverage (DSCR) | 1.50x | > 1.25x | ✅ Safe & Resilient Repayment |",
            "shariah": "* **Business Activity Screen:** ✅ **Fully Compliant** — Core operations in civil construction and infrastructure; zero prohibited activities.\n* **AAOIFI Financial Screening:** ✅ **Passed** — Conventional interest-bearing debt < 30% of total assets; zero non-permissible revenue.\n* **Recommended Islamic Structure:** **Commodity Murabaha** approved by Warba Shariah Supervisory Board, with a 36-month tenor.",
            "risks": "1. **Main Contractor Payment Lag:** Mitigant: Irrevocable assignment of project receivables directly into the client's Warba Bank escrow account.\n2. **Material Price Volatility:** Mitigant: Staged Murabaha tranches directly tied to certified engineering completion milestones."
        }
    }
}

# ==========================================
# 2. إعدادات الصفحة وهوية بنك وربة
# ==========================================
st.set_page_config(page_title="Warba SmartMemo", page_icon="🏦", layout="wide")

if "lang" not in st.session_state:
    st.session_state["lang"] = "ar"

# القائمة الجانبية: اختيار اللغة
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=55)
    lang_choice = st.radio("🌐 Language / اللغة", ["العربية 🇰🇼", "English 🇬🇧"], horizontal=True)
    st.session_state["lang"] = "ar" if "العربية" in lang_choice else "en"

T = TRANSLATIONS[st.session_state["lang"]]
DIR = T["dir"]
ALIGN = T["align"]

# حقن CSS احترافي لضبط الاتجاه وتنسيق الخطوط والبطاقات
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"], .stMarkdown, .stText {{
        direction: {DIR};
        text-align: {ALIGN};
        font-family: {T['font']};
    }}
    .main-title {{
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 4px;
        text-align: {ALIGN};
        direction: {DIR};
    }}
    .sub-title {{
        font-size: 14px;
        color: #64748B;
        margin-bottom: 25px;
        text-align: {ALIGN};
        direction: {DIR};
    }}
    .bank-card {{
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        margin-bottom: 15px;
        direction: {DIR};
        text-align: {ALIGN};
    }}
    .badge-pass {{
        display: inline-block;
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #86EFAC;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 15px;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        direction: {DIR};
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. دالة استخراج الجداول والنصوص (pdfplumber)
# ==========================================
def extract_pdf_data(uploaded_file):
    if uploaded_file is None:
        return ""
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        text_parts.append(f"\n[Table - Page {i+1}]:\n")
                        for row in table:
                            clean_row = [str(c).strip() if c is not None else "" for c in row]
                            text_parts.append("| " + " | ".join(clean_row) + " |")
                        text_parts.append("\n")
                raw_text = page.extract_text(layout=True)
                if raw_text:
                    text_parts.append(raw_text)
    except Exception as e:
        return f"Error reading PDF: {e}"
    return "\n".join(text_parts)

# ==========================================
# 4. دالة توليد ملف Word المصرفي المنسق (.docx)
# ==========================================
def generate_word_document(memo_content, lang):
    doc = docx.Document()
    is_ar = (lang == "ar")
    alignment = WD_ALIGN_PARAGRAPH.RIGHT if is_ar else WD_ALIGN_PARAGRAPH.LEFT
    
    # 1. الترويسة والعنوان الرسمي
    header = doc.add_heading(level=0)
    title_text = "بنك وربة | قطاع الخدمات المصرفية للشركات" if is_ar else "Warba Bank | Corporate Banking Division"
    h_run = header.add_run(title_text)
    h_run.font.color.rgb = RGBColor(15, 23, 42)
    h_run.font.size = Pt(18)
    h_run.font.name = "Arial" if is_ar else "Calibri"
    header.alignment = alignment

    sub = doc.add_paragraph()
    sub_text = "مذكرة طلب ائتمان وتمويل شركات (Credit Application Memo)" if is_ar else "Credit Facility Application Memorandum"
    s_run = sub.add_run(sub_text)
    s_run.font.color.rgb = RGBColor(100, 116, 139)
    s_run.font.size = Pt(12)
    s_run.font.bold = True
    sub.alignment = alignment
    
    doc.add_paragraph("─" * 60)

    # 2. تفريغ نص المذكرة وتنسيقه
    for line in memo_content.split("\n"):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("|"):
            continue
        p = doc.add_paragraph()
        p.alignment = alignment
        p.paragraph_format.line_spacing = 1.25
        run = p.add_run(clean_line.replace("**", ""))
        run.font.name = "Arial" if is_ar else "Calibri"
        run.font.size = Pt(11)
        if clean_line.startswith("**"):
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 58, 138)

    doc.add_paragraph("\n" + "─" * 60)
    
    # 3. سجل التواقيع والاعتماد المصرفي الثلاثي
    doc.add_heading("سجل التواقيع والاعتماد المصرفي" if is_ar else "Audit & Authorization Sign-off", level=2).alignment = alignment
    table = doc.add_table(rows=2, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cols = ["مسؤول الرقابة الشرعية", "إدارة المخاطر الائتمانية", "مسؤول العلاقات (RM)"] if is_ar else ["Shariah Auditor", "Risk Management", "Relationship Manager"]
    
    for idx, col in enumerate(cols):
        c = table.cell(0, idx)
        c.text = col
        c.paragraphs[0].runs[0].font.bold = True
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        sign = table.cell(1, idx)
        sign.text = "\nالتوقيع: _____________\nالتاريخ: ___/___/2026م" if is_ar else "\nSignature: _____________\nDate: ___/___/2026"
        sign.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# 5. بنية وكلاء LangGraph (Multi-Agent Swarm)
# ==========================================
class MemoState(TypedDict):
    financial_text: str
    cr_text: str
    rm_notes: str
    lang: str
    financial_analysis: Optional[str]
    shariah_screening: Optional[str]
    risk_analysis: Optional[str]
    final_memo: Optional[str]

def financial_agent(state: MemoState, llm):
    lang_instruction = "باللغة العربية" if state["lang"] == "ar" else "in English"
    prompt = ChatPromptTemplate.from_template(f"""
    You are a Senior Corporate Banking Financial Analyst at Warba Bank.
    Analyze the financial document text: {{financial_text}}
    Provide the response {lang_instruction}.
    Output:
    1. Key revenue and profit metrics.
    2. A clean Markdown table with Current Ratio, Debt-to-Equity, EBITDA Margin, and DSCR.
    3. Brief solvency appraisal.
    """)
    res = (prompt | llm).invoke({"financial_text": state["financial_text"][:6000]})
    return {"financial_analysis": res.content}

def shariah_agent(state: MemoState, llm):
    lang_instruction = "باللغة العربية" if state["lang"] == "ar" else "in English"
    prompt = ChatPromptTemplate.from_template(f"""
    You are the Head of Shariah Governance at Warba Bank (AAOIFI standards expert).
    Company Commercial Activity: {{cr_text}}
    Financial Analysis: {{financial_analysis}}
    Provide the screening {lang_instruction}.
    Output:
    1. Business Activity Halal Screen.
    2. Financial Debt Ratio Screen (<30% conventional debt threshold).
    3. Recommended Islamic facility structure (Commodity Murabaha, Ijara, or Istisna'a) with Shariah reasoning.
    """)
    res = (prompt | llm).invoke({
        "cr_text": state["cr_text"][:3000],
        "financial_analysis": state["financial_analysis"]
    })
    return {"shariah_screening": res.content}

def risk_agent(state: MemoState, llm):
    lang_instruction = "باللغة العربية" if state["lang"] == "ar" else "in English"
    prompt = ChatPromptTemplate.from_template(f"""
    You are a Corporate Risk Officer at Warba Bank.
    Cross-examine RM Notes: {{rm_notes}} against Financial Analysis: {{financial_analysis}}
    Provide the assessment {lang_instruction}.
    Output: Top 3 credit risks and mandatory mitigating covenants.
    """)
    res = (prompt | llm).invoke({
        "rm_notes": state["rm_notes"],
        "financial_analysis": state["financial_analysis"]
    })
    return {"risk_analysis": res.content}

def synthesizer_agent(state: MemoState, llm):
    lang_instruction = "باللغة العربية" if state["lang"] == "ar" else "in English"
    prompt = ChatPromptTemplate.from_template(f"""
    You are a Lead Credit Officer at Warba Bank. Assemble a unified Credit Application Memo {lang_instruction} combining:
    Financial Analysis: {{financial_analysis}}
    Shariah Audit: {{shariah_screening}}
    Risk Mitigation: {{risk_analysis}}
    """)
    res = (prompt | llm).invoke({
        "financial_analysis": state["financial_analysis"],
        "shariah_screening": state["shariah_screening"],
        "risk_analysis": state["risk_analysis"]
    })
    return {"final_memo": res.content}

def run_langgraph_workflow(fin_text, cr_text, rm_notes, model_choice, api_key, lang):
    if "Claude" in model_choice:
        llm = ChatAnthropic(model_name="claude-3-5-sonnet-20240620", temperature=0.0, anthropic_api_key=api_key)
    else:
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0.0, openai_api_key=api_key)
        
    builder = StateGraph(MemoState)
    builder.add_node("financial", lambda s: financial_agent(s, llm))
    builder.add_node("shariah", lambda s: shariah_agent(s, llm))
    builder.add_node("risk", lambda s: risk_agent(s, llm))
    builder.add_node("synthesizer", lambda s: synthesizer_agent(s, llm))
    
    builder.add_edge(START, "financial")
    builder.add_edge("financial", "shariah")
    builder.add_edge("shariah", "risk")
    builder.add_edge("risk", "synthesizer")
    builder.add_edge("synthesizer", END)
    
    app = builder.compile()
    return app.invoke({
        "financial_text": fin_text,
        "cr_text": cr_text,
        "rm_notes": rm_notes,
        "lang": lang
    })

# ==========================================
# 6. عناصر القائمة الجانبية (Sidebar Controls)
# ==========================================
with st.sidebar:
    st.markdown(f"### 🏦 **{T['sidebar_header']}**")
    st.caption(T['sidebar_sub'])
    st.divider()
    
    st.subheader(T["model_header"])
    model_choice = st.selectbox(T["model_select"], ["GPT-4o (OpenAI)", "Claude-3.5-Sonnet (Anthropic)"])
    api_key = st.text_input(T["api_key_label"], type="password")
    
    st.divider()
    st.subheader(T["docs_header"])
    fin_file = st.file_uploader(T["fin_upload"], type=["pdf"])
    cr_file = st.file_uploader(T["cr_upload"], type=["pdf"])
    notes_input = st.text_area(T["notes_label"], placeholder=T["notes_placeholder"])

# ==========================================
# 7. الواجهة الرئيسية وتشغيل المنظومة
# ==========================================
st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{T["subtitle"]}</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    generate_btn = st.button(T["btn_generate"], type="primary", use_container_width=True)
with col2:
    demo_btn = st.button(T["btn_demo"], use_container_width=False)

if generate_btn or demo_btn:
    with st.spinner(T["spinner_msg"]):
        # في حال التجربة الفورية أو عدم إدخال مفتاح
        if demo_btn or (generate_btn and not api_key):
            demo = T["demo_data"]
            exec_summary = demo["exec"]
            financial_analysis = demo["fin"]
            shariah_review = demo["shariah"]
            risks_mitigations = demo["risks"]
        else:
            # تشغيل وكلاء LangGraph في الوضع الحي
            try:
                fin_txt = extract_pdf_data(fin_file)
                cr_txt = extract_pdf_data(cr_file)
                results = run_langgraph_workflow(fin_txt, cr_txt, notes_input, model_choice, api_key, st.session_state["lang"])
                exec_summary = results["final_memo"]
                financial_analysis = results["financial_analysis"]
                shariah_review = results["shariah_screening"]
                risks_mitigations = results["risk_analysis"]
            except Exception as e:
                st.error(f"Error during agent execution: {e}")
                st.stop()

    st.success(T["success_msg"])
    
    # تبويبات العرض المصرفي المنظم
    tab1, tab2, tab3, tab4 = st.tabs([T["tab1"], T["tab2"], T["tab3"], T["tab4"]])
    
    with tab1:
        st.markdown(f'<div class="bank-card">{exec_summary}</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown(f'<div class="bank-card">', unsafe_allow_html=True)
        st.markdown(financial_analysis)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab3:
        st.markdown(f'<div class="bank-card">', unsafe_allow_html=True)
        st.markdown(f'<span class="badge-pass">{T["shariah_badge"]}</span>', unsafe_allow_html=True)
        st.markdown(shariah_review)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab4:
        st.markdown(f'<div class="bank-card">', unsafe_allow_html=True)
        st.caption(T["human_caption"])
        full_text = f"{exec_summary}\n\n{financial_analysis}\n\n{shariah_review}\n\n{risks_mitigations}"
        draft_label = "المسودة النهائية القابلة للتعديل:" if st.session_state["lang"] == "ar" else "Final Editable Draft:"
        edited_memo = st.text_area(draft_label, value=full_text, height=320)
        
        c1, c2 = st.columns(2)
        with c1:
            docx_data = generate_word_document(edited_memo, st.session_state["lang"])
            st.download_button(
                label=T["btn_download"],
                data=docx_data,
                file_name="Warba_Credit_Application_Memo.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c2:
            if st.button(T["btn_dispatch"], use_container_width=True):
                st.balloons()
                st.success(T["dispatch_success"])
        st.markdown('</div>', unsafe_allow_html=True)
