#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OllamaClientクラスのテストモジュール。
"""

import pytest
import json
from unittest.mock import patch, MagicMock, call
from src.ollama_client import OllamaClient

# src.ollama_client内のollamaをモック
patch_path = "src.ollama_client.ollama"


# ollamaモジュールをモック
class MockOllama:
    def __init__(self):
        self.host = None

    def list(self):
        return {"models": []}

    def chat(self, **kwargs):
        return {"message": {"role": "assistant", "content": "This is a mock response"}}

    def show(self, model_name):
        return {}


ollama_mock = MagicMock(spec=MockOllama)


@pytest.fixture
def ollama_client():
    """
    テスト用のOllamaClientインスタンスを提供するフィクスチャ。
    """
    return OllamaClient(host="http://localhost:11434")


def test_init():
    """
    OllamaClientの初期化をテストします。
    """
    client = OllamaClient()
    assert client.host == "http://localhost:11434"

    custom_host = "http://custom-host:11434"
    client = OllamaClient(host=custom_host)
    assert client.host == custom_host


@patch(patch_path)
def test_list_models_success(mock_ollama, ollama_client):
    """
    list_modelsメソッドが成功した場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_models = {"models": [{"name": "llama2", "size": 3791730298}, {"name": "mistral", "size": 4128796694}]}
    mock_ollama.list.return_value = mock_models

    # テスト実行
    result = ollama_client.list_models()

    # 検証
    assert result == mock_models["models"]
    mock_ollama.list.assert_called_once()


@patch(patch_path)
@patch("src.ollama_client.requests.get")
@patch("src.ollama_client.subprocess.run")
def test_list_models_error(mock_run, mock_get, mock_ollama, ollama_client):
    """
    list_modelsメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_run: subprocessのrunメソッドのモック
        mock_get: requestsのgetメソッドのモック
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_ollama.list.side_effect = Exception("Connection error")
    mock_get.side_effect = Exception("HTTP error")
    mock_run.side_effect = Exception("Command error")

    # テスト実行
    result = ollama_client.list_models()

    # 検証
    assert result == []
    mock_ollama.list.assert_called_once()
    mock_get.assert_called_once()
    mock_run.assert_called_once()


@patch(patch_path)
@patch("src.ollama_client.requests.post")
def test_chat_success(mock_post, mock_ollama, ollama_client):
    """
    chatメソッドが成功した場合のテスト。

    Args:
        mock_post: requestsのpostメソッドのモック
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_response = {"message": {"role": "assistant", "content": "こんにちは、何かお手伝いできますか？"}}
    mock_ollama.chat.return_value = mock_response

    # HTTPレスポンスのモック
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    mock_post_response.iter_lines.return_value = [
        json.dumps({"message": {"content": "こんにちは、", "role": "assistant"}}).encode("utf-8"),
        json.dumps({"message": {"content": "何かお手伝いできますか？", "role": "assistant"}, "done": True}).encode("utf-8"),
    ]
    mock_post.return_value = mock_post_response

    # テスト用のパラメータ
    model = "llama2"
    messages = [{"role": "user", "content": "こんにちは"}]

    # テスト実行
    result = ollama_client.chat(model, messages)

    # 検証
    assert result["message"]["content"] == "こんにちは、何かお手伝いできますか？"
    assert result["message"]["role"] == "assistant"
    mock_post.assert_called_once()


