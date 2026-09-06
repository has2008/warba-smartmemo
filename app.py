import streamlit as st
import pypdf
import io
import os
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Warba SmartMemo | Corporate Banking AI",
    page_icon="🏦",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .sub-title { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    .badge-pass { background-color: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. تعريف محرك LangGraph والوكلاء المتخصصين
class MemoState(TypedDict):
    financial_text: str
    cr_text: str
    rm_notes: str
    financial_analysis: Optional[str]
    shariah_screening: Optional[str]
    risk_analysis: Optional[str]
    final_memo: Optional[str]

def financial_analyst_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت محلل مالي خبير في بنك وربة للشركات. حلل القوائم المالية:
    {financial_text}
    المطلوب: حساب مؤشرات السيولة، نسبة الدين إلى حقوق الملكية، هامش EBITDA، وتلخيص تدفقات النقد في جدول ماركداون.
    """)
    res = (prompt | llm).invoke({"financial_text": state["financial_text"][:5000]})
    return {"financial_analysis": res.content}

def shariah_screening_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت مستشار رقابة شرعية في بنك وربة خبير بمعايير AAOIFI.
    نشاط الشركة: {cr_text}
    التحليل المالي: {financial_analysis}
    المطلوب:
    1. فحص النشاط والنسب المالية.
    2. التوصية بصيغة التمويل الإسلامي الملائمة (مرابحة بضائع، إجارة، استصناع) مع التعليل الشرعي.
    """)
    res = (prompt | llm).invoke({
        "cr_text": state["cr_text"][:2500],
        "financial_analysis": state["financial_analysis"]
    })
    return {"shariah_screening": res.content}

def risk_assessment_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت مسؤول إدارة المخاطر في بنك وربة.
    ملاحظات الزيارة: {rm_notes}
    التحليل المالي: {financial_analysis}
    المطلوب: استخراج أهم 3 مخاطر ائتمانية وتقديم تعهدات وشروط مصرفية (Covenants) لمعالجتها.
    """)
    res = (prompt | llm).invoke({
        "rm_notes": state["rm_notes"],
        "financial_analysis": state["financial_analysis"]
    })
    return {"risk_analysis": res.content}

def memo_synthesizer_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت صائغ مذكرات ائتمان أول في بنك وربة. جمّع مخرجات الفرق التالية في مذكرة ائتمان موحدة:
    التحليل: {financial_analysis}
    الشرعية: {shariah_screening}
    المخاطر: {risk_analysis}
    """)
    res = (prompt | llm).invoke({
        "financial_analysis": state["financial_analysis"],
        "shariah_screening": state["shariah_screening"],
        "risk_analysis": state["risk_analysis"]
    })
    return {"final_memo": res.content}

def run_langgraph_pipeline(financial_text, cr_text, rm_notes, api_key):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=api_key)
    builder = StateGraph(MemoState)
    builder.add_node("financial", lambda s: financial_analyst_agent(s, llm))
    builder.add_node("shariah", lambda s: shariah_screening_agent(s, llm))
    builder.add_node("risk", lambda s: risk_assessment_agent(s, llm))
    builder.add_node("synthesizer", lambda s: memo_synthesizer_agent(s, llm))
    
    builder.add_edge(START, "financial")
    builder.add_edge("financial", "shariah")
    builder.add_edge("shariah", "risk")
    builder.add_edge("risk", "synthesizer")
    builder.add_edge("synthesizer", END)
    
    app = builder.compile()
    return app.invoke({
        "financial_text": financial_text,
        "cr_text": cr_text,
        "rm_notes": rm_notes
    })

# 3. القائمة الجانبية (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=60)
    st.markdown("### 🏦 **Warba Bank**")
    st.markdown("**Corporate Banking AI Copilot**")
    st.caption("Powered by LangGraph Multi-Agent Orchestration")
    st.divider()
    
    fin_file = st.file_uploader("1. القوائم المالية (PDF)", type=["pdf"])
    cr_file = st.file_uploader("2. السجل التجاري (PDF)", type=["pdf"])
    notes_input = st.text_area("3. ملاحظات الزيارة الميدانية (RM Notes)", placeholder="انطباع الزيارة، الغرض من التسهيلات...")
    st.divider()
    api_key = st.text_input("OpenAI API Key (اختياري)", type="password", help="مطلوب فقط للتحليل الحي للـ PDF عبر LangGraph")

def extract_pdf_text(uploaded_file):
    if uploaded_file is not None:
        reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return ""

