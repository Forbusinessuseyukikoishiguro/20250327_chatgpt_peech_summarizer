from django.db import models
from django.utils import timezone
import os
import uuid


def upload_to_path(instance, filename):
    """アップロードされたファイルのパスを生成する関数"""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("uploads", filename)


class Summary(models.Model):
    """要約データを保存するモデル"""

    INPUT_TYPES = [
        ("text", "テキスト入力"),
        ("url", "URL入力"),
        ("file", "ファイル入力"),
    ]

    title = models.CharField("タイトル", max_length=255, blank=True)
    input_type = models.CharField("入力タイプ", max_length=10, choices=INPUT_TYPES)
    input_content = models.TextField("入力内容", blank=True)
    url = models.URLField("URL", blank=True)
    uploaded_file = models.FileField(
        "アップロードファイル", upload_to=upload_to_path, blank=True, null=True
    )
    original_text = models.TextField("元のテキスト", blank=True)
    summary_text = models.TextField("要約テキスト", blank=True)
    audio_file = models.FileField(
        "音声ファイル", upload_to="audio/", blank=True, null=True
    )
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    class Meta:
        verbose_name = "要約"
        verbose_name_plural = "要約一覧"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"要約 {self.id}"

    def file_name(self):
        """アップロードされたファイルの名前を取得"""
        if self.uploaded_file:
            return os.path.basename(self.uploaded_file.name)
        return None

    def get_input_type_display(self):
        """入力タイプの表示名を取得"""
        return dict(self.INPUT_TYPES).get(self.input_type, "")
