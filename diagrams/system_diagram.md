# PawPal+ System Diagram

PawPal+ has two paths through the same app: a **scheduling path** (tasks, sorting, recurrence, conflicts) that is plain deterministic Python, and an **Ask PawPal path** that uses retrieval-augmented generation (RAG). Both are checked by tests, by guardrails and by the owner.

```mermaid
flowchart LR
    owner(["👤 Pet owner"])
    ui["Streamlit UI<br/>app.py"]
    owner -->|"pets, tasks, questions"| ui

    subgraph SCHED ["Scheduling path (no AI)"]
        sch["Scheduler + data model<br/>validate, sort, filter,<br/>recurrence, conflicts"]
    end
    ui -->|"form values"| sch
    sch -->|"sorted table,<br/>conflict warnings"| ui

    subgraph RAG ["Ask PawPal path (RAG)"]
        direction LR
        g1{"Input guardrails"}
        retr["Retriever<br/>TF-IDF, filtered<br/>by pet species"]
        prompt["Prompt builder"]
        llm["LLM<br/>Gemini or Claude"]
        g2{"Output guardrails"}
        fb["Fallback:<br/>retrieved passages only"]
        g1 -->|"safe"| retr --> prompt --> llm --> g2
        g2 -->|"failed"| fb
    end
    kb[("Knowledge base<br/>knowledge/*.md")] --> retr
    ui -->|"question + pet"| g1
    g1 -->|"blocked: refusal"| ui
    sch -.->|"schedule context"| prompt
    g2 -->|"answer + sources"| ui
    fb -->|"passages + sources"| ui

    h1["👁 Human: owner reads the answer<br/>and its sources"]
    h2["👁 Human: owner resolves conflicts<br/>(app warns, never auto-moves)"]
    h3["👁 Human: developer reviews<br/>the guides and the log"]
    ui --> h1
    ui --> h2
    kb -.-> h3

    log[("pawpal.log<br/>keys redacted")]
    SCHED -.-> log
    RAG -.-> log
    log -.-> h3

    tests{{"✅ pytest, 54 tests"}}
    tests -.->|"checks"| SCHED
    tests -.->|"checks"| RAG
```

## How data flows

| Step | Input | Process | Output |
|------|-------|---------|--------|
| 1. Manage pets and tasks | Form values from the owner | Validate, store in `Owner` / `Pet` / `Task`, then `Scheduler` sorts, filters, creates recurring copies and finds overlaps | Sorted schedule table and conflict warnings |
| 2. Ask a question | Question text and the selected pet | Clean the text, block suspicious questions, retrieve the best guide sections for that species, add the pet's schedule, ask the LLM | Written answer with sources |
| 3. When the AI is unavailable | Same question | The retrieved passages are shown directly | Answer made only of guide text, with a note |

## Where humans and tests check the AI

- **Retrieval quality:** tests assert that each species' questions find the right guide section and that a rabbit never receives dog or cat advice.
- **Guardrails:** tests cover blocked injection attempts, empty or oversized model replies, model failures falling back safely, and API keys being redacted from logs.
- **Grounding:** the prompt tells the model to use only the retrieved passages and the schedule, and every answer shows its sources, so the owner can verify it.
- **Owner:** reads the answer and sources, and resolves schedule conflicts. The app only warns.
- **Developer:** reviews the guides in `knowledge/` and `pawpal.log` for blocked or failed questions. There is no automated scoring of answer quality, so a person has to judge whether answers are good.
- **Safety net:** the general guide tells owners to call a vet in emergencies, and the model is told to suggest a vet when the guide does not cover a question.
