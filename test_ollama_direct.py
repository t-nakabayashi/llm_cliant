#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ollamaサーバーとの直接通信をテストするスクリプト。
"""

import requests
import json
import subprocess
import platform
import time


def test_list_running_models():
    """
    起動中のモデル一覧を取得するテスト。
    """
    print("=== 起動中のモデル一覧のテスト ===")

    # 直接HTTPリクエストを送信
    try:
        url = "http://localhost:11434/api/ps"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        print(f"HTTP API応答: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if "processes" in data:
            processes = data["processes"]
            if processes:
                print(f"起動中のモデル数: {len(processes)}")
                for process in processes:
                    print(f"モデル: {process.get('model', 'unknown')}, ID: {process.get('id', 'unknown')}")
            else:
                print("起動中のモデルはありません。")
        else:
            print("応答に 'processes' フィールドがありません。")
    except Exception as e:
        print(f"HTTPリクエストでのモデル一覧取得に失敗しました: {e}")

    # コマンドラインでの取得を試みる
    try:
        print("\nコマンドラインでの取得を試みます...")
        result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
        print(f"コマンド出力:\n{result.stdout}")

        if result.stderr:
            print(f"エラー出力:\n{result.stderr}")
    except Exception as e:
        print(f"コマンドラインでのモデル一覧取得に失敗しました: {e}")


def test_gpu_info():
    """
    GPU情報を取得するテスト。
    """
    print("\n=== GPU情報のテスト ===")

    system = platform.system()
    print(f"実行環境: {system}")

    try:
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
                return

            print("GPU情報:")
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = line.split(", ")
                if len(parts) >= 5:
                    gpu_index = parts[0]
                    gpu_name = parts[1]
                    gpu_util = float(parts[2])
                    gpu_mem_used = float(parts[3])
                    gpu_mem_total = float(parts[4])
                    gpu_mem_percent = (gpu_mem_used / gpu_mem_total) * 100 if gpu_mem_total > 0 else 0

                    print(f"GPU {gpu_index}: {gpu_name}")
                    print(f"  使用率: {gpu_util}%")
                    print(f"  メモリ: {gpu_mem_used}MB / {gpu_mem_total}MB ({gpu_mem_percent:.1f}%)")

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
                return

            print("GPU情報:")
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = line.split(", ")
                if len(parts) >= 5:
                    gpu_index = parts[0]
                    gpu_name = parts[1]
                    gpu_util = float(parts[2])
                    gpu_mem_used = float(parts[3])
                    gpu_mem_total = float(parts[4])
                    gpu_mem_percent = (gpu_mem_used / gpu_mem_total) * 100 if gpu_mem_total > 0 else 0

                    print(f"GPU {gpu_index}: {gpu_name}")
                    print(f"  使用率: {gpu_util}%")
                    print(f"  メモリ: {gpu_mem_used}MB / {gpu_mem_total}MB ({gpu_mem_percent:.1f}%)")

        else:
            print(f"未対応のOS: {system}")

    except Exception as e:
        print(f"GPU情報の取得に失敗しました: {e}")


def test_kill_model():
    """
    モデルを終了するテスト。
    注意: このテストは実際にモデルを終了するため、慎重に実行してください。
    """
    print("\n=== モデル終了のテスト ===")
    print("注意: このテストは実際にモデルを終了します。")

    # まず起動中のモデルを取得
    try:
        url = "http://localhost:11434/api/ps"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "processes" in data and data["processes"]:
            processes = data["processes"]
            print(f"起動中のモデル数: {len(processes)}")

            # 終了するモデルのIDを入力
            print("\n起動中のモデル:")
            for i, process in enumerate(processes):
                print(f"{i + 1}. モデル: {process.get('model', 'unknown')}, ID: {process.get('id', 'unknown')}")

            choice = input("\n終了するモデルの番号を入力してください（終了しない場合は何も入力せずにEnterを押してください）: ")
            if choice and choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(processes):
                    model_id = processes[index]["id"]

                    # モデルを終了
                    print(f"\nモデル（ID: {model_id}）を終了します...")
                    kill_url = f"{url.replace('/ps', '/kill')}"
                    kill_response = requests.post(kill_url, json={"id": model_id})
                    kill_response.raise_for_status()

                    print("モデルを終了しました。")

                    # 終了後の状態を確認
                    time.sleep(1)  # 少し待機
                    print("\n終了後の状態:")
                    test_list_running_models()
                else:
                    print("無効な番号です。")
            else:
                print("モデルの終了をスキップします。")
        else:
            print("起動中のモデルがありません。")
    except Exception as e:
        print(f"モデル終了のテストに失敗しました: {e}")


if __name__ == "__main__":
    test_list_running_models()
    test_gpu_info()

    # モデル終了のテストは慎重に実行
    run_kill_test = input("\nモデル終了のテストを実行しますか？（y/N）: ")
    if run_kill_test.lower() == "y":
        test_kill_model()
    else:
        print("モデル終了のテストをスキップします。")
