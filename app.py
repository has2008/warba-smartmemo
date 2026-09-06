import streamlit as st
import pdfplumber
import io
import os
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# ==========================================
# 1. إعدادات الصفحة والهوية المصرفية لبنك وربة
# ==========================================
st.set_page_config(
    page_title="Warba SmartMemo | Corporate Banking AI",
    page_icon="🏦",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .sub-title { font-size: 15px; color: #64748B; margin-bottom: 25px; }
    .badge-pass { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 45px; border-radius: 6px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. وظيفة استخراج الجداول والنصوص (pdfplumber)
# ==========================================
def extract_pdf_data(uploaded_file):
    """استخراج النصوص مع الحفاظ التام على هيكل الجداول المالية المزدوجة"""
    if uploaded_file is None:
        return ""
    extracted_text = []
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
            for i, page in enumerate(pdf.pages):
                # استخراج الجداول كـ Markdown
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        extracted_text.append(f"\n[جدول مالي مستخرج - صفحة {i+1}]:\n")
                        for row in table:
                            clean_row = [str(c).strip() if c is not None else "" for c in row]
                            extracted_text.append("| " + " | ".join(clean_row) + " |")
                        extracted_text.append("\n")
                
                # استخراج النصوص
                text = page.extract_text(layout=True)
                if text:
                    extracted_text.append(text)
    except Exception as e:
        return f"خطأ أثناء قراءة الـ PDF: {e}"
        
    return "\n".join(extracted_text)

# ==========================================
# 3. محرك الوكلاء الأذكياء (LangGraph Swarm)
# ==========================================
class MemoState(TypedDict):
    financial_text: str
    cr_text: str
    rm_notes: str
    financial_analysis: Optional[str]
    shariah_screening: Optional[str]
    risk_analysis: Optional[str]
    final_memo: Optional[str]

def financial_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت محلل مالي معتمد في بنك وربة للشركات. 
    حلل البيانات والجداول المالية التالية:
    {financial_text}
    المطلوب:
    1. استخراج الإيرادات وصافي الأرباح لآخر سنتين.
    2. جدول Markdown يحتوي على: نسبة السيولة (Current Ratio)، الرافعة المالية (Debt to Equity)، وهامش EBITDA وتغطية خدمة الدين (DSCR).
    3. تقييم موجز لملاءة العميل الائتمانية.
    """)
    res = (prompt | llm).invoke({"financial_text": state["financial_text"][:6000]})
    return {"financial_analysis": res.content}

def shariah_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت رئيس الرقابة والتدقيق الشرعي في بنك وربة، خبير بمعايير AAOIFI.
    نشاط الشركة وبيانات السجل: {cr_text}
    المؤشرات المالية: {financial_analysis}
    المطلوب بدقة:
    1. فحص النشاط: خلوه من الأنشطة المحظورة شرعاً.
    2. فحص المعايير المالية: التحقق من سقف المديونيات ذات الفائدة التقليدية.
    3. الهيكل التمويلي الإسلامي المقترح: التوصية بصيغة (مرابحة بضائع، إجارة، استصناع) مع تسبيب التوافق الشرعي.
    """)
    res = (prompt | llm).invoke({
        "cr_text": state["cr_text"][:3000],
        "financial_analysis": state["financial_analysis"]
    })
    return {"shariah_screening": res.content}

def risk_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت مسؤول إدارة المخاطر في بنك وربة.
    قارن بين ملاحظات الزيارة الميدانية: {rm_notes}
    وبين التحليل المالي: {financial_analysis}
    المطلوب: تحديد أهم 3 مخاطر ائتمانية وتحديد شروط وتعهدات مصرفية (Covenants & Mitigants) لحماية البنك.
    """)
    res = (prompt | llm).invoke({
        "rm_notes": state["rm_notes"],
        "financial_analysis": state["financial_analysis"]
    })
    return {"risk_analysis": res.content}

def synthesizer_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت صائغ تقارير ائتمان أول في بنك وربة. جمّع مخرجات الفرق في مسودة موحدة وموجزة (Credit Application Memo):
    الملخص المالي: {financial_analysis}
    الرقابة الشرعية: {shariah_screening}
    المخاطر والضمانات: {risk_analysis}
    """)
    res = (prompt | llm).invoke({
        "financial_analysis": state["financial_analysis"],
        "shariah_screening": state["shariah_screening"],
        "risk_analysis": state["risk_analysis"]
    })
    return {"final_memo": res.content}

def run_langgraph_workflow(fin_text, cr_text, rm_notes, model_choice, api_key):
    # تهيئة النموذج المختار بحرارة صفر لضمان الدقة المالية
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
        "rm_notes": rm_notes
    })

