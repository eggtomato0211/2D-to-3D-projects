"""DeepCAD ベンチで複数モデルを A/B 比較する。

対象パイプライン: Phase 1 analyze → Phase 2 generate → execute（CadQuery）
- compile rate: スクリプトが実行できる割合
- chamfer / IoU: 生成 STL と GT STL の形状一致度

Verify は cost と LLM 依存性が大きいので本ランナーでは含めない（必要なら別途）。

例:
    docker compose run --rm backend python -m experiments.deepcad.model_comparison \\
      --dataset-name dataset_v1 --num-samples 20 \\
      --models claude-opus-4-6,claude-sonnet-4-6,gpt-5,gpt-5.5
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, "/app")

EXPERIMENT_DIR = Path(__file__).resolve().parent

ANTHROPIC_MODELS = {
    "claude-opus-4-7", "claude-opus-4-6", "claude-opus-4-5",
    "claude-sonnet-4-6", "claude-sonnet-4-5",
    "claude-haiku-4-5",
}
OPENAI_MODELS = {
    "gpt-5.5", "gpt-5.4", "gpt-5", "gpt-5-mini",
    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
    "gpt-4o", "gpt-4o-mini",
    "o3", "o3-mini", "o4-mini",
}


def _build_verifier(verifier_model: str):
    """固定 verifier（モデル比較対象とは独立、意味的差異の評価用）を構築。

    既定では `claude-sonnet-4-6` を使う（コスト/精度バランス）。
    """
    from app.infrastructure.verification.anthropic_model_verifier import (
        AnthropicModelVerifier,
    )
    api_key = os.environ["ANTHROPIC_API_KEY"]
    v = AnthropicModelVerifier(api_key=api_key, model=verifier_model)
    return v


def _build_renderers():
    """4 視点レンダラ（line + shaded）を返す。

    headless 環境で pyrender が初期化できない場合は shaded を None にし、
    呼び出し側で line_views を shaded 代用にする（verifier は両方の入力を要求するため）。
    """
    from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer
    line_r = CadQuerySvgRenderer()
    shaded_r = None
    try:
        from app.infrastructure.rendering.trimesh_pyrender_renderer import (
            TrimeshPyrenderRenderer,
        )
        shaded_r = TrimeshPyrenderRenderer()
    except Exception as e:
        print(f"[!] shaded renderer unavailable ({type(e).__name__}: {str(e)[:80]}); "
              "line_views will be used as shaded too")
    return line_r, shaded_r


def _build_components(model: str, exclude_ids: set[str] | None = None):
    """モデル名から (analyzer, script_generator) を組み立てる。

    exclude_ids が指定された場合、Reference Code RAG retriever に渡してリーク防止。
    """
    # RAG retriever（共有 singleton）を model_factory 経由で取得
    from app.infrastructure.vlm.model_factory import (
        _get_docs_retriever, _get_reference_retriever,
    )
    docs_r = _get_docs_retriever()
    ref_r = _get_reference_retriever()
    if ref_r is not None and exclude_ids:
        ref_r.set_exclude_ids(exclude_ids)

    if model in ANTHROPIC_MODELS:
        from app.infrastructure.vlm.anthropic.anthropic_blueprint_analyzer import (
            AnthropicBlueprintAnalyzer,
        )
        from app.infrastructure.vlm.anthropic.anthropic_script_generator import (
            AnthropicScriptGenerator,
        )
        api_key = os.environ["ANTHROPIC_API_KEY"]
        analyzer = AnthropicBlueprintAnalyzer(api_key=api_key, model=model)
        sg = AnthropicScriptGenerator(
            api_key=api_key, model=model,
            docs_retriever=docs_r, ref_retriever=ref_r,
        )
        analyzer.client = analyzer.client.with_options(timeout=120.0, max_retries=2)
        sg.client = sg.client.with_options(timeout=120.0, max_retries=2)
    elif model in OPENAI_MODELS:
        from app.infrastructure.vlm.openai.openai_blueprint_analyzer import (
            OpenAIBlueprintAnalyzer,
        )
        from app.infrastructure.vlm.openai.openai_script_generator import (
            OpenAIScriptGenerator,
        )
        api_key = os.environ["OPENAI_API_KEY"]
        analyzer = OpenAIBlueprintAnalyzer(api_key=api_key, model=model)
        sg = OpenAIScriptGenerator(
            api_key=api_key, model=model,
            docs_retriever=docs_r, ref_retriever=ref_r,
        )
    else:
        raise ValueError(f"unknown model: {model}")
    return analyzer, sg


def _compute_shape_metrics(gt_stl: str, gen_stl: str,
                           num_points: int = 4096,
                           voxel_pitch: float = 0.02,
                           icp_align: bool = True) -> dict:
    """点群＋ボクセルベースのメトリクス。

    icp_align=True の場合、24 軸整合回転 × ICP の組合せで生成メッシュを GT に整列してから
    chamfer/IoU を測る（回転ズレを補正）。整列前の値も raw として保持する。
    """
    gt_mesh = trimesh.load(gt_stl, force="mesh")
    gen_mesh = trimesh.load(gen_stl, force="mesh")

    def _normalize(m: trimesh.Trimesh) -> trimesh.Trimesh:
        m2 = m.copy()
        m2.apply_translation(-m2.bounds.mean(axis=0))
        scale = max(m2.extents)
        if scale > 1e-9:
            m2.apply_scale(1.0 / scale)
        return m2

    gt_n = _normalize(gt_mesh)
    gen_n = _normalize(gen_mesh)

    from scipy.spatial import cKDTree

    gt_pts = gt_n.sample(num_points)

    def _chamfer(gt_pts_arr: np.ndarray, gen_pts_arr: np.ndarray) -> tuple[float, float]:
        tg = cKDTree(gt_pts_arr)
        tn = cKDTree(gen_pts_arr)
        d1, _ = tg.query(gen_pts_arr)
        d2, _ = tn.query(gt_pts_arr)
        return float(np.mean(d1) + np.mean(d2)), float(max(d1.max(), d2.max()))

    # raw（整列なし）
    gen_pts_raw = gen_n.sample(num_points)
    chamfer_raw, hausdorff_raw = _chamfer(gt_pts, gen_pts_raw)

    # 整列後（24 軸整合回転をベースに ICP）
    chamfer = chamfer_raw
    hausdorff = hausdorff_raw
    aligned_mesh = gen_n
    if icp_align:
        try:
            from trimesh.registration import icp
            from itertools import permutations, product
            # 24 軸整合回転の生成（OK な回転行列のみ、行列式 = +1）
            axes_perms = list(permutations([0, 1, 2]))
            sign_combos = list(product([1, -1], repeat=3))
            best_chamfer = chamfer_raw
            best_matrix = np.eye(4)
            best_pts = gen_pts_raw
            for perm in axes_perms:
                for signs in sign_combos:
                    R = np.zeros((3, 3))
                    for i, axis_idx in enumerate(perm):
                        R[i, axis_idx] = signs[i]
                    if abs(np.linalg.det(R) - 1.0) > 1e-6:
                        continue
                    T = np.eye(4)
                    T[:3, :3] = R
                    pts_rot = trimesh.transform_points(gen_pts_raw, T)
                    cd, _ = _chamfer(gt_pts, pts_rot)
                    if cd < best_chamfer:
                        best_chamfer = cd
                        best_matrix = T
                        best_pts = pts_rot
            # ICP で微調整（best_matrix を初期推定として）
            try:
                refined_matrix, _, _ = icp(
                    gen_pts_raw, gt_pts,
                    initial=best_matrix,
                    threshold=1e-5,
                    max_iterations=30,
                )
                pts_refined = trimesh.transform_points(gen_pts_raw, refined_matrix)
                cd_refined, hd_refined = _chamfer(gt_pts, pts_refined)
                if cd_refined < best_chamfer:
                    chamfer = cd_refined
                    hausdorff = hd_refined
                    best_matrix = refined_matrix
                else:
                    chamfer = best_chamfer
                    hausdorff = _chamfer(gt_pts, best_pts)[1]
            except Exception:
                chamfer = best_chamfer
                hausdorff = _chamfer(gt_pts, best_pts)[1]
            # IoU 用にメッシュへも transform を適用
            aligned_mesh = gen_n.copy()
            aligned_mesh.apply_transform(best_matrix)
        except Exception:
            pass

    iou = float("nan")
    try:
        gt_vox = gt_n.voxelized(pitch=voxel_pitch).fill()
        gen_vox = aligned_mesh.voxelized(pitch=voxel_pitch).fill()
        gt_idx = set(tuple(np.round(p / voxel_pitch).astype(int)) for p in gt_vox.points)
        gen_idx = set(tuple(np.round(p / voxel_pitch).astype(int)) for p in gen_vox.points)
        if gt_idx and gen_idx:
            inter = len(gt_idx & gen_idx)
            union = len(gt_idx | gen_idx)
            iou = float(inter / union) if union else 0.0
    except Exception:
        pass

    # ----- match_score: 絶対スケールでの Volume IoU（"全く同じか" を一発で測る) -----
    # 正規化前の mm 座標で並進整列 + ICP し、最大辺基準の voxel pitch でボクセル化して IoU。
    # スケール違い・形状違い・トポロジ違いの全てが減点として乗る。
    match_score = float("nan")
    volume_ratio = float("nan")
    try:
        from trimesh.registration import icp as _icp
        from itertools import permutations as _perms, product as _prod
        # 絶対スケール: 並進のみ揃える（中心化）。スケールは触らない
        gt_abs = gt_mesh.copy()
        gen_abs = gen_mesh.copy()
        gt_abs.apply_translation(-gt_abs.bounds.mean(axis=0))
        gen_abs.apply_translation(-gen_abs.bounds.mean(axis=0))

        # voxel pitch を「GT の最大辺の 1/50」に設定（≒ 2mm 相当 @ 100mm モデル）
        gt_max_edge = float(max(gt_abs.extents))
        if gt_max_edge < 1e-9:
            raise ValueError("degenerate gt bbox")
        abs_pitch = gt_max_edge / 50.0

        # 整列: 24 軸回転 × ICP（絶対スケール空間で実施）
        gt_pts_abs = gt_abs.sample(num_points)
        gen_pts_abs = gen_abs.sample(num_points)
        best_T = np.eye(4)
        best_cd = float("inf")
        for perm in _perms([0, 1, 2]):
            for signs in _prod([1, -1], repeat=3):
                R = np.zeros((3, 3))
                for i, axis_idx in enumerate(perm):
                    R[i, axis_idx] = signs[i]
                if abs(np.linalg.det(R) - 1.0) > 1e-6:
                    continue
                T = np.eye(4)
                T[:3, :3] = R
                pts_rot = trimesh.transform_points(gen_pts_abs, T)
                cd, _ = _chamfer(gt_pts_abs, pts_rot)
                if cd < best_cd:
                    best_cd = cd
                    best_T = T
        try:
            refined, _, _ = _icp(
                gen_pts_abs, gt_pts_abs,
                initial=best_T, threshold=1e-4, max_iterations=30,
            )
            pts_ref = trimesh.transform_points(gen_pts_abs, refined)
            cd_ref, _ = _chamfer(gt_pts_abs, pts_ref)
            if cd_ref < best_cd:
                best_T = refined
        except Exception:
            pass

        gen_aligned_abs = gen_abs.copy()
        gen_aligned_abs.apply_transform(best_T)

        # 絶対スケール voxel IoU
        gt_vox_abs = gt_abs.voxelized(pitch=abs_pitch).fill()
        gen_vox_abs = gen_aligned_abs.voxelized(pitch=abs_pitch).fill()
        gt_idx_abs = set(
            tuple(np.round(p / abs_pitch).astype(int)) for p in gt_vox_abs.points
        )
        gen_idx_abs = set(
            tuple(np.round(p / abs_pitch).astype(int)) for p in gen_vox_abs.points
        )
        if gt_idx_abs and gen_idx_abs:
            inter_abs = len(gt_idx_abs & gen_idx_abs)
            union_abs = len(gt_idx_abs | gen_idx_abs)
            match_score = float(inter_abs / union_abs) if union_abs else 0.0
        # 体積比（参考: 1.0 ぴったりなら同体積）
        gt_vol = float(gt_abs.volume) if gt_abs.is_volume else len(gt_idx_abs) * abs_pitch ** 3
        gen_vol = float(gen_aligned_abs.volume) if gen_aligned_abs.is_volume else len(gen_idx_abs) * abs_pitch ** 3
        if gt_vol > 1e-9:
            volume_ratio = gen_vol / gt_vol
    except Exception:
        pass

    return {
        "chamfer": chamfer,
        "chamfer_raw": chamfer_raw,
        "hausdorff": hausdorff,
        "iou": iou,
        # 「完全一致 = 1, 別物 = 0」の一発スコア（絶対スケール + 整列後）
        "match_score": match_score,
        "volume_ratio": volume_ratio,
    }


def run_one(entry_dir: Path, analyzer, sg, work_dir: Path,
            verifier=None, line_renderer=None, shaded_renderer=None,
            loop_iters: int = 0, match_threshold: float = 0.8) -> dict:
    """1 サンプルを実行: analyze → generate → execute → shape メトリクス → verify。

    verifier / renderers が None の場合は verify ステップをスキップ。
    loop_iters > 0 の場合、以下のいずれかで corrector を呼んで反復修正:
      (1) critical > 0
      (2) critical=0 だが match_score < match_threshold（形状が違う場合）
    上限 or critical=0 かつ match_score ≥ match_threshold で早期終了。
    """
    obj_id = entry_dir.name
    drawing_path = entry_dir / "drawing.png"
    gt_stl = entry_dir / "model.stl"

    rec = {"id": obj_id}
    started = time.time()

    # Phase 1: 図面 → 設計手順
    from app.domain.entities.blueprint import Blueprint
    bp = Blueprint(
        id=f"bp_{obj_id}",
        file_path=str(drawing_path),
        file_name="drawing.png",
        content_type="image/png",
    )
    try:
        steps, clarifications = analyzer.analyze(bp)
        rec["steps_count"] = len(steps)
        rec["clarifications_count"] = len(clarifications)
    except Exception as e:
        rec["analyze_error"] = f"{type(e).__name__}: {str(e)[:120]}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # Phase 2 Step 2: 設計手順 → CadQuery
    try:
        cad_script = sg.generate(steps, clarifications)
        rec["script_chars"] = len(cad_script.content)
    except Exception as e:
        rec["generate_error"] = f"{type(e).__name__}: {str(e)[:120]}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # Phase 2 Step 3: 実行（STL + STEP の両方を出力）
    namespace: dict = {}
    work_stl = work_dir / f"{obj_id}.stl"
    work_step = work_dir / f"{obj_id}.step"
    try:
        exec(cad_script.content, namespace)
        result = namespace.get("result") or namespace.get("part")
        if result is None:
            rec["compile_ok"] = False
            rec["execute_error"] = "no result/part variable"
            rec["elapsed"] = round(time.time() - started, 2)
            return rec
        import cadquery as cq
        cq.exporters.export(result, str(work_stl))
        cq.exporters.export(result, str(work_step))
        rec["compile_ok"] = True
    except Exception as e:
        rec["compile_ok"] = False
        rec["execute_error"] = f"{type(e).__name__}: {str(e)[:120]}"
        rec["elapsed"] = round(time.time() - started, 2)
        return rec

    # Shape メトリクス（ICP 整列込み）
    try:
        metrics = _compute_shape_metrics(str(gt_stl), str(work_stl))
        rec.update(metrics)
    except Exception as e:
        rec["metrics_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # Verify ステップ（固定モデル）: 元図面 vs 生成 4 視点
    v_result = None
    line_views = None
    shaded_views = None
    if verifier is not None and line_renderer is not None:
        try:
            line_views = line_renderer.render(str(work_step))
            if shaded_renderer is not None:
                shaded_views = shaded_renderer.render(str(work_stl))
            else:
                shaded_views = line_views  # headless fallback
            v_result = verifier.verify(
                blueprint_image_path=str(drawing_path),
                line_views=line_views,
                shaded_views=shaded_views,
            )
            rec["verify_critical"] = v_result.critical_count()
            rec["verify_major"] = v_result.major_count()
            rec["verify_minor"] = v_result.minor_count()
            rec["verify_is_valid"] = v_result.is_valid
            rec["verify_discrepancies"] = [
                {
                    "severity": d.severity,
                    "feature": d.feature_type,
                    "description": d.description[:120],
                }
                for d in v_result.discrepancies
            ]
        except Exception as e:
            rec["verify_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # --- Verify-Correct ループ（loop_iters > 0 のとき）---
    initial_match = rec.get("match_score")
    needs_loop = (
        loop_iters > 0
        and v_result is not None
        and (
            v_result.critical_count() > 0
            or (isinstance(initial_match, float) and initial_match < match_threshold)
        )
    )
    if needs_loop:
        rec["loop_history"] = []
        best_state = {
            "script": cad_script,
            "stl_path": str(work_stl),
            "step_path": str(work_step),
            "critical": v_result.critical_count(),
            "major": v_result.major_count(),
            "minor": v_result.minor_count(),
            "match_score": rec.get("match_score"),
            "iter": 0,
        }
        current_script = cad_script
        # critical=0 だが match_score 低い場合、合成 Discrepancy を注入して corrector に
        # 「全体形状が GT と違う」とフィードバックする
        from app.domain.value_objects.discrepancy import Discrepancy as _Disc
        if v_result.critical_count() == 0 and isinstance(initial_match, float) and initial_match < match_threshold:
            synthetic = _Disc(
                feature_type="outline",
                severity="critical",
                description=(
                    f"全体形状が参照と一致していません（体積一致度 match_score = {initial_match:.2f}, "
                    "目標 ≥ 0.8）。proportions / aspect ratio / 主要寸法 / 体積比 を見直して再生成してください。"
                ),
                expected="参照図面と同じ全体形状・寸法スケール",
                actual=f"生成側は参照と異なる比率／体積（IoU = {rec.get('iou', 'N/A')}）",
                confidence="high",
                location_hint=None,
                dimension_hint=None,
            )
            current_discrepancies = (synthetic, *v_result.discrepancies)
        else:
            current_discrepancies = v_result.discrepancies
        iteration_history = []
        import cadquery as cq

        for it in range(1, loop_iters + 1):
            # Corrector を呼ぶ（text-based; correct_script は画像も受ける）
            try:
                corrected_script = sg.correct_script(
                    current_script,
                    current_discrepancies,
                    blueprint_image_path=str(drawing_path),
                    line_views=line_views,
                    shaded_views=shaded_views,
                )
            except Exception as e:
                rec["loop_history"].append({
                    "iter": it,
                    "error": f"correct_script: {type(e).__name__}: {str(e)[:80]}",
                })
                break

            # 再実行
            iter_stl = work_dir / f"{obj_id}_iter{it}.stl"
            iter_step = work_dir / f"{obj_id}_iter{it}.step"
            try:
                ns2: dict = {}
                exec(corrected_script.content, ns2)
                r2 = ns2.get("result") or ns2.get("part")
                if r2 is None:
                    rec["loop_history"].append({"iter": it, "error": "no result/part"})
                    break
                cq.exporters.export(r2, str(iter_stl))
                cq.exporters.export(r2, str(iter_step))
            except Exception as e:
                rec["loop_history"].append({
                    "iter": it,
                    "error": f"execute: {type(e).__name__}: {str(e)[:80]}",
                })
                break

            # 再 verify
            try:
                iter_line = line_renderer.render(str(iter_step))
                iter_shaded = shaded_renderer.render(str(iter_stl)) if shaded_renderer else iter_line
                iter_v = verifier.verify(
                    blueprint_image_path=str(drawing_path),
                    line_views=iter_line,
                    shaded_views=iter_shaded,
                )
            except Exception as e:
                rec["loop_history"].append({
                    "iter": it,
                    "error": f"verify: {type(e).__name__}: {str(e)[:80]}",
                })
                break

            # メトリクスも再計算
            try:
                iter_metrics = _compute_shape_metrics(str(gt_stl), str(iter_stl))
            except Exception:
                iter_metrics = {}

            iter_summary = {
                "iter": it,
                "critical": iter_v.critical_count(),
                "major": iter_v.major_count(),
                "minor": iter_v.minor_count(),
                "match_score": iter_metrics.get("match_score"),
                "iou": iter_metrics.get("iou"),
                "chamfer": iter_metrics.get("chamfer"),
            }
            rec["loop_history"].append(iter_summary)

            # best 判定: critical 少ない方優先、同値なら match_score 高い方
            cur_match = iter_metrics.get("match_score") or 0
            best_match = best_state.get("match_score") or 0
            is_better = (
                iter_v.critical_count() < best_state["critical"]
                or (iter_v.critical_count() == best_state["critical"] and cur_match > best_match)
            )
            if is_better:
                best_state = {
                    "script": corrected_script,
                    "stl_path": str(iter_stl),
                    "step_path": str(iter_step),
                    "critical": iter_v.critical_count(),
                    "major": iter_v.major_count(),
                    "minor": iter_v.minor_count(),
                    "match_score": iter_metrics.get("match_score"),
                    "iter": it,
                }

            # 早期終了: critical=0 かつ match_score >= threshold
            iter_match = iter_metrics.get("match_score")
            if iter_v.critical_count() == 0 and (
                not isinstance(iter_match, float) or iter_match >= match_threshold
            ):
                break

            current_script = corrected_script
            # 次イテレーション用の Discrepancies を組み立て（合成形状フィードバックを再注入）
            if iter_v.critical_count() == 0 and isinstance(iter_match, float) and iter_match < match_threshold:
                syn2 = _Disc(
                    feature_type="outline",
                    severity="critical",
                    description=(
                        f"全体形状が参照とまだ一致していません（match_score = {iter_match:.2f}, "
                        f"前回 = {initial_match if initial_match is not None else 'N/A'}）。"
                        "別アプローチで作り直してください。"
                    ),
                    expected="参照図面と同じ全体形状",
                    actual=f"match_score = {iter_match:.2f}",
                    confidence="high",
                    location_hint=None,
                    dimension_hint=None,
                )
                current_discrepancies = (syn2, *iter_v.discrepancies)
            else:
                current_discrepancies = iter_v.discrepancies

        # 最終的に best iteration の指標を rec に上書き
        if best_state["iter"] > 0:
            rec["best_iter"] = best_state["iter"]
            rec["verify_critical"] = best_state["critical"]
            rec["verify_major"] = best_state["major"]
            rec["verify_minor"] = best_state["minor"]
            rec["verify_is_valid"] = (best_state["critical"] == 0)
            # 最終 STL で shape メトリクスを再計算
            try:
                final_metrics = _compute_shape_metrics(str(gt_stl), best_state["stl_path"])
                rec.update(final_metrics)
            except Exception:
                pass

    rec["elapsed"] = round(time.time() - started, 2)
    return rec


def run_for_model(model: str, entries: list[Path], out_dir: Path,
                  verifier=None, line_renderer=None, shaded_renderer=None,
                  loop_iters: int = 0, match_threshold: float = 0.8) -> dict:
    """1 モデルで N サンプル走らせ、結果を集計して保存する。

    Reference Code RAG リーク防止: 評価対象の全 entry ID を retriever に渡して exclude。
    """
    print(f"\n=== model: {model} (N={len(entries)}, "
          f"loop_iters={loop_iters}, match_threshold={match_threshold}) ===")
    exclude_ids = {p.name for p in entries}
    analyzer, sg = _build_components(model, exclude_ids=exclude_ids)

    work_dir = out_dir / "work" / model.replace("/", "_")
    work_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for i, entry in enumerate(entries, 1):
        try:
            rec = run_one(entry, analyzer, sg, work_dir,
                          verifier=verifier,
                          line_renderer=line_renderer,
                          shaded_renderer=shaded_renderer,
                          loop_iters=loop_iters,
                          match_threshold=match_threshold)
        except Exception as e:
            print(f"  [{i}/{len(entries)}] {entry.name} FAIL: {type(e).__name__}: {str(e)[:80]}")
            traceback.print_exc()
            continue
        results.append(rec)
        ok = "OK" if rec.get("compile_ok") else "FAIL"
        cd = rec.get("chamfer")
        cd_str = f"chamfer={cd:.4f}" if isinstance(cd, float) else "chamfer=N/A"
        ms = rec.get("match_score")
        ms_str = f"match={ms:.3f}" if isinstance(ms, float) and not np.isnan(ms) else "match=N/A"
        print(f"  [{i}/{len(entries)}] {rec['id']} {ok} {cd_str} {ms_str} ({rec['elapsed']}s)")
        # 中間保存
        (out_dir / f"{model}.partial.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # 集計
    n = len(results)
    compile_ok = sum(1 for r in results if r.get("compile_ok"))
    chamfers = [r["chamfer"] for r in results if isinstance(r.get("chamfer"), float)]
    chamfers_raw = [r["chamfer_raw"] for r in results if isinstance(r.get("chamfer_raw"), float)]
    ious = [r["iou"] for r in results if isinstance(r.get("iou"), float) and not np.isnan(r["iou"])]
    match_scores = [r["match_score"] for r in results if isinstance(r.get("match_score"), float) and not np.isnan(r["match_score"])]
    crits = [r["verify_critical"] for r in results if isinstance(r.get("verify_critical"), int)]
    majors = [r["verify_major"] for r in results if isinstance(r.get("verify_major"), int)]
    minors = [r["verify_minor"] for r in results if isinstance(r.get("verify_minor"), int)]
    valids = sum(1 for r in results if r.get("verify_is_valid") is True)

    summary = {
        "model": model,
        "n": n,
        "compile_rate": (100 * compile_ok / n) if n else 0.0,
        "compile_ok_count": compile_ok,
        "chamfer_mean": statistics.mean(chamfers) if chamfers else None,
        "chamfer_median": statistics.median(chamfers) if chamfers else None,
        "chamfer_raw_mean": statistics.mean(chamfers_raw) if chamfers_raw else None,
        "iou_mean": statistics.mean(ious) if ious else None,
        "iou_median": statistics.median(ious) if ious else None,
        # 全体一致スコア（完全一致 = 1, 別物 = 0、絶対スケール + 整列後の Volume IoU）
        "match_score_mean": statistics.mean(match_scores) if match_scores else None,
        "match_score_median": statistics.median(match_scores) if match_scores else None,
        "match_score_ge_0_95": (sum(1 for s in match_scores if s >= 0.95) / len(match_scores))
                              if match_scores else None,
        "match_score_ge_0_80": (sum(1 for s in match_scores if s >= 0.80) / len(match_scores))
                              if match_scores else None,
        "verify_critical_mean": statistics.mean(crits) if crits else None,
        "verify_major_mean": statistics.mean(majors) if majors else None,
        "verify_minor_mean": statistics.mean(minors) if minors else None,
        "verify_valid_rate": (100 * valids / len(crits)) if crits else None,
        "verify_n": len(crits),
    }

    # 保存
    (out_dir / f"{model}.results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / f"{model}.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  >> {model}: compile={summary['compile_rate']:.1f}% "
          f"chamfer={summary['chamfer_mean'] or 'N/A'} iou={summary['iou_mean'] or 'N/A'}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", default="dataset_v1",
                        help="experiments/deepcad/<name>/ 内のデータセット")
    parser.add_argument("-n", "--num-samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--models", required=True,
                        help="カンマ区切りモデル名（例: claude-opus-4-6,gpt-5,gpt-5.5）")
    parser.add_argument("--output-name", default="model_compare_v1",
                        help="experiments/deepcad/<output-name>/ に保存")
    parser.add_argument("--verifier-model", default="claude-sonnet-4-6",
                        help="固定 verifier モデル（critical_count 取得用）。"
                             "None / 'off' で verify をスキップ")
    parser.add_argument("--ids", default=None,
                        help="特定 ID リスト（カンマ区切り）。指定時は -n / --seed 無視")
    parser.add_argument("--ids-file", default=None,
                        help="ID リストを JSON 配列で含むファイルパス。"
                             "--ids と排他")
    parser.add_argument("--loop-iters", type=int, default=0,
                        help="verify→correct のループ最大反復数（0 で無効）。"
                             "critical > 0 または match_score < threshold で反復")
    parser.add_argument("--match-threshold", type=float, default=0.8,
                        help="ループ継続の match_score 閾値（default 0.8）")
    args = parser.parse_args()

    dataset_dir = EXPERIMENT_DIR / args.dataset_name
    if not (dataset_dir / "manifest.json").exists():
        print(f"[!] no manifest at {dataset_dir}")
        return 1

    manifest = json.loads((dataset_dir / "manifest.json").read_text())
    all_entries = [dataset_dir / e["path"] for e in manifest["entries"]]
    by_id = {p.name: p for p in all_entries}

    # サンプリング: --ids / --ids-file 優先、それ以外は seed ランダム
    explicit_ids: list[str] | None = None
    if args.ids:
        explicit_ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    elif args.ids_file:
        ids_path = Path(args.ids_file)
        if not ids_path.exists():
            print(f"[!] --ids-file not found: {ids_path}")
            return 1
        explicit_ids = json.loads(ids_path.read_text())
        if not isinstance(explicit_ids, list):
            print("[!] --ids-file must contain a JSON array")
            return 1

    if explicit_ids:
        entries = []
        missing = []
        for s in explicit_ids:
            if s in by_id:
                entries.append(by_id[s])
            else:
                missing.append(s)
        if missing:
            print(f"[!] {len(missing)} ids not found in dataset: {missing[:5]}...")
        entries.sort(key=lambda p: p.name)
    else:
        import random
        rng = random.Random(args.seed)
        entries = sorted(rng.sample(all_entries, min(args.num_samples, len(all_entries))))

    out_dir = EXPERIMENT_DIR / args.output_name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "selected_ids.json").write_text(
        json.dumps([p.name for p in entries], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    print(f"=== model_comparison: {len(models)} models × N={len(entries)} ===")
    print(f"models: {models}")
    print(f"output: {out_dir}")
    print(f"verifier: {args.verifier_model}\n")

    # 固定 verifier + renderer をセットアップ（verify_off の場合は None）
    verifier = None
    line_renderer = None
    shaded_renderer = None
    if args.verifier_model and args.verifier_model.lower() not in ("off", "none", ""):
        verifier = _build_verifier(args.verifier_model)
        line_renderer, shaded_renderer = _build_renderers()

    summaries: list[dict] = []
    for model in models:
        try:
            s = run_for_model(model, entries, out_dir,
                              verifier=verifier,
                              line_renderer=line_renderer,
                              shaded_renderer=shaded_renderer,
                              loop_iters=args.loop_iters,
                              match_threshold=args.match_threshold)
            summaries.append(s)
        except Exception as e:
            print(f"\n[!] model {model} aborted: {type(e).__name__}: {e}")
            traceback.print_exc()

    # 全体サマリ表示
    print("\n" + "=" * 100)
    print(f"=== Final Comparison (N={len(entries)}) ===\n")
    header = f"{'model':<22}{'compile':>10}{'match':>10}{'≥0.95':>8}{'≥0.80':>8}{'chamfer':>10}{'iou':>8}{'crit':>7}{'valid':>7}"
    print(header)
    print("-" * 110)
    for s in summaries:
        match = f"{s['match_score_mean']:.3f}" if s.get("match_score_mean") is not None else "N/A"
        ge95 = f"{100*s['match_score_ge_0_95']:.0f}%" if s.get("match_score_ge_0_95") is not None else "N/A"
        ge80 = f"{100*s['match_score_ge_0_80']:.0f}%" if s.get("match_score_ge_0_80") is not None else "N/A"
        cd = f"{s['chamfer_mean']:.4f}" if s.get("chamfer_mean") else "N/A"
        iou = f"{s['iou_mean']:.3f}" if s.get("iou_mean") else "N/A"
        crit = f"{s['verify_critical_mean']:.2f}" if s.get("verify_critical_mean") is not None else "N/A"
        valid = f"{s['verify_valid_rate']:.0f}%" if s.get("verify_valid_rate") is not None else "N/A"
        print(f"{s['model']:<22}{s['compile_rate']:>9.1f}%{match:>10}{ge95:>8}{ge80:>8}{cd:>10}{iou:>8}{crit:>7}{valid:>7}")

    (out_dir / "comparison.json").write_text(
        json.dumps({"n": len(entries), "summaries": summaries},
                   ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[*] saved to {out_dir / 'comparison.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
