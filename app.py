import streamlit as st
import fitz  # PyMuPDF
import re
import io
import zipfile

# إعدادات الصفحة
st.set_page_config(
    page_title="Recruitment Privacy Shield", 
    page_icon="🛡️", 
    layout="centered"
)

# تصميم الواجهة الترحيبية (Intro & Welcome Banner)
st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 25px; border-radius: 12px; border: 1px solid #334155; text-align: center; margin-bottom: 25px;">
        <h1 style="color: #38bdf8; margin-bottom: 10px; font-size: 24px;">🛡️ مرحباً بك في أداة حماية وتطهير السي فيهات</h1>
        <p style="color: #94a3b8; font-size: 14px; margin: 0;">النظام الآمن لإزالة أرقام الهواتف، الإيميلات، والروابط تلقائياً قبل إرسالها للعملاء.</p>
    </div>
""", unsafe_allow_html=True)

# شرح سريع للخطوات
st.markdown("### 📋 خطوات الاستخدام:")
st.markdown("1. اختر ملفاً أو مجموعة من ملفات الـ PDF (السير الذاتية).")
st.markdown("2. اضغط على زر **بدء التنظيف الجماعي**.")
st.markdown("3. حمل الملفات النظيفة بضغطة زر واحدة مجدولة داخل ملف ZIP.")

st.markdown("---")

# منطقة رفع الملفات
uploaded_files = st.file_uploader("📂 رفـع ملفـات السي فـي (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"✨ تم اختيار {len(uploaded_files)} ملف جاهز للمعالجة.")
    
    if st.button("🚀 بدء التنظيف الجماعي وإخفاء البيانات", type="primary", use_container_width=True):
        with st.spinner("⏳ جاري فحص ومعالجة الملفات بدقة... برجاء الانتظار"):
            try:
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    phone_pattern = r'(?:\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{4,}'
                    url_pattern = r'(https?://\S+|www\.\S+|linkedin\.com/\S+|github\.com/\S+)'
                    keywords = ["Address", "Location", "Street", "City", "العنوان", "المحافظة", "المدينة", "الشارع", "محل الإقامة"]

                    for uploaded_file in uploaded_files:
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        
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
                        
                        clean_filename = f"Cleaned_{uploaded_file.name}"
                        zip_file.writestr(clean_filename, output_pdf.getvalue())

                zip_buffer.seek(0)
                st.success("🎉 تم الانتهاء من تطهير جميع السي فيهات بنجاح تام!")
                
                st.download_button(
                    label="⬇️ تحميل كافة السي فيهات النظيفة (ZIP)",
                    data=zip_buffer,
                    file_name="Cleaned_CVs.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"حدث خطأ غير متوقع أثناء المعالجة: {e}")
