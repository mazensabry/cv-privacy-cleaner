import streamlit as st
import fitz  # PyMuPDF
import re
import io
import zipfile

# إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="oldorado | CV Privacy Shield", 
    page_icon="🛡️", 
    layout="centered"
)

# تطبيق تنسيقات CSS لتحسين المحاذاة والواجهة
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    p, h1, h2, h3, h4, div, span {
        text-align: right !important;
        direction: rtl !important;
    }

    .welcome-banner {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        padding: 30px 20px;
        border-radius: 12px;
        border: 1px solid #38bdf8;
        text-align: center !important;
        margin-bottom: 25px;
    }
    
    .welcome-banner h1 {
        color: #38bdf8 !important;
        text-align: center !important;
        margin-bottom: 8px;
        font-size: 26px;
        font-weight: bold;
    }

    .welcome-banner p {
        color: #94a3b8 !important;
        text-align: center !important;
        font-size: 15px;
        margin: 0;
    }

    .steps-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 25px;
    }

    .step-item {
        margin-bottom: 10px;
        color: #cbd5e1;
        font-size: 14px;
    }

    [data-testid="stFileUploader"] {
        direction: rtl;
    }
    </style>
""", unsafe_allow_html=True)

# 1. البانر الترحيبي بالجملة الجديدة
st.markdown("""
    <div class="welcome-banner">
        <h1>oldorado | CV Privacy Shield</h1>
        <p>إزالة بيانات التواصل من الـ CVs قبل إرسالها لأصحاب العمل</p>
    </div>
""", unsafe_allow_html=True)

# 2. كارت الشرح
st.markdown("""
    <div class="steps-card">
        <h4 style="color: #f8fafc; margin-top: 0; margin-bottom: 14px;">📋 طريقة الاستخدام:</h4>
        <div class="step-item"><b>١.</b> قم برفع ملف واحد أو عدة ملفات CVs بصيغة PDF.</div>
        <div class="step-item"><b>٢.</b> اضغط على زر <b>معالجة وتنظيف الـ CVs</b>.</div>
        <div class="step-item"><b>٣.</b> تحمِيل مباشر للملف المفرد بصيغة PDF، أو ملف ZIP مضغوط للمجموعة.</div>
    </div>
""", unsafe_allow_html=True)

# 3. رفع الملفات
uploaded_files = st.file_uploader("📂 رفع ملفات الـ CVs (PDF)", type=["pdf"], accept_multiple_files=True)

# دالة معالجة الـ PDF
def redact_pdf(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{4,}'
    url_pattern = r'(https?://\S+|www\.\S+|linkedin\.com/\S+|github\.com/\S+)'
    keywords = ["Address", "Location", "Street", "City", "العنوان", "المحافظة", "المدينة", "الشارع", "محل الإقامة"]

    for page in doc:
        text = page.get_text("text")
        rects = []
        
        for email in re.findall(email_pattern, text):
            rects.extend(page.search_for(email))
        for url in re.findall(url_pattern, text):
            rects.extend(page.search_for(url))
        for phone in re.findall(phone_pattern, text):
            match_str = phone[0] if isinstance(phone, tuple) else phone
            clean_phone = match_str.strip()
            if len(re.sub(r'\D', '', clean_phone)) >= 7:
                rects.extend(page.search_for(clean_phone))
        for kw in keywords:
            for rect in page.search_for(kw):
                extended = fitz.Rect(rect.x0 - 50, rect.y0 - 5, rect.x1 + 300, rect.y1 + 5)
                rects.append(extended)

        for rect in rects:
            page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()

    output_pdf = io.BytesIO()
    doc.save(output_pdf)
    doc.close()
    return output_pdf.getvalue()


if uploaded_files:
    num_files = len(uploaded_files)
    st.info(f"✨ تم اختيار {num_files} ملف جاهز للمعالجة.")
    
    if st.button("🚀 معالجة وتنظيف الـ CVs", type="primary", use_container_width=True):
        with st.spinner("⏳ جاري فحص الملفات وإخفاء بيانات التواصل... برجاء الانتظار"):
            try:
                # حالة ملف واحد فقط
                if num_files == 1:
                    single_file = uploaded_files[0]
                    cleaned_data = redact_pdf(single_file.read())
                    
                    st.success("🎉 تم معالجة الـ CV بنجاح!")
                    st.download_button(
                        label="⬇️ تحميل الـ CV المعالج (PDF)",
                        data=cleaned_data,
                        file_name=f"Cleaned_{single_file.name}",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # حالة أكثر من ملف
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for uploaded_file in uploaded_files:
                            cleaned_data = redact_pdf(uploaded_file.read())
                            clean_filename = f"Cleaned_{uploaded_file.name}"
                            zip_file.writestr(clean_filename, cleaned_data)

                    zip_buffer.seek(0)
                    st.success("🎉 تم معالجة كافة الـ CVs بنجاح!")
                    
                    st.download_button(
                        label="⬇️ تحميل كافة الـ CVs المعالجة (ZIP)",
                        data=zip_buffer,
                        file_name="oldorado_Cleaned_CVs.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة البرمجية: {e}")
