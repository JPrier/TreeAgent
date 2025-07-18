# TreeAgent 🌳🤖 (MVP)

TreeAgent is a tiny, work-in-progress experiment in **hierarchical, multi-agent orchestration** for code-generation tasks.  
It is maintained by a single developer and **has not been run, profiled, or tested end-to-end yet**. Expect breaking changes and dragons. 🐉

---

## ✨ Project Goal

*Create an “AI engineering tree” where a **root agent** (the “Principal Engineer”) decomposes a user request into subtasks,  
hands them to **planner** and **executor** child agents, and bubbles results back up—all on consumer hardware, entirely offline if desired.*

Why bother?

1. **Deliberate planning.** Test-time tree structures let small models explore alternative plans instead of committing to the first idea.  
2. **Isolation & safety.** Each node operates with a minimal toolset and context window, keeping accidental prompt leaks and runaway costs in check.  
3. **Modularity.** Nodes live in their own Python packages so they can be swapped, parallelised, or rate-limited independently.

---

## 🗺️ Current Status (Pre-Alpha)

| Area            | State | Notes |
|-----------------|-------|-------|
| Core data models (`Task`, `ModelResponse`) | ✅ Drafted | Pydantic schemas in `src/dataModel/` |
| Recursive orchestration (`AgentOrchestrator`)           | ✅ First pass | Needs error handling & logging |
| Parallel execution logic                                | 🟡 Prototype | Sibling-task **non-concurrency** still WIP |
| CLI / entry-point                                      | 🟥 Todo | Basic `python -m treeagent …` runner planned |
| Tests & CI                                             | 🟥 Todo | No unit tests yet |
| Docs / examples                                        | 🟥 Todo | This README is step 1 |

---

## 🚀 Quick Start

```bash
git clone https://github.com/JPrier/TreeAgent.git
cd TreeAgent
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # very small for now
python -m treeagent.demo          # stub script prints skeleton task tree
```

> Heads-up: you’ll need an OpenAI (or other) API key in your shell once the first agent stubs call an LLM.


## 🧮 Repository Structure
```bash
TreeAgent/
├── src/
│   ├── orchestrator/
│   ├── dataModel/          # pydantic task / response schemas
│   └── ...
├── examples/               # minimal end-to-end scenarios (coming soon)
├── tests/                  # pytest suite
├── requirements.txt
└── README.md
```

### Spawn Rules Configuration

Agent spawning behaviour is controlled by a JSON file named
`spawn_rules.json`. The orchestrator looks for this file in `config/` or the
current working directory. Each task type lists which child types it may
create and the maximum number allowed:

```json
{
  "HLD": { "can_spawn": { "LLD": 5, "RESEARCH": 5, "TEST": 1 }, "self_spawn": false },
  "LLD": { "can_spawn": { "IMPLEMENT": 5, "RESEARCH": 3, "TEST": 1 }, "self_spawn": false }
}
```

Adjust these numbers to experiment with deeper or shallower trees.

## 🧪 Running Tests

Install the optional dev dependencies to enable coverage reporting:

```bash
pip install -e .[dev] pytest
```

Execute the suite with coverage enabled:

```bash
pytest --cov=src
```

### Resuming From Checkpoints

Each project run writes snapshots to the directory specified by
`--checkpoint-dir` (defaults to `checkpoints`). If the process stops you can
continue where it left off:

```bash
python -m treeagent.cli --resume checkpoints/20240101010101
```

The orchestrator will load the latest snapshot in that directory and resume
processing the remaining tasks.

## 🛣️ Roadmap
1. Minimal runnable demo – wire up a root → planner → executor flow that prints a toy result.

2. Deterministic retries – enforce schema-valid responses via structured-output loops.

3. Sandboxed execution – run generated code in a subprocess with time & memory limits.

4. CLI + config files – YAML or TOML to pick local vs. cloud models and set parallelism hints.

5. Metrics & logging – capture token counts, wall-clock time, and per-node error traces.

6. Extensible UI – optional graph-viz or web dashboard to visualise task trees.
