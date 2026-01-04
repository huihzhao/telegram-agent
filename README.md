# Telegram Intelligence Agent 🧠

A local AI-powered agent that monitors your Telegram messages, learns your habits, and organizes actionable items into a premium local dashboard.

## ✨ Features

### 🧠 Intelligent Analysis
- **Smart Monitoring**: Listens to "Saved Messages", DMs, **Mentions**, **Replies**, and **Keyword Triggers** (e.g., your name).
- **Gemini 2.0 Powered**: Analyzes context, importance, and deadlines.
- **Long-Term Memory**:
  - **Context Aware**: Checks your last 5 completed tasks to avoid duplicates.
  - **Habit Learning**: Learns from your "Rejected" tasks to ignore similar future requests.
  - **Sender Reputation**: Builds trust based on who sends you accepted vs. rejected tasks.

### 📊 Premium Dashboard 2.0
- **Modern UI**: Dark mode, glassmorphism, and smooth animations.
- **Task Management**:
  - **Active**: View and manage pending tasks.
  - **History**: Archive of Done and Rejected tasks.
  - **Undo**: Reopen any completed or rejected task instantly.
- **Visual Cues**: Priority badges, deadlines, and sender info.

### ⚙️ Core Reliability
- **Persistence**: Tasks are saved to `tasks.json` and survive restarts.
- **Performance**: In-memory session management prevents database locks.
- **Privacy**: Runs locally on your machine.

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
1. **Send a message** (e.g., "Remind me to buy milk") to your Saved Messages.
   - *Or ask a friend to rely to you in a group.*
2. **View the Dashboard**: Go to **http://localhost:8000**.
3. **Manage Tasks**:
   - Click **Done** to complete.
   - Click **Reject** to teach the AI you don't want this.
   - Click **Reopen** to undo.

**Stop the Agent:**
Press `Ctrl+C`. The persistent storage ensures no data is lost.

## 🏗️ Architecture

- **`main.py`**: Orchestrator. Runs `listener` and `server` concurrently.
- **`listener.py`**: Telegram Client (Pyrogram). Handles message events, filters, and passes memory context.
- **`agent.py`**: Intelligence Engine. Calls Gemini API with memory-augmented prompts (`analyze_message`).
- **`server.py`**: FastAPI backend serving the Dashboard and API endpoints.
- **`task_manager.py`**: Handles storage, persistence (`tasks.json`), and retrieval logic.
- **`templates/dashboard.html`**: Premium Single-Page Application (HTML/JS/TailwindCSS).

## 🛡️ Security Note
This agent runs **locally**. Your credentials and session data are stored only on your machine (or in your `.env`). No data is sent to third-party servers other than Telegram (connection) and Google (content analysis).
