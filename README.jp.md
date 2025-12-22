<p align="center">
  <h1 align="center">🚀 Pushikoo</h1>
  <p align="center">プラットフォーム間でコンテンツを集約、処理、配信するための強力で拡張可能なメッセージ同期フレームワーク。</p>
</p>

<p align="center">
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>
  <a href="https://github.com/Pushikoo/Pushikoo/actions"><img src="https://img.shields.io/github/actions/workflow/status/Pushikoo/Pushikoo/package.yml" alt="Build Status"></a>
  <a href="https://pypi.org/project/pushikoo"><img src="https://img.shields.io/pypi/pyversions/pushikoo" alt="Python"></a>
  <a href="https://pypi.org/project/pushikoo"><img src="https://badge.fury.io/py/pushikoo.svg" alt="PyPI version"></a>
  <a href="https://github.com/Pushikoo/Pushikoo/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Pushikoo/Pushikoo.svg" alt="License"></a>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.zhcn.md">简体中文</a> |
  <a href="README.jp.md">日本語</a>
</p>

---

## ✨ 機能

- **🔌 プラグインベースのアダプター** — インストール可能なアダプターパッケージ（Getter、Processer、Pusher）で機能を拡張
- **🔄 柔軟なフローパイプライン** — アダプターインスタンスを連鎖させてカスタムデータ処理パイプラインを構築
- **⏰ スケジュール自動化** — フロー実行を自動化するクーロンジョブを設定
- **🌐 モダンな Web ダッシュボード** — 直感的な Vue 3 + Vuetify UI で完全な管理
- **🔐 デフォルトでセキュア** — トークンベースの認証、オプションの SSO 対応
- **🌍 多言語サポート** — 英語、中国語、日本語の国際化を内蔵

## 📦 インストール

### 仮想環境の作成

```bash
# uvを使用（推奨）
uv venv

# またはPythonを使用
python -m venv .venv
```

### 仮想環境のアクティベート

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Bash / Zsh:**

```bash
source .venv/bin/activate
```

### Pushikoo のインストール

```bash
# uvを使用（推奨）
uv pip install pushikoo

# またはpipを使用
pip install pushikoo
```

### 環境変数の設定

**PowerShell:**

```powershell
$env:ENVIRONMENT = "production"
...
```

**Bash / Zsh:**

```bash
export ENVIRONMENT='production'
...
```

または、作業ディレクトリに `.env` ファイルを作成すると、Pushikoo が自動的に読み込みます。完全な `.env` テンプレートは [`.env.example`](./backend/.env.example) を参照してください。

### Pushikoo の実行

```bash
pushikoo
```

## :wrench: 開発

### 前提条件

- Node.js 18+ with pnpm
- [uv](https://github.com/astral-sh/uv)

### バックエンドセットアップ

```bash
cd backend
uv sync
python src/pushikoo/main.py
```

### フロントエンドセットアップ

```bash
cd frontend
pnpm install
pnpm dev
```

### API 変更の同期

バックエンド API エンドポイントを変更した後、フロントエンドクライアントを再生成：

```bash
# ルートディレクトリから
./backend/.venv/scripts/activate
python script/generate_api_client.py
```

### 本番用ビルド

```bash
# ルートディレクトリから
./backend/.venv/scripts/activate
python script/build.py
```

## 📖 コアコンセプト

### アダプター

アダプターは 3 つのインターフェースのいずれかを実装するプラグイン可能な Python パッケージです：

| タイプ    | 目的                                 |
| --------- | ------------------------------------ |
| Getter    | ソースから新しいメッセージを取得     |
| Processer | メッセージを変換またはフィルタリング |
| Pusher    | 宛先にメッセージを送信               |

Web ダッシュボードまたは pip を使用してアダプターをインストール：

```bash
pip install pushikoo-getter-rss
pip install pushikoo-pusher-telegram
```

### インスタンス

インスタンスはアダプターの設定済みデプロイメントです。各インスタンスには以下が含まれます：

- 一意の識別子
- アダプター固有の設定（資格情報、オプションなど）

### フロー

フローはアダプターインスタンスを連鎖させて処理パイプラインを定義します：

```
Getter (RSS Feed) → Processer (Translate) → Pusher (Telegram Bot)
```

### クーロン

クーロンは標準の cron 式を使用して自動フロー実行をスケジュールします：

| フィールド数 | フォーマット                                  |
| ------------ | --------------------------------------------- |
| 5            | `minute hour day month dayOfWeek`             |
| 6            | `second minute hour day month dayOfWeek`      |
| 7            | `second minute hour day month dayOfWeek year` |

## 🌐 Web ダッシュボード

ダッシュボードは完全な管理インターフェースを提供します：

- **ダッシュボード** — 概要とクイックナビゲーション
- **アダプター** — アダプターパッケージのインストール、アップグレード、設定
- **インスタンス** — アダプターインスタンスの作成と管理
- **フロー** — データ処理パイプラインの構築とテスト
- **クーロン** — 自動フロー実行のスケジュール
- **メッセージ** — 処理済みメッセージの閲覧と検索
- **警告** — アラート受信者の設定
- **システム** — グローバル設定とポリシー

## 🤝 コントリビューション

コントリビューションは歓迎です！お気軽に issue や pull request を提出してください。

## 📄 ライセンス

このプロジェクトは **GNU Affero General Public License v3.0** でライセンスされています
