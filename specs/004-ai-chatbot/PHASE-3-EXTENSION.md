# Phase 3 Extension: Priority Support & Chat History

**Status**: 🚀 **PLANNING**
**Date**: 2025-12-18
**Feature**: ai-chatbot
**Branch**: phase-3-extension

## Overview

Extension to Phase 3 AI-powered Todo chatbot adding three major features:

1. **Priority Field Support** - Tasks with priority levels (low/medium/high) with NLP detection
2. **Chat History Persistence** - Conversations stored in database with 2-day retention
3. **Improved Chat UI** - Better message formatting with clear sender/receiver distinction

---

## Feature 1: Priority Support

### Current State
- ✅ Task model already has `priority: str` field (default: "medium")
- ✅ add_task MCP tool accepts priority (currently hardcoded to "medium")
- ❌ NLP detection of priority from user input not implemented
- ❌ No dedicated priority MCP tools
- ❌ Agent instructions don't handle priority extraction

### Requirements

**R1.1 - Priority Levels**
- Values: "low", "medium", "high"
- Stored as lowercase string in database
- Default: "medium"

**R1.2 - Natural Language Detection**
- Detect priority keywords: "high", "urgent", "low", "minor", "medium", "normal"
- Support phrases: "make it high priority", "this is urgent", "low priority task"
- Apply detected priority when creating/updating tasks

**R1.3 - Priority MCP Tools**

Tool 1: `set_priority(user_id, task_id, priority)`
- Set task priority to low/medium/high
- Returns: `{"task_id": int, "status": "updated", "priority": str}`
- User isolation: Only user's own tasks

Tool 2: `list_tasks_by_priority(user_id, priority, status="all")`
- Filter tasks by priority level
- Optional: Filter by completion status
- Returns: `{"count": int, "priority": str, "tasks": [...]}`

**R1.4 - Agent Instructions Enhancement**
- Update AGENT_INSTRUCTIONS in todo_agent.py
- Document priority extraction patterns
- Add examples: "Create high priority task", "Make task 5 urgent"
- Update bulk_update_tasks agent instruction to preserve priority

**R1.5 - Update Task MCP Tool**
- Enhance update_task to support priority updates
- Current signature: `update_task(user_id, task_id, title, description)`
- New signature: `update_task(user_id, task_id, title, description, priority=None)`

### Implementation Files

**Models** (already implemented):
- `backend/models.py`: Task.priority field ✅

**MCP Tools** (new):
- `backend/mcp_server/tools.py`: Add set_priority, list_tasks_by_priority
- `backend/mcp_server/tools.py`: Enhance update_task with priority support

**Agent** (modifications):
- `backend/agent_config/todo_agent.py`: AGENT_INSTRUCTIONS
  - Add priority detection patterns
  - Document priority MCP tools

**Tests** (new):
- `backend/tests/test_priority_tools.py`: Unit tests for priority operations

---

## Feature 2: Chat History Persistence

### Current State
- ❌ No chat history database models
- ❌ Chat endpoint doesn't persist conversations
- ❌ Frontend loads chat history from ChatKit session, not database
- ❌ No message retention policy

### Requirements

**R2.1 - Database Models**

Model 1: `Conversation`
```
- id: str (UUID primary key)
- user_id: str (foreign key via index, from Better Auth)
- title: str (conversation title - auto-generated or user-set)
- created_at: datetime
- updated_at: datetime (auto-update on new message)
- is_active: bool (default: true)
```

Model 2: `ChatMessage`
```
- id: str (UUID primary key)
- conversation_id: str (foreign key via index)
- user_id: str (for isolation verification, indexed)
- sender: str (enum: "user" or "assistant")
- content: str (message text, max 5000 chars)
- created_at: datetime
- expires_at: datetime (now + 2 days, used for cleanup)
- metadata: dict (JSON - optional: token_count, model, etc.)
```

**R2.2 - API Changes**

