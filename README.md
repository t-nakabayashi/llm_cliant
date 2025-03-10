# LLM Chat Client

ollamaサーバーを使用したLLMチャットWebアプリケーションです。ブラウザ上でLLMとチャットができます。

## 機能

- ollamaサーバーからモデル一覧を取得・表示
- モデルの選択とチャット開始
- ユーザーメッセージの送信とLLMからの応答表示
- ストリーミングレスポンスのリアルタイム表示（`<think>`タグの内容も含む）
- モデルパラメータの設定（温度、top_p、top_k、コンテキスト長、繰り返しペナルティ）

## 必要条件

- Python 3.8以上
- ollamaサーバーが実行されていること（デフォルトでは`http://localhost:11434`）

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/t-nakabayashi/llm_cliant.git
cd llm_cliant

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使い方

アプリケーションの起動:

```bash
python -m src.main
```

起動後、ブラウザで http://127.0.0.1:5000 にアクセスすると、チャットインターフェースが表示されます。

### 環境変数

以下の環境変数を設定することで、アプリケーションの動作をカスタマイズできます:

- `OLLAMA_HOST`: ollamaサーバーのホスト（デフォルト: `http://localhost:11434`）
- `HOST`: Webサーバーのホスト（デフォルト: `127.0.0.1`）
- `PORT`: Webサーバーのポート（デフォルト: `5000`）
- `DEBUG`: デバッグモードの有効/無効（デフォルト: `True`）

### Dockerを使用する場合

開発環境をDockerで構築することもできます。

1. 開発環境の起動:

```bash
docker compose up -d
```

2. コンテナ内でコマンドを実行:

```bash
# コンテナのシェルにアクセス
docker compose exec app /bin/bash
```

3. 開発環境の停止:

```bash
docker compose down
```

## テスト

テストの実行:

```bash
pytest
```

### Dockerでのテスト実行

コンテナ内でテストを実行:

```bash
docker compose exec app pytest
```

## プロジェクト構成

- `src/`: ソースコード
  - `app.py`: Webアプリケーションのメインモジュール
  - `main.py`: アプリケーションのエントリーポイント
  - `chat_session.py`: チャットセッションを管理するモジュール
  - `ollama_client.py`: ollamaサーバーとの通信を担当するモジュール
  - `static/`: 静的ファイル（CSS、JavaScript）
  - `templates/`: HTMLテンプレート
- `tests/`: テストコード
- `docs/`: ドキュメント