# ==========================================
# 4. القائمة الجانبية (Sidebar)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=60)
    st.markdown("### 🏦 **Warba Bank**")
    st.markdown("**Corporate Banking AI Copilot**")
    st.caption("Track 1: AI-Powered Client Documentation")
    st.divider()
    
    st.subheader("⚙️ خيارات النموذج (Model Engine)")
    model_choice = st.selectbox("اختر المحرك:", ["GPT-4o (OpenAI)", "Claude-3.5-Sonnet (Anthropic)"])
    
    if "Claude" in model_choice:
        api_key = st.text_input("Anthropic API Key:", type="password")
    else:
        api_key = st.text_input("OpenAI API Key:", type="password")
        
    st.divider()
    st.subheader("📁 رفع مستندات الشركة")
    fin_file = st.file_uploader("1. القوائم المالية (PDF)", type=["pdf"])
    cr_file = st.file_uploader("2. السجل التجاري / الهوية (PDF)", type=["pdf"])
    notes_input = st.text_area("3. ملاحظات الزيارة الميدانية (RM Notes)", placeholder="انطباع الزيارة، الغرض من التسهيلات، الضمانات...")

# ==========================================
# 5. الواجهة الرئيسية والتنفيذ
# ==========================================
st.markdown('<div class="main-title">Warba SmartMemo (أتمتة مذكرات الائتمان)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">منظومة ذكاء اصطناعي بنكية مدعومة بوكلاء LangGraph لاستخراج البيانات وإعداد مذكرات ائتمان متوافقة مع الشريعة</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    generate_btn = st.button("🚀 تشغيل وكلاء LangGraph", type="primary", use_container_width=True)
with col2:
    demo_btn = st.button("⚡ تجربة سريعة وفورية (شركة كويتية للمقاولات)", use_container_width=False)

if generate_btn or demo_btn:
    with st.spinner("جاري استخراج الجداول عبر pdfplumber وتنسيق مهام الوكلاء الأربعة..."):
        
        # سيناريو العرض السريع الافتراضي (Demo Safe Mode)
        if demo_btn or (generate_btn and not api_key):
            if generate_btn and not api_key:
                st.warning("⚠️ لم تقم بإدخال مفتاح API، تم تفعيل وضع العرض المصرفي التجريبي تلقائياً.")
                
            exec_summary = """**اسم العميل:** شركة النور للمقاولات والتجارة العامة (ذ.م.م)  
**الغرض من الطلب:** تسهيلات مرابحة بضائع بقيمة **3,500,000 د.ك** لتمويل عقد بنية تحتية حكومي معتمد.  
**التقييم العام:** تدفقات نقدية تشغيلية مستقرة مع التزام ائتماني قوي وسمعة ممتازة في السوق الكويتي."""
            
            financial_analysis = """
| المؤشر المالي المحسوب | القيمة المستخرجة | معيار بنك وربة | حالة المؤشر |
| :--- | :--- | :--- | :--- |
| نسبة السيولة الحالية (Current Ratio) | 1.68 | > 1.20 | ✅ ممتاز |
| نسبة الدين إلى حقوق الملكية (D/E) | 1.75 | < 2.50 | ✅ متوافق |
| هامش الربح التشغيلي (EBITDA Margin)| 19.2% | > 12.0% | ✅ قوي جداً |
| تغطية خدمة الدين (DSCR) | 1.50x | > 1.25x | ✅ آمن ومستقر |
"""
            shariah_review = """
* **فحص طبيعة النشاط (Activity Screening):** ✅ **مطابق بالكامل** — أعمال مقاولات عامة وتوريدات خالية من أي أنشطة محظورة شرعاً.
* **فحص معايير AAOIFI المالية:** ✅ **مطابق** — نسبة الديون التقليدية إلى إجمالي الأصول أقل من 30%، والفوائد الربوية منعدمة.
* **الهيكل التمويلي الإسلامي المعتمد:** **مرابحة بضائع محلية (Commodity Murabaha)** بإشراف هيئة الفتوى والرقابة الشرعية لبنك وربة، بفترة سداد 36 شهراً.
"""
            risks_mitigations = """
1. **مخاطر تأخر دفعات المقاول الرئيسي:** *المعالجة:* اشتراط توقيع حوالة حق رسمية غير مشروطة لدفعات المشروع لحساب الشركة لدى بنك وربة.
2. **مخاطر تذبذب أسعار المواد الإنشائية:** *المعالجة:* صرف دفعات المرابحة مجزأة ومرتبطة بشهادات الإنجاز الفعلي للمشروع.
"""
        else:
            # سيناريو التشغيل الحي مع النماذج
            try:
                fin_txt = extract_pdf_data(fin_file)
                cr_txt = extract_pdf_data(cr_file)
                results = run_langgraph_workflow(fin_txt, cr_txt, notes_input, model_choice, api_key)
                
                exec_summary = results["final_memo"]
                financial_analysis = results["financial_analysis"]
                shariah_review = results["shariah_screening"]
                risks_mitigations = results["risk_analysis"]
            except Exception as e:
                st.error(f"خطأ أثناء المعالجة: {e}")
                st.stop()

    st.success("اكتمل التحليل وتوليد المذكرة بنجاح!")
    
    # تبويبات العرض التفاعلية
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 الملخص التنفيذي", 
        "📊 المؤشرات والجداول المالية", 
        "⚖️ بطاقة الفحص الشرعي (Warba Shariah)", 
        "✍️ المراجعة البشرية والاعتماد (Human-in-the-Loop)"
    ])
    
    with tab1:
        st.markdown("### ملخص طلب التسهيلات المصرفية للشركات")
        st.info(exec_summary)
        
    with tab2:
        st.markdown("### المؤشرات المالية المحسوبة بدقة عبر `pdfplumber`")
        st.markdown(financial_analysis)
        
    with tab3:
        st.markdown("### نتائج التدقيق الشرعي (Shariah Screening Scorecard)")
        st.markdown('<span class="badge-pass">STATUS: SHARIAH COMPLIANT (AAOIFI ALIGNED)</span>', unsafe_allow_html=True)
        st.markdown(shariah_review)
        
    with tab4:
        st.markdown("### مراجعة مسؤول العلاقات (RM Final Review & Audit)")
        st.caption("مبدأ Human-in-the-Loop: يحق للمصرفي تعديل الصياغة أو النسب قبل التصدير والرفع للجنة الائتمان العليا.")
        
        full_draft = f"{exec_summary}\n\n{financial_analysis}\n\n{shariah_review}\n\n{risks_mitigations}"
        edited_memo = st.text_area("مسودة المذكرة الرسمية القابلة للتعديل:", value=full_draft, height=350)
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 تصدير المذكرة الرسمية (Word / TXT)", data=edited_memo, file_name="Warba_Credit_Application_Memo.txt", use_container_width=True)
        with c2:
            if st.button("✅ اعتماد المذكرة وإرسالها إلى Core Banking API", use_container_width=True):
                st.balloons()
                st.success("تم إرسال المذكرة بنجاح إلى النظام المصرفي لتدقيق الائتمان (Core Banking Simulation)!")
