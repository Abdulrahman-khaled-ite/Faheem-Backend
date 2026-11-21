import io
import os
import hashlib
from typing import Optional, List, Dict, Any
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from .models import DriveFile, SourceRevision, EducationalMaterial, MaterialCategory, StudyDepartment


class GoogleDriveService:
    """
    خدمة الاتصال والمزامنة الكاملة مع Google Drive API:
    - فحص المجلدات والمواد والمحاضرات.
    - إنشاء المجلدات الفرعية برمجياً وفق هيكلية الكلية الرسمية.
    - رفع ملفات المحاضرات والدورات الجديدة إلى درايف.
    - رصد ملفات العلامات الجديدة بصيغة PDF وتنزيلها محلياً لحساب بصمتها SHA-256.
    """

    def __init__(self):
        self.config = settings.FAHEEM_CONFIG
        self.service = self._init_drive_service()

    def _init_drive_service(self):
        """تهيئة عميل Drive API بملف Service Account بصلاحيات القراءة والكتابة الكاملة."""
        creds_path = self.config.get('GOOGLE_SERVICE_ACCOUNT_FILE')
        if creds_path and os.path.exists(creds_path):
            scopes = ['https://www.googleapis.com/auth/drive']
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=scopes
            )
            return build('drive', 'v3', credentials=credentials)
        return None

    def is_configured(self) -> bool:
        return self.service is not None

    def list_folder_contents(self, folder_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """جلب محتويات مجلد في Google Drive."""
        if not self.service:
            return []

        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(
            q=query,
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, createdTime, size)"
        ).execute()

        return results.get('files', [])

    def download_file_to_storage(self, file_id: str, destination_path: Path) -> str:
        """
        تنزيل ملف من درايف إلى التخزين المحلي وحساب بصمة SHA-256.
        """
        if not self.service:
            raise RuntimeError("Google Drive client is not configured with valid credentials.")

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        request = self.service.files().get_media(fileId=file_id)

        hasher = hashlib.sha256()
        with open(destination_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

        with open(destination_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()

    def create_or_get_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        إنشاء مجلد في درايف إن لم يكن موجوداً مسبقاً، وإرجاع المعرف الخاص به (folder_id).
        """
        if not self.service:
            raise RuntimeError("Google Drive client is not configured.")

        # البحث أولاً عن المجلد
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            return files[0]['id']

        # إنشاء المجلد إن لم يوجد
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]

        created_folder = self.service.files().create(
            body=folder_metadata,
            fields='id, name'
        ).execute()

        return created_folder['id']

    def upload_file(
        self,
        local_path: Path,
        parent_folder_id: str,
        file_name: Optional[str] = None,
        mime_type: str = 'application/pdf'
    ) -> Dict[str, Any]:
        """
        رفع ملف من التخزين المحلي إلى مجلد محدد على Google Drive.
        """
        if not self.service:
            raise RuntimeError("Google Drive client is not configured.")

        upload_name = file_name or local_path.name
        file_metadata = {
            'name': upload_name,
            'parents': [parent_folder_id]
        }
        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

        uploaded_file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink, size'
        ).execute()

        return uploaded_file

    def get_or_create_course_material_folder(
        self,
        study_year_label: str,
        department_label: str,
        course_name: str,
        category: str,
        root_folder_id: Optional[str] = None
    ) -> str:
        """
        بناء المسار الهرمي للمادة والمجلد الفرعي في درايف وإرجاع folder_id المجلد النهائي:
        الجذر -> مواد دراسة و دورات... -> سنة X -> اختصاص -> المقرر -> محاضرات/سلالم/دورات
        """
        current_parent = root_folder_id or self.config.get('GOOGLE_DRIVE_ROOT_FOLDER_ID')

        # 1. مجلد المواد الرئيسي
        materials_root = self.create_or_get_folder("مواد دراسة و دورات و سلالم تصحيح و زنقة", current_parent)

        # 2. مجلد السنة
        year_folder = self.create_or_get_folder(study_year_label, materials_root)

        # 3. مجلد الاختصاص (إن وجد اختصاص أو عام)
        dept_folder = self.create_or_get_folder(department_label, year_folder)

        # 4. مجلد المادة
        course_folder = self.create_or_get_folder(course_name, dept_folder)

        # 5. المجلد الفرعي (محاضرات، دورات، سلالم، سلايدات، زنقة، ملحق)
        category_folder = self.create_or_get_folder(category, course_folder)

        return category_folder

    def register_or_update_file(
        self,
        file_info: Dict[str, Any],
        parent_folder_id: Optional[str] = None,
        drive_path: Optional[str] = None
    ) -> DriveFile:
        """تسجيل أو تحديث معلومات ملف درايف في قاعدة البيانات."""
        drive_file, _ = DriveFile.objects.update_or_create(
            drive_file_id=file_info['id'],
            defaults={
                'name': file_info.get('name', 'بدون اسم'),
                'mime_type': file_info.get('mimeType', 'application/octet-stream'),
                'parent_folder_id': parent_folder_id,
                'drive_path': drive_path,
                'web_view_link': file_info.get('webViewLink'),
                'active': True
            }
        )
        return drive_file

    def record_pdf_revision(self, drive_file: DriveFile, local_path: Path, digest: str) -> SourceRevision:
        """تسجيل إصدار جديد لملف علامات أو وثيقة رسمية بصيغة PDF."""
        file_size = local_path.stat().st_size if local_path.exists() else 0
        revision = SourceRevision.objects.create(
            drive_file=drive_file,
            pdf_digest=digest,
            snapshot_ref=str(local_path),
            file_size_bytes=file_size
        )
        return revision

    def index_educational_material(
        self,
        drive_file: DriveFile,
        study_year: int,
        department: str,
        course_name: str,
        category: str,
        title: str
    ) -> EducationalMaterial:
        """فهرسة المادة التعليمية وربطها بملف درايف."""
        material, _ = EducationalMaterial.objects.update_or_create(
            drive_file=drive_file,
            defaults={
                'study_year': study_year,
                'department': department,
                'course_name': course_name,
                'category': category,
                'title': title,
                'is_published': True
            }
        )
        return material
