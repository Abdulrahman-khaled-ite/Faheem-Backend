import re


def normalize_arabic_text(text: str) -> str:
    """
    تطبيع النصوص والأسماء العربية للبحث والمطابقة الدقيقة:
    - إزالة التشكيل والتنوين والشدة.
    - توحيد أشكال الألف (أ، إ، آ -> ا).
    - توحيد الياء والألف المقصورة (ى -> ي).
    - توحيد التاء المربوطة والهاء (ة -> ه).
    - إزالة التطويل (الكشيدة).
    - تنظيف الفراغات المزدوجة.
    """
    if not text:
        return ""

    text = str(text)

    # 1. إزالة التشكيل
    tashkeel_regex = re.compile(r'[\u064B-\u0652\u0656-\u065F\u0670]')
    text = tashkeel_regex.sub('', text)

    # 2. إزالة التطويل (ـ)
    text = re.sub(r'[\u0640]', '', text)

    # 3. توحيد الألف
    text = re.sub(r'[إأآٱ]', 'ا', text)

    # 4. توحيد الياء
    text = re.sub(r'[ىي]', 'ي', text)

    # 5. توحيد التاء المربوطة
    text = re.sub(r'[ة]', 'ه', text)

    # 6. تنظيف المسافات الزائدة
    text = re.sub(r'\s+', ' ', text).strip()

    return text
