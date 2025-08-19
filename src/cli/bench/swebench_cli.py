import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: list[str]) -> int:
    print("➤", " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def sanity(args):
    """Run the official gold patch on a single instance."""
    cmd = [
        sys.executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        args.dataset,
        "--predictions_path",
        "gold",
        "--max_workers",
        "1",
        "--instance_ids",
        args.instance_id,
        "--run_id",
        f"validate-gold-{args.instance_id}",
    ]
    if args.namespace is not None:
        cmd += ["--namespace", args.namespace]
    sys.exit(_run(cmd))


def agent(args):
    """
    Minimal adapter:
    - (A) obtain a unified diff for the instance (either from your agent
          or via SWE-agent CLI)
    - (B) write predictions.jsonl
    - (C) call the official harness to score it
    """
    work = Path(tempfile.mkdtemp(prefix="swebench_"))
    preds = work / "predictions.jsonl"

    if args.patch_file:
        diff_text = Path(args.patch_file).read_text()
    elif args.use_swe_agent:
        out_dir = work / "traj"
        out_dir.mkdir(parents=True, exist_ok=True)
        swe_cmd = [
            "sweagent",
            "run",
            "--benchmark.dataset_name",
            args.dataset,
            "--benchmark.instance_filter",
            args.instance_id,
            "--agent.model.name",
            args.model_name,
            "--output.dir",
            str(out_dir),
        ]
        rc = _run(swe_cmd)
        if rc != 0:
            sys.exit(rc)
        all_preds = next(out_dir.rglob("all_preds.jsonl"))
        preds.write_text(all_preds.read_text())
    else:
        print(
            "No --patch_file provided and --use_swe_agent not set. "
            "Either pass a diff via --patch_file or implement your agent call.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not preds.exists():
        if args.patch_file:
            line = {
                "instance_id": args.instance_id,
                "model": args.model_name or "TreeAgent",
                "prediction": diff_text,
            }
            preds.write_text(json.dumps(line) + "\n")

    eval_cmd = [
        sys.executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        args.dataset,
        "--predictions_path",
        str(preds),
        "--max_workers",
        "1",
        "--instance_ids",
        args.instance_id,
        "--run_id",
        f"treeagent-{args.instance_id}",
        "--cache_level",
        "env",
        "--clean",
        "True",
    ]
    if args.namespace is not None:
        eval_cmd += ["--namespace", args.namespace]
    sys.exit(_run(eval_cmd))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a single SWE-bench instance from TreeAgent",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dataset", default="princeton-nlp/SWE-bench_Lite"
    )
    common.add_argument(
        "--instance-id",
        required=True,
        help="e.g., sympy__sympy-20590",
    )
    common.add_argument(
        "--namespace",
        default=None,
        help="Set to '' on Apple Silicon/ARM to build images locally",
    )

    ps = sub.add_parser(
        "sanity",
        parents=[common],
        help="Validate Docker & harness using gold patch",
    )
    ps.set_defaults(func=sanity)

    pa = sub.add_parser(
        "agent",
        parents=[common],
        help="Run your agent (or SWE-agent) and evaluate",
    )
    pa.add_argument(
        "--patch-file", help="Path to a unified diff if you already have one"
    )
    pa.add_argument(
        "--use-swe-agent",
        action="store_true",
        help="Use SWE-agent CLI to generate the patch",
    )
    pa.add_argument(
        "--model-name",
        default="gpt-4o",
        help="Only used if --use-swe-agent",
    )
    pa.set_defaults(func=agent)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
