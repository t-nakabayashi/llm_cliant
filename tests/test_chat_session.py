#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChatSessionクラスのテストモジュール。
"""

from src.chat_session import ChatSession


def test_init():
    """
    ChatSessionの初期化をテストします。
    """
    session = ChatSession()
    assert session.messages == []


def test_add_message():
    """
    add_messageメソッドをテストします。
    """
    session = ChatSession()

    # ユーザーメッセージの追加
    session.add_message("user", "こんにちは")
    assert len(session.messages) == 1
    assert session.messages[0]["role"] == "user"
    assert session.messages[0]["content"] == "こんにちは"

    # アシスタントメッセージの追加
    session.add_message("assistant", "こんにちは、何かお手伝いできますか？")
    assert len(session.messages) == 2
    assert session.messages[1]["role"] == "assistant"
    assert session.messages[1]["content"] == "こんにちは、何かお手伝いできますか？"


def test_get_messages():
    """
    get_messagesメソッドをテストします。
    """
    session = ChatSession()

    # メッセージを追加
    session.add_message("user", "こんにちは")
    session.add_message("assistant", "こんにちは、何かお手伝いできますか？")

    # メッセージの取得
    messages = session.get_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "こんにちは"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "こんにちは、何かお手伝いできますか？"


def test_clear():
    """
    clearメソッドをテストします。
    """
    session = ChatSession()

    # メッセージを追加
    session.add_message("user", "こんにちは")
    session.add_message("assistant", "こんにちは、何かお手伝いできますか？")

    # メッセージをクリア
    session.clear()
    assert session.messages == []
