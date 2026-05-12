"""Case B (実図面 RING) 評価 orchestrator。

Case A との違い:
- reference は **実 2D 図面の画像ファイル**（CadQuery で生成しない）
- candidate のみ CadQuery で生成 → A/D で 4 視点レンダ
- VLM には「reference = 図面 1 枚」「candidate = 4 視点レンダ」で渡す
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from case_b import CASE_B_VARIANTS, CaseBVariant  # noqa: E402
from cases import OUTPUT_DIR  # noqa: E402
from prompts import ALL_PROMPTS, P3_STRUCTURED_JSON, PromptTemplate  # noqa: E402,F401
from render_utils import render_both  # noqa: E402
from vlm_clients import IVlmClient, VlmResponse, default_clients  # noqa: E402

CASE_B_OUTPUT = OUTPUT_DIR / "case_b"


# ---- 画像セット定義 ----------------------------------------------------------
def _candidate_image_dir(variant_name: str, mode: str) -> Path:
    return CASE_B_OUTPUT / "renders" / variant_name / mode


def image_set_4_line(variant: CaseBVariant) -> tuple[list[Path], list[Path]]:
    """ref = 図面 1 枚 / cand = D 線画 4 視点"""
    views = ("top", "front", "side", "iso")
    ref = [variant.drawing_path]
    cand = [_candidate_image_dir(variant.name, "line") / f"{v}.png" for v in views]
    return ref, cand


def image_set_4_shaded(variant: CaseBVariant) -> tuple[list[Path], list[Path]]:
    """ref = 図面 1 枚 / cand = A 影付き 4 視点"""
    views = ("top", "front", "side", "iso")
    ref = [variant.drawing_path]
    cand = [_candidate_image_dir(variant.name, "shaded") / f"{v}.png" for v in views]
    return ref, cand


def image_set_8_mixed(variant: CaseBVariant) -> tuple[list[Path], list[Path]]:
    """ref = 図面 1 枚 / cand = D 線画 4 + A 影付き 4 = 8 視点"""
    views = ("top", "front", "side", "iso")
    ref = [variant.drawing_path]
    cand = (
        [_candidate_image_dir(variant.name, "line")   / f"{v}.png" for v in views] +
        [_candidate_image_dir(variant.name, "shaded") / f"{v}.png" for v in views]
    )
    return ref, cand


IMAGE_SETS = {
    "IS_b_4_line":   image_set_4_line,
    "IS_b_4_shaded": image_set_4_shaded,
    "IS_b_8_mixed":  image_set_8_mixed,
}


# ---- レンダリング ------------------------------------------------------------
def ensure_renders(force: bool = False) -> None:
    for v in CASE_B_VARIANTS:
        target_dir = CASE_B_OUTPUT / "renders" / v.name
        if force or not target_dir.exists():
            print(f"[render] {v.name} -> {target_dir}")
            render_both(v.candidate_cad_script, target_dir)
        else:
            print(f"[render] {v.name} already exists, skipping")


# ---- 評価ループ --------------------------------------------------------------
def evaluate_one(client: IVlmClient, variant: CaseBVariant,
                 image_set_name: str, image_set_fn,
                 prompt: PromptTemplate = P3_STRUCTURED_JSON) -> dict:
    ref_imgs, cand_imgs = image_set_fn(variant)
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
        "variant":        variant.name,
        "ground_truth":   [asdict(d) for d in variant.ground_truth],
        "prompt":         prompt.name,
        "image_set":      image_set_name,
        "client":         client.name,
        "response":       resp.text,
        "input_tokens":   resp.input_tokens,
        "output_tokens":  resp.output_tokens,
        "duration_sec":   round(resp.duration_sec, 2),
        "error":          resp.error,
    }


def run(variants: tuple[CaseBVariant, ...], image_sets: dict,
        clients: list[IVlmClient], prompt: PromptTemplate,
        dry_run: bool = False) -> list[dict]:
    results: list[dict] = []
    total = len(variants) * len(image_sets) * len(clients)
    if dry_run:
        print(f"[dry-run] would make {total} VLM calls")
        return results
    print(f"[*] Total VLM calls: {total}")
    for v in variants:
        print(f"\n=== variant: {v.name} ({v.note}) ===")
        for iset_name, iset_fn in image_sets.items():
            for c in clients:
                results.append(evaluate_one(c, v, iset_name, iset_fn, prompt))
    return results


# ---- 結果出力 ----------------------------------------------------------------
def write_summary_html(results: list[dict]) -> Path:
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
            text = (r.get("error") or r.get("response", ""))
            text_html = (
                text.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace("\n", "<br>")
            )
            cost = f"in={r['input_tokens']} / out={r['output_tokens']} ({r['duration_sec']}s)"
            rows_html += (
                f'<tr>'
                f'<td class="meta"><b>{r["client"]}</b><br>'
                f'<span class="iset">{r["image_set"]}</span><br>'
                f'<span class="cost">{cost}</span></td>'
                f'<td><pre>{text_html}</pre></td>'
                f'</tr>'
            )
        parts.append(
            f'<section><h2>{variant_name}</h2>'
            f'<details open><summary>Ground truth (人手)</summary>{gt_html}</details>'
            f'<table>{rows_html}</table>'
            f'</section>'
        )

    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"><title>Case B eval</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 16px; background: #f5f5f5; }}
section {{ background: white; padding: 12px; margin-bottom: 24px; border: 1px solid #ddd; }}
h2 {{ margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; }}
td.meta {{ width: 220px; background: #fafafa; font-size: 12px; }}
.iset {{ color: #888; }}
.cost {{ color: #aaa; font-size: 11px; }}
pre {{ font-family: -apple-system, sans-serif; white-space: pre-wrap; margin: 0; font-size: 13px; }}
</style></head><body>
<h1>Case B eval — 実図面 RING</h1>
{"".join(parts)}
</body></html>
"""
    out = CASE_B_OUTPUT / "summary.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--re-render", action="store_true")
    parser.add_argument("--only-image-set")
    parser.add_argument("--prompt", default="P3_structured_json",
                        help="使用するプロンプト名 (P3_structured_json | P4_structured_strict)")
    args = parser.parse_args()

    prompt_map = {p.name: p for p in ALL_PROMPTS}
    if args.prompt not in prompt_map:
        print(f"[!] Unknown prompt: {args.prompt}. Available: {list(prompt_map)}")
        return 1
    prompt = prompt_map[args.prompt]
    print(f"[*] Prompt: {prompt.name}")

    CASE_B_OUTPUT.mkdir(parents=True, exist_ok=True)

    print("=== Stage 1: render candidates ===")
    ensure_renders(force=args.re_render)

    print("\n=== Stage 2: VLM evaluation ===")
    image_sets = IMAGE_SETS
    if args.only_image_set:
        image_sets = {k: v for k, v in image_sets.items() if k == args.only_image_set}

    clients = default_clients()
    if not clients:
        print("[!] No VLM client available")
        return 1

    results = run(CASE_B_VARIANTS, image_sets, clients, prompt, dry_run=args.dry_run)
    if args.dry_run or not results:
        return 0

    results_path = CASE_B_OUTPUT / "results.json"
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path = write_summary_html(results)
    print(f"\n[*] Results JSON: {results_path}")
    print(f"[*] Summary HTML: {html_path}")
    print(f"[*] Open from host: open {html_path}")
    total_in = sum(r["input_tokens"] for r in results)
    total_out = sum(r["output_tokens"] for r in results)
    print(f"[*] Token usage — in: {total_in:,}, out: {total_out:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
