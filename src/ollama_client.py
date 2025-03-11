#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ollamaサーバーとの通信を担当するモジュール。

このモジュールはollamaサーバーとの通信を行い、
モデルの一覧取得やチャット実行などの機能を提供します。
"""

import json
import requests
import re
import subprocess
import platform
from typing import Dict, List, Any, Optional, Callable, Iterator

# テスト中にollamaパッケージがなくてもインポートできるようにする
try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

    # テスト用のダミーモジュール
    class DummyOllama:
        host = None

        @staticmethod
        def list():
            return {"models": []}

        @staticmethod
        def chat(**kwargs):
            return {"message": {"role": "assistant", "content": "This is a dummy response for testing."}}

        @staticmethod
        def show(model_name):
            return {}

    ollama = DummyOllama()


class OllamaClient:
    """
    ollamaサーバーとの通信を担当するクラス。

    ollamaサーバーとの通信を行い、モデルの一覧取得やチャット実行などの機能を提供します。
    """

    def __init__(self, host: str = "http://localhost:11434"):
        """
        OllamaClientクラスのコンストラクタ。

        Args:
            host: ollamaサーバーのホスト（デフォルト: http://localhost:11434）
        """
        self.host = host.rstrip("/")
        # ollamaクライアントの設定
        if OLLAMA_AVAILABLE:
            ollama.host = host

    def list_models(self) -> List[Dict[str, Any]]:
        """
        利用可能なモデルの一覧を取得します。

        Returns:
            List[Dict[str, Any]]: モデル情報のリスト
        """
        try:
            # まず、ollama-pythonを使用して試みる
            try:
                if OLLAMA_AVAILABLE:
                    response = ollama.list()
                    print(f"ollama.list() の応答: {response}")

                    # レスポンスの形式を確認
                    if isinstance(response, dict) and "models" in response:
                        return response.get("models", [])
                    elif isinstance(response, dict):
                        # 新しいAPIの形式に対応
                        print("新しいAPI形式を検出しました")
                        return [{"name": name, "size": model.get("size", 0)} for name, model in response.items()]
                    elif isinstance(response, list):
                        # リスト形式の場合
                        return response
            except Exception as e:
                print(f"ollama-pythonでのモデル一覧取得に失敗しました: {e}")

            # 直接HTTPリクエストを送信
            print("直接HTTPリクエストでモデル一覧を取得します")
            url = f"{self.host}/api/tags"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            print(f"HTTP API応答: {data}")

            # レスポンスの形式を確認
            if "models" in data:
                return data["models"]
            elif isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # ollamaの新しいAPIでは、モデル一覧が{"model1": {...}, "model2": {...}}の形式で返される場合がある
                return [{"name": name, "size": info.get("size", 0)} for name, info in data.items()]
            else:
                print(f"未知のHTTP APIレスポンス形式: {type(data)}")
                return []
        except Exception as e:
            print(f"モデル一覧の取得に失敗しました: {e}")

            # 最後の手段として、コマンドラインの出力からモデル一覧を取得
            try:
                import subprocess

                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                output = result.stdout
                print(f"ollama list コマンド出力: {output}")

                # 出力を解析してモデル一覧を取得
                models = []
                lines = output.strip().split("\n")
                if len(lines) > 1:  # ヘッダー行をスキップ
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 3:
                            name = parts[0]
                            size_str = parts[2]
                            # サイズを数値に変換（例: "19 GB" -> 19000000000）
                            size = 0
                            try:
                                size_val = float(size_str.split()[0])
                                size_unit = size_str.split()[1].upper()
                                if size_unit == "GB":
                                    size = int(size_val * 1024 * 1024 * 1024)
                                elif size_unit == "MB":
                                    size = int(size_val * 1024 * 1024)
                            except Exception:
                                pass
                            models.append({"name": name, "size": size})
                return models
            except Exception as e:
                print(f"コマンドラインからのモデル一覧取得に失敗しました: {e}")
                return []

    def list_running_models(self) -> List[Dict[str, Any]]:
        """
        現在起動中のモデルの一覧を取得します。

        Returns:
            List[Dict[str, Any]]: 起動中のモデル情報のリスト
        """
        try:
            # 直接HTTPリクエストを送信
            url = f"{self.host}/api/ps"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            print(f"起動中のモデル一覧の応答: {data}")

            # レスポンスの形式を確認
            if "processes" in data:
                return data["processes"]
            elif "models" in data:
                # 新しいAPIの形式に対応
                models = data["models"]
                # モデル情報を標準化
                return [
                    {
                        "id": model.get("digest", "")[:12],  # digestの先頭12文字をIDとして使用
                        "model": model.get("name", "unknown"),
                    }
                    for model in models
                ]
            elif isinstance(data, list):
                return data
            else:
                print(f"未知のHTTP APIレスポンス形式: {type(data)}")
                return []
        except Exception as e:
            print(f"起動中のモデル一覧の取得に失敗しました: {e}")

            # 最後の手段として、コマンドラインの出力から起動中のモデル一覧を取得
            try:
                result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
                output = result.stdout
                print(f"ollama ps コマンド出力: {output}")

                # 出力を解析して起動中のモデル一覧を取得
                models = []
                lines = output.strip().split("\n")
                if len(lines) > 1:  # ヘッダー行をスキップ
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 2:
                            model_name = parts[0]
                            model_id = parts[1]
                            models.append({"id": model_id, "model": model_name})
                return models
            except Exception as e:
                print(f"コマンドラインからの起動中のモデル一覧取得に失敗しました: {e}")
                return []

    def kill_model(self, model_id: str) -> bool:
        """
        指定したモデルを終了します。

        Args:
            model_id: 終了するモデルのID（または名前）

        Returns:
            bool: 終了に成功した場合はTrue、失敗した場合はFalse
        """
        # 起動中のモデル一覧を取得して、IDからモデル名を特定
        model_name = None
        try:
            running_models = self.list_running_models()
            for model in running_models:
                if model.get("id", "").startswith(model_id) or model.get("model", "") == model_id:
                    model_name = model.get("model", model_id)
                    break
        except Exception as e:
            print(f"起動中のモデル一覧の取得に失敗しました: {e}")

        # モデル名が特定できなかった場合は、IDをそのまま使用
        if not model_name:
            model_name = model_id
            print(f"モデル名が特定できなかったため、ID '{model_id}' をそのまま使用します")

        # APIエンドポイントを試す
        success = False

        # /api/stop エンドポイントを試す（モデル名を使用）
        try:
            url = f"{self.host}/api/stop"
            payload = {"name": model_name}
            print(f"モデル終了APIを試行中: {url}, ペイロード: {payload}")
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"モデル終了APIが成功: {url}")
            success = True
        except Exception as e:
            print(f"モデル終了API /api/stop (name) の呼び出しに失敗: {e}")

            # /api/stop エンドポイントを試す（IDを使用）
            try:
                url = f"{self.host}/api/stop"
                payload = {"id": model_id}
                print(f"モデル終了APIを試行中: {url}, ペイロード: {payload}")
                response = requests.post(url, json=payload)
                response.raise_for_status()
                print(f"モデル終了APIが成功: {url}")
                success = True
            except Exception as e:
                print(f"モデル終了API /api/stop (id) の呼び出しに失敗: {e}")

        # /api/kill エンドポイントを試す（後方互換性のため）
        if not success:
            try:
                url = f"{self.host}/api/kill"
                payload = {"id": model_id}
                print(f"モデル終了APIを試行中: {url}, ペイロード: {payload}")
                response = requests.post(url, json=payload)
                response.raise_for_status()
                print(f"モデル終了APIが成功: {url}")
                success = True
            except Exception as e:
                print(f"モデル終了API /api/kill の呼び出しに失敗: {e}")

        # コマンドラインでの終了を試みる
        if not success:
            try:
                cmd = ["ollama", "stop", model_name]
                print(f"コマンドラインでのモデル終了を試行中: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"コマンドラインでのモデル終了が成功: {' '.join(cmd)}")
                    success = True
                else:
                    print(f"コマンドラインでのモデル終了に失敗: {result.stderr}")
            except Exception as e:
                print(f"コマンドラインでのモデル終了の実行に失敗: {e}")

        return success

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """
        GPUの情報と使用率を取得します。

        Returns:
            List[Dict[str, Any]]: GPU情報のリスト
        """
        try:
            # OSに応じてGPU情報を取得
            system = platform.system()

            if system == "Windows":
                # Windowsの場合はnvidia-smiを使用
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"nvidia-smiの実行に失敗しました: {result.stderr}")
                    return []

                # 出力を解析してGPU情報を取得
                gpus = []
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    parts = line.split(", ")
                    if len(parts) >= 5:
                        gpu_index = parts[0]
                        gpu_name = parts[1]
                        gpu_util = float(parts[2])
                        gpu_mem_used = float(parts[3])
                        gpu_mem_total = float(parts[4])

                        gpus.append(
                            {
                                "index": gpu_index,
                                "name": gpu_name,
                                "utilization": gpu_util,
                                "memory_used": gpu_mem_used,
                                "memory_total": gpu_mem_total,
                                "memory_used_percent": (gpu_mem_used / gpu_mem_total) * 100 if gpu_mem_total > 0 else 0,
                            }
                        )

                return gpus

            elif system == "Linux":
                # Linuxの場合もnvidia-smiを使用
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"nvidia-smiの実行に失敗しました: {result.stderr}")
                    return []

                # 出力を解析してGPU情報を取得
                gpus = []
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    parts = line.split(", ")
                    if len(parts) >= 5:
                        gpu_index = parts[0]
                        gpu_name = parts[1]
                        gpu_util = float(parts[2])
                        gpu_mem_used = float(parts[3])
                        gpu_mem_total = float(parts[4])

                        gpus.append(
                            {
                                "index": gpu_index,
                                "name": gpu_name,
                                "utilization": gpu_util,
                                "memory_used": gpu_mem_used,
                                "memory_total": gpu_mem_total,
                                "memory_used_percent": (gpu_mem_used / gpu_mem_total) * 100 if gpu_mem_total > 0 else 0,
                            }
                        )

                return gpus

            elif system == "Darwin":
                # macOSの場合はMPSツールを使用（Apple Silicon用）
                # 注意: これはApple Silicon搭載のMacでのみ動作します
                try:
                    # まず、ioregを使用してGPUの名前を取得
                    result = subprocess.run(["ioreg", "-l", "-w", "0"], capture_output=True, text=True)

                    gpu_name = "Apple GPU"
                    for line in result.stdout.split("\n"):
                        if "model" in line.lower() and "gpu" in line.lower():
                            match = re.search(r'"model"\s*=\s*"([^"]+)"', line)
                            if match:
                                gpu_name = match.group(1)
                                break

                    # powermetrics を使用してGPUの使用率を取得
                    # 注意: これには管理者権限が必要な場合があります
                    result = subprocess.run(
                        ["sudo", "powermetrics", "--samplers", "gpu", "-n", "1", "-i", "100"], capture_output=True, text=True
                    )

                    gpu_util = 0
                    for line in result.stdout.split("\n"):
                        if "gpu active" in line.lower():
                            match = re.search(r"(\d+)%", line)
                            if match:
                                gpu_util = float(match.group(1))
                                break

                    return [
                        {
                            "index": "0",
                            "name": gpu_name,
                            "utilization": gpu_util,
                            "memory_used": 0,  # Apple GPUではメモリ使用量を取得できない
                            "memory_total": 0,
                            "memory_used_percent": 0,
                        }
                    ]
                except Exception as e:
                    print(f"macOSでのGPU情報取得に失敗しました: {e}")
                    return []

            else:
                print(f"未対応のOS: {system}")
                return []

        except Exception as e:
            print(f"GPU情報の取得に失敗しました: {e}")
            return []

    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        チャットを実行し、ストリーミングレスポンスを返します。

        Args:
            model: 使用するモデル名
            messages: メッセージのリスト
            context: コンテキスト（省略可）
            options: オプション（省略可）
            callback: 各チャンクを受け取るコールバック関数（省略可）

        Yields:
            Dict[str, Any]: チャットの応答（チャンク単位）
        """
        # オプションの設定
        opts = options or {}

        # 直接HTTPリクエストを使用してストリーミングレスポンスを処理
        url = f"{self.host}/api/chat"
        payload = {"model": model, "messages": messages, "options": opts}
        if context:
            payload["context"] = context

        print(f"HTTP APIリクエスト: {url}, ペイロード: {payload}")

        # ストリーミングレスポンスを取得
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()

        # 完全なレスポンステキストを構築
        full_content = ""

        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")

                try:
                    json_obj = json.loads(line_str)

                    if "message" in json_obj and "content" in json_obj["message"]:
                        content = json_obj["message"]["content"]
                        full_content += content

                        # コールバック関数が指定されている場合は呼び出す
                        if callback:
                            callback(content)

                        # 完了フラグをチェック
                        if json_obj.get("done", False):
                            # 最終的なレスポンスを返す
                            json_obj["message"]["content"] = full_content
                            yield json_obj
                            return

                        # 現在のチャンクを返す
                        yield json_obj
                except json.JSONDecodeError as e:
                    print(f"JSONデコードエラー: {e}")

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        チャットを実行します。

        Args:
            model: 使用するモデル名
            messages: メッセージのリスト
            context: コンテキスト（省略可）
            options: オプション（省略可）

        Returns:
            Dict[str, Any]: チャットの応答
        """
        try:
            # オプションの設定
            opts = options or {}

            # 直接HTTPリクエストを使用してストリーミングレスポンスを処理
            url = f"{self.host}/api/chat"
            payload = {"model": model, "messages": messages, "options": opts}
            if context:
                payload["context"] = context

            print(f"HTTP APIリクエスト: {url}, ペイロード: {payload}")

            # ストリーミングレスポンスを取得
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()

            # 完全なレスポンステキストを構築
            full_content = ""
            last_json_obj = None

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")

                    try:
                        json_obj = json.loads(line_str)
                        last_json_obj = json_obj

                        if "message" in json_obj and "content" in json_obj["message"]:
                            content = json_obj["message"]["content"]
                            full_content += content
                    except json.JSONDecodeError as e:
                        print(f"JSONデコードエラー: {e}")

            # 空の応答の場合はデフォルトメッセージを設定
            if not full_content:
                full_content = "申し訳ありませんが、応答を生成できませんでした。"

            # 最後のJSONオブジェクトを更新して完全なコンテンツを含める
            if last_json_obj:
                last_json_obj["message"]["content"] = full_content
                return last_json_obj
            else:
                return {"message": {"role": "assistant", "content": full_content}}
        except Exception as e:
            print(f"チャットの実行に失敗しました: {e}")
            return {"message": {"role": "assistant", "content": f"エラーが発生しました: {str(e)}"}}

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        指定したモデルの情報を取得します。

        Args:
            model_name: モデル名

        Returns:
            Dict[str, Any]: モデル情報
        """
        try:
            # ollama-pythonを使用
            if OLLAMA_AVAILABLE:
                try:
                    response = ollama.show(model_name)
                    return response
                except Exception as e:
                    print(f"ollama-pythonでのモデル情報取得に失敗しました: {e}")

            # 直接HTTPリクエストを送信
            url = f"{self.host}/api/show"
            payload = {"name": model_name}
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"モデル情報の取得に失敗しました: {e}")
            return {}
