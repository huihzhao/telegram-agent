# Telegram Intelligence Agent 🧠

A local AI-powered agent that monitors your Telegram messages, learns your habits, and organizes actionable items into a premium local dashboard, synced directly to **Notion**.

## ✨ Features

### 🧠 Intelligent Analysis
- **Smart Monitoring**: Listens to "Saved Messages", DMs, **Mentions**, **Replies**, and **Keyword Triggers**.
- **Gemini 2.0 Powered**: Analyzes context, importance, and deadlines.
- **Context Aware**: Checks your Notion database to avoid duplicates.

### 📚 Notion Integration (SSOT)
- **Single Source of Truth**: All tasks are stored directly in a Notion Database.
- **Two-Way Sync**:
  - **Telegram -> Notion**: New tasks appear instantly.
  - **Dashboard -> Notion**: Updates (Done, Reject, Reopen) reflect instantly.
- **Robust API**: Uses efficient Search and UUID handling for reliability.

### 📊 Premium Dashboard 2.0
- **Modern UI**: Dark mode, glassmorphism, and smooth animations.
- **Real-Time**: Fetches live data from Notion.
- **Visual Cues**: Priority badges, deadlines, and sender info.
- **Daily Briefing**: Sends a summary of Top Tasks to your **Saved Messages** every morning.

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Telegram Account
- [Google AI Studio API Key](https://aistudio.google.com/)
- [Notion Integration Token](https://www.notion.so/my-integrations)

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
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
SESSION_STRING=  # Generated in Step 3
```
*See `notion_setup_guide.md` for detailed Notion configuration.*

### 3. Generate Session String (One-time)
```bash
python generate_session.py
```
Paste the output into `SESSION_STRING` in your `.env`.

## 🏃‍♂️ Usage

**Start the Agent:**
```bash
python main.py
```

**How to use:**
1. **Send a message** (e.g., "Buy coffee") to your Saved Messages.
2. **View the Dashboard**: Go to **http://localhost:8000**.
3. **Manage Tasks**: Click Done/Reject/Reopen. Updates sync to Notion instantly.

## 🏗️ Architecture

- **`main.py`**: Orchestrator running concurrent Listener and Server.
- **`listener.py`**: Telegram Client (Pyrogram). Handles messages and AI analysis.
- **`agent.py`**: Intelligence Engine. Uses `system_prompt.txt` (Jinja2) to prompt Gemini.
- **`notion_sync.py`**: Handling all Notion API interactions (Search, Create, Update).
- **`task_manager.py`**: Stateless proxy directing all calls to `NotionSync`.
- **`server.py`**: FastAPI backend for the Dashboard.

## 🛡️ Security Note
This agent runs **locally**. Your credentials stay on your machine. Data flows only between Telegram, Google (analysis), and Notion (storage).
