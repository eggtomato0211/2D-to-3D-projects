はじめに — CadQuery Documentation























-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-








-

- はじめに

-









# はじめに

## CadQueryとは

CadQueryは、パラメトリック3 D CADモデルを構築するための、直感的で使いやすいPythonライブラリです。次のような目標があります。

-

すでに確立されている標準的なプログラミング言語を使用して、オブジェクトを人間に説明する方法に可能な限り近いスクリプトでモデルを構築します。

-

エンドユーザが非常に簡単にカスタマイズできるパラメトリックモデルを作成します

-

従来のSTL形式に加えて、STEPやAMFと3MFなどの高品質なCAD形式を出力します。

-

Webブラウザのみで編集および実行できる、独自仕様ではないプレーン・テキスト・モデル・フォーマットを提供します。

CadQuery2はオープンソースの OpenCascade モデリングカーネル用のPythonバインディングのセットである OCP に基づいています。

CadQueryを使用すると、非常に少ないコード量で完全なパラメトリックモデルを構築することができます。例えば、このシンプルなスクリプトは、中央に穴の開いた平板を作成します。

```python
thickness = 0.5
width = 2.0
result = Workplane("front").box(width, width, thickness).faces(">Z").hole(thickness)

```

これはちょっとディキシーカップ的な例ですね。しかし、より有用な部品である、標準的な608サイズのボールベアリング用のパラメトリック・ピローブロックに非常によく似ています:

```python
(length, height, diam, thickness, padding) = (30.0, 40.0, 22.0, 10.0, 8.0)

result = (
    Workplane("XY")
    .box(length, height, thickness)
    .faces(">Z")
    .workplane()
    .hole(diam)
    .faces(">Z")
    .workplane()
    .rect(length - padding, height - padding, forConstruction=True)
    .vertices()
    .cboreHole(2.4, 4.4, 2.1)
)

```

さらに多くのサンプルが Examples にあります。

## CadQueryはライブラリ、GUIは別物

CadQueryは、意図的にGUIレスで使用できるように設計されたライブラリです。これにより、プログラムで3Dモデルを作成する様々なエンジニアリングや科学的なアプリケーションで使用することができます。

GUIを希望する場合、いくつかの選択肢があります:

-

QtベースのGUI CQ-editor

-

Jupyter 拡張機能として jupyter-cadquery

## なぜOpenSCADではなくCadQueryなのか？

OpenSCADと同様に、CadQueryはオープンソースのスクリプトベースのパラメトリックモデルジェネレータです。しかし、CadQueryにはいくつかの重要な利点があります。

-

スクリプトは標準的なプログラミング言語 であるPythonを使用しているため、関連するインフラストラクチャの恩恵を受けることができます。これには多くの標準的なライブラリやIDEが含まれます。

-

より強力なCADカーネル OpenCascadeは、CGALよりはるかに強力です。OCCがネイティブにサポートする機能は、CGALがサポートする標準的なCSG操作に加え、NURBS、スプライン、サーフェス縫製、STL修復、STEPインポート/エクスポート、その他の複雑な操作などです。

-

STEPとDXFのインポート/エクスポート機能 CADパッケージで作成したSTEPモデルから始めて、パラメトリックな機能を追加できることが重要だと考えています。 OpenSCADではSTLを使えば可能ですが、STLはロッシーフォーマットです。

-

少ないコードと簡単なスクリプト CadQueryスクリプトは、他のフィーチャー、ワークプレーン、頂点などの位置に基づいてフィーチャーを配置することができるため、ほとんどのオブジェクトを作成するのに少ないコードしか必要としません。

-

より良いパフォーマンス CadQueryスクリプトは、OpenSCADよりも速くSTL、STEP、AMF、3MFを構築することができます。

## CadQueryの名前の由来は？

CadQueryは、JavaScriptを使ったWeb開発に革命を起こした人気のフレームワーク、 jQuery にインスパイアされています。

CadQueryは3D CADのためのものであり、JavaScriptのためのjQueryです。jQueryの動作に詳しい方なら、CadQueryが使っているいくつかのjQueryの機能にお気づきでしょう。

-

クリーンで読みやすいコードを作成するための流暢なAPI

-

他のPythonライブラリと並行して使用することが可能

-

明確で完全なドキュメント、豊富なサンプル。