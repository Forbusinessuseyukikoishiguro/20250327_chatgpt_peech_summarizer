from django import forms


class TextInputForm(forms.Form):
    """テキスト入力フォーム"""

    INPUT_TYPES = [
        ("text", "テキストを直接入力"),
        ("url", "URLからテキストを取得"),
        ("file", "ファイルをアップロード"),
    ]

    FEATURE_CHOICES = [
        ("summary", "要約のみ"),
        ("speech", "読み上げのみ"),
        ("both", "要約と読み上げ"),
    ]

    VOICE_CHOICES = [
        ("nova", "Nova (女性 - 日本語対応)"),
        ("alloy", "Alloy (多言語)"),
        ("echo", "Echo (多言語)"),
        ("fable", "Fable (多言語)"),
        ("onyx", "Onyx (多言語)"),
        ("shimmer", "Shimmer (多言語)"),
    ]

    SUMMARY_LENGTH_CHOICES = [
        ("100", "超短縮（約100語/約400文字）"),
        ("200", "短縮（約200語/約800文字）"),
        ("300", "標準（約300語/約1200文字）"),
        ("500", "詳細（約500語/約2000文字）"),
        ("800", "非常に詳細（約800語/約3200文字）"),
        ("custom", "カスタム"),
    ]

    title = forms.CharField(
        label="タイトル",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "任意のタイトル"}
        ),
    )

    input_type = forms.ChoiceField(
        label="入力方法",
        choices=INPUT_TYPES,
        widget=forms.RadioSelect(),
        initial="text",
    )

    text_content = forms.CharField(
        label="テキスト",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "テキストを入力してください",
            }
        ),
    )

    url = forms.URLField(
        label="URL",
        required=False,
        widget=forms.URLInput(
            attrs={"class": "form-control", "placeholder": "https://example.com"}
        ),
    )

    file = forms.FileField(
        label="ファイル",
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )

    feature = forms.ChoiceField(
        label="実行する機能",
        choices=FEATURE_CHOICES,
        widget=forms.RadioSelect(),
        initial="both",
    )

    voice_type = forms.ChoiceField(
        label="音声の種類",
        choices=VOICE_CHOICES,
        widget=forms.RadioSelect(),
        initial="nova",
    )

    summary_length = forms.ChoiceField(
        label="要約の長さ",
        choices=SUMMARY_LENGTH_CHOICES,
        widget=forms.RadioSelect(),
        initial="300",
    )

    custom_length = forms.IntegerField(
        label="カスタム長さ（単語数）",
        required=False,
        min_value=50,
        max_value=2000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        input_type = cleaned_data.get("input_type")
        text_content = cleaned_data.get("text_content")
        url = cleaned_data.get("url")
        file = cleaned_data.get("file")
        feature = cleaned_data.get("feature")
        summary_length = cleaned_data.get("summary_length")
        custom_length = cleaned_data.get("custom_length")

        # 入力タイプに応じたバリデーション
        if input_type == "text" and not text_content:
            self.add_error("text_content", "テキストを入力してください")
        elif input_type == "url" and not url:
            self.add_error("url", "URLを入力してください")
        elif input_type == "file" and not file:
            self.add_error("file", "ファイルをアップロードしてください")

        # カスタム長さのバリデーション
        if (
            (feature in ["summary", "both"])
            and summary_length == "custom"
            and not custom_length
        ):
            self.add_error("custom_length", "カスタム長さを入力してください")

        return cleaned_data
