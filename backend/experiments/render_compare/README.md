# Render comparison — 4 方式の目視評価

Phase 2 設計案 §4.1 で挙げた 4 方式のレンダラを実装し、同一テストモデルに対して
4 視点（top / front / side / iso）の画像を生成して目視比較する。

## 4 方式

| Slug | 実装 | 特徴 |
|---|---|---|
| `A_trimesh_pyrender` | `method_a_trimesh_pyrender.py` | 影付き、軽量、OSMesa headless |
| `B_vedo` | `method_b_vedo.py` | VTK 系、API シンプル |
| `C_open3d` | `method_c_open3d.py` | 高品質、パッケージ大 |
| `D_cadquery_svg` | `method_d_cadquery_svg.py` | 線画、CadQuery 直結、GL 不要 |

## 実行

```bash
# プロジェクトルートから
docker compose --profile render-compare run --rm render-compare
```

初回は `Dockerfile.render-compare` のビルド（5〜10 分）が走る。Open3D の
ダウンロードがあるため時間がかかる。

## 出力

```
backend/experiments/render_compare/output/
├── input.stl                         # テストモデル (CadQuery で生成)
├── A_trimesh_pyrender/{top,front,side,iso}.png
├── B_vedo/{top,front,side,iso}.png
├── C_open3d/{top,front,side,iso}.png
├── D_cadquery_svg/{top,front,side,iso}.{svg,png}
└── summary.html                      # 一覧比較ページ
```

ホスト側から開く:

```bash
open backend/experiments/render_compare/output/summary.html
```

失敗した方式があっても他は動くよう orchestrator が握り潰すので、まずは
`summary.html` で全体を確認する。

## テストモデル

`shared.py` の `TEST_MODEL_SCRIPT` に CadQuery スクリプトとして定義:

- 80×50×20 のブロック
- 上面に φ12 と φ6×2 の貫通穴
- Z 平行エッジに R3 フィレット
- 上下端エッジに C0.5 面取り

複雑な特徴（フィレット・面取り・複数穴）を含むので、各方式がエッジや陰影を
どう表現するかを比較しやすい。

## カメラ規約

`shared.py` の `VIEWS` に定義。第三角法に準拠:

| view | カメラ位置 | 投影 |
|---|---|---|
| top | +Z | orthographic |
| front | -Y | orthographic |
| side | +X | orthographic |
| iso | (+1,-1,+1) 方向 | perspective (yfov=35°) |

## Phase 2 への接続

採用した方式の `render(stl_path, out_dir)` シグネチャをそのまま `infrastructure/rendering/`
配下に移し、`IFourViewRenderer` の実装として登録する想定。
