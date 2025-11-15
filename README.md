# 🤖 Lyzr PR Review Agent

<div align="center">

**Automated GitHub Pull Request Review Agent with Multi-Agent AI Architecture**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Intelligent code review system powered by AI agents*

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [API](#-api-endpoints)

</div>

---

## 📖 Overview

The **Lyzr PR Review Agent** is an intelligent, automated code review system that analyzes GitHub Pull Requests and generates structured, actionable review comments using specialized AI agents. Built with FastAPI and Streamlit, powered by OpenRouter (DeepSeek) for fast and accurate code analysis.

### Key Highlights

- 🎯 **Multi-Agent Architecture** - Specialized AI agents for different review aspects
- ⚡ **Fast & Efficient** - Quick review mode for large PRs
- 🎨 **Beautiful UI** - Interactive Streamlit frontend
- 🔌 **Easy Integration** - RESTful API for seamless workflow integration
- 🔒 **Security Focused** - Dedicated security agent for vulnerability detection

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🧠 **Logic Agent** | Identifies bugs, logic errors, and edge cases |
| 📖 **Readability Agent** | Ensures code clarity and maintainability |
| ⚡ **Performance Agent** | Detects bottlenecks and optimization opportunities |
| 🔒 **Security Agent** | Finds vulnerabilities and security risks |
| 📊 **Structured Output** | JSON-formatted comments with severity levels |
| 🔄 **Manual Diff Support** | Review code changes without GitHub PRs |

### User Experience

- **Streamlit Frontend** - Beautiful, interactive web UI
- **FastAPI Backend** - Modern, async Python backend with auto-generated docs
- **Progress Indicators** - Real-time progress tracking
- **Filterable Results** - Filter comments by severity and category
- **Actionable Suggestions** - Each issue includes suggested fixes

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenRouter API key ([Get one here](https://openrouter.ai/))
- GitHub Personal Access Token (optional, for private repos)

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd lyzr_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Edit `.env` file:

```env
# OpenRouter Configuration (Recommended)
OPENROUTER_API_KEY=your_api_key_here
LLM_PROVIDER=openrouter
MODEL_NAME=deepseek/deepseek-chat-v3.1

# Optional: GitHub Token for private repos
GITHUB_TOKEN=your_github_token_here
```

### Running the Application

**Start Backend:**
```bash
python run.py
```
API available at: `http://localhost:8000`

**Start Frontend (new terminal):**
```bash
python run_frontend.py
```
UI opens at: `http://localhost:8501`

---

## 🏗️ Architecture

### System Flow

```
┌─────────────┐
│  Streamlit  │  User Interface
│     UI      │
└──────┬──────┘
       │
┌──────▼──────┐
│   FastAPI   │  REST API Server
│   Backend   │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌─▼────┐
│GitHub│ │ LLM  │
│ API  │ │Provider│
└──────┘ └──────┘
```

### Multi-Agent System

```
Input (PR/Diff)
    │
    ├─► Logic Agent ────────┐
    ├─► Readability Agent ──┤
    ├─► Performance Agent ───┤──► Aggregated Review
    └─► Security Agent ──────┘
```

---

## 📚 Documentation

### API Endpoints

#### `POST /api/review/pr`

Review a GitHub Pull Request.

**Request:**
```json
{
  "repo_owner": "octocat",
  "repo_name": "Hello-World",
  "pr_number": 1,
  "quick_review": true
}
```

**Response:**
```json
{
  "pr_number": 1,
  "repo": "octocat/Hello-World",
  "total_files_changed": 5,
  "total_comments": 12,
  "comments": [
    {
      "file_path": "src/main.py",
      "line_number": 42,
      "category": "security",
      "severity": "critical",
      "title": "SQL Injection Vulnerability",
      "description": "User input is directly concatenated...",
      "code_snippet": "query = f'SELECT * FROM users WHERE id = {user_id}'",
      "suggestion": "Use parameterized queries"
    }
  ],
  "summary": "Found 12 review comment(s)..."
}
```

#### `POST /api/review/diff`

Review a manual Git diff.

**Request:**
```json
{
  "diff_text": "diff --git a/file.py b/file.py\n...",
  "file_path": "src/main.py"
}
```

#### `GET /health`

Health check endpoint.

#### `GET /api/review/stats`

Get information about available agents and categories.

**Interactive API Docs:** Visit `http://localhost:8000/docs` for Swagger UI

---

## 💻 Usage Examples

### Using cURL

```bash
# Review a GitHub PR
curl -X POST "http://localhost:8000/api/review/pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "octocat",
    "repo_name": "Hello-World",
    "pr_number": 1
  }'
```

### Using Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/review/pr",
    json={
        "repo_owner": "owner",
        "repo_name": "repo",
        "pr_number": 123,
        "quick_review": True
    },
    timeout=600.0
)

review = response.json()
print(f"Summary: {review['summary']}")
print(f"Total Comments: {review['total_comments']}")

for comment in review['comments']:
    print(f"\n[{comment['severity'].upper()}] {comment['title']}")
    print(f"File: {comment['file_path']}:{comment['line_number']}")
```

See `example_usage.py` for more examples.

---

## 🎯 Review Categories

| Category | Icon | Focus Area |
|----------|------|------------|
| **Logic** | 🧠 | Bugs, logic errors, edge cases |
| **Readability** | 📖 | Code clarity, maintainability |
| **Performance** | ⚡ | Bottlenecks, optimization |
| **Security** | 🔒 | Vulnerabilities, risks |
| **Best Practices** | ✨ | Coding standards, conventions |
| **Testing** | 🧪 | Test coverage, quality |

### Severity Levels

| Level | Icon | Description |
|-------|------|-------------|
| **Critical** | 🔴 | Must fix before merging |
| **Major** | 🟠 | Should fix |
| **Minor** | 🟡 | Nice to fix |
| **Suggestion** | 🟢 | Optional improvements |

---

## 📁 Project Structure

```
lyzr_backend/
├── main.py                 # FastAPI application
├── agents.py               # Multi-agent review system
├── models.py               # Pydantic data models
├── config.py               # Configuration settings
├── github_client.py        # GitHub API client
├── diff_parser.py          # Git diff parser
├── openrouter_llm.py       # OpenRouter LLM integration
├── watsonx_llm.py          # IBM Watsonx LLM integration
├── streamlit_app.py        # Streamlit frontend UI
├── run.py                  # Backend launcher
├── run_frontend.py         # Frontend launcher
├── example_usage.py        # Usage examples
├── setup_env.py            # Environment helper
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **LangChain** - LLM orchestration framework
- **Pydantic** - Data validation
- **httpx** - Async HTTP client

### Frontend
- **Streamlit** - Interactive web UI
- **Custom CSS** - Styled components

### LLM Providers
- **OpenRouter** (Primary) - DeepSeek and other models
- **IBM Watsonx** - Granite models
- **OpenAI** - GPT models
- **Anthropic** - Claude models

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Yes* |
| `LLM_PROVIDER` | Provider: `openrouter`, `watsonx`, `openai`, `anthropic` | Yes |
| `MODEL_NAME` | Model identifier | Yes |
| `TEMPERATURE` | Sampling temperature (0.0-1.0) | No |
| `MAX_TOKENS` | Maximum response tokens | No |
| `GITHUB_TOKEN` | GitHub personal access token | No |

*Required based on selected LLM provider

### Quick Review Mode

Enable quick review mode to:
- Review only 3 files (instead of 5)
- Use only Logic and Security agents
- Get faster response times (~30-60 seconds)

---

## 🤝 Contributing

This project is part of the **Lyzr AI Backend Engineering Intern Challenge**.

### Development

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📝 License

This project is part of the Lyzr AI Backend Engineering Intern Challenge.

---

## 🙏 Acknowledgments

- **Lyzr AI** - Challenge opportunity
- **OpenRouter** - Free tier LLM access
- **FastAPI** - Excellent web framework
- **Streamlit** - Beautiful UI framework

---

<div align="center">

**Built with ❤️ for the Lyzr AI Backend Engineering Challenge**

[⬆ Back to Top](#-lyzr-pr-review-agent)

</div>
