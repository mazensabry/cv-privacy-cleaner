import streamlit as st
import fitz  # PyMuPDF
import re
import io
import zipfile

# إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="oldorado | CV Privacy Shield", 
    page_icon="🛡️", 
    layout="wide"
)

# حقن كود CSS للتنسيق والمحاذاة والاتجاه (RTL)
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

    /* تنسيق القائمة الجانبية Sidebar */
    [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
        background-color: #0f172a;
        border-left: 1px solid #1e293b;
    }

    .welcome-banner {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        padding: 25px 20px;
        border-radius: 12px;
        border: 1px solid #38bdf8;
        text-align: center !important;
        margin-bottom: 20px;
    }
    
    .welcome-banner h1 {
        color: #38bdf8 !important;
        text-align: center !important;
        margin-bottom: 8px;
        font-size: 24px;
        font-weight: bold;
    }

    .welcome-banner p {
        color: #94a3b8 !important;
        text-align: center !important;
        font-size: 14px;
        margin: 0;
    }

    .steps-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 20px;
    }

    .step-item {
        margin-bottom: 8px;
        color: #cbd5e1;
        font-size: 14px;
    }

    [data-testid="stFileUploader"] {
        direction: rtl;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. القائمة الجانبية للتحكم بالإعدادات (Sidebar Controls) ---
st.sidebar.title("⚙️ إعدادات التطهير")
st.sidebar.markdown("تخصيص خيارات المعالجة:")

# اختيار لون التظليل
color_option = st.sidebar.selectbox(
    "اختر لون التظليل:",
    ["أسود (Default)", "أحمر", "رمادي داكن"]
)

color_map = {
    "أسود (Default)": (0, 0, 0),
    "أحمر": (0.8, 0.1, 0.1),
    "رمادي داكن": (0.3, 0.3, 0.3)
}
selected_color = color_map[color_option]

st.sidebar.markdown("---")
st.sidebar.subheader("البيانات المستهدفة:")
remove_emails = st.sidebar.checkbox("إخفاء البريد الإلكتروني (Emails)", value=True)
remove_phones = st.sidebar.checkbox("إخفاء أرقام الهواتف (Phones)", value=True)
remove_urls = st.sidebar.checkbox("إخفاء الروابط وسائل التواصل (URLs)", value=True)
remove_addresses = st.sidebar.checkbox("إخفاء العناوين والموقع (Address)", value=True)


# --- 2. الواجهة الرئيسية ---
st.markdown("""
    <div class="welcome-banner">
        <h1>oldorado | CV Privacy Shield Pro</h1>
        <p>إزالة بيانات التواصل من الـ CVs قبل إرسالها لأصحاب العمل</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="steps-card">
        <h4 style="color: #f8fafc; margin-top: 0; margin-bottom: 10px;">📋 طريقة الاستخدام:</h4>
        <div class="step-item"><b>١.</b> قم بضبط خيارات التطهير من القائمة الجانبية (يمين الشاشة).</div>
        <div class="step-item"><b>٢.</b> ارفع ملفات الـ CVs واضغط على زر <b>معالجة وتنظيف الـ CVs</b>.</div>
        <div class="step-item"><b>٣.</b> قم بتحميل الملفات المنظفة فوراً بصيغة PDF أو ZIP.</div>
    </div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("📂 رفع ملفات الـ CVs (PDF)", type=["pdf"], accept_multiple_files=True)

# --- 3. دالة المعالجة وتجميع الإحصائيات ---
def redact_pdf(file_bytes, fill_color):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{4,}'
    url_pattern = r'(https?://\S+|www\.\S+|linkedin\.com/\S+|github\.com/\S+|behance\.net/\S+|facebook\.com/\S+|twitter\.com/\S+|x\.com/\S+)'
    keywords = [
        "Address", "Location", "Street", "City", "Residence", "Country",
        "العنوان", "المحافظة", "المدينة", "الشارع", "محل الإقامة", "السكن", "البلد"
    ]

    total_redactions_found = 0

    for page in doc:
        text = page.get_text("text")
        rects = []
        
        if remove_emails:
            emails = re.findall(email_pattern, text)
            total_redactions_found += len(emails)
            for email in emails:
                rects.extend(page.search_for(email))
                
        if remove_urls:
            urls = re.findall(url_pattern, text)
            total_redactions_found += len(urls)
            for url in urls:
                rects.extend(page.search_for(url))
                
        if remove_phones:
            phones = re.findall(phone_pattern, text)
            for phone in phones:
                match_str = phone[0] if isinstance(phone, tuple) else phone
                clean_phone = match_str.strip()
                if len(re.sub(r'\D', '', clean_phone)) >= 7:
                    total_redactions_found += 1
                    rects.extend(page.search_for(clean_phone))
                    
        if remove_addresses:
            for kw in keywords:
                found_kw = page.search_for(kw)
                total_redactions_found += len(found_kw)
                for rect in found_kw:
                    extended = fitz.Rect(rect.x0 - 50, rect.y0 - 5, rect.x1 + 300, rect.y1 + 5)
                    rects.append(extended)

        for rect in rects:
            page.add_redact_annot(rect, fill=fill_color)
        page.apply_redactions()

    output_pdf = io.BytesIO()
    doc.save(output_pdf)
    doc.close()
    return output_pdf.getvalue(), total_redactions_found


# --- 4. معالجة الملفات وشريط التقدم ---
if uploaded_files:
    num_files = len(uploaded_files)
    st.info(f"✨ تم اختيار {num_files} ملف جاهز للمعالجة.")
    
    if st.button("🚀 معالجة وتنظيف الـ CVs", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_items_hidden = 0
        
        try:
            # معالجة ملف واحد
            if num_files == 1:
                single_file = uploaded_files[0]
                status_text.text(f"جاري معالجة: {single_file.name}")
                progress_bar.progress(50)
                
                cleaned_data, hidden_count = redact_pdf(single_file.read(), selected_color)
                total_items_hidden += hidden_count
                
                progress_bar.progress(100)
                status_text.empty()
                
                st.success("🎉 تم معالجة الـ CV بنجاح!")
                
                # عرض لوحة الإحصائيات (Stats Dashboard)
                col1, col2 = st.columns(2)
                col1.metric("الملفات المعالجة", "1 ملف")
                col2.metric("إجمالي البيانات المخفية", f"{total_items_hidden} عنصر")
                
                st.download_button(
                    label="⬇️ تحميل الـ CV المعالج (PDF)",
                    data=cleaned_data,
                    file_name=f"Cleaned_{single_file.name}",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # معالجة دفعة ملفات
            else:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, uploaded_file in enumerate(uploaded_files):
                        # تحديث شريط التقدم
                        percent = int(((idx + 1) / num_files) * 100)
                        progress_bar.progress(percent)
                        status_text.text(f"جاري معالجة ({idx + 1}/{num_files}): {uploaded_file.name}")
                        
                        cleaned_data, hidden_count = redact_pdf(uploaded_file.read(), selected_color)
                        total_items_hidden += hidden_count
                        
                        clean_filename = f"Cleaned_{uploaded_file.name}"
                        zip_file.writestr(clean_filename, cleaned_data)

                zip_buffer.seek(0)
                status_text.empty()
                st.success("🎉 تم معالجة كافة الـ CVs بنجاح!")
                
                # عرض لوحة الإحصائيات (Stats Dashboard)
                col1, col2 = st.columns(2)
                col1.metric("إجمالي الملفات المعالجة", f"{num_files} ملفات")
                col2.metric("إجمالي البيانات المخفية", f"{total_items_hidden} عنصر")
                
                st.download_button(
                    label="⬇️ تحميل كافة الـ CVs المعالجة (ZIP)",
                    data=zip_buffer,
                    file_name="oldorado_Cleaned_CVs.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة البرمجية: {e}")
