# 🤖 Lyzr PR Review Agent

> **Automated GitHub Pull Request Review Agent with Multi-Agent AI Architecture**

An intelligent, automated code review system that analyzes GitHub Pull Requests and generates structured, actionable review comments using specialized AI agents. Built with FastAPI, Streamlit, and powered by OpenRouter (DeepSeek) for fast, accurate code analysis.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Contributing](#contributing)

---

## 🎯 Overview

The **Lyzr PR Review Agent** is a production-ready automated code review system that leverages a multi-agent AI architecture to provide comprehensive code analysis. Each agent specializes in a specific aspect of code quality:

- **Logic Agent** 🧠 - Identifies bugs, logic errors, and edge cases
- **Readability Agent** 📖 - Ensures code clarity and maintainability  
- **Performance Agent** ⚡ - Detects bottlenecks and optimization opportunities
- **Security Agent** 🔒 - Finds vulnerabilities and security risks

The system provides both a **RESTful API** (FastAPI) and a **beautiful web interface** (Streamlit) for seamless integration into your development workflow.

---

## ✨ Features

### Core Capabilities
- 🤖 **Multi-Agent Architecture** - Specialized AI agents for different review aspects
- 🔍 **Comprehensive Analysis** - Reviews logic, readability, performance, and security
- 📊 **Structured Output** - JSON-formatted comments with severity levels and suggestions
- 🔌 **GitHub Integration** - Direct integration with GitHub API for PR reviews
- 📝 **Manual Diff Support** - Review code changes without GitHub PRs
- ⚡ **Quick Review Mode** - Faster reviews for large PRs (analyzes fewer files)

### User Experience
- 🎨 **Streamlit Frontend** - Beautiful, interactive web UI
- 🚀 **FastAPI Backend** - Modern, async Python backend with auto-generated docs
- 📈 **Progress Indicators** - Real-time progress tracking during reviews
- 🎯 **Filterable Results** - Filter comments by severity and category
- 💡 **Actionable Suggestions** - Each issue includes suggested fixes

### Technical Features
- 🔄 **Async Processing** - Non-blocking API calls for better performance
- 🛡️ **Error Handling** - Robust error handling with user-friendly messages
- 🔐 **Token Caching** - Optimized API calls with IAM token caching
- 📦 **Rate Limiting** - Built-in rate limit handling for API providers
- 🎛️ **Configurable** - Support for multiple LLM providers (OpenRouter, Watsonx, OpenAI, Anthropic)

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐
│  Streamlit UI   │  ← User Interface
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI Server │  ← REST API
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│ GitHub│ │  LLM    │
│  API  │ │ Provider│
└───────┘ └─────────┘
```

### Multi-Agent Review Flow

```
PR/Diff Input
     │
     ├─► Logic Agent ──────┐
     ├─► Readability Agent ─┤
     ├─► Performance Agent ─┤──► Aggregated Review
     └─► Security Agent ─────┘
```

### Agent Specializations

| Agent | Focus Area | Example Issues |
|-------|-----------|----------------|
| **Logic** 🧠 | Correctness, Bugs | Missing null checks, off-by-one errors, incorrect conditionals |
| **Readability** 📖 | Code Quality | Unclear names, complex code, missing comments |
| **Performance** ⚡ | Optimization | Inefficient algorithms, N+1 queries, missing caching |
| **Security** 🔒 | Vulnerabilities | SQL injection, XSS, insecure authentication |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenRouter API key (recommended - free tier available)
- OR IBM Watsonx credentials
- OR OpenAI/Anthropic API key
- GitHub Personal Access Token (optional, for private repos)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd lyzr_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# See Configuration section below
```

### 3. Start the Backend

```bash
python run.py
```

The API will be available at `http://localhost:8000`

### 4. Start the Frontend (New Terminal)

```bash
python run_frontend.py
```

The UI will open at `http://localhost:8501`

---

## 📦 Installation

### Detailed Installation Steps

1. **Install Python Dependencies**

```bash
pip install -r requirements.txt
```

2. **Set Up Environment Variables**

Create a `.env` file in the project root:

```env
# OpenRouter Configuration (Recommended - Free tier available)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# LLM Provider: "openrouter", "watsonx", "openai", or "anthropic"
LLM_PROVIDER=openrouter
MODEL_NAME=deepseek/deepseek-chat-v3.1

# Temperature (0.0 to 1.0) - lower is more deterministic
TEMPERATURE=0.5

# Max tokens for response
MAX_TOKENS=500

# GitHub Configuration (optional, for private repos)
GITHUB_TOKEN=your_github_token_here
```

### Alternative LLM Providers

#### IBM Watsonx
```env
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=us-south.ml.cloud.ibm.com
LLM_PROVIDER=watsonx
MODEL_NAME=ibm/granite-3-3-8b-instruct
```

#### OpenAI
```env
OPENAI_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
MODEL_NAME=gpt-4-turbo-preview
```

#### Anthropic
```env
ANTHROPIC_API_KEY=your_anthropic_api_key
LLM_PROVIDER=anthropic
MODEL_NAME=claude-3-opus-20240229
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Yes* | - |
| `LLM_PROVIDER` | LLM provider: `openrouter`, `watsonx`, `openai`, `anthropic` | Yes | `openrouter` |
| `MODEL_NAME` | Model identifier | Yes | `deepseek/deepseek-chat-v3.1` |
| `TEMPERATURE` | Sampling temperature (0.0-1.0) | No | `0.5` |
| `MAX_TOKENS` | Maximum response tokens | No | `500` |
| `GITHUB_TOKEN` | GitHub personal access token | No | - |

*Required based on selected LLM provider

### Quick Review Mode

Enable quick review mode in the Streamlit UI or API request to:
- Review only 3 files (instead of 5)
- Use only Logic and Security agents (instead of all 4)
- Faster response times (~30-60 seconds)

---

## 💻 Usage

### Using the Streamlit UI

1. **Start both servers** (backend and frontend)
2. **Open** `http://localhost:8501` in your browser
3. **Enter PR details:**
   - Repository Owner
   - Repository Name
   - PR Number
4. **Click** "Start Review"
5. **View results** with filterable comments

### Using the API

#### Review a GitHub PR

```bash
curl -X POST "http://localhost:8000/api/review/pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "octocat",
    "repo_name": "Hello-World",
    "pr_number": 1,
    "quick_review": true
  }'
```

#### Review a Manual Diff

```bash
curl -X POST "http://localhost:8000/api/review/diff" \
  -H "Content-Type: application/json" \
  -d '{
    "diff_text": "diff --git a/file.py b/file.py\n...",
    "file_path": "src/main.py"
  }'
```

#### Python Example

```python
import httpx

# Review a PR
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
    if comment.get('suggestion'):
        print(f"💡 {comment['suggestion']}")
```

See `example_usage.py` for more examples.

---

## 📚 API Documentation

### Endpoints

#### `POST /api/review/pr`

Review a GitHub Pull Request.

**Request Body:**
```json
{
  "repo_owner": "string",
  "repo_name": "string",
  "pr_number": integer,
  "github_token": "string (optional)",
  "quick_review": boolean (optional, default: false)
}
```

**Response:**
```json
{
  "pr_number": 123,
  "repo": "owner/repo",
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
  "summary": "Found 12 review comment(s)...",
  "review_metadata": {
    "pr_title": "Add user authentication",
    "pr_author": "developer",
    "files_changed": ["src/main.py"]
  }
}
```

#### `POST /api/review/diff`

Review a manual Git diff.

**Request Body:**
```json
{
  "diff_text": "string",
  "file_path": "string (optional)"
}
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "llm_provider": "openrouter",
  "model": "deepseek/deepseek-chat-v3.1",
  "openrouter_configured": true
}
```

#### `GET /api/review/stats`

Get information about available agents and categories.

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

---

## 📁 Project Structure

```
lyzr_backend/
├── main.py                 # FastAPI application and endpoints
├── models.py               # Pydantic data models
├── config.py               # Configuration and settings
├── agents.py               # Multi-agent review system
├── github_client.py        # GitHub API client
├── diff_parser.py          # Git diff parser
├── openrouter_llm.py       # OpenRouter LLM integration
├── watsonx_llm.py          # IBM Watsonx LLM integration
├── streamlit_app.py        # Streamlit frontend UI
├── run.py                  # Backend quick start script
├── run_frontend.py         # Frontend quick start script
├── example_usage.py        # API usage examples
├── setup_env.py            # Environment setup helper
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

### Key Components

- **`main.py`** - FastAPI application with REST endpoints
- **`agents.py`** - Multi-agent system with specialized reviewers
- **`github_client.py`** - Handles GitHub API interactions
- **`diff_parser.py`** - Parses Git diffs into structured format
- **`streamlit_app.py`** - Web UI for easy interaction
- **`openrouter_llm.py`** - OpenRouter/DeepSeek integration
- **`watsonx_llm.py`** - IBM Watsonx integration

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework with async support
- **LangChain** - LLM orchestration and agent framework
- **Pydantic** - Data validation and settings management
- **httpx** - Async HTTP client for API calls
- **Python 3.9+** - Modern Python features

### Frontend
- **Streamlit** - Interactive web UI framework
- **Custom CSS** - Styled components and visualizations

### LLM Providers
- **OpenRouter** (Primary) - Access to multiple models including DeepSeek
- **IBM Watsonx** - Granite models
- **OpenAI** - GPT models
- **Anthropic** - Claude models

### Integrations
- **GitHub API** - Direct PR and diff access
- **Git Diff Parsing** - Custom diff parser

---

## 🎯 Review Categories & Severity

### Categories

| Category | Description | Example Issues |
|----------|-------------|----------------|
| **Logic** 🧠 | Correctness and bugs | Missing null checks, incorrect conditionals |
| **Readability** 📖 | Code clarity | Unclear names, complex code |
| **Performance** ⚡ | Optimization | Inefficient algorithms, N+1 queries |
| **Security** 🔒 | Vulnerabilities | SQL injection, XSS, insecure auth |
| **Best Practices** ✨ | Standards | Code conventions, patterns |
| **Testing** 🧪 | Test quality | Missing tests, poor coverage |

### Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| **Critical** 🔴 | Must fix before merging | Security issues, critical bugs |
| **Major** 🟠 | Should fix | Significant issues |
| **Minor** 🟡 | Nice to fix | Small improvements |
| **Suggestion** 🟢 | Optional | Enhancements |

---

## 🤝 Contributing

This project is part of the **Lyzr AI Backend Engineering Intern Challenge**.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

---

## 📝 License

This project is part of the Lyzr AI Backend Engineering Intern Challenge.

---

## 🙏 Acknowledgments

- **Lyzr AI** - For the challenge opportunity
- **OpenRouter** - For providing free tier access to LLM models
- **FastAPI** - For the excellent web framework
- **Streamlit** - For the beautiful UI framework

---

## 📞 Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the example usage in `example_usage.py`
3. Check the health endpoint at `/health` for configuration status

---

**Built with ❤️ for the Lyzr AI Backend Engineering Challenge**
#   m u l t i - a g e n t - A I  
 