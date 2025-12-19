<p align="center">
  <h1 align="center">🚀 Pushikoo</h1>
  <p align="center">一个强大、可扩展的消息同步框架，用于跨平台聚合、处理和推送内容。</p>
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

## ✨ 功能特性

- **🔌 插件化适配器** — 通过安装适配器包（Getter、Processer、Pusher）扩展功能
- **🔄 灵活的流程管道** — 通过链接适配器实例构建自定义数据处理管道
- **⏰ 定时自动化** — 设置定时任务自动执行流程
- **🌐 现代化 Web 仪表板** — 直观的 Vue 3 + Vuetify UI 进行完整管理
- **🔐 默认安全** — 基于令牌的身份验证，支持可选的 SSO
- **🌍 多语言支持** — 内置英语、中文和日语国际化

## 📦 安装

### 创建虚拟环境

```bash
# 使用 uv（推荐）
uv venv

# 或使用 Python
python -m venv .venv
```

### 激活虚拟环境

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Bash / Zsh:**

```bash
source .venv/bin/activate
```

### 安装 Pushikoo

```bash
# 使用 uv（推荐）
uv pip install pushikoo

# 或使用 pip
pip install pushikoo
```

### 运行 Pushikoo

```bash
pushikoo
```

## :wrench: 开发

### 前置条件

- Python 3.12+
- Node.js 18+ with pnpm
- [uv](https://github.com/astral-sh/uv)（Python 包管理器）

### 后端设置

```bash
cd backend
uv sync
python src/pushikoo/main.py
```

### 前端设置

```bash
cd frontend
pnpm install
pnpm dev
```

### 同步 API 更改

修改后端 API 端点后，重新生成前端客户端：

```bash
# 在根目录
./backend/.venv/scripts/activate
python script/generate_api_client.py
```

### 构建生产版本

```bash
# 在根目录
./backend/.venv/scripts/activate
python script/build.py
```

## 📖 核心概念

### 适配器

适配器是实现三种接口之一的可插拔 Python 包：

| 类型      | 用途                 |
| --------- | -------------------- |
| Getter    | 从源获取新消息       |
| Processer | 转换或过滤消息       |
| Pusher    | 将消息发送到目标位置 |

通过 Web 仪表板或使用 pip 安装适配器：

```bash
pip install pushikoo-getter-rss
pip install pushikoo-pusher-telegram
```

### 实例

实例是适配器的配置部署。每个实例包含：

- 唯一标识符
- 适配器特定配置（凭据、选项等）

### 流程

流程通过链接适配器实例来定义处理管道：

```
Getter (RSS Feed) → Processer (Translate) → Pusher (Telegram Bot)
```

### 定时任务

定时任务使用标准 cron 表达式调度自动流程执行：

| 字段数 | 格式                                          |
| ------ | --------------------------------------------- |
| 5      | `minute hour day month dayOfWeek`             |
| 6      | `second minute hour day month dayOfWeek`      |
| 7      | `second minute hour day month dayOfWeek year` |

## 🌐 Web 仪表板

仪表板提供完整的管理界面：

- **仪表板** — 概览和快速导航
- **适配器** — 安装、升级和配置适配器包
- **实例** — 创建和管理适配器实例
- **流程** — 构建和测试数据处理管道
- **定时任务** — 调度自动流程执行
- **消息** — 浏览和搜索已处理的消息
- **警告** — 配置警报接收者
- **系统** — 全局配置和策略

## 🤝 贡献

欢迎贡献！请随时提交 issues 和 pull requests。

## 📄 许可证

本项目采用 **GNU Affero 通用公共许可证 v3.0** 授权
