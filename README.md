# TreeAgent (MVP)

TreeAgent is a work-in-progress experiment in hierarchical, deterministic multi-agent orchestration for software engineering tasks.

It is designed, built, and maintained by a single developer. Expect rapid iteration, sharp edges, and opinionated design.

---

## Project Goal

Modern AI coding agents often produce code that is inconsistent, insecure, duplicative, or strangely structured. These problems stem largely from the design assumption that a single LLM with a large context window should manage everything—retain full knowledge, select from many tools, and make countless tiny decisions.

But this isn't how human engineers work.

Human engineers solve complex problems by structuring them. They begin with a High-Level Design (HLD) to outline the approach, then break it down into Low-Level Designs (LLDs) and discrete units of work. These are passed to others who may not have the original context—but can contribute reliably because each task is scoped, reviewed, and clearly defined.

TreeAgent applies this principle to autonomous agents. It transforms vague requests into structured workflows, using layered agents with strict roles and limited context. Each LLM interaction is minimized, targeted, and constrained to ensure correctness and reproducibility—not speculation.

> Build an “AI engineering tree” where a root agent (like a Principal Engineer) decomposes a request and delegates to a hierarchy of sub-agents—planners, designers, implementers, reviewers, and more— to solve the problem accurately, deterministically, and autonomously, using consumer-grade hardware, with no cloud APIs and no human intervention unless truly necessary.

## Why This Exists

TreeAgent is built around a few non-negotiable beliefs:

✅ Correctness is king. Accuracy and logical consistency come before speed or style.

✅ Determinism is essential. The same input should always yield the same result.

✅ Autonomy is the goal. Agents must operate independently, escalate only when stuck, and self-verify results.

✅ Latency is irrelevant. We prefer a slow, correct agent over a fast, wrong one.

✅ LLMs are tools, not magic. All actions must be grounded in real inputs and audited outputs.

✅ Local-first. Everything should work offline, without vendor lock-in or hosted dependencies.

TreeAgent is not a chatbot. It is not a copilot. It is a workflow engine—and it plays by strict rules to get reliable results from unreliable components.

## 🔥 TreeAgent Tenets

Latency is not a priority. Every decision, interaction, and tool should serve correctness and reliability over speed.

### 🧠 Core Objective: Accurate & Reliable Results
- **Maximize Accuracy of Results** – every agent decision should be correct, relevant, and grounded. Prompts, tools, and workflows must work together to reduce hallucination, ensure logical soundness, and complete tasks exactly as intended.
- **Maximize Determinism** – given the same input and tool access, the same result should be produced. Agent behavior is controlled via fixed prompt templates, stateless tool usage, temperature=0, and reproducible workflows.
- **Minimize Human Interaction** – the agent should operate independently unless it explicitly detects uncertainty or conflict. When it needs help it must generate a clear, minimal escalation query with all needed context so the issue can be resolved once and work can resume.

### ⚙️ Execution Optimization: Resource Efficiency
- **Minimize Number of LLM Requests** – avoid unnecessary decompositions, reuse validated outputs, and skip trivial steps whenever possible, but never at the cost of accuracy or completeness.
- **Minimize External Dependencies** – prefer local, auditable tooling and offline workflows. Cloud APIs are optional, not required.
- **Minimize Prompt Context Size** – keep context tightly scoped to what's essential to reduce token usage, improve focus, and enforce a single source of truth. Brevity must never undermine correctness.

### 🧭 Tradeoff Philosophy
If a tradeoff must be made between speed and correctness:

✅ Always choose correctness.
✅ Always choose determinism.
✅ Always choose self-sufficiency.
❌ Never choose speed at the cost of reliability.
❌ Never trust model inference without verification.

---

## 🗺️ Current Status (Pre-Alpha)

| Area            | State | Notes |
|-----------------|-------|-------|
| Core data models (`Task`, `ModelResponse`) | ✅ Drafted | Pydantic schemas in `src/dataModel/` |
| Recursive orchestration (`AgentOrchestrator`)           | ✅ First pass | Needs error handling & logging |
| Parallel execution logic                                | 🟡 Prototype | Sibling-task **non-concurrency** still WIP |
| CLI / entry-point                                      | ✅ Basic CLI | `treeagent` command available |
| Tests & CI                                             | ✅ Passing | pytest & ruff via GitHub Actions |
| Docs / examples                                        | 🟥 Todo | This README is step 1 |

---

## 🚀 Quick Start

```bash
git clone https://github.com/JPrier/TreeAgent.git
cd TreeAgent
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .                  # install package and CLI
treeagent "hello world"           # prints skeleton task tree
```

> Heads-up: you’ll need an OpenAI (or other) API key in your shell once the first agent stubs call an LLM.


## 🧮 Repository Structure
```bash
TreeAgent/
├── src/
│   ├── orchestrator/
│   ├── dataModel/          # pydantic task / response schemas
│   └── ...
├── config/                 # spawn rules
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