@patch(patch_path)
@patch("src.ollama_client.requests.post")
def test_chat_with_options(mock_post, mock_ollama, ollama_client):
    """
    chatメソッドがオプション付きで呼び出された場合のテスト。

    Args:
        mock_post: requestsのpostメソッドのモック
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_response = {"message": {"role": "assistant", "content": "こんにちは、何かお手伝いできますか？"}}
    mock_ollama.chat.return_value = mock_response

    # HTTPレスポンスのモック
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    mock_post_response.iter_lines.return_value = [
        json.dumps({"message": {"content": "こんにちは、", "role": "assistant"}}).encode("utf-8"),
        json.dumps({"message": {"content": "何かお手伝いできますか？", "role": "assistant"}, "done": True}).encode("utf-8"),
    ]
    mock_post.return_value = mock_post_response

    # テスト用のパラメータ
    model = "llama2"
    messages = [{"role": "user", "content": "こんにちは"}]
    options = {"temperature": 0.7, "top_p": 0.9}

    # テスト実行
    result = ollama_client.chat(model, messages, options=options)

    # 検証
    assert result["message"]["content"] == "こんにちは、何かお手伝いできますか？"
    assert result["message"]["role"] == "assistant"
    mock_post.assert_called_once()
    # オプションが正しく渡されていることを確認
    assert mock_post.call_args[1]["json"]["options"] == options


@patch(patch_path)
@patch("src.ollama_client.requests.post")
def test_chat_error(mock_post, mock_ollama, ollama_client):
    """
    chatメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_post: requestsのpostメソッドのモック
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    error_message = "Model not found"
    mock_ollama.chat.side_effect = Exception(error_message)

    # HTTPリクエストのモック
    mock_post.side_effect = Exception(error_message)

    # テスト用のパラメータ
    model = "unknown-model"
    messages = [{"role": "user", "content": "こんにちは"}]

    # テスト実行
    result = ollama_client.chat(model, messages)

    # 検証
    assert "エラーが発生しました" in result["message"]["content"]
    assert error_message in result["message"]["content"]
    mock_post.assert_called_once()


@patch(patch_path)
def test_get_model_info_success(mock_ollama, ollama_client):
    """
    get_model_infoメソッドが成功した場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_info = {"license": "...", "modelfile": "...", "parameters": "...", "template": "..."}
    mock_ollama.show.return_value = mock_info

    # テスト実行
    result = ollama_client.get_model_info("llama2")

    # 検証
    assert result == mock_info
    mock_ollama.show.assert_called_once_with("llama2")


@patch(patch_path)
def test_get_model_info_error(mock_ollama, ollama_client):
    """
    get_model_infoメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_ollama.show.side_effect = Exception("Model not found")

    # テスト実行
    result = ollama_client.get_model_info("unknown-model")

    # 検証
    assert result == {}
    mock_ollama.show.assert_called_once_with("unknown-model")


@patch("src.ollama_client.requests.get")
def test_list_running_models_success(mock_get, ollama_client):
    """
    list_running_modelsメソッドが成功した場合のテスト。

    Args:
        mock_get: requestsのgetメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "processes": [{"id": "abc123", "model": "llama2"}, {"id": "def456", "model": "mistral"}]
    }
    mock_get.return_value = mock_response

    # テスト実行
    result = ollama_client.list_running_models()

    # 検証
    assert len(result) == 2
    assert result[0]["id"] == "abc123"
    assert result[0]["model"] == "llama2"
    assert result[1]["id"] == "def456"
    assert result[1]["model"] == "mistral"
    mock_get.assert_called_once_with("http://localhost:11434/api/ps")


@patch("src.ollama_client.requests.get")
def test_list_running_models_error(mock_get, ollama_client):
    """
    list_running_modelsメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_get: requestsのgetメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_get.side_effect = Exception("Connection error")

    # テスト実行
    result = ollama_client.list_running_models()

    # 検証
    assert result == []
    mock_get.assert_called_once_with("http://localhost:11434/api/ps")


