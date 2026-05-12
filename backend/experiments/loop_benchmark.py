"""§10 Corrector 改善効果の統計的評価。

RING の失敗候補に対して /verify-and-correct を N 回走らせ、
critical 削減数 / 反復数 / final_status の分布を測る。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import urllib.parse
import urllib.request

API = "http://localhost:8000"
BLUEPRINT_PATH = (
    Path(__file__).resolve().parent / "vlm_eval" / "cases_b" / "ring" / "drawing.png"
)
RING_FAILED = """\
import cadquery as cq
result = cq.Workplane("XY").circle(27).extrude(3)
cutter = cq.Workplane("XY").polarArray(radius=27, startAngle=45, angle=360, count=4).circle(6).extrude(3)
result = result.cut(cutter)
result = result.faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(20)
result = result.faces(">Z").workplane(centerOption="CenterOfBoundBox").center(0, 18).hole(3)
"""


def _post_multipart(url: str, file_path: Path, filename: str) -> dict:
    """超軽量 multipart upload"""
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
        url,
        data=data,
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


def _post_json(url: str, body: dict, timeout: int = 600) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
        return json.loads(raw, strict=False)


def _run_one(blueprint_id: str, max_iterations: int = 5) -> dict:
    """1 サンプル: 失敗 RING を生成 → verify-and-correct → 結果を返す"""
    gen = _post_query(f"{API}/test/generate", {
        "blueprint_id": blueprint_id,
        "script_override": RING_FAILED,
    })
    model_id = gen["model_id"]

    started = time.time()
    result = _post_json(
        f"{API}/models/{model_id}/verify-and-correct",
        {"max_iterations": max_iterations},
        timeout=900,
    )
    elapsed = time.time() - started

    initial_critical = result["iterations"][0]["critical_count"] if result["iterations"] else None
    best_critical = result["final"]["critical_count"]
    return {
        "model_id": model_id,
        "elapsed_sec": round(elapsed, 1),
        "final_status": result["final_status"],
        "best_iteration": result["best_iteration"],
        "iter_count": len(result["iterations"]),
        "initial_critical": initial_critical,
        "best_critical": best_critical,
        "critical_reduction": (
            initial_critical - best_critical if initial_critical is not None else None
        ),
        "iterations": [
            {
                "iter": it["iteration"],
                "c": it["critical_count"],
                "M": it["major_count"],
                "m": it["minor_count"],
                "outcome": it["outcome"],
            }
            for it in result["iterations"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-samples", type=int, default=5)
    parser.add_argument("--max-iter", type=int, default=5)
    args = parser.parse_args()

    print(f"=== Loop benchmark: N={args.num_samples}, max_iter={args.max_iter} ===\n")

    print("[*] uploading RING blueprint...")
    bp = _post_multipart(f"{API}/blueprints/upload", BLUEPRINT_PATH, "ring.png")
    bp_id = bp["blueprint_id"]
    print(f"    blueprint_id = {bp_id}\n")

    samples: list[dict] = []
    for i in range(1, args.num_samples + 1):
        print(f"[*] sample {i}/{args.num_samples} ...")
        try:
            s = _run_one(bp_id, args.max_iter)
        except Exception as e:
            print(f"    FAIL: {e}")
            continue
        samples.append(s)
        prog = " → ".join(f"c={it['c']}" for it in s["iterations"])
        print(
            f"    elapsed={s['elapsed_sec']}s outcome={s['final_status']} "
            f"best=iter{s['best_iteration']} c={s['best_critical']} "
            f"(reduction {s['initial_critical']}→{s['best_critical']})"
        )
        print(f"    progression: {prog}\n")

    if not samples:
        print("[!] no samples succeeded")
        return 1

    # 集計
    bcs = [s["best_critical"] for s in samples]
    inits = [s["initial_critical"] for s in samples]
    reds = [s["critical_reduction"] for s in samples]
    elapsed = [s["elapsed_sec"] for s in samples]
    outcomes: dict[str, int] = {}
    for s in samples:
        outcomes[s["final_status"]] = outcomes.get(s["final_status"], 0) + 1

    print("=" * 60)
    print("=== Summary ===")
    print(f"samples completed: {len(samples)}/{args.num_samples}")
    print(f"\ninitial critical:")
    print(f"  mean={statistics.mean(inits):.2f}  median={statistics.median(inits):.0f}  "
          f"range=[{min(inits)}, {max(inits)}]")
    print(f"\nfinal best critical:")
    print(f"  mean={statistics.mean(bcs):.2f}  median={statistics.median(bcs):.0f}  "
          f"range=[{min(bcs)}, {max(bcs)}]")
    print(f"\ncritical reduction (init - best):")
    print(f"  mean={statistics.mean(reds):.2f}  median={statistics.median(reds):.0f}  "
          f"range=[{min(reds)}, {max(reds)}]")
    print(f"\nelapsed (sec):")
    print(f"  mean={statistics.mean(elapsed):.0f}s  median={statistics.median(elapsed):.0f}s")
    print(f"\noutcome distribution:")
    for k, v in sorted(outcomes.items(), key=lambda x: -x[1]):
        pct = 100.0 * v / len(samples)
        print(f"  {k}: {v} ({pct:.0f}%)")

    success_rate = outcomes.get("success", 0) / len(samples) * 100
    convergence_rate = sum(1 for s in samples if s["best_critical"] == 0) / len(samples) * 100
    print(f"\nsuccess rate (final_status==success): {success_rate:.0f}%")
    print(f"convergence rate (best_critical==0):  {convergence_rate:.0f}%")

    out_path = Path(__file__).resolve().parent / "loop_benchmark_results.json"
    out_path.write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] raw samples saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