Endpoint: `POST /api/chat` (existing)
- Modifications:
  - Accept optional `conversation_id` parameter
  - Create new Conversation if not provided
  - Save all messages to ChatMessage table
  - Return messages with conversation_id

New Endpoint: `GET /api/conversations`
- List user's conversations (sorted by updated_at DESC)
- Pagination support (default: 10 per page)
- Response: `{"conversations": [...], "total": int, "page": int}`

New Endpoint: `GET /api/conversations/{conversation_id}/messages`
- Retrieve messages from conversation
- Only return messages created in last 2 days
- Pagination support
- User isolation via conversation_id + user_id verification

New Endpoint: `DELETE /api/conversations/{conversation_id}`
- Delete conversation and all messages
- User isolation verification

**R2.3 - Message Retention Policy**

- Store all messages (no hard delete on creation)
- Display only messages from last 2 days in UI
- Background job: Delete messages older than 2 days
  - Run daily (via APScheduler or background task)
  - Query: `ChatMessage.expires_at < now()`
  - Delete matching records

**R2.4 - Frontend Integration**

Changes to ChatKit UI:
- Load initial messages from GET /api/conversations/{id}/messages
- On new message, POST to /api/chat with conversation_id
- Display messages with sender label (You / Assistant)
- Show conversation history list

### Implementation Files

**Models** (new):
- `backend/models.py`: Add Conversation, ChatMessage classes

**Database** (migration):
- `backend/alembic/versions/`: Create migration for new tables

**API Endpoints** (new/modified):
- `backend/routes/chat.py`: Modify POST /api/chat, add GET endpoints
- `backend/routes/conversations.py`: New file for conversation management

**Services** (new):
- `backend/services/conversation_service.py`: Conversation CRUD
- `backend/services/message_service.py`: Message persistence

**Background Jobs** (new):
- `backend/tasks/message_cleanup.py`: 2-day retention policy

**Tests** (new):
- `backend/tests/test_conversation_api.py`: API endpoint tests
- `backend/tests/test_message_retention.py`: Retention policy tests

---

## Feature 3: Chat UI Improvements

### Current State
- ChatKit frontend displays messages
- Messages from user and assistant appear in same format
- No clear visual distinction between sender/receiver
- Limited metadata display

### Requirements

**R3.1 - Message Formatting**
- User messages: Right-aligned, blue background
- Assistant messages: Left-aligned, gray background
- Clear labels: "You said:", "Assistant said:"
- Timestamp for each message

**R3.2 - Conversation Container**
- Clear message grouping
- Smooth scrolling to newest message
- Visual separator between messages

**R3.3 - Input Area Improvements**
- Clear send button
- Enter to send (Shift+Enter for newline)
- Show loading state while message is being sent
- Disable send while awaiting response

### Implementation Files

**Frontend Components** (modifications):
- `frontend/components/ChatBox.tsx`: Message display component
- `frontend/components/ChatMessage.tsx`: Individual message styling
- `frontend/components/ChatInput.tsx`: Input field improvements
- `frontend/styles/chat.css`: Styling for message bubbles

---

## User Stories

### US1: Create Task with Priority
```
As a user,
I want to create a task with a priority level,
So that I can organize tasks by importance.

Acceptance:
- "Create a high priority task to buy milk" → Task created with high priority
- "Add medium priority task: call dentist" → Task created with medium priority
- "Add a task without priority" → Default medium priority assigned
- "Make task 5 urgent" → Task 5 priority updated to high
```

### US2: View Tasks by Priority
```
As a user,
I want to see tasks filtered by priority,
So that I can focus on important work first.

Acceptance:
- "Show me high priority tasks" → List only high priority tasks
- "What low priority items do I have?" → List low priority tasks
- "Show all pending high priority tasks" → Filter by priority + status
```

### US3: Persist Chat History
```
As a user,
I want my conversation history saved,
So that I can resume conversations after page refresh.

Acceptance:
- Create task → Refresh page → Message history still visible
- Conversation history loads within 1 second
- Messages older than 2 days automatically removed
```

