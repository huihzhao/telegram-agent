# Task: Phase 1 (Core Agent) - COMPLETE
- [x] Investigate `listener.py` logic
- [x] Fix filtering for DMs/Saved Messages
- [x] Setup Session String (Database Fix)
- [x] Enhanced Message Filters (Reply-to-Me, Keywords)
- [x] Implement Long-Term Memory (Context, Reputation, Rejection)
- [x] Implement Dashboard 2.0 (UI, Reopen, History)
- [x] Externalize System Prompt

# Task: Phase 2 (Future Enhancements)
- [x] **Proactive Notifications**: Daily Digest via Telegram DM
    - [x] Create `Scheduler` mechanism
    - [x] Implement `generate_digest()`
    - [x] Send digest to Saved Messages
- [x] **External Sync**: Notion Integration
    - [x] Install `notion-client`
    - [x] Create `notion_sync.py` module
    - [x] Integrate Sync Logic into `TaskManager`
    - [x] Fix `get_tasks` query bug (UUID format)
    - [x] Fix `create_task_page` bug (Prompt Syntax)
    - [x] Verify SSOT (No local tasks.json)
- [ ] **Multi-Modal Support**: Analyze Photos & Voice Notes
- [ ] **Two-Way Actions**: Auto-Replies & Command Execution
- [x] **Startup Catch-Up Mechanism**: Process missed messages on boot
    - [x] Refactor filter logic into reusable function
    - [x] Implement `run_catch_up()` (Scan DMs, Groups, Saved Messages)
    - [x] Integrate into startup sequence
