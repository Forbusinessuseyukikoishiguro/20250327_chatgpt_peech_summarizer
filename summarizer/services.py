import requests
from bs4 import BeautifulSoup
import os
import tempfile
import PyPDF2
from datetime import datetime
import logging
from django.conf import settings

# ロガーの設定
logger = logging.getLogger(__name__)


class TextProcessor:
    """テキスト処理クラス"""

    @staticmethod
    def extract_text_from_url(url):
        """URLからテキストを抽出する"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding

            # HTMLの解析
            soup = BeautifulSoup(response.text, "html.parser")

            # タイトル取得
            title = soup.title.string if soup.title else url

            # 本文取得
            paragraphs = soup.find_all("p")
            text_content = "\n".join([p.get_text() for p in paragraphs])

            # コンテンツが少ない場合はbody全体を取得
            if len(text_content) < 500:
                text_content = soup.body.get_text(separator="\n", strip=True)

            return {"success": True, "title": title, "content": text_content}
        except Exception as e:
            logger.error(f"URL処理エラー: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def extract_text_from_pdf(file_path):
        """PDFファイルからテキストを抽出する"""
        try:
            pdf_reader = PyPDF2.PdfReader(file_path)
            text = ""

            # メタデータ取得
            info = pdf_reader.metadata
            title = info.title if info and info.title else os.path.basename(file_path)

            # 各ページからテキストを抽出
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"

            return {"success": True, "title": title, "content": text}
        except Exception as e:
            logger.error(f"PDF処理エラー: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def summarize_text(text, max_words=300):
        """OpenAI APIを使ってテキストを要約する"""
        try:
            api_url = "https://api.openai.com/v1/chat/completions"

            # 文字数の目安を計算（日本語では単語数×4程度が文字数の目安）
            char_estimate = max_words * 4

            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": f"あなたは与えられた文章を約{max_words}語（約{char_estimate}文字）に要約するアシスタントです。",
                    },
                    {
                        "role": "user",
                        "content": f"以下の文章を約{max_words}語（約{char_estimate}文字）に要約してください:\n\n{text}",
                    },
                ],
            }

            response = requests.post(api_url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                summary = result["choices"][0]["message"]["content"]

                return {"success": True, "summary": summary}
            else:
                return {
                    "success": False,
                    "error": f"API エラー: {response.status_code}, 詳細: {response.text}",
                }

        except Exception as e:
            logger.error(f"要約処理エラー: {e}")
            return {"success": False, "error": str(e)}


class SpeechGenerator:
    """音声生成クラス"""

    @staticmethod
    def generate_speech(text, voice="nova"):
        """OpenAI Text-to-Speech APIでテキストから音声を生成する"""
        try:
            api_url = "https://api.openai.com/v1/audio/speech"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            data = {"model": "tts-1", "voice": voice, "input": text}

            response = requests.post(api_url, headers=headers, json=data)

            if response.status_code == 200:
                # 一意のファイル名を生成
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"speech_{timestamp}_{voice}.mp3"

                # 音声ファイルの保存先
                file_path = os.path.join(settings.AUDIO_DIR, filename)

                # 音声データをファイルに保存
                with open(file_path, "wb") as f:
                    f.write(response.content)

                # 相対パスを返す（Djangoのファイルシステムパス）
                relative_path = os.path.join("audio", filename)

                return {"success": True, "file_path": relative_path}
            else:
                return {
                    "success": False,
                    "error": f"API エラー: {response.status_code}, 詳細: {response.text}",
                }

        except Exception as e:
            logger.error(f"音声生成エラー: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def process_long_text(text, voice="nova", max_chunk_length=4000):
        """長いテキストを分割して処理する"""
        # テキストが短い場合はそのまま処理
        if len(text) <= max_chunk_length:
            return SpeechGenerator.generate_speech(text, voice)

        # 長いテキストは分割して処理
        import re

        sentences = re.split(r"(?<=[。．！？\.\!\?])", text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk)

        # 最初のチャンクだけ処理して返す（ファイルが多すぎるとUIが複雑になるので）
        if chunks:
            return SpeechGenerator.generate_speech(chunks[0], voice)

        return {"success": False, "error": "処理するテキストがありませんでした"}