### US4: Clear Message Formatting
```
As a user,
I want clear distinction between my messages and assistant's,
So that I can easily follow the conversation.

Acceptance:
- My messages appear on right with blue background
- Assistant messages appear on left with gray background
- Labels show "You said:" and "Assistant said:"
- Each message shows timestamp
```

---

## Technical Stack

**Backend**:
- FastAPI (existing)
- SQLModel (existing)
- Alembic (existing)
- APScheduler (new - for background cleanup jobs)

**Frontend**:
- Next.js 16 (existing)
- ChatKit (existing)
- Tailwind CSS (existing)

**Database**:
- Neon PostgreSQL (existing)

---

## Implementation Phases

### Phase A: Priority Support (3-4 hours)
1. Add priority MCP tools (set_priority, list_tasks_by_priority)
2. Enhance add_task to detect priority from NLP
3. Update agent instructions
4. Write and pass tests

### Phase B: Chat Models (2-3 hours)
1. Create Conversation and ChatMessage SQLModel classes
2. Create Alembic migration
3. Run migration
4. Verify tables created

### Phase C: Chat Persistence API (3-4 hours)
1. Create conversation_service.py
2. Modify POST /api/chat to save messages
3. Add GET /api/conversations endpoint
4. Add GET /api/conversations/{id}/messages endpoint
5. Add DELETE /api/conversations/{id} endpoint
6. Write and pass tests

### Phase D: Message Cleanup (1-2 hours)
1. Create background job for 2-day retention
2. Configure APScheduler
3. Write and pass tests

### Phase E: Frontend UI (2-3 hours)
1. Update ChatMessage component for better formatting
2. Improve chat input styling
3. Load initial messages from API
4. Add conversation history sidebar
5. Test UI improvements

### Phase F: Documentation (1 hour)
1. Update CLAUDE.md
2. Create PHR
3. Update tasks.md with new tasks

---

## Success Criteria

**Priority Support**:
- ✅ User can create task with priority via natural language
- ✅ Agent correctly extracts priority from user input
- ✅ set_priority MCP tool works correctly
- ✅ list_tasks_by_priority filters accurately
- ✅ All 8 priority tests pass

**Chat History**:
- ✅ Chat messages persist in database
- ✅ Conversation history loads on page refresh
- ✅ 2-day retention policy works
- ✅ Messages older than 2 days automatically deleted
- ✅ All 10 chat history tests pass

**Chat UI**:
- ✅ User/assistant messages clearly distinguished
- ✅ Messages properly formatted with sender labels
- ✅ Timestamps displayed
- ✅ UI loads quickly
- ✅ Manual acceptance testing passes

---

## Dependencies & Constraints

**Dependencies**:
- Existing Task model ✅
- Existing task MCP tools ✅
- Better Auth for user isolation ✅
- Neon PostgreSQL ✅

**Constraints**:
- Must maintain user isolation
- Must not break existing task operations
- Message cleanup must not impact active conversations
- Chat history must load in <1 second

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Alembic migration fails | Database schema corrupted | Test migration on dev first, have rollback ready |
| Background cleanup deletes active messages | Users lose recent chat | Add 2-day buffer, not 2-day exact |
| Priority detection breaks agent | Agent can't create tasks | Fallback to default "medium" priority |
| Chat history slow | Poor UX | Index conversation_id, paginate messages |

---

## Estimated Timeline

**Total**: 12-17 hours

| Phase | Hours | Status |
|-------|-------|--------|
| A - Priority Support | 3-4 | Planning |
| B - Chat Models | 2-3 | Planning |
| C - Chat Persistence API | 3-4 | Planning |
| D - Message Cleanup | 1-2 | Planning |
| E - Frontend UI | 2-3 | Planning |
| F - Documentation | 1 | Planning |

---

## Next Steps

1. ✅ User approval of requirements (DONE)
2. ⏳ Create detailed tasks.md for extension
3. ⏳ Begin Phase A implementation (Priority Support)
4. ⏳ Test and verify each phase
5. ⏳ Create PHR upon completion
