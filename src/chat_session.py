#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
チャットセッションを管理するモジュール。

このモジュールはチャットの履歴やコンテキストを管理します。
"""

from typing import Dict, List, Literal


class ChatSession:
    """
    チャットセッションを管理するクラス。

    チャットの履歴やコンテキストを保持し、メッセージの追加や取得を行います。
    """

    def __init__(self):
        """
        ChatSessionクラスのコンストラクタ。

        チャット履歴を初期化します。
        """
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: Literal["user", "assistant"], content: str) -> None:
        """
        チャット履歴にメッセージを追加します。

        Args:
            role: メッセージの送信者（'user'または'assistant'）
            content: メッセージの内容
        """
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """
        チャット履歴のすべてのメッセージを取得します。

        Returns:
            List[Dict[str, str]]: チャット履歴のメッセージリスト
        """
        return self.messages

    def clear(self) -> None:
        """
        チャット履歴をクリアします。
        """
        self.messages = []
