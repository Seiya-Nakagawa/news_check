import json
import os
from typing import Dict

from google import genai
from google.genai import types


class Summarizer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # テストで動作が確認された gemini-flash-latest をデフォルトに使用
        self.model_id = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    def summarize(self, transcript: str) -> Dict:
        """
        Gemini APIを使用して字幕を要約する。
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
        try:
            # プレフィックスなしで試行
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            error_str = str(e)
            print(f"DEBUG: Initial attempt failed for {self.model_id}: {error_str}")

            # 404の場合、models/ プレフィックスを付けて再試行
            if "404" in error_str and not self.model_id.startswith("models/"):
                try:
                    retry_model = f"models/{self.model_id}"
                    print(f"DEBUG: Retrying with {retry_model}")
                    response = self.client.models.generate_content(
                        model=retry_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        ),
                    )
                    return json.loads(response.text)
                except Exception as e2:
                    error_str = f"{error_str} | Retry failed: {str(e2)}"

            print(f"Error in Gemini summarization: {error_str}")
            with open("gemini_error.log", "a") as f:
                f.write(error_str + "\n")
            return {
                "summary": f"要約の生成に失敗しました。({error_str[:60]}...)",
                "key_points": [],
            }
