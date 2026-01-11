import os
from google import genai
from google.genai import types
from typing import List, Dict
import json

class Summarizer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # models/ プレフィックスを付けるのが SDK の標準
        self.model_id = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash")

    def summarize(self, transcript: str) -> Dict:
        """
        Gemini APIを使用して字幕を要約する。
        構造化されたデータを返す。
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
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            return json.loads(response.text)
        except Exception as e:
            error_msg = f"Error in Gemini summarization: {str(e)}"
            print(error_msg)
            # ログファイルにも書き込む
            with open("gemini_error.log", "a") as f:
                f.write(error_msg + "\n")
            return {
                "summary": f"要約の生成に失敗しました。({str(e)[:50]}...)",
                "key_points": []
            }
