import streamlit as st
import fitz  # PyMuPDF
import re
import io

# إعدادات واجهة الموقع
st.set_page_config(page_title="أداة تنظيف السير الذاتية", page_icon="🛡️", layout="centered")

st.title("🛡️ Recruitment Privacy Shield")
st.markdown("ارفع السيرة الذاتية بصيغة PDF لإخفاء أرقام الهواتف، البريد الإلكتروني، والروابط تلقائياً.")

# منطقة رفع الملف
uploaded_file = st.file_uploader("اختر ملف السي في (PDF)", type=["pdf"])

if uploaded_file is not None:
    if st.button("بدء التنظيف", type="primary"):
        with st.spinner("جاري مسح البيانات الحساسة..."):
            try:
                # قراءة الملف من الذاكرة
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                
                # أنماط البحث (Regex)
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                phone_pattern = r'(?:\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{4,}'
                url_pattern = r'(https?://\S+|www\.\S+|linkedin\.com/\S+|github\.com/\S+)'
                keywords = ["Address", "Location", "Street", "City", "العنوان", "المحافظة", "المدينة", "الشارع", "محل الإقامة"]

                # معالجة كل صفحة
                for page in doc:
                    text = page.get_text("text")
                    rects = []
                    
                    # استخراج الإحداثيات لكل نمط
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
                            # توسيع المستطيل لطمس العنوان بالكامل
                            extended = fitz.Rect(rect.x0 - 50, rect.y0 - 5, rect.x1 + 300, rect.y1 + 5)
                            rects.append(extended)

                    # رسم مستطيل أسود فوق الإحداثيات
                    for rect in rects:
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                    page.apply_redactions()

                # حفظ الملف الجديد في الذاكرة
                output_pdf = io.BytesIO()
                doc.save(output_pdf)
                doc.close()

                st.success("✅ تم إخفاء البيانات بنجاح!")
                
                # زر تحميل الملف النهائي
                st.download_button(
                    label="⬇️ تحميل السي في النظيف",
                    data=output_pdf.getvalue(),
                    file_name=f"Cleaned_{uploaded_file.name}",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
