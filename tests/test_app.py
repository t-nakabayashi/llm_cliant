#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flaskアプリケーションのテストモジュール。
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.app import app


@pytest.fixture
def client():
    """
    テスト用のFlaskクライアントを提供するフィクスチャ。
    """
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # CSRFを無効化
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """
    インデックスルートのテスト。

    Args:
        client: テスト用のFlaskクライアント
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"LLM" in response.data  # タイトルにLLMが含まれていることを確認


@patch("src.app.ollama_client.list_models")
def test_get_models_route(mock_list_models, client):
    """
    モデル一覧取得ルートのテスト。

    Args:
        mock_list_models: ollama_client.list_modelsのモック
        client: テスト用のFlaskクライアント
    """
    # モックの設定
    mock_models = [{"name": "llama2", "size": 3791730298}, {"name": "mistral", "size": 4128796694}]
    mock_list_models.return_value = mock_models

    # テスト実行
    response = client.get("/api/models")

    # 検証
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "models" in data
    assert data["models"] == mock_models
    mock_list_models.assert_called_once()


@patch("src.app.ollama_client.get_model_info")
def test_select_model_route_success(mock_get_model_info, client):
    """
    モデル選択ルートの成功テスト。

    Args:
        mock_get_model_info: ollama_client.get_model_infoのモック
        client: テスト用のFlaskクライアント
    """
    # モックの設定
    mock_model_info = {"license": "...", "modelfile": "...", "parameters": "...", "template": "..."}
    mock_get_model_info.return_value = mock_model_info

    # テスト実行
    response = client.post("/api/select_model", data=json.dumps({"model": "llama2"}), content_type="application/json")

    # 検証
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["model"] == "llama2"
    assert data["model_info"] == mock_model_info
    mock_get_model_info.assert_called_once_with("llama2")


def test_select_model_route_failure(client):
    """
    モデル選択ルートの失敗テスト（モデル名なし）。

    Args:
        client: テスト用のFlaskクライアント
    """
    # テスト実行
    response = client.post("/api/select_model", data=json.dumps({}), content_type="application/json")

    # 検証
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "error" in data


def test_get_model_params_route(client):
    """
    モデルパラメータ取得ルートのテスト。

    Args:
        client: テスト用のFlaskクライアント
    """
    # テスト実行
    response = client.get("/api/model_params")

    # 検証
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "params" in data
    assert "temperature" in data["params"]
    assert "top_p" in data["params"]
    assert "top_k" in data["params"]
    assert "context_length" in data["params"]
    assert "repeat_penalty" in data["params"]


def test_update_model_params_route(client):
    """
    モデルパラメータ更新ルートのテスト。

    Args:
        client: テスト用のFlaskクライアント
    """
    # テスト用のパラメータ
    test_params = {"temperature": 0.8, "top_p": 0.95, "top_k": 50, "context_length": 8192, "repeat_penalty": 1.2}

    # テスト実行
    response = client.post("/api/model_params", data=json.dumps({"params": test_params}), content_type="application/json")

    # 検証
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert "params" in data
    assert data["params"]["temperature"] == test_params["temperature"]
    assert data["params"]["top_p"] == test_params["top_p"]
    assert data["params"]["top_k"] == test_params["top_k"]
    assert data["params"]["context_length"] == test_params["context_length"]
    assert data["params"]["repeat_penalty"] == test_params["repeat_penalty"]


def test_update_model_params_validation(client):
    """
    モデルパラメータ更新の検証テスト。

    Args:
        client: テスト用のFlaskクライアント
    """
    # 範囲外の値を含むパラメータ
    invalid_params = {
        "temperature": 2.0,  # 0.0〜1.0の範囲外
        "top_p": -0.1,  # 0.0〜1.0の範囲外
        "top_k": 0,  # 1以上の範囲外
        "context_length": 100,  # 512以上の範囲外
        "repeat_penalty": 3.0,  # 1.0〜2.0の範囲外
    }

    # テスト実行
    response = client.post("/api/model_params", data=json.dumps({"params": invalid_params}), content_type="application/json")

    # 検証
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert "params" in data

    # 値が適切に制限されていることを確認
    assert data["params"]["temperature"] == 1.0  # 最大値に制限
    assert data["params"]["top_p"] == 0.0  # 最小値に制限
    assert data["params"]["top_k"] == 1  # 最小値に制限
    assert data["params"]["context_length"] == 512  # 最小値に制限
    assert data["params"]["repeat_penalty"] == 2.0  # 最大値に制限