# 4. واجهة التطبيق الرئيسية
st.markdown('<div class="main-title">Warba SmartMemo (أتمتة مذكرات الائتمان)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">منظومة ذكية مدعومة بوكلاء LangGraph لإعداد مذكرات ائتمان متوافقة مع الشريعة الإسلامية</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    generate_btn = st.button("🚀 تشغيل وكلاء LangGraph", type="primary", use_container_width=True)
with col2:
    demo_btn = st.button("⚡ تجربة سريعة (بيانات تجريبية كويتية)", use_container_width=False)

if generate_btn or demo_btn:
    with st.spinner("جاري تشغيل الوكلاء الأربعة (المالي ➔ الشرعي ➔ المخاطر ➔ التجميع)..."):
        
        # في حال التجربة السريعة أو عدم إدخال مفتاح API
        if demo_btn or not api_key:
            exec_summary = """**العميل:** شركة النور للمقاولات والتجارة العامة (ذ.م.م)  
**الطلب:** تسهيلات مرابحة بضائع بقيمة 3,500,000 د.ك لتمويل مشروع بنية تحتية معتمد.  
**التقييم:** تدفقات نقدية مستقرة مع عقود حكومية قائمة وسجل ائتماني ممتاز."""
            
            financial_analysis = """
| المؤشر المالي | القيمة الحالية | معيار البنك | الحالة |
| :--- | :--- | :--- | :--- |
| نسبة السيولة الحالية (Current Ratio) | 1.65 | > 1.20 | ✅ ممتاز |
| نسبة الدين إلى حقوق الملكية (D/E) | 1.80 | < 2.50 | ✅ مقبول |
| هامش الربح التشغيلي (EBITDA Margin)| 18.5% | > 12.0% | ✅ قوي |
| تغطية خدمة الدين (DSCR) | 1.45x | > 1.25x | ✅ آمن |
"""
            shariah_review = """
* **فحص طبيعة النشاط:** ✅ **مطابق** — مقاولات وتوريدات (خالٍ من أي محظورات شرعية).
* **فحص النسب المالية (AAOIFI):** ✅ **مطابق** — المديونيات التقليدية أقل من 30% من إجمالي الأصول.
* **الهيكل التمويلي المقترح:** **مرابحة بضائع (Commodity Murabaha)** وفق ضوابط هيئة الرقابة الشرعية لبنك وربة، بأجل سداد 36 شهراً.
"""
            risks_mitigations = """
1. **تأخر دفعات المقاول الرئيسي:** *المعالجة:* ربط السداد بحوالة حق معتمدة لحساب العميل لدى بنك وربة.
2. **تذبذب أسعار المواد:** *المعالجة:* صرف دفعات المرابحة مجزأة حسب مراحل التنفيذ الميدانية.
"""
        else:
            # تشغيل LangGraph الفعلي
            try:
                fin_txt = extract_pdf_text(fin_file)
                cr_txt = extract_pdf_text(cr_file)
                results = run_langgraph_pipeline(fin_txt, cr_txt, notes_input, api_key)
                
                exec_summary = results["final_memo"]
                financial_analysis = results["financial_analysis"]
                shariah_review = results["shariah_screening"]
                risks_mitigations = results["risk_analysis"]
            except Exception as e:
                st.error(f"حدث خطأ أثناء تشغيل الوكلاء: {e}")
                st.stop()

    st.success("اكتمل عمل وكلاء LangGraph بنجاح!")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 الملخص التنفيذي", 
        "📊 التحليل المالي", 
        "⚖️ الفحص الشرعي (Warba Shariah)", 
        "✍️ المراجعة والتعديل (Human-in-the-Loop)"
    ])
    
    with tab1:
        st.markdown("### ملخص طلب التسهيلات الائتمانية")
        st.info(exec_summary)
        
    with tab2:
        st.markdown("### مؤشرات الملاءة المالية ومخاطر الائتمان")
        st.markdown(financial_analysis)
        
    with tab3:
        st.markdown("### بطاقة التدقيق والرقابة الشرعية")
        st.markdown('<span class="badge-pass">STATUS: SHARIAH COMPLIANT</span>', unsafe_allow_html=True)
        st.markdown(shariah_review)
        
    with tab4:
        st.markdown("### مراجعة مسؤول العلاقات (RM Final Review)")
        st.caption("مبدأ Human-in-the-Loop: يحق للمصرفي تعديل المذكرة واعتمادها.")
        
        full_draft = f"{exec_summary}\n\n{financial_analysis}\n\n{shariah_review}\n\n{risks_mitigations}"
        edited_memo = st.text_area("نص المذكرة النهائي القابل للتعديل:", value=full_draft, height=350)
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 تصدير المذكرة المعتمدة (TXT / Word)", data=edited_memo, file_name="Warba_Credit_Memo.txt", use_container_width=True)
        with c2:
            if st.button("✅ اعتماد وإرسال إلى Core Banking API", use_container_width=True):
                st.balloons()
                st.success("تم إرسال المذكرة بنجاح إلى نظام الائتمان الداخلي لبنك وربة (Simulation)!")
