import os
from google import genai
from google.genai import types
from typing import List, Dict
import json

class Summarizer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # 1.5-flash が 404 の場合があるため 2.5-flash-preview を優先的に試行
        self.model_id = "gemini-2.5-flash-preview-09-2025"

    def summarize(self, transcript: str) -> Dict:
        """
        Gemini APIを使用して字幕を要約する。
        構造化されたデータを返す。
        """
        prompt = f"""
以下のYouTube動画の字幕テキストを読み取り、ニュースの内容を要約してください。
出力は以下のJSON形式でお願いします。

{{
  "summary": "動画全体の要約（300文字程度）",
  "key_points": [
    "重要ポイント1",
    "重要ポイント2",
    "重要ポイント3"
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
            print(f"Error in Gemini summarization: {e}")
            return {
                "summary": "要約の生成に失敗しました。",
                "key_points": []
            }
