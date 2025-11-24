# ADR-007: Gradio for Web UI

**Status:** Accepted

---

## Context and Problem Statement

ragged v0.5.4 added a web UI for users who prefer graphical interfaces over CLI. The web framework choice affects development speed, feature richness, and maintainability.

## Decision Drivers

1. **Development Speed**: Rapid prototyping and iteration
2. **Python-Native**: Integrate with existing ragged codebase
3. **Built-in Components**: Chat interface, file upload, markdown rendering
4. **Deployment Simplicity**: Easy to containerise and serve
5. **Maintenance Burden**: Minimal frontend expertise required

## Considered Options

### Option 1: Gradio 6.0 (Chosen)

**Description**: Python web framework optimised for ML/AI applications with built-in chat UI.

**Pros**:
- Python-native (no JavaScript required)
- Built-in chat interface (`gr.Chatbot`)
- File upload widgets out-of-box
- Auto-generates API endpoints
- Fast iteration (change Python, reload browser)
- Good documentation, active community
- Docker-friendly

**Cons**:
- Less customisable than React
- Opinionated UI design
- Tied to Gradio's release cycle

### Option 2: Streamlit

**Description**: Python web framework for data apps.

**Pros**:
- Python-native
- Very simple for basic apps
- Large community

**Cons**:
- Reruns entire script on interaction (performance issues)
- No built-in chat UI (must build custom)
- Less suitable for conversational interfaces

### Option 3: FastAPI + React

**Description**: Full-stack approach with REST API (FastAPI) and React frontend.

**Pros**:
- Maximum customisation
- Modern web stack
- Separate frontend/backend

**Cons**:
- High development effort (2 codebases)
- Requires JavaScript/React expertise
- Slower iteration cycles
- Complex build pipeline

### Option 4: Flask + Jinja Templates

**Description**: Traditional server-rendered web app.

**Pros**:
- Simple, well-understood
- Python-only

**Cons**:
- No modern UI components
- Must build chat interface from scratch
- Less interactive than modern frameworks

## Decision Outcome

**Chosen Option**: "Gradio 6.0"

**Justification**:

Gradio optimised for exactly ragged's use case:

1. **Built-in Chat UI**: `gr.Chatbot` provides complete chat interface with message history, markdown rendering, file attachments. Building this in React would take weeks.

2. **Python-Native**: Entire UI in `src/web/gradio/ui.py`. No context switching between languages. Easy for Python developers to contribute.

3. **Rapid Development**: v0.5.4 web UI built in <1 day. Gradio's declarative API enables fast iteration.

4. **Docker-Friendly**: Simple `docker compose up ragged-ui` - no build steps, webpack configs, or npm complexity.

5. **Auto-Generated API**: Gradio creates REST API automatically. Can use UI or programmatic access interchangeably.

**Trade-Off Accepted**: Less UI customisation than React. ragged prioritises functionality and development speed over pixel-perfect design.

**Consequences**:
- **Positive**:
  - Fast development and iteration
  - Python-only codebase (no JavaScript)
  - Built-in chat components
  - Simple deployment
  - Easy contributor onboarding
  - Auto-generated API endpoints

- **Negative**:
  - Limited UI customisation
  - Tied to Gradio's design system
  - Breaking changes in Gradio updates (6.0 was breaking change from 4.x)

## Implementation Notes

**When**: Implemented in v0.5.4

**File Structure**:
```
src/web/gradio/
  ├── ui.py          # Main Gradio interface
  ├── __init__.py
  └── components/    # Custom components if needed
```

**Docker Deployment**:
```yaml
ragged-ui:
  build: .
  command: python -m src.web.gradio.ui
  ports:
    - "7860:7860"
```

## References

- [Gradio Documentation](https://www.gradio.app/docs)
- [Gradio 6.0 Release Notes](https://github.com/gradio-app/gradio/releases/tag/v6.0.0)
- Web UI Implementation

---

**Supersedes**: N/A

**Superseded By**: N/A
