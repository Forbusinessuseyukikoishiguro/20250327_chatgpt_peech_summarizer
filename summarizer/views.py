from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import logging

from .models import Summary
from .forms import TextInputForm
from .services import TextProcessor, SpeechGenerator

# ロガー設定
logger = logging.getLogger(__name__)


def index(request):
    """メインページを表示"""
    form = TextInputForm()
    context = {"form": form, "title": "音声要約アプリ"}
    return render(request, "summarizer/index.html", context)


def process_text(request):
    """テキスト処理を実行"""
    if request.method != "POST":
        return redirect("index")

    form = TextInputForm(request.POST, request.FILES)

    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{error}")
        return redirect("index")

    # フォームから入力データを取得
    title = form.cleaned_data["title"]
    input_type = form.cleaned_data["input_type"]
    feature = form.cleaned_data["feature"]
    voice_type = form.cleaned_data["voice_type"]

    # 入力によってテキストを取得
    original_text = ""

    try:
        if input_type == "text":
            original_text = form.cleaned_data["text_content"]
            if not title:
                title = "直接入力テキスト"

        elif input_type == "url":
            url = form.cleaned_data["url"]
            result = TextProcessor.extract_text_from_url(url)

            if not result["success"]:
                messages.error(
                    request,
                    f"URLからのテキスト取得に失敗しました: {result.get('error')}",
                )
                return redirect("index")

            original_text = result["content"]
            if not title:
                title = result["title"]

        elif input_type == "file":
            uploaded_file = request.FILES["file"]
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()

            # PDFファイルの場合
            if file_ext == ".pdf":
                # 一時ファイルとして保存
                file_path = os.path.join(settings.UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                result = TextProcessor.extract_text_from_pdf(file_path)

                if not result["success"]:
                    messages.error(
                        request,
                        f"PDFファイルからのテキスト取得に失敗しました: {result.get('error')}",
                    )
                    return redirect("index")

                original_text = result["content"]
                if not title:
                    title = result["title"]

                # 一時ファイルを削除
                os.remove(file_path)
            else:
                messages.error(
                    request,
                    "サポートされていないファイル形式です。PDFファイルをアップロードしてください。",
                )
                return redirect("index")

        # 要約が必要な場合
        summary_text = ""
        audio_file = None

        if feature in ["summary", "both"]:
            summary_length = form.cleaned_data["summary_length"]

            # 要約の長さを決定
            if summary_length == "custom":
                max_words = form.cleaned_data["custom_length"]
            else:
                max_words = int(summary_length)

            # 要約を実行
            result = TextProcessor.summarize_text(original_text, max_words)

            if not result["success"]:
                messages.error(
                    request, f"テキストの要約に失敗しました: {result.get('error')}"
                )
                return redirect("index")

            summary_text = result["summary"]

        # 音声生成が必要な場合
        if feature in ["speech", "both"]:
            # 要約モードの場合は要約テキストを読み上げ、それ以外は元のテキストを読み上げ
            text_to_speak = (
                summary_text if feature == "both" and summary_text else original_text
            )

            # 音声生成を実行
            result = SpeechGenerator.process_long_text(text_to_speak, voice_type)

            if not result["success"]:
                messages.error(
                    request, f"音声生成に失敗しました: {result.get('error')}"
                )
                return redirect("index")

            audio_file = result.get("file_path")

        # データベースに保存
        summary = Summary(
            title=title,
            input_type=input_type,
            original_text=original_text,
            summary_text=summary_text,
        )

        if input_type == "url":
            summary.url = form.cleaned_data["url"]

        if input_type == "file" and request.FILES.get("file"):
            summary.uploaded_file = request.FILES["file"]

        if audio_file:
            summary.audio_file = audio_file

        summary.save()

        messages.success(request, "処理が完了しました")
        return redirect("detail", pk=summary.id)

    except Exception as e:
        logger.error(f"処理エラー: {e}")
        messages.error(request, f"エラーが発生しました: {str(e)}")
        return redirect("index")


def history(request):
    """履歴一覧を表示"""
    summaries = Summary.objects.all().order_by("-created_at")
    context = {"summaries": summaries, "title": "履歴一覧"}
    return render(request, "summarizer/history.html", context)


def detail(request, pk):
    """要約の詳細を表示"""
    summary = get_object_or_404(Summary, pk=pk)
    context = {"summary": summary, "title": summary.title}
    return render(request, "summarizer/detail.html", context)


def delete(request, pk):
    """要約データを削除"""
    summary = get_object_or_404(Summary, pk=pk)

    if request.method == "POST":
        summary.delete()
        messages.success(request, "削除しました")
        return redirect("history")

    context = {"summary": summary, "title": f"{summary.title} - 削除確認"}
    return render(request, "summarizer/delete.html", context)


def play_audio(request, pk):
    """音声ファイルを再生"""
    summary = get_object_or_404(Summary, pk=pk)

    if not summary.audio_file:
        messages.error(request, "音声ファイルがありません")
        return redirect("detail", pk=pk)

    # 音声ファイルのパス
    file_path = os.path.join(settings.MEDIA_ROOT, str(summary.audio_file))

    if not os.path.exists(file_path):
        messages.error(request, "音声ファイルが見つかりません")
        return redirect("detail", pk=pk)

    with open(file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="audio/mpeg")
        response["Content-Disposition"] = (
            f'inline; filename="{os.path.basename(file_path)}"'
        )
        return response
