import json
import os
import random
import time
from typing import Dict

from google import genai
from google.genai import types


class Summarizer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # 現時点で動作とクォータが確認できた gemini-3-flash-preview をデフォルトに使用
        self.model_id = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    def summarize(self, transcript: str) -> Dict:
        """
        Gemini APIを使用して字幕を要約する。(YouTube動画用)
        """
        prompt = f"""
あなたはプロのニュース編集者です。提供された「YouTubeニュース動画のテキスト（字幕または説明文）」を解析し、視聴者が短時間で内容を把握できる高品質な要約を作成してください。

【注意点】
- 「この字幕テキストは...」「テレビ朝日がお届けする...」「最新ニュースをライブで...」といった、動画の内容そのものではないメタ情報や定型文、チャンネルの紹介などは、要約や重要ポイントに含めないでください。
- 放送された具体的な「事実（事件、事故、政治、経済、気象など）」にのみ焦点を当ててください。
- まだ要約すべきニュース事実がない場合は、その旨を簡潔に記述してください。

【出力形式】
以下のJSON形式で出力してください。
{{
  "summary": "動画全体の流れを掴むための簡潔な要約（300文字程度）。事実に基づいた具体的な内容にすること。",
  "key_points": [
    "重要なニュース項目1の具体的な内容",
    "重要なニュース項目2の具体的な内容",
    "重要なニュース項目3の具体的な内容",
    "..."
  ]
}}

対象のテキスト:
{transcript}
"""
        return self._generate_summary(prompt)

    def summarize_article(self, article_text: str) -> Dict:
        """
        Gemini APIを使用してニュース記事を要約する。(NHKニュース等のテキスト記事用)
        """
        prompt = f"""
あなたはプロのニュース編集者です。提供された「ニュース記事のテキスト」を解析し、読者が短時間で内容を把握できる高品質な要約を作成してください。

【注意点】
- 記事の具体的な「事実（事件、事故、政治、経済、気象、国際情勢など）」にのみ焦点を当ててください。
- 5W1H（いつ、どこで、誰が、何を、なぜ、どのように）を意識した要約を心がけてください。
- 重要ポイントは3〜5項目程度に絞ってください。

【出力形式】
以下のJSON形式で出力してください。
{{
  "summary": "記事の内容を掴むための簡潔な要約（200〜300文字程度）。事実に基づいた具体的な内容にすること。",
  "key_points": [
    "重要ポイント1",
    "重要ポイント2",
    "重要ポイント3"
  ]
}}

対象の記事テキスト:
{article_text}
"""
        return self._generate_summary(prompt)

    def _generate_summary(self, prompt: str) -> Dict:
        """Gemini APIを呼び出して要約を生成する共通処理 (リトライ機能付き)"""
        max_retries = 2
        base_delay = 2.0  # seconds

        for attempt in range(max_retries + 1):
            try:
                # プレフィックスなしで試行
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        safety_settings=[
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                        ],
                    ),
                )
                if response.text is None:
                    # 詳細な原因究明のためにレスポンスの中身を確認
                    finish_reason = "Unknown"
                    safety_ratings = []
                    if response.candidates:
                        finish_reason = response.candidates[0].finish_reason
                        safety_ratings = response.candidates[0].safety_ratings

                    error_msg = f"Gemini returned empty response. FinishReason: {finish_reason}, SafetyRatings: {safety_ratings}"
                    raise Exception(error_msg)
                return json.loads(response.text)
            except Exception as e:
                error_str = str(e)
                # 429 Resource Exhausted handling
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries:
                        # Exponential backoff + jitter
                        delay = base_delay * (2**attempt) + random.uniform(0, 1)
                        print(
                            f"DEBUG: Rate limit hit. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        print("DEBUG: Max retries reached for rate limit.")

                print(f"DEBUG: Initial attempt failed for {self.model_id}: {error_str}")

                # 404の場合、models/ プレフィックスを付けて再試行 (1回のみ)
                # (Rate limit以外のエラーで、かつ404の場合のみ)
                if (
                    "404" in error_str
                    and not self.model_id.startswith("models/")
                    and "429" not in error_str
                ):
                    try:
                        retry_model = f"models/{self.model_id}"
                        print(f"DEBUG: Retrying with {retry_model}")
                        response = self.client.models.generate_content(
                            model=retry_model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                safety_settings=[
                                    types.SafetySetting(
                                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                                    ),
                                    types.SafetySetting(
                                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                                    ),
                                    types.SafetySetting(
                                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                                    ),
                                    types.SafetySetting(
                                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                                    ),
                                    types.SafetySetting(
                                        category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                                    ),
                                ],
                            ),
                        )
                        if response.text is None:
                            raise Exception("Gemini returned empty response (None) even on retry.")
                        return json.loads(response.text)
                    except Exception as e2:
                        error_str = f"{error_str} | Retry failed: {str(e2)}"
                        # Retryで429が出た場合のハンドリングは複雑になるため、ここではループ外のエラー処理に任せる
                        # 必要であればここもループに含める設計にすべきだが、まずは簡易対応

                # リトライでもダメだった、あるいはリトライ対象外のエラー
                if attempt == max_retries or (
                    "429" not in error_str and "RESOURCE_EXHAUSTED" not in error_str
                ):
                    print(f"Error in Gemini summarization: {error_str}")
                    with open("gemini_error.log", "a") as f:
                        f.write(error_str + "\n")
                    return {
                        "summary": f"要約の生成に失敗しました。({error_str[:60]}...)",
                        "key_points": [],
                    }
