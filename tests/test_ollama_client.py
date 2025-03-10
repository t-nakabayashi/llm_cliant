#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OllamaClientクラスのテストモジュール。
"""

import pytest
from unittest.mock import patch, MagicMock
from src.ollama_client import OllamaClient

# ollamaモジュールをモック
ollama_mock = MagicMock()
# src.ollama_client内のollamaをモック
patch_path = "src.ollama_client.ollama"


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
def test_list_models_error(mock_ollama, ollama_client):
    """
    list_modelsメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_ollama.list.side_effect = Exception("Connection error")

    # テスト実行
    result = ollama_client.list_models()

    # 検証
    assert result == []
    mock_ollama.list.assert_called_once()


@patch(patch_path)
def test_chat_success(mock_ollama, ollama_client):
    """
    chatメソッドが成功した場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_response = {"message": {"role": "assistant", "content": "こんにちは、何かお手伝いできますか？"}}
    mock_ollama.chat.return_value = mock_response

    # テスト用のパラメータ
    model = "llama2"
    messages = [{"role": "user", "content": "こんにちは"}]

    # テスト実行
    result = ollama_client.chat(model, messages)

    # 検証
    assert result == mock_response
    mock_ollama.chat.assert_called_once_with(model=model, messages=messages, context=None, options={})


@patch(patch_path)
def test_chat_with_options(mock_ollama, ollama_client):
    """
    chatメソッドがオプション付きで呼び出された場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    mock_response = {"message": {"role": "assistant", "content": "こんにちは、何かお手伝いできますか？"}}
    mock_ollama.chat.return_value = mock_response

    # テスト用のパラメータ
    model = "llama2"
    messages = [{"role": "user", "content": "こんにちは"}]
    options = {"temperature": 0.7, "top_p": 0.9}

    # テスト実行
    result = ollama_client.chat(model, messages, options=options)

    # 検証
    assert result == mock_response
    mock_ollama.chat.assert_called_once_with(model=model, messages=messages, context=None, options=options)


@patch(patch_path)
def test_chat_error(mock_ollama, ollama_client):
    """
    chatメソッドがエラーを発生させた場合のテスト。

    Args:
        mock_ollama: ollamaモジュールのモック
        ollama_client: OllamaClientインスタンス
    """
    # モックの設定
    error_message = "Model not found"
    mock_ollama.chat.side_effect = Exception(error_message)

    # テスト用のパラメータ
    model = "unknown-model"
    messages = [{"role": "user", "content": "こんにちは"}]

    # テスト実行
    result = ollama_client.chat(model, messages)

    # 検証
    assert "エラーが発生しました" in result["message"]["content"]
    assert error_message in result["message"]["content"]
    mock_ollama.chat.assert_called_once()


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
