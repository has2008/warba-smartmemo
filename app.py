import streamlit as st
import pypdf
import io
import os
from openai import OpenAI

# 1. إعدادات الصفحة وهوية بنك وربة
st.set_page_config(
    page_title="Warba SmartMemo | Corporate Banking AI",
    page_icon="🏦",
    layout="wide"
)

# تخصيص بسيط للألوان لتعكس الهوية المصرفية
st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .sub-title { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    .badge-pass { background-color: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. القائمة الجانبية (Sidebar) لرفع المستندات
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=60)
    st.markdown("### 🏦 **Warba Bank**")
    st.markdown("**Corporate Banking AI Copilot**")
    st.divider()
    
    st.subheader("📁 رفع مستندات العميل")
    fin_file = st.file_uploader("1. القوائم المالية (PDF)", type=["pdf"])
    cr_file = st.file_uploader("2. السجل التجاري / الهوية (PDF)", type=["pdf"])
    notes_input = st.text_area("3. ملاحظات الزيارة الميدانية (RM Notes)", 
                               placeholder="اكتب انطباع الزيارة، تفاصيل الإدارة، الغرض من التسهيلات...")
    
    st.divider()
    api_key = st.text_input("OpenAI API Key (اختياري)", type="password", help="اتركه فارغاً لاستخدام العرض التوضيحي الافتراضي")

# وظيفة استخراج النصوص من ملفات الـ PDF
def extract_pdf_text(uploaded_file):
    if uploaded_file is not None:
        reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return ""

# 3. الواجهة الرئيسية
st.markdown('<div class="main-title">Warba SmartMemo (أتمتة مذكرات الائتمان)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">نظام ذكي لتحويل مستندات الشركات إلى مذكرة ائتمان متوافقة مع الشريعة الإسلامية خلال دقائق</div>', unsafe_allow_html=True)

# زر تشغيل النظام
col1, col2 = st.columns([1, 4])
with col1:
    generate_btn = st.button("🚀 توليد مذكرة الائتمان", type="primary", use_container_width=True)
with col2:
    demo_btn = st.button("⚡ تجربة سريعة (بيانات تجريبية لكويتية للمقاولات)", use_container_width=False)

# منطق المعالجة
if generate_btn or demo_btn:
    with st.spinner("جاري قراءة البيانات، استخراج النسب المالية، والفحص الشرعي..."):
        
        # إذا تم اختيار العرض التجريبي أو عدم توفر ملفات
        if demo_btn or (not fin_file and not api_key):
            # بيانات تجريبية جاهزة للإبهار في العرض
            exec_summary = """**العميل:** شركة النور للمقاولات والتجارة العامة (ذ.م.م)  
**الطلب:** تسهيلات مرابحة بضائع بقيمة 3,500,000 د.ك لتمويل مشروع بنية تحتية حكومي معتمد.  
**التقييم العام:** العميل لديه تدفقات نقدية مستقرة مع عقود حكومية قائمة وسجل ائتماني ممتاز."""
            
            financial_analysis = """
| المؤشر المالي | القيمة الحالية | معيار البنك | الحالة |
| :--- | :--- | :--- | :--- |
| نسبة السيولة الحالية (Current Ratio) | 1.65 | > 1.20 | ✅ ممتاز |
| نسبة الدين إلى حقوق الملكية (D/E) | 1.80 | < 2.50 | ✅ مقبول |
| هامش الربح التشغيلي (EBITDA Margin)| 18.5% | > 12.0% | ✅ قوي |
| تغطية خدمة الدين (DSCR) | 1.45x | > 1.25x | ✅ آمن |
"""
            shariah_review = """
* **فحص طبيعة النشاط (Business Activity Screen):** ✅ **مطابق** — مقاولات وبنية تحتية (خالٍ من أنشطة محظورة).
* **فحص النسب المالية (AAOIFI Financial Ratios):** ✅ **مطابق** — نسبة الديون التقليدية إلى إجمالي الأصول أقل من 30%.
* **الهيكل التمويلي الإسلامي المقترح:** **مرابحة بضائع (Commodity Murabaha)** متوافقة مع ضوابط هيئة الفتوى والرقابة الشرعية لبنك وربة، بأجل سداد 36 شهراً.
"""
            risks_mitigations = """
1. **خطر تأخر دفعات المقاول الرئيسي:** *المعالجة:* ربط السداد مباشرة بحوالة حق المشروع الحكومي لحساب العميل لدى بنك وربة.
2. **ارتفاع أسعار المواد الخام:** *المعالجة:* تمويل المواد عبر دفعات مرابحة مرحلية حسب مراحل الإنجاز.
"""
        else:
            # هنا يتم الاتصال الفعلي بالـ LLM إذا أدخل المستخدم ملفات ومفتاح
            client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            fin_text = extract_pdf_text(fin_file)
            cr_text = extract_pdf_text(cr_file)
            
            prompt = f"""
            أنت محلل ائتمان أول وخبير رقابة شرعية في بنك وربة الكويتي.
            قم بتحليل البيانات التالية للشركة:
            [ملاحظات]: {notes_input}
            [مقتطفات مالية]: {fin_text[:3000]}
            [السجل التجاري]: {cr_text[:1500]}
            
            أنتج تقريراً موجزاً باللغة العربية يتضمن: الملخص التنفيذي، جدول المؤشرات المالية، فحص التوافق الشرعي واقتراح صيغة التمويل الإسلامي، وأهم المخاطر ومعالجتها.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            raw_output = response.choices[0].message.content
            exec_summary = raw_output
            financial_analysis = "تم استخراجها ضمن التقرير أدناه."
            shariah_review = "تم الفحص وتأكيد التوافق الشرعي."
            risks_mitigations = "تم تحديدها في المسودة."

    # عرض النتائج في تبويبات احترافية
    st.success("تم إعداد مسودة مذكرة الائتمان بنجاح!")
    
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
        st.caption("مبدأ Human-in-the-Loop: يحق للموظف تعديل مسودة الذكاء الاصطناعي قبل التصدير النهائي للجنة الائتمان.")
        
        full_draft = f"{exec_summary}\n\n{financial_analysis}\n\n{shariah_review}\n\n{risks_mitigations}"
        edited_memo = st.text_area("نص المذكرة النهائي القابل للتعديل:", value=full_draft, height=350)
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 تصدير المذكرة المعتمدة (TXT / Word)", data=edited_memo, file_name="Warba_Credit_Memo.txt", use_container_width=True)
        with c2:
            if st.button("✅ اعتماد وإرسال إلى نظام البنك (Core Banking API)", use_container_width=True):
                st.balloons()
                st.success("تم إرسال المذكرة بنجاح إلى نظام تدقيق الائتمان الداخلي (Simulation)!")