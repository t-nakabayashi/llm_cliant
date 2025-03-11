#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLMチャットWebアプリケーションのメインモジュール。

このモジュールはFlaskを使用してWebサーバーを起動し、
チャットインターフェースを提供します。
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from src.chat_session import ChatSession
from src.ollama_client import OllamaClient

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"
socketio = SocketIO(app)

# チャットセッションの初期化
chat_session = ChatSession()

# ollamaクライアントの初期化
ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
ollama_client = OllamaClient(host=ollama_host)

# 現在選択されているモデル
current_model = None

# モデルパラメータの設定
model_params = {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "context_length": 4096, "repeat_penalty": 1.1}


@app.route("/")
def index():
    """
    メインページを表示します。

    Returns:
        str: レンダリングされたHTMLテンプレート
    """
    return render_template("index.html")


@app.route("/api/models")
def get_models():
    """
    利用可能なモデルの一覧を取得します。

    Returns:
        Response: モデル情報のJSONレスポンス
    """
    models = ollama_client.list_models()
    return jsonify({"models": models})


@app.route("/api/running_models")
def get_running_models():
    """
    現在起動中のモデルの一覧を取得します。

    Returns:
        Response: 起動中のモデル情報のJSONレスポンス
    """
    models = ollama_client.list_running_models()
    return jsonify({"models": models})


@app.route("/api/kill_model", methods=["POST"])
def kill_model():
    """
    指定したモデルを終了します。

    Returns:
        Response: 終了結果のJSONレスポンス
    """
    data = request.json
    model_id = data.get("id")

    if not model_id:
        return jsonify({"success": False, "error": "モデルIDが指定されていません"}), 400

    success = ollama_client.kill_model(model_id)
    return jsonify({"success": success})


@app.route("/api/gpu_info")
def get_gpu_info():
    """
    GPUの情報と使用率を取得します。

    Returns:
        Response: GPU情報のJSONレスポンス
    """
    gpu_info = ollama_client.get_gpu_info()
    return jsonify({"gpus": gpu_info})


@app.route("/api/select_model", methods=["POST"])
def select_model():
    """
    モデルを選択します。

    Returns:
        Response: 選択結果のJSONレスポンス
    """
    data = request.json
    model_name = data.get("model")

    if not model_name:
        return jsonify({"success": False, "error": "モデル名が指定されていません"}), 400

    global current_model
    current_model = model_name

    # チャットセッションをクリア
    chat_session.clear()

    # モデル情報を取得
    model_info = ollama_client.get_model_info(model_name)

    return jsonify({"success": True, "model": model_name, "model_info": model_info})


@app.route("/api/model_params", methods=["GET"])
def get_model_params():
    """
    現在のモデルパラメータを取得します。

    Returns:
        Response: モデルパラメータのJSONレスポンス
    """
    return jsonify({"params": model_params})


@app.route("/api/model_params", methods=["POST"])
def update_model_params():
    """
    モデルパラメータを更新します。

    Returns:
        Response: 更新結果のJSONレスポンス
    """
    data = request.json
    params = data.get("params", {})

    global model_params

    # パラメータの検証と更新
    if "temperature" in params:
        temp = float(params["temperature"])
        model_params["temperature"] = max(0.0, min(1.0, temp))

    if "top_p" in params:
        top_p = float(params["top_p"])
        model_params["top_p"] = max(0.0, min(1.0, top_p))

    if "top_k" in params:
        top_k = int(params["top_k"])
        model_params["top_k"] = max(1, top_k)

    if "context_length" in params:
        ctx_len = int(params["context_length"])
        model_params["context_length"] = max(512, min(32768, ctx_len))

    if "repeat_penalty" in params:
        penalty = float(params["repeat_penalty"])
        model_params["repeat_penalty"] = max(1.0, min(2.0, penalty))

    return jsonify({"success": True, "params": model_params})


@socketio.on("send_message")
def handle_message(data):
    """
    クライアントからのメッセージを処理します。

    Args:
        data (dict): クライアントから送信されたメッセージデータ
            - message: ユーザーが入力したメッセージ
    """
    user_message = data.get("message", "")

    # メッセージをセッションに追加
    chat_session.add_message("user", user_message)

    # モデルが選択されていない場合はオウム返し
    if current_model is None:
        response = user_message
        chat_session.add_message("assistant", response)
        socketio.emit("receive_message", {"sender": "assistant", "message": response})
        return

    try:
        # ollamaを使用してチャット
        messages = chat_session.get_messages()

        # 進行状況を通知
        socketio.emit("status_update", {"status": "thinking", "message": "考え中..."})

        # ストリーミングチャットの実行
        def on_chunk(chunk):
            """
            チャンクを受け取るたびに呼び出されるコールバック関数
            """
            # クライアントにチャンクを送信
            socketio.emit("receive_chunk", {"content": chunk})

        # 完全なレスポンスを構築
        full_content = ""

        # ストリーミングチャットを実行
        for response_chunk in ollama_client.chat_stream(
            model=current_model,
            messages=messages,
            options={
                "temperature": model_params["temperature"],
                "top_p": model_params["top_p"],
                "top_k": model_params["top_k"],
                "num_ctx": model_params["context_length"],
                "repeat_penalty": model_params["repeat_penalty"],
            },
            callback=on_chunk,
        ):
            # 完了フラグをチェック
            if response_chunk.get("done", False):
                # 最終的なレスポンスを取得
                assistant_message = response_chunk.get("message", {}).get("content", "")

                # 空の応答の場合はデフォルトメッセージを設定
                if not assistant_message:
                    assistant_message = "申し訳ありませんが、応答を生成できませんでした。"

                # レスポンスをセッションに追加
                chat_session.add_message("assistant", assistant_message)

                # クライアントに完了を通知
                socketio.emit("receive_message", {"sender": "assistant", "message": assistant_message})
                socketio.emit("status_update", {"status": "ready", "message": "準備完了"})
                break
            else:
                # チャンクからコンテンツを取得
                chunk_content = response_chunk.get("message", {}).get("content", "")
                full_content += chunk_content

    except Exception as e:
        error_message = f"エラーが発生しました: {str(e)}"
        socketio.emit("receive_message", {"sender": "system", "message": error_message})
        socketio.emit("status_update", {"status": "error", "message": "エラーが発生しました"})


def main():
    """
    アプリケーションのエントリーポイント。

    テスト中は実際にサーバーを起動しないようにするため、
    この関数が直接呼び出された場合のみサーバーを起動します。
    """
    # テスト中でない場合のみサーバーを起動
    if os.environ.get("PYTEST_CURRENT_TEST") is None:
        host = os.environ.get("HOST", "127.0.0.1")
        port = int(os.environ.get("PORT", 5000))
        debug = os.environ.get("DEBUG", "False").lower() == "true"

        # 起動メッセージ
        print("ollama簡易クライアントを起動しています...")
        print(f"サーバーアドレス: http://{host}:{port}")
        print(f"ollamaサーバー: {ollama_host}")

        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