@patch("src.ollama_client.requests.get")
@patch("src.ollama_client.requests.post")
def test_kill_model_success(mock_post, mock_get, ollama_client):
    """
    kill_modelメソッドが成功した場合のテスト。

    Args:
        mock_post: requestsのpostメソッドのモック
        mock_get: requestsのgetメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # list_running_modelsのモック設定
    mock_get_response = MagicMock()
    mock_get_response.raise_for_status.return_value = None
    mock_get_response.json.return_value = {"processes": [{"id": "abc123", "model": "llama2"}]}
    mock_get.return_value = mock_get_response

    # kill_modelのモック設定
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    mock_post.return_value = mock_post_response

    # テスト実行
    result = ollama_client.kill_model("abc123")

    # 検証
    assert result is True
    assert mock_post.call_args_list[0] == call("http://localhost:11434/api/stop", json={"name": "llama2"})


@patch("src.ollama_client.requests.get")
@patch("src.ollama_client.requests.post")
def test_kill_model_error(mock_post, mock_get, ollama_client):
    """
    kill_modelメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_post: requestsのpostメソッドのモック
        mock_get: requestsのgetメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # list_running_modelsのモック設定
    mock_get.side_effect = Exception("Connection error")

    # kill_modelのモック設定
    mock_post.side_effect = Exception("Connection error")

    # テスト実行
    result = ollama_client.kill_model("abc123")

    # 検証
    assert result is False
    # すべてのAPIコールが失敗することを確認
    assert mock_post.call_count == 3
    assert mock_post.call_args_list == [
        call("http://localhost:11434/api/stop", json={"name": "abc123"}),
        call("http://localhost:11434/api/stop", json={"id": "abc123"}),
        call("http://localhost:11434/api/kill", json={"id": "abc123"}),
    ]


@patch("src.ollama_client.platform.system")
@patch("src.ollama_client.subprocess.run")
def test_get_gpu_info_windows(mock_run, mock_system, ollama_client):
    """
    get_gpu_infoメソッドがWindows環境で成功した場合のテスト。

    Args:
        mock_run: subprocessのrunメソッドのモック
        mock_system: platformのsystemメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_system.return_value = "Windows"
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "0, NVIDIA GeForce RTX 3080, 50, 5000, 10000"
    mock_run.return_value = mock_process

    # テスト実行
    result = ollama_client.get_gpu_info()

    # 検証
    assert len(result) == 1
    assert result[0]["index"] == "0"
    assert result[0]["name"] == "NVIDIA GeForce RTX 3080"
    assert result[0]["utilization"] == 50.0
    assert result[0]["memory_used"] == 5000.0
    assert result[0]["memory_total"] == 10000.0
    assert result[0]["memory_used_percent"] == 50.0
    mock_system.assert_called_once()
    mock_run.assert_called_once()


@patch("src.ollama_client.platform.system")
@patch("src.ollama_client.subprocess.run")
def test_get_gpu_info_linux(mock_run, mock_system, ollama_client):
    """
    get_gpu_infoメソッドがLinux環境で成功した場合のテスト。

    Args:
        mock_run: subprocessのrunメソッドのモック
        mock_system: platformのsystemメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_system.return_value = "Linux"
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "0, NVIDIA GeForce RTX 3080, 50, 5000, 10000"
    mock_run.return_value = mock_process

    # テスト実行
    result = ollama_client.get_gpu_info()

    # 検証
    assert len(result) == 1
    assert result[0]["index"] == "0"
    assert result[0]["name"] == "NVIDIA GeForce RTX 3080"
    assert result[0]["utilization"] == 50.0
    assert result[0]["memory_used"] == 5000.0
    assert result[0]["memory_total"] == 10000.0
    assert result[0]["memory_used_percent"] == 50.0
    mock_system.assert_called_once()
    mock_run.assert_called_once()


@patch("src.ollama_client.platform.system")
def test_get_gpu_info_unsupported_os(mock_system, ollama_client):
    """
    get_gpu_infoメソッドが未対応のOS環境で呼び出された場合のテスト。

    Args:
        mock_system: platformのsystemメソッドのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_system.return_value = "Unsupported OS"

    # テスト実行
    result = ollama_client.get_gpu_info()

    # 検証
    assert result == []
    mock_system.assert_called_once()
