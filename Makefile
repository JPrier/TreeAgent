.PHONY: swe-sanity swe-one
INSTANCE ?= sympy__sympy-20590
DATASET ?= princeton-nlp/SWE-bench_Lite

swe-sanity:
	python -m pip install -q swebench
	treeagent-swebench sanity --dataset $(DATASET) --instance-id $(INSTANCE) --namespace ''

# Run via SWE-agent (optional)
swe-one:
	python -m pip install -q swebench sweagent
	treeagent-swebench agent --dataset $(DATASET) --instance-id $(INSTANCE) --use-swe-agent --model-name gpt-4o --namespace ''
