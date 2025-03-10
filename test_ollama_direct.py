#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ollamaクライアントの直接テスト用スクリプト。
"""

import json
import re
import requests
from src.ollama_client import OllamaClient


def clean_response(response_text):
    """
    レスポンスから<think>タグとその内容を削除します。

    Args:
        response_text: ollamaからのレスポンステキスト

    Returns:
        str: クリーニングされたテキスト
    """
    # <think>タグとその内容を削除
    if "<think>" in response_text:
        # <think>と</think>の間の内容を削除
        response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)
        # 残りの<think>タグを削除
        response_text = response_text.replace("<think>", "")
        # 残りの</think>タグを削除
        response_text = response_text.replace("</think>", "")
        # 空白行を削除
        response_text = re.sub(r"\n\s*\n", "\n\n", response_text)
        # 先頭と末尾の空白を削除
        response_text = response_text.strip()

    return response_text


def chat_with_direct_api(model_name, messages, options=None):
    """
    直接HTTPリクエストを使用してチャットを実行します。

    Args:
        model_name: 使用するモデル名
        messages: メッセージのリスト
        options: オプション（省略可）

    Returns:
        str: 完全なレスポンステキスト
    """
    url = "http://localhost:11434/api/chat"
    payload = {"model": model_name, "messages": messages, "options": options or {}}

    print(f"直接APIリクエスト: {url}, ペイロード: {payload}")

    # ストリーミングレスポンスを取得
    response = requests.post(url, json=payload, stream=True)
    response.raise_for_status()

    # 完全なレスポンステキストを構築
    full_content = ""
    all_json_lines = []

    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")
            print(f"受信ライン: {line_str}")
            all_json_lines.append(line_str)

            try:
                json_obj = json.loads(line_str)
                if "message" in json_obj and "content" in json_obj["message"]:
                    content = json_obj["message"]["content"]
                    full_content += content

                    # 完了フラグをチェック
                    if json_obj.get("done", False):
                        print("レスポンス完了")
            except json.JSONDecodeError as e:
                print(f"JSONデコードエラー: {e}")

    return full_content, all_json_lines


def main():
    """
    メイン関数。
    """
    # ollamaクライアントの初期化
    client = OllamaClient()

    # 利用可能なモデルの一覧を取得
    models = client.list_models()
    print(f"利用可能なモデル: {models}")

    if not models:
        print("利用可能なモデルがありません。ollamaサーバーが起動しているか確認してください。")
        return

    # 最初のモデルを使用
    model_name = models[0]["name"]
    print(f"使用するモデル: {model_name}")

    # チャットの実行
    messages = [{"role": "user", "content": "あなたは誰ですか？"}]

    options = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_ctx": 4096,
        "repeat_penalty": 1.1,
    }

    print("\n=== OllamaClient.chat() を使用 ===")
    print("チャットを実行中...")
    response = client.chat(
        model=model_name,
        messages=messages,
        options=options,
    )

    print("\n--- 生のレスポンス ---")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    # レスポンスからメッセージを取得
    assistant_message = response.get("message", {}).get("content", "応答がありませんでした")

    # レスポンスをクリーニング
    cleaned_message = clean_response(assistant_message)

    print("\n--- クリーニング後のメッセージ ---")
    print(cleaned_message)

    print("\n=== 直接APIを使用 ===")
    print("チャットを実行中...")
    full_content, all_json_lines = chat_with_direct_api(model_name, messages, options)

    print("\n--- 完全なレスポンステキスト ---")
    print(full_content)

    # レスポンスをクリーニング
    cleaned_content = clean_response(full_content)

    print("\n--- クリーニング後のメッセージ ---")
    print(cleaned_content)


if __name__ == "__main__":
    main()
