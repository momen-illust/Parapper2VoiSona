# Parapper2VoiSona

Parapper-ASRの音声認識結果をVoiSona Talkへ送信し、リアルタイムに音声合成・読み上げを行うWindows向けツールです。

## 概要

Parapper-ASRが認識したテキストをHTTP経由で受信し、VoiSona TalkのREST APIに送信します。

受信したテキストはキューに追加され、受信順に音声合成リクエストを送信します。音声合成の完了を待たずに次のリクエストを処理します。

## 必要なソフトウェア

- Windows
- Parapper-ASR
- VoiSona Talk（REST APIを利用できる環境）

配布版exeの実行にPythonのインストールは不要です。

## 導入方法

1. GitHub Releasesから配布用ZIPをダウンロードして展開します。
2. `config.env.example` を `config.env` にコピーします（配布物に `config.env` が含まれている場合はコピー不要）。
3. `config.env` にVoiSona TalkのREST API用メールアドレス・パスワード・ポート番号を設定します。
4. VoiSona Talkを起動し、REST APIを有効にします。
5. `Parapper2VoiSona.exe` を起動します。
6. Parapper-ASRのDeveloper HTTP送信先を次のURLに設定します。

   `http://127.0.0.1:15522/api/events`

7. Parapper-ASRで音声認識を行うと、確定したテキストがVoiSona Talkで読み上げられます。

## 設定項目

| 項目 | 説明 | 初期値 |
|---|---|---|
| `SERVER_HOST` | HTTPサーバーの待受アドレス | `127.0.0.1` |
| `SERVER_PORT` | HTTPサーバーの待受ポート | `15522` |
| `VOISONA_HOST` | VoiSona Talkの接続先 | `127.0.0.1` |
| `VOISONA_PORT` | VoiSona TalkのREST APIポート | `32766` |
| `VOISONA_USER` | REST API認証用メールアドレス | 必須 |
| `VOISONA_API_PASSWORD` | REST API認証用パスワード | 必須 |
| `QUEUE_MAX_SIZE` | テキストの最大待機件数 | `100` |

## 動作仕様

- Parapper-ASRの `turn.final` イベントのみを読み上げ対象にします。
- 受信したテキストはFIFOキューで管理します。
- VoiSona Talkへのリクエストは1件ずつ順番に送信します。
- 音声合成の完了を待たずに次のテキストを処理します。
- キューが満杯の場合、新しいテキストを破棄します。
- VoiSona Talkへの送信に失敗した場合はログにエラーを表示し、次のテキストの処理を継続します。
- 使用するボイスは、取得した日本語対応ボイスの先頭を自動選択します。

## 終了方法

起動したコンソール画面で `Ctrl+C` を押すと終了します。

## 開発環境

- Python 3.14
- uv
- Python標準ライブラリ
- PyInstaller（exe生成用）

## 注意事項

- Parapper-ASRおよびVoiSona Talkは別途導入が必要です。
- `config.env` には認証情報が平文で保存されます。第三者に共有しないでください。
- 読み上げ順序はVoiSona Talk側の再生キュー処理にも依存します。
- 本ツールはParapper-ASRおよびVoiSona Talkの非公式連携ツールです。


## 開発者向け情報

### 開発環境

- Windows
- Python 3.14
- uv（Pythonパッケージ・環境管理）
- PyInstaller（exeビルド用）
- UPX（exe圧縮用、任意）

本プロジェクトはPython標準ライブラリのみで動作します。FastAPI、Uvicorn、httpxなどの外部ライブラリは使用していません。

### 開発環境の構築

リポジトリをクローンします。

```bash
git clone https://github.com/momen-illust/Parapper2VoiSona.git
cd Parapper2VoiSona
```

uvで開発環境を同期します。

```bash
uv sync
```

`config.env.example` を `config.env` にコピーします。

Windows PowerShellの場合：

```powershell
Copy-Item config.env.example config.env
```

`config.env` を開き、VoiSona Talk REST APIの認証情報を設定してください。

### Pythonで実行

VoiSona Talkを起動してREST APIを有効にした後、次のコマンドを実行します。

```bash
uv run python run.py
```

起動後、Parapper-ASRのDeveloper HTTP送信先を以下に設定します。

```text
http://127.0.0.1:15522/api/events
```

### exeのビルド

PyInstallerを使用してWindows用exeを生成します。

```bash
uv run pyinstaller --onefile --clean --noconfirm --name Parapper2VoiSona --console run.py
```

ビルドに成功すると、以下のファイルが生成されます。

```text
dist/Parapper2VoiSona.exe
```

### UPXを使用した圧縮ビルド

UPXをインストールしている場合は、次のように指定できます。

```powershell
uv run pyinstaller --onefile --clean --noconfirm --name Parapper2VoiSona --console --upx-dir "C:\Tools\upx" run.py
```

`C:\Tools\upx` は実際のUPX配置先に変更してください。

### 配布用ファイルの準備

ビルドしたexeと設定ファイルを同じフォルダに配置します。

```text
Parapper2VoiSona/
├── Parapper2VoiSona.exe
├── config.env
└── README.txt
```

配布用の `config.env` には、認証情報を記載しないでください。

### プロジェクト構成

```text
Parapper2VoiSona/
├── main.py               # HTTPサーバー、イベント受信、キュー処理
├── voisona_client.py     # VoiSona Talk REST API通信
├── config.py             # 設定ファイル読み込み
├── run.py                # アプリケーション起動処理
├── config.env.example    # 設定ファイルのテンプレート
├── pyproject.toml        # プロジェクト・開発依存関係
├── uv.lock               # uvのロックファイル
└── README.md             # ドキュメント
```

### 動作確認

1. VoiSona Talkを起動し、REST APIを有効にします。
2. `uv run python run.py` でHTTPサーバーを起動します。
3. Parapper-ASRから `turn.final` イベントを送信します。
4. コンソールにキュー追加・音声合成受付のログが表示されることを確認します。
5. VoiSona Talkで音声が再生されることを確認します。

### 注意事項

- 実際の認証情報が入った `config.env` をGitにコミットしないでください。
- HTTPサーバーは初期設定でローカルホストのみ待ち受けます。
- exe化した場合、Pythonのインストールは不要です。
- Windows環境以外での動作確認はしておりません。
