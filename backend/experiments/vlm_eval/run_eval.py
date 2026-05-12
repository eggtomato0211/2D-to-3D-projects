"""VLM 評価実験 orchestrator。

工程:
1. reference モデルと variants を全て A/D でレンダリング（既にあればスキップ）
2. 全組み合わせ (variant × prompt × image_set × model) で VLM を呼び出し
3. results.json に raw 出力を保存、summary.html で目視比較できるようにする
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cases import (  # noqa: E402
    OUTPUT_DIR,
    REFERENCE_SCRIPT,
    RESULTS_DIR,
    VARIANTS,
    Variant,
    reference_image_dir,
    variant_image_dir,
)
from prompts import ALL_PROMPTS, PromptTemplate  # noqa: E402
from render_utils import render_both  # noqa: E402
from vlm_clients import IVlmClient, VlmResponse, default_clients  # noqa: E402


# ----- 画像セット定義 ---------------------------------------------------------

def image_set_iso_only(name: str) -> tuple[list[Path], list[Path]]:
    """IS1: iso 1 枚（line drawing 同士）の最小セット"""
    ref_files = [reference_image_dir("line") / "iso.png"]
    cand_files = [variant_image_dir(name, "line") / "iso.png"]
    return ref_files, cand_files


def image_set_4_line(name: str) -> tuple[list[Path], list[Path]]:
    """IS2: 4 視点 line drawing 同士"""
    views = ("top", "front", "side", "iso")
    ref_files = [reference_image_dir("line") / f"{v}.png" for v in views]
    cand_files = [variant_image_dir(name, "line") / f"{v}.png" for v in views]
    return ref_files, cand_files


def image_set_4_shaded(name: str) -> tuple[list[Path], list[Path]]:
    """IS4: 4 視点 影付き raster 同士（D 単独 vs A 単独の比較用）"""
    views = ("top", "front", "side", "iso")
    ref_files = [reference_image_dir("shaded") / f"{v}.png" for v in views]
    cand_files = [variant_image_dir(name, "shaded") / f"{v}.png" for v in views]
    return ref_files, cand_files


def image_set_8_mixed(name: str) -> tuple[list[Path], list[Path]]:
    """IS3: 線画 4 + 影付き 4 = 8 枚（最大セット）"""
    views = ("top", "front", "side", "iso")
    ref_files = (
        [reference_image_dir("line")   / f"{v}.png" for v in views] +
        [reference_image_dir("shaded") / f"{v}.png" for v in views]
    )
    cand_files = (
        [variant_image_dir(name, "line")   / f"{v}.png" for v in views] +
        [variant_image_dir(name, "shaded") / f"{v}.png" for v in views]
    )
    return ref_files, cand_files


IMAGE_SETS = {
    "IS1_iso_only":  image_set_iso_only,
    "IS2_4_line":    image_set_4_line,
    "IS3_8_mixed":   image_set_8_mixed,
    "IS4_4_shaded":  image_set_4_shaded,
}


# ----- レンダリング -----------------------------------------------------------

def ensure_renders(force: bool = False) -> None:
    ref_dir = reference_image_dir("line").parent
    if force or not ref_dir.exists():
        print(f"[render] reference -> {ref_dir}")
        render_both(REFERENCE_SCRIPT, ref_dir)
    else:
        print(f"[render] reference already exists, skipping")
    for v in VARIANTS:
        var_dir = variant_image_dir(v.name, "line").parent
        if force or not var_dir.exists():
            print(f"[render] {v.name} -> {var_dir}")
            render_both(v.cad_script, var_dir)
        else:
            print(f"[render] {v.name} already exists, skipping")


# ----- 評価ループ -------------------------------------------------------------

def evaluate_one(
    client: IVlmClient,
    prompt: PromptTemplate,
    variant: Variant,
    image_set_name: str,
    image_set_fn,
) -> dict:
    ref_imgs, cand_imgs = image_set_fn(variant.name)
    print(
        f"  [{client.name} | {prompt.name} | {image_set_name}] "
        f"ref={len(ref_imgs)} cand={len(cand_imgs)} ...",
        end="",
        flush=True,
    )
    resp: VlmResponse = client.call(prompt.system, prompt.user_text, ref_imgs, cand_imgs)
    if resp.error:
        print(f" ERROR ({resp.error})")
    else:
        print(f" {resp.duration_sec:.1f}s, in={resp.input_tokens} out={resp.output_tokens}")
    return {
        "variant":     variant.name,
        "ground_truth": [asdict(d) for d in variant.ground_truth],
        "prompt":      prompt.name,
        "image_set":   image_set_name,
        "client":      client.name,
        "response":    resp.text,
        "input_tokens":  resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "duration_sec":  round(resp.duration_sec, 2),
        "error":         resp.error,
    }


def run(
    variants: tuple[Variant, ...],
    prompts: tuple[PromptTemplate, ...],
    image_sets: dict,
    clients: list[IVlmClient],
    dry_run: bool = False,
) -> list[dict]:
    results: list[dict] = []
    total = len(variants) * len(prompts) * len(image_sets) * len(clients)
    if dry_run:
        print(f"[dry-run] would make {total} VLM calls")
        return results

    print(f"[*] Total VLM calls: {total}")
    for variant in variants:
        print(f"\n=== variant: {variant.name} ({variant.note}) ===")
        for image_set_name, image_set_fn in image_sets.items():
            for prompt in prompts:
                for client in clients:
                    r = evaluate_one(client, prompt, variant, image_set_name, image_set_fn)
                    results.append(r)
    return results


# ----- 結果出力 ---------------------------------------------------------------

def save_results(results: list[dict]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = RESULTS_DIR / "results.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_json


def write_summary_html(results: list[dict]) -> Path:
    """variant × (image_set × prompt) × client のグリッドで結果を表示"""
    grouped: dict = {}
    for r in results:
        grouped.setdefault(r["variant"], []).append(r)

    parts: list[str] = []
    for variant_name, rows in grouped.items():
        gt_html = "<ul>" + "".join(
            f"<li><b>[{d['severity']}]</b> {d['feature_type']} — {d['description']}</li>"
            for d in rows[0]["ground_truth"]
        ) + "</ul>"

        rows_html = ""
        for r in rows:
            cls = "err" if r.get("error") else ""
            text = r.get("error") or r.get("response", "")
            text_html = (
                text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            )
            cost = f"in={r['input_tokens']} / out={r['output_tokens']} ({r['duration_sec']}s)"
            rows_html += (
                f'<tr class="{cls}">'
                f'<td class="meta">'
                f'<b>{r["client"]}</b><br>'
                f'<span class="prompt">{r["prompt"]}</span><br>'
                f'<span class="iset">{r["image_set"]}</span><br>'
                f'<span class="cost">{cost}</span>'
                f'</td>'
                f'<td><pre>{text_html}</pre></td>'
                f'</tr>'
            )

        parts.append(
            f'<section><h2>{variant_name}</h2>'
            f'<details open><summary>Ground truth</summary>{gt_html}</details>'
            f'<table>{rows_html}</table>'
            f'</section>'
        )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>VLM eval results</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 16px; background: #f5f5f5; }}
section {{ background: white; padding: 12px; margin-bottom: 24px; border: 1px solid #ddd; }}
h2 {{ margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; }}
td.meta {{ width: 220px; background: #fafafa; font-size: 12px; }}
.prompt {{ color: #555; }}
.iset {{ color: #888; }}
.cost {{ color: #aaa; font-size: 11px; }}
.err {{ background: #fee; }}
pre {{ font-family: -apple-system, sans-serif; white-space: pre-wrap; margin: 0; font-size: 13px; }}
</style>
</head>
<body>
<h1>VLM eval — Case A (controlled variants)</h1>
{"".join(parts)}
</body>
</html>
"""
    out = OUTPUT_DIR / "summary.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="API 呼ばずに対象数だけ表示")
    parser.add_argument("--re-render", action="store_true", help="画像を再生成")
    parser.add_argument("--only-variant", help="特定 variant のみ実行")
    parser.add_argument("--only-prompt", help="特定 prompt のみ実行")
    parser.add_argument("--only-image-set", help="特定 image_set のみ実行")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Stage 1: render ===")
    ensure_renders(force=args.re_render)

    print("\n=== Stage 2: VLM evaluation ===")
    variants = VARIANTS
    prompts = ALL_PROMPTS
    image_sets = IMAGE_SETS
    if args.only_variant:
        variants = tuple(v for v in variants if v.name == args.only_variant)
    if args.only_prompt:
        prompts = tuple(p for p in prompts if p.name == args.only_prompt)
    if args.only_image_set:
        image_sets = {k: v for k, v in image_sets.items() if k == args.only_image_set}

    clients = default_clients()
    if not clients:
        print("[!] No VLM client available (need ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        return 1

    results = run(variants, prompts, image_sets, clients, dry_run=args.dry_run)
    if args.dry_run or not results:
        return 0

    json_path = save_results(results)
    html_path = write_summary_html(results)
    print(f"\n[*] Results JSON: {json_path}")
    print(f"[*] Summary HTML: {html_path}")
    print(f"[*] Open from host: open {html_path}")
    total_in = sum(r["input_tokens"] for r in results)
    total_out = sum(r["output_tokens"] for r in results)
    print(f"[*] Token usage — in: {total_in:,}, out: {total_out:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
