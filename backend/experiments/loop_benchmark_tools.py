"""§10.6 Tool Use 化の効果測定。

text-based vs tool-based を同じケースで比較。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "http://localhost:8000"
EXPERIMENT_DIR = Path(__file__).resolve().parent
SIMPLE_BLUEPRINT = EXPERIMENT_DIR / "simple_blueprint.png"
RING_BLUEPRINT = EXPERIMENT_DIR / "vlm_eval" / "cases_b" / "ring" / "drawing.png"

SIMPLE_FAILED = """\
import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(12)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").center(25, 0).hole(6)
    .edges("|Z").fillet(3)
)
"""

RING_FAILED = """\
import cadquery as cq
result = cq.Workplane("XY").circle(27).extrude(3)
cutter = cq.Workplane("XY").polarArray(radius=27, startAngle=45, angle=360, count=4).circle(6).extrude(3)
result = result.cut(cutter)
result = result.faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(20)
result = result.faces(">Z").workplane(centerOption="CenterOfBoundBox").center(0, 18).hole(3)
"""


def _post_multipart(url: str, file_path: Path, filename: str) -> dict:
    boundary = "----b2cbench"
    body = []
    body.append(f"--{boundary}\r\n".encode())
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.append(b"Content-Type: image/png\r\n\r\n")
    body.append(file_path.read_bytes())
    body.append(f"\r\n--{boundary}\r\n".encode())
    body.append(b'Content-Disposition: form-data; name="filename"\r\n\r\n')
    body.append(filename.encode())
    body.append(f"\r\n--{boundary}--\r\n".encode())
    data = b"".join(body)
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _post_query(url: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}", method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _post_json(url: str, body: dict, timeout: int = 900) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
        return json.loads(raw, strict=False)


def _run_one(blueprint_id: str, failed_script: str,
             use_tool: bool, max_iter: int,
             early_stop_k: int | None = None) -> dict:
    gen = _post_query(f"{API}/test/generate", {
        "blueprint_id": blueprint_id,
        "script_override": failed_script,
    })
    model_id = gen["model_id"]
    body = {
        "max_iterations": max_iter,
        "use_tool_based_correction": use_tool,
    }
    if early_stop_k is not None:
        body["early_stop_no_improve_k"] = early_stop_k
    started = time.time()
    result = _post_json(
        f"{API}/models/{model_id}/verify-and-correct",
        body,
        timeout=900,
    )
    elapsed = time.time() - started
    init_c = result["iterations"][0]["critical_count"] if result["iterations"] else None
    best_c = result["final"]["critical_count"]
    return {
        "use_tool": use_tool,
        "elapsed": round(elapsed, 1),
        "outcome": result["final_status"],
        "best_iter": result["best_iteration"],
        "init_critical": init_c,
        "best_critical": best_c,
        "reduction": (init_c - best_c) if init_c is not None else None,
        "progression": [it["critical_count"] for it in result["iterations"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["simple", "ring"], default="simple")
    parser.add_argument("-n", "--num-samples", type=int, default=2)
    parser.add_argument("--max-iter", type=int, default=5)
    parser.add_argument("--early-stop", type=int, default=None,
                        help="Early stop after K iterations without improvement")
    args = parser.parse_args()

    if args.case == "simple":
        blueprint_path = SIMPLE_BLUEPRINT
        failed = SIMPLE_FAILED
        case_label = "Simple (1 missing hole)"
    else:
        blueprint_path = RING_BLUEPRINT
        failed = RING_FAILED
        case_label = "RING"

    print(f"=== Tool Use vs Text-based: {case_label}, N={args.num_samples} per mode ===\n")
    bp = _post_multipart(f"{API}/blueprints/upload", blueprint_path, blueprint_path.name)
    bp_id = bp["blueprint_id"]
    print(f"blueprint_id = {bp_id}\n")

    samples_per_mode: dict[str, list[dict]] = {"text": [], "tool": []}
    for mode in ("text", "tool"):
        use_tool = (mode == "tool")
        print(f"--- Mode: {mode} ---")
        for i in range(1, args.num_samples + 1):
            try:
                s = _run_one(bp_id, failed, use_tool, args.max_iter, args.early_stop)
            except Exception as e:
                print(f"  sample {i}/{args.num_samples} FAIL: {e}")
                continue
            samples_per_mode[mode].append(s)
            prog = " → ".join(f"c={c}" for c in s["progression"])
            print(
                f"  sample {i}: {s['outcome']:<14} init={s['init_critical']} best={s['best_critical']} "
                f"({prog}) elapsed={s['elapsed']}s"
            )
        print()

    # 集計
    print("=" * 60)
    print(f"=== Summary: {case_label} ===")
    for mode in ("text", "tool"):
        ss = samples_per_mode[mode]
        if not ss:
            print(f"\n{mode}: no samples")
            continue
        reds = [s["reduction"] for s in ss if s["reduction"] is not None]
        bests = [s["best_critical"] for s in ss]
        elapsed = [s["elapsed"] for s in ss]
        outcomes: dict[str, int] = {}
        for s in ss:
            outcomes[s["outcome"]] = outcomes.get(s["outcome"], 0) + 1
        print(f"\nmode={mode} (N={len(ss)}):")
        print(f"  reduction:    mean={statistics.mean(reds):.2f}  range=[{min(reds)}, {max(reds)}]")
        print(f"  best critical: mean={statistics.mean(bests):.2f}")
        print(f"  elapsed:      mean={statistics.mean(elapsed):.0f}s")
        print(f"  outcomes:     {outcomes}")
        conv = sum(1 for s in ss if s["best_critical"] == 0) / len(ss) * 100
        print(f"  convergence:  {conv:.0f}%")

    out = EXPERIMENT_DIR / f"loop_benchmark_tools_{args.case}.json"
    out.write_text(json.dumps(samples_per_mode, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
