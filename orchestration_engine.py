from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# 1. تعريف الحالة المشتركة بين جميع الوكلاء (Graph State)
class MemoState(TypedDict):
    financial_text: str          # نص القوائم المالية
    cr_text: str                 # نص السجل التجاري
    rm_notes: str                # ملاحظات موظف البنك
    financial_analysis: Optional[str]   # ناتج وكيل التحليل المالي
    shariah_screening: Optional[str]    # ناتج وكيل الفحص الشرعي
    risk_analysis: Optional[str]        # ناتج وكيل تقييم المخاطر
    final_memo: Optional[str]           # المذكرة الائتمانية النهائية

# 2. إنشاء نموذج اللغة (LLM)
def get_llm(api_key: str):
    return ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=api_key)

# --------------------------------------------------------------------
# 3. بناء الوكلاء (Agent Nodes)
# --------------------------------------------------------------------

# الوكيل الأول: المحلل المالي (Financial Analyst Agent)
def financial_analyst_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت محلل مالي خبير في بنك وربة للشركات. 
    قم بتحليل نص القوائم المالية المرفقة:
    {financial_text}
    
    المطلوب:
    1. استخراج الإيرادات وصافي الأرباح لآخر سنتين.
    2. حساب جدول باللغة العربية يتضمن: 
       - نسبة السيولة الحالية (Current Ratio)
       - نسبة المديونية لحقوق الملكية (Debt to Equity)
       - هامش EBITDA
    3. تقييم موجز للتدفقات النقدية التشغيلية.
    """)
    chain = prompt | llm
    result = chain.invoke({"financial_text": state["financial_text"][:6000]})
    return {"financial_analysis": result.content}

# الوكيل الثاني: المدقق الشرعي (Shariah Screening Agent)
def shariah_screening_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت مستشار رقابة شرعية معتمد في بنك وربة (بنك إسلامي كويتي) خبير بمعايير AAOIFI.
    بناءً على نشاط الشركة في السجل التجاري:
    {cr_text}
    وبناءً على نتائج التحليل المالي:
    {financial_analysis}
    
    المطلوب:
    1. فحص النشاط: هل النشاط الأساسي متوافق مع الشريعة الإسلامية؟
    2. فحص النسب المالية: نسبة الاقتراض التقليدي وحجم الإيرادات العرضية المحظورة.
    3. تحديد وتفصيل الهيكل التمويلي الإسلامي المناسب للطلب (مرابحة بضائع، إجارة، استصناع) مع بيان الأسباب شرعياً ومصرفياً.
    """)
    chain = prompt | llm
    result = chain.invoke({
        "cr_text": state["cr_text"][:3000],
        "financial_analysis": state["financial_analysis"]
    })
    return {"shariah_screening": result.content}

# الوكيل الثالث: مسؤول المخاطر والتحري (Risk Due-Diligence Agent)
def risk_assessment_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت مسؤول إدارة المخاطر الائتمانية في قطاع الشركات.
    قارن بين ملاحظات الزيارة الميدانية لمسؤول العلاقات (RM):
    {rm_notes}
    وبين التحليل المالي المستخرج:
    {financial_analysis}
    
    المطلوب:
    1. استخراج أهم 3 مخاطر جوهرية (مثل: تركز العملاء، فجوات السيولة، الاعتماد على شخص رئيسي).
    2. اقتراح معالجات وتعهدات مصرفية مشروطة (Covenants & Mitigants) لحماية البنك.
    """)
    chain = prompt | llm
    result = chain.invoke({
        "rm_notes": state["rm_notes"],
        "financial_analysis": state["financial_analysis"]
    })
    return {"risk_analysis": result.content}

# الوكيل الرابع: صائغ المذكرة الائتمانية (Memo Synthesizer Agent)
def memo_synthesizer_agent(state: MemoState, llm):
    prompt = ChatPromptTemplate.from_template("""
    أنت كاتب تقارير ائتمان أول في بنك وربة.
    مهمتك تجميع مخرجات الفرق المتخصصة في مذكرة ائتمان رسمية موحدة (Credit Application Memo).
    
    المدخلات:
    - التحليل المالي: {financial_analysis}
    - الرقابة الشرعية: {shariah_screening}
    - تقييم المخاطر: {risk_analysis}
    
    قم بصياغة المذكرة بشكل احترافي مع أقسام واضحة، جدول المؤشرات، حالة التدقيق الشرعي باللون الأخضر، وتوصية نهائية للجنة الائتمان بالبنك.
    """)
    chain = prompt | llm
    result = chain.invoke({
        "financial_analysis": state["financial_analysis"],
        "shariah_screening": state["shariah_screening"],
        "risk_analysis": state["risk_analysis"]
    })
    return {"final_memo": result.content}

# --------------------------------------------------------------------
# 4. بناء مخطط التدفق والتنسيق (Building the LangGraph Workflow)
# --------------------------------------------------------------------
def build_credit_memo_graph(api_key: str):
    llm = get_llm(api_key)
    
    # تعريف المخطط
    builder = StateGraph(MemoState)
    
    # إضافة العقد (Nodes)
    builder.add_node("financial_node", lambda state: financial_analyst_agent(state, llm))
    builder.add_node("shariah_node", lambda state: shariah_screening_agent(state, llm))
    builder.add_node("risk_node", lambda state: risk_assessment_agent(state, llm))
    builder.add_node("synthesizer_node", lambda state: memo_synthesizer_agent(state, llm))
    
    # ربط الحواف (Edges) لتتابع تدفق البيانات
    builder.add_edge(START, "financial_node")
    builder.add_edge("financial_node", "shariah_node")
    builder.add_edge("shariah_node", "risk_node")
    builder.add_edge("risk_node", "synthesizer_node")
    builder.add_edge("synthesizer_node", END)
    
    # ترجمة وبناء المخطط
    return builder.compile()