<p align="center">
  <h1 align="center">🚀 Pushikoo</h1>
  <p align="center">A powerful, extensible message synchronization framework for aggregating, processing, and pushing content across platforms.</p>
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

## ✨ Features

- **🔌 Plugin-Based Adapters** — Extend functionality with installable adapter packages (Getters, Processers, Pushers)
- **🔄 Flexible Flow Pipelines** — Build custom data processing pipelines by chaining adapter instances
- **⏰ Scheduled Automation** — Set up cron jobs to automate flow execution
- **🌐 Modern Web Dashboard** — Intuitive Vue 3 + Vuetify UI for complete management
- **🔐 Secure by Default** — Token-based authentication with optional SSO support
- **🌍 Multi-language Support** — Built-in i18n for English, Chinese, and Japanese

## 📦 Installation

### Create Virtual Environment

```bash
# Using uv (recommended)
uv venv

# Or using Python
python -m venv .venv
```

### Activate Virtual Environment

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Bash / Zsh:**

```bash
source .venv/bin/activate
```

### Install Pushikoo

```bash
# Using uv (recommended)
uv pip install pushikoo

# Or using pip
pip install pushikoo
```

### Configure Environment Variables

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

Or create a `.env` file in the working directory — Pushikoo will load it automatically. See [`.env.example`](./backend/.env.example) for the full template.

### Run Pushikoo

```bash
pushikoo
```

## :wrench: Development

### Prerequisites

- Node.js 18+ with pnpm
- [uv](https://github.com/astral-sh/uv)

### Backend Setup

```bash
cd backend
uv sync
python src/pushikoo/main.py
```

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

### Sync API Changes

After modifying backend API endpoints, regenerate the frontend client:

```bash
# From root directory
./backend/.venv/scripts/activate
python script/generate_api_client.py
```

### Build for Production

```bash
# From root directory
./backend/.venv/scripts/activate
python script/build.py
```

## 📖 Core Concepts

### Adapters

Adapters are pluggable Python packages that implement one of three interfaces:

| Type      | Purpose                         |
| --------- | ------------------------------- |
| Getter    | Fetch new messages from sources |
| Processer | Transform or filter messages    |
| Pusher    | Send messages to destinations   |

Install adapters via the web dashboard or using pip:

```bash
pip install pushikoo-getter-rss
pip install pushikoo-pusher-telegram
```

### Instances

Instances are configured deployments of adapters. Each instance has:

- A unique identifier
- Adapter-specific configuration (credentials, options, etc.)

### Flows

Flows define processing pipelines by chaining adapter instances:

```
Getter (RSS Feed) → Processer (Translate) → Pusher (Telegram Bot)
```

### Crons

Crons schedule automatic flow execution using standard cron expressions:

| Fields | Format                                        |
| ------ | --------------------------------------------- |
| 5      | `minute hour day month dayOfWeek`             |
| 6      | `second minute hour day month dayOfWeek`      |
| 7      | `second minute hour day month dayOfWeek year` |

## 🌐 Web Dashboard

The dashboard provides a complete management interface:

- **Dashboard** — Overview and quick navigation
- **Adapters** — Install, upgrade, and configure adapter packages
- **Instances** — Create and manage adapter instances
- **Flows** — Build and test data processing pipelines
- **Crons** — Schedule automated flow execution
- **Messages** — Browse and search processed messages
- **Warnings** — Configure alert recipients
- **System** — Global configuration and policies

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0**
