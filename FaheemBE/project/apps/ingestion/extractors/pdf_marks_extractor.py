import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import fitz  # PyMuPDF
from .arabic_normalizer import normalize_arabic_text


class PDFMarksExtractor:
    """
    مستخرج علامات الطلاب من ملفات PDF الرسمية الصادرة عن الكلية:
    - فحص الجداول والصفوف.
    - استخراج: الرقم الامتحاني (5 خانات)، الاسم الكامل، العلامة النهائية، والأجزاء (نظري/عملي).
    - توثيق مرجع كل صف (الصفحة / السطر) لدعم الـ Provenance.
    """

    @classmethod
    def extract_rows_from_pdf(cls, pdf_path: str) -> List[Dict[str, Any]]:
        extracted_rows = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            tables = page.find_tables()

            if tables.tables:
                for table_idx, tab in enumerate(tables.tables):
                    df_data = tab.extract()
                    # معالجة الصفوف المستخرجة من الجدول
                    for row_idx, row in enumerate(df_data):
                        parsed_row = cls._parse_table_row(row, page_num + 1, row_idx + 1)
                        if parsed_row:
                            extracted_rows.append(parsed_row)
            else:
                # محاولة استخراج كتل النصوص عند غياب الجداول الصريحة
                text = page.get_text("text")
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                for line_idx, line in enumerate(lines):
                    parsed_line = cls._parse_text_line(line, page_num + 1, line_idx + 1)
                    if parsed_line:
                        extracted_rows.append(parsed_line)

        doc.close()
        return extracted_rows

    @classmethod
    def _parse_table_row(cls, row: List[Any], page_num: int, row_num: int) -> Optional[Dict[str, Any]]:
        """تحليل صف من جدول لاستخراج بيانات الطالب والعلامة."""
        cleaned_cells = [str(c).strip() if c is not None else "" for c in row]
        row_str = " ".join(cleaned_cells)

        # البحث عن رقم امتحاني مكون من 4 أو 5 أرقام
        exam_match = re.search(r'\b\d{4,5}\b', row_str)
        if not exam_match:
            return None

        exam_number = exam_match.group(0)

        # البحث عن علامة نهائية ضمن [0, 100]
        marks = re.findall(r'\b(?:100|[1-9]?[0-9])\b', row_str)
        # استبعاد الرقم الامتحاني من قائمة العلامات المحتملة
        possible_marks = [int(m) for m in marks if m != exam_number]
        final_mark = possible_marks[-1] if possible_marks else None

        # استخراج الاسم العربي
        arabic_words = re.findall(r'[\u0600-\u06FF]+', row_str)
        # تصفية الكلمات العامة للترويسة إن وجدت
        ignored = {'جامعة', 'دمشق', 'كلية', 'الهندسة', 'المعلوماتية', 'مقرر', 'دورة', 'نتيجة', 'امتحان'}
        filtered_words = [w for w in arabic_words if w not in ignored]
        raw_name = " ".join(filtered_words) if filtered_words else "غير محدد"

        if len(raw_name) < 4:
            return None

        return {
            'row_ref': f"page:{page_num}/row:{row_num}",
            'raw_name': raw_name,
            'normalized_name': normalize_arabic_text(raw_name),
            'exam_number': exam_number,
            'final_mark': final_mark,
            'absence_reason': 'غائب' if 'غائب' in row_str or 'غياب' in row_str else None,
            'components': []
        }

    @classmethod
    def _parse_text_line(cls, line: str, page_num: int, line_num: int) -> Optional[Dict[str, Any]]:
        """تحليل سطر نصي منفصل لاستخراج النتيجة."""
        exam_match = re.search(r'\b\d{4,5}\b', line)
        if not exam_match:
            return None

        return cls._parse_table_row([line], page_num, line_num)
