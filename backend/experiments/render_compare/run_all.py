"""4 方式のレンダラを順次実行して結果を比較する orchestrator。

各方式は **subprocess 内で実行** してプロセス分離する（segfault が伝播しないため）。
失敗してもログを残して次に進む。最後に summary.html を生成して
全方式 × 全視点を一覧表示できるようにする。
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

# このファイルと同じディレクトリにある shared.py を import 可能にする
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared import VIEW_NAMES, export_test_stl  # noqa: E402

OUTPUT_ROOT = SCRIPT_DIR / "output"

METHOD_TIMEOUT_SEC = 180


METHODS = [
    ("A_trimesh_pyrender", "method_a_trimesh_pyrender", "trimesh + pyrender (OSMesa)"),
    ("B_vedo",             "method_b_vedo",             "vedo (VTK ラッパ)"),
    ("C_open3d",           "method_c_open3d",           "Open3D OffscreenRenderer"),
    ("D_cadquery_svg",     "method_d_cadquery_svg",     "CadQuery SVG → cairosvg PNG"),
]


def run_method(slug: str, module_name: str, label: str, stl_path: Path) -> dict:
    out_dir = OUTPUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    result = {
        "slug": slug,
        "label": label,
        "ok": False,
        "duration_sec": 0.0,
        "error": None,
        "files": [],
    }

    script_path = SCRIPT_DIR / f"{module_name}.py"
    try:
        proc = subprocess.run(
            [sys.executable, "-u", str(script_path), str(stl_path), str(out_dir)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=METHOD_TIMEOUT_SEC,
        )
        if proc.returncode == 0:
            files = sorted(out_dir.glob("*.png"))
            if files:
                result["ok"] = True
                result["files"] = [str(p.relative_to(OUTPUT_ROOT)) for p in files]
            else:
                result["error"] = "subprocess returned 0 but no PNG output"
        else:
            tail_stderr = "\n".join(proc.stderr.strip().splitlines()[-5:])
            tail_stdout = "\n".join(proc.stdout.strip().splitlines()[-5:])
            result["error"] = (
                f"exit={proc.returncode}\n"
                f"--- stderr (tail) ---\n{tail_stderr}\n"
                f"--- stdout (tail) ---\n{tail_stdout}"
            )
    except subprocess.TimeoutExpired:
        result["error"] = f"timeout after {METHOD_TIMEOUT_SEC}s"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        result["duration_sec"] = time.time() - started
    return result


def write_summary_html(results: list[dict], stl_rel: str) -> Path:
    """4方式 × 4視点を grid 表示する HTML を生成"""
    rows = []
    for r in results:
        cells = []
        for view in VIEW_NAMES:
            if r["ok"]:
                src = f"{r['slug']}/{view}.png"
                cells.append(
                    f'<td><div class="vlabel">{view}</div>'
                    f'<img src="{src}" alt="{r["slug"]}/{view}"/></td>'
                )
            else:
                cells.append('<td class="err">×</td>')
        status = "✓ OK" if r["ok"] else f"✗ FAIL: {r['error'].splitlines()[0] if r['error'] else ''}"
        rows.append(
            f'<tr><th>{r["label"]}<br>'
            f'<span class="status">{status}</span><br>'
            f'<span class="dur">{r["duration_sec"]:.1f}s</span></th>'
            + "".join(cells) + "</tr>"
        )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Render comparison</title>
<style>
body {{ font-family: -apple-system, sans-serif; padding: 16px; background: #f5f5f5; }}
h1 {{ margin-bottom: 4px; }}
.input {{ color: #555; margin-bottom: 12px; font-size: 13px; }}
table {{ border-collapse: collapse; background: white; }}
th, td {{ border: 1px solid #ccc; padding: 6px; vertical-align: top; }}
th {{ background: #e8e8e8; min-width: 140px; text-align: left; font-size: 13px; }}
img {{ max-width: 320px; max-height: 320px; display: block; }}
.vlabel {{ font-size: 11px; color: #666; margin-bottom: 4px; }}
.status {{ font-size: 11px; color: #444; font-weight: normal; }}
.dur {{ font-size: 11px; color: #888; font-weight: normal; }}
.err {{ background: #fee; color: #a00; text-align: center; font-size: 24px; }}
</style>
</head>
<body>
<h1>Render comparison — 4 methods × 4 views</h1>
<p class="input">Input STL: <code>{stl_rel}</code></p>
<table>
<thead>
<tr><th>Method</th><th>Top</th><th>Front</th><th>Side</th><th>Iso</th></tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</body>
</html>
"""
    out = OUTPUT_ROOT / "summary.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    print("[*] Generating test STL...")
    stl_path = OUTPUT_ROOT / "input.stl"
    export_test_stl(stl_path)
    print(f"    -> {stl_path}")

    results: list[dict] = []
    for slug, module_name, label in METHODS:
        print(f"\n[*] Method {slug}: {label}")
        r = run_method(slug, module_name, label, stl_path)
        if r["ok"]:
            print(f"    OK ({r['duration_sec']:.1f}s) -> {len(r['files'])} files")
            for f in r["files"]:
                print(f"       {f}")
        else:
            print(f"    FAIL ({r['duration_sec']:.1f}s)")
            first = (r["error"] or "").splitlines()[0]
            print(f"       {first}")
        results.append(r)

    summary = write_summary_html(results, stl_path.relative_to(OUTPUT_ROOT).as_posix())
    print(f"\n[*] Summary HTML: {summary}")
    print(f"[*] Open from host:  open {summary}")

    succeeded = sum(1 for r in results if r["ok"])
    print(f"\n[*] {succeeded}/{len(results)} methods succeeded.")
    return 0 if succeeded > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
