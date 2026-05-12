"""§10 Corrector の単純ケース動作確認。

簡単なターゲット: 80×50×20 の箱 + 3 穴 (φ12 中央 + φ6×2 両側) + R3 縦フィレット
失敗候補: 同じだが左の φ6 穴が欠落（critical 1 件）

これが収束しないなら R1〜R6 実装のどこかに本質的な欠陥がある。
収束するなら RING のような複雑ケース特有の難しさで Tool Use 化が必要、と切り分けできる。
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "http://localhost:8000"
EXPERIMENT_DIR = Path(__file__).resolve().parent
BLUEPRINT_PNG = EXPERIMENT_DIR / "simple_blueprint.png"

# 正解モデル: 80×50×20 箱 + 中央 φ12 + 両側 φ6 + R3 縦フィレット
REFERENCE_SCRIPT = """\
import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(12)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").center(25, 0).hole(6)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").center(-25, 0).hole(6)
    .edges("|Z").fillet(3)
)
"""

# 失敗候補: 左の φ6 を削除
FAILED_SCRIPT = """\
import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(12)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").center(25, 0).hole(6)
    .edges("|Z").fillet(3)
)
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


def _ensure_blueprint_png() -> None:
    """正解モデルの iso 線画を blueprint として用意"""
    if BLUEPRINT_PNG.exists():
        print(f"[*] blueprint already exists: {BLUEPRINT_PNG}")
        return

    # CadQuery で正解モデルを生成 → SVG → PNG
    sys.path.insert(0, "/app")  # コンテナ内パス
    sys.path.insert(0, str(EXPERIMENT_DIR.parent))  # ホスト内パス
    import cadquery as cq
    import cairosvg

    namespace: dict = {}
    exec(REFERENCE_SCRIPT, namespace)
    result = namespace["result"]
    svg = cq.exporters.getSVG(
        cq.exporters.toCompound(result),
        opts={
            "width": 1024,
            "height": 1024,
            "marginLeft": 50,
            "marginTop": 50,
            "showAxes": False,
            "projectionDir": (1.0, -1.0, 1.0),  # iso
            "strokeWidth": 0.5,
            "strokeColor": (0, 0, 0),
            "hiddenColor": (160, 160, 160),
            "showHidden": True,
        },
    )
    png_bytes = cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        output_width=1024,
        output_height=1024,
        background_color="white",
    )
    BLUEPRINT_PNG.write_bytes(png_bytes)
    print(f"[*] generated blueprint: {BLUEPRINT_PNG}")


def _run_one(blueprint_id: str, max_iterations: int = 5) -> dict:
    gen = _post_query(f"{API}/test/generate", {
        "blueprint_id": blueprint_id,
        "script_override": FAILED_SCRIPT,
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
    parser.add_argument("-n", "--num-samples", type=int, default=3)
    parser.add_argument("--max-iter", type=int, default=5)
    parser.add_argument("--prepare-blueprint-only", action="store_true",
                        help="blueprint PNG を生成して終わる（コンテナ内で実行用）")
    args = parser.parse_args()

    _ensure_blueprint_png()
    if args.prepare_blueprint_only:
        return 0

    print(f"\n=== Simple-case loop benchmark: N={args.num_samples}, max_iter={args.max_iter} ===\n")

    print("[*] uploading simple blueprint...")
    bp = _post_multipart(f"{API}/blueprints/upload", BLUEPRINT_PNG, "simple.png")
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

    bcs = [s["best_critical"] for s in samples]
    inits = [s["initial_critical"] for s in samples]
    reds = [s["critical_reduction"] for s in samples]
    elapsed = [s["elapsed_sec"] for s in samples]
    outcomes: dict[str, int] = {}
    for s in samples:
        outcomes[s["final_status"]] = outcomes.get(s["final_status"], 0) + 1

    print("=" * 60)
    print("=== Summary (Simple case: 1 missing hole) ===")
    print(f"samples completed: {len(samples)}/{args.num_samples}")
    print(f"\ninitial critical:    mean={statistics.mean(inits):.2f}  range=[{min(inits)}, {max(inits)}]")
    print(f"final best critical: mean={statistics.mean(bcs):.2f}  range=[{min(bcs)}, {max(bcs)}]")
    print(f"reduction:           mean={statistics.mean(reds):.2f}  range=[{min(reds)}, {max(reds)}]")
    print(f"elapsed:             mean={statistics.mean(elapsed):.0f}s")
    print(f"\noutcome:")
    for k, v in sorted(outcomes.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({100.0*v/len(samples):.0f}%)")

    success_rate = outcomes.get("success", 0) / len(samples) * 100
    convergence_rate = sum(1 for s in samples if s["best_critical"] == 0) / len(samples) * 100
    print(f"\nsuccess rate:    {success_rate:.0f}%")
    print(f"convergence:     {convergence_rate:.0f}%")

    out_path = EXPERIMENT_DIR / "loop_benchmark_simple_results.json"
    out_path.write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[*] raw samples saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
