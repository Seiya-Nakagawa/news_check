import os
from google import genai
from google.genai import types
from typing import List, Dict
import json

class Summarizer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # 環境のリストにあった実在するモデル名 gemini-flash-latest を使用
        self.model_id = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    def summarize(self, transcript: str) -> Dict:
        """
        Gemini APIを使用して字幕を要約する。
        """
        prompt = f"""
以下のYouTubeニュース動画の字幕テキストを解析し、内容を要約してください。

【出力形式】
1. "summary" フィールドには、動画全体の流れを掴むための簡潔な要約（300文字程度）を記述してください。
2. "key_points" フィールドには、放送された個別のニュース項目をすべて抽出し、リスト形式で列挙してください。各項目は具体的な事実関係を含めて短くまとめてください。

{{
  "summary": "動画全体の簡潔な要約（300文字程度）",
  "key_points": [
    "ニュース項目1の内容",
    "ニュース項目2の内容",
    "ニュース項目3の内容",
    "..."
  ]
}}

字幕テキスト:
{transcript}
"""
        try:
            # プレフィックスなしで試行
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
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
                        )
                    )
                    return json.loads(response.text)
                except Exception as e2:
                    error_str = f"{error_str} | Retry failed: {str(e2)}"

            print(f"Error in Gemini summarization: {error_str}")
            with open("gemini_error.log", "a") as f:
                f.write(error_str + "\n")
            return {
                "summary": f"要約の生成に失敗しました。({error_str[:60]}...)",
                "key_points": []
            }
