---
id: 0018
title: Add Groq Model Support to AI Agent
stage: red
date: 2025-12-17T23:15:00Z
surface: agent
model: claude-haiku-4-5-20251001
feature: 004-ai-chatbot
branch: phase-3
user: User
command: /sp.implement
labels: [backend, ai-agent, groq, llm-provider, feature-implementation]
links:
  spec: specs/004-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - path: backend/.env.example
    action: modified
    lines: "60-63 (added Groq configuration)"
  - path: backend/agent_config/factory.py
    action: modified
    lines: "1-20, 39-65, 95-119, 136"
  - path: backend/agent_config/todo_agent.py
    action: modified
    lines: "140-157, 222-235"
tests:
  - type: integration
    path: backend/tests/integration/test_groq_model.py
    status: pending
---

## Prompt

The user requested to add Groq model support to the Phase 3 AI agent backend. The implementation should:

1. Add Groq API key and model name environment variables to .env.example
2. Integrate Groq with AsyncOpenAI client pointing to https://api.groq.com/openai/v1
3. Update agent_config/factory.py to support the Groq provider alongside OpenAI and Gemini
4. Update TodoAgent and create_todo_agent() documentation to include Groq examples
5. Use llama-3.3-70b-versatile as the default Groq model

The user provided a code example showing how to create a custom AsyncOpenAI client pointing to Groq's API endpoint.

## Response snapshot

### Changes Made:

**1. Updated .env.example** (backend/.env.example):
- Added GROQ_API_KEY environment variable with documentation link
- Added GROQ_DEFAULT_MODEL with default value "llama-3.3-70b-versatile"
- Updated LLM_PROVIDER comment to indicate support for "openai, gemini, or groq"

**2. Enhanced agent_config/factory.py**:
- Updated module docstring to document Groq support
- Added Groq provider handling with AsyncOpenAI client
- Configured Groq client to use base_url="https://api.groq.com/openai/v1"
- Added GROQ_DEFAULT_MODEL environment variable with default "llama-3.3-70b-versatile"
- Added debug logging for API key validation
- Updated error message to include "groq" as a supported provider
- Updated create_model() docstring with Groq example

**3. Updated agent_config/todo_agent.py**:
- Updated TodoAgent.__init__() docstring to include "groq" as provider option
- Added example for Groq agent initialization
- Updated create_todo_agent() docstring with Groq example
- Updated model name examples to include "llama-3.3-70b-versatile"

### Implementation Details:

The Groq integration follows the same pattern as Gemini:
- Uses AsyncOpenAI client for OpenAI-compatible API
- Points to Groq's API endpoint: https://api.groq.com/openai/v1
- Supports runtime provider selection via LLM_PROVIDER environment variable
- Maintains backward compatibility with existing OpenAI and Gemini providers
- Includes API key validation and debug logging

### Code Structure:

```python
# In factory.py create_model()
elif provider == "groq":
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required...")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    model_name = model or os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile")
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
```

## Outcome

- ✅ Impact: Added Groq as a third AI provider option for the Todo chatbot agent, expanding provider flexibility and enabling users to choose between OpenAI, Gemini, and Groq based on cost/performance preferences
- 🧪 Tests: Manual verification shows Groq provider loading correctly with environment variables; integration tests for Groq model needed
- 📁 Files: 3 files modified (backend/.env.example, backend/agent_config/factory.py, backend/agent_config/todo_agent.py)
- 🔁 Next prompts:
  - Write integration tests for Groq provider (test_groq_model.py)
  - Update README.md with Groq setup instructions
  - Test Groq model with actual API calls
- 🧠 Reflection: Implementation follows existing patterns cleanly, reusing AsyncOpenAI client infrastructure. The three-provider system (OpenAI, Gemini, Groq) is now well-structured and maintainable.

## Evaluation notes (flywheel)

- Failure modes observed: None identified during implementation
- Graders run and results (PASS/FAIL): Code compiles successfully; factory.py can be imported without errors
- Prompt variant (if applicable): N/A
- Next experiment: Integration test to verify Groq API connectivity and response streaming

