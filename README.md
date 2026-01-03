# Telegram Intelligence Agent 🧠

A local AI-powered agent that monitors your "Saved Messages" in Telegram, analyzes them using Google Gemini 2.0, and organizes actionable items into a sleek local web dashboard.

## ✨ Features

- **🔎 Real-time Monitoring**: Listens to messages you send to your **Saved Messages** (or DMs).
- **🤖 AI Analysis**: Uses **Gemini 2.0 Flash** to:
  - Rate urgency/importance (0-10).
  - Summarize content.
  - Detect action items.
  - **Extract Deadlines** (e.g., "by Friday 5pm").
- **📊 Web Dashboard**: A beautiful, local Dark Mode interface to manage your tasks.
  - Live updates (Optimistic UI).
  - Filter by priority (High/Medium/Low).
  - Mark tasks as **Done** with a click.
  - "Deadline" badges for time-sensitive tasks.
- **⚡ Fast & Reliable**:
  - Uses `Pyrogram` with **Smart Session Management** (In-Memory) to prevent database locks.
  - Concurrent `FastAPI` server and Telegram Client execution.
  - Instant startup and graceful <5s shutdown.

## 🚀 Installation

### Prerequisites
- Python 3.10+
- A Telegram Account
- [Google AI Studio API Key](https://aistudio.google.com/)

### 1. Clone & Setup
```bash
git clone https://github.com/0xcrypto2024/telegram-agent.git
cd telegram-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```bash
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
GENAI_KEY=your_gemini_api_key
SESSION_STRING=  # Leave empty initially
```
*Get your Telegram credentials from [my.telegram.org](https://my.telegram.org).*

### 3. Generate Session String (One-time)
To avoid local database issues and file locking, we use a Session String.
Run the generator script and follow the login prompts:
```bash
python generate_session.py
```
Copy the output string and paste it into your `.env`:
```bash
SESSION_STRING=your_long_session_string_here
```

## 🏃‍♂️ Usage

**Start the Agent:**
```bash
python main.py
```

**How to use:**
1. Open Telegram and go to **Saved Messages**.
2. Send a message like:
   > "Remind me to submit the tax report by Friday 5pm."
3. The Agent will reply: `✅ Task Added`
4. Open the Dashboard at **http://localhost:8000** to see your task!

**Stop the Agent:**
Press `Ctrl+C`. The services will shut down cleanly within seconds.

## 🏗️ Architecture

- **`main.py`**: Orchestrator. Runs `listener` and `server` concurrently using `asyncio`.
- **`listener.py`**: Telegram Client (Pyrogram). Handles message events and loop management.
- **`agent.py`**: Intelligence Engine. Calls Gemini API for JSON-structured analysis.
- **`server.py`**: FastAPI backend serving the Dashboard.
- **`templates/dashboard.html`**: Single-page application (HTML/JS/TailwindCSS).
- **`task_manager.py`**: In-memory store for active tasks.

## 🛡️ Security Note
This agent runs **locally**. Your credentials and session data are stored only on your machine (or in your `.env`). No data is sent to third-party servers other than Telegram (connection) and Google (content analysis).
