CadQueryクラスの概要 — CadQuery Documentation























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








-

- CadQueryクラスの概要

-









# CadQueryクラスの概要

このページでは、CadQuery クラスのすべてのメソッドと関数について、アルファベット順に整理して説明しています。

参考

機能分野別の一覧は、 API Reference をご覧ください。

## コアクラス

`Sketch`(parent, locs, obj)

2Dスケッチ。

`Workplane`(, obj=None))

2次元座標を使用できる空間上の座標系を定義します。

`Assembly`([obj, loc, name, color, material, ...])

WorkplaneとShapeオブジェクトの相対的な位置を定義するネストされたアセンブリ。

`Constraint`

:py:class:`~cadquery.occ_impl.solver.ConstraintSpec`の別名です。

## トポロジカルクラス

`Shape`(obj)

システム内の形状を表します。

`Vertex`(obj[, forConstruction])

空間の中の一点

`Edge`(obj)

面の境界を表すトリミングされた曲線

`cadquery.occ_impl.shapes.Mixin1D`()

`Wire`(obj)

接続され、順序付けられた一連のEdgeで、通常、Faceを囲みます。

`Face`(obj)

固体の境界の一部を表す有界面

`Shell`(obj)

サーフェスの外側の境界線

`cadquery.occ_impl.shapes.Mixin3D`()

`Solid`(obj)

単体

`Compound`(obj)

切断された固体の集合体

## ジオメトリークラス

`Vector`()

3次元ベクトルを作成する

`Matrix`()

3d , 4x4 の変換行列。

`Plane`(origin[, xDir, normal])

空間における2次元座標系

`Location`(t)

3D空間での位置。

## セレクタクラス

`Selector`()

オブジェクトのリストにフィルタをかける。

`NearestToPointSelector`(pnt)

指定された点に最も近いオブジェクトを選択します。

`BoxSelector`(point0, point1[, boundingbox])

2点で定義された3Dボックス内のオブジェクトを選択します。

`BaseDirSelector`(vector[, tolerance])

単一の方向ベクトルに基づく選択を処理するセレクタ。

`ParallelDirSelector`(vector[, tolerance])

指定した方向と平行なオブジェクトを選択します。

`DirectionSelector`(vector[, tolerance])

指定した方向に並んだオブジェクトを選択します。

`PerpendicularDirSelector`(vector[, tolerance])

指定した方向と直交するオブジェクトを選択します。

`TypeSelector`(typeString)

所定のジオメトリタイプを持つオブジェクトを選択します。

`RadiusNthSelector`(n[, directionMax, tolerance])

N 番目の半径を持つオブジェクトを選択します。

`CenterNthSelector`(vector, n[, directionMax, ...])

オブジェクトを、指定された方向に投影された中心からの距離によって決まる順序でリストにソートします。

`DirectionMinMaxSelector`(vector[, ...])

指定した方向に最も近い、または最も遠いオブジェクトを選択します。

`DirectionNthSelector`(vector, n[, ...])

Filters for objects parallel (or normal) to the specified direction then returns the Nth one.

`LengthNthSelector`(n[, directionMax, tolerance])

Select the object(s) with the Nth length

`AreaNthSelector`(n[, directionMax, tolerance])

Selects the object(s) with Nth area

`BinarySelector`(left, right)

Base class for selectors that operates with two other selectors.

`AndSelector`(left, right)

Intersection selector.

`SumSelector`(left, right)

Union selector.

`SubtractSelector`(left, right)

Difference selector.

`InverseSelector`(selector)

Inverts the selection of given selector.

`StringSyntaxSelector`(selectorString)

Filter lists objects using a simple string syntax.

## Class Details

class cadquery.Assembly(obj: Optional[Union[Shape, Workplane]] = None, loc: Optional[Location] = None, name: Optional[str] = None, color: Optional[Color] = None, material: Optional[Material] = None, metadata: Optional[Dict[str, Any]] = None)[ソース]

ベースクラス: `object`

WorkplaneとShapeオブジェクトの相対的な位置を定義するネストされたアセンブリ。

パラメータ:

-

obj (Optional[Union[Shape, Workplane]]) --

-

loc (Location) --

-

name (str) --

-

color (Optional[Color]) --

-

material (Optional[Material]) --

-

metadata (Dict[str, Any]) --

__dir__()[ソース]

Modified __dir__ for autocompletion.

__getattr__(name: str) → Union[Assembly, Shape][ソース]

. based access to children.

パラメータ:

name (str) --

戻り値の型:

Union[Assembly, Shape]

__getitem__(name: str) → Union[Assembly, Shape][ソース]

[] based access to children.

パラメータ:

name (str) --

戻り値の型:

Union[Assembly, Shape]

__getstate__()[ソース]

Explicit getstate needed due to getattr.

__init__(obj: Optional[Union[Shape, Workplane]] = None, loc: Optional[Location] = None, name: Optional[str] = None, color: Optional[Color] = None, material: Optional[Material] = None, metadata: Optional[Dict[str, Any]] = None)[ソース]

construct an assembly

パラメータ:

-

obj (Optional[Union[Shape, Workplane]]) -- root object of the assembly (default: None)

-

loc (Optional[Location]) -- location of the root object (default: None, interpreted as identity transformation)

-

name (Optional[str]) -- unique name of the root object (default: None, resulting in an UUID being generated)

-

color (Optional[Color]) -- color of the added object (default: None)

-

material (Optional[Material]) -- material (for visual and/or physical properties) of the added object (default: None)

-

metadata (Optional[Dict[str, Any]]) -- a store for user-defined metadata (default: None)

戻り値:

An Assembly object.

To create an empty assembly use:

```python
assy = Assembly(None)

```

To create one constraint a root object:

```python
b = Workplane().box(1, 1, 1)
assy = Assembly(b, Location(Vector(0, 0, 1)), name="root")

```

__iter__(loc: Optional[Location] = None, name: Optional[str] = None, color: Optional[Color] = None) → Iterator[Tuple[Shape, str, Location, Optional[Color]]][ソース]

Assembly iterator yielding shapes, names, locations and colors.

パラメータ:

-

loc (Optional[Location]) --

-

name (Optional[str]) --

-

color (Optional[Color]) --

戻り値の型:

Iterator[Tuple[Shape, str, Location, Optional[Color]]]

__setstate__(d)[ソース]

Explicit setstate needed due to getattr.

__weakref__

list of weak references to the object (if defined)

add(obj: Assembly, loc: Optional[Location] = None, name: Optional[str] = None, color: Optional[Color] = None, material: Optional[Union[Material, str]] = None) → Self[ソース]

add(obj: Optional[Union[Shape, Workplane]], loc: Optional[Location] = None, name: Optional[str] = None, color: Optional[Color] = None, material: Optional[Union[Material, str]] = None, metadata: Optional[Dict[str, Any]] = None) → Self

Add a subassembly to the current assembly.

addSubshape(s: Shape, name: Optional[str] = None, color: Optional[Color] = None, layer: Optional[str] = None) → Assembly[ソース]

Handles name, color and layer metadata for subshapes.

パラメータ:

-

s (Shape) -- The subshape to add metadata to.

-

name (Optional[str]) -- The name to assign to the subshape.

-

color (Optional[Color]) -- The color to assign to the subshape.

-

layer (Optional[str]) -- The layer to assign to the subshape.

戻り値:

The modified assembly.

戻り値の型:

Assembly

constrain(q1: str, q2: str, kind: Literal['Plane', 'Point', 'Axis', 'PointInPlane', 'Fixed', 'FixedPoint', 'FixedAxis', 'PointOnLine', 'FixedRotation'], param: Any = None) → Self[ソース]

constrain(q1: str, kind: Literal['Plane', 'Point', 'Axis', 'PointInPlane', 'Fixed', 'FixedPoint', 'FixedAxis', 'PointOnLine', 'FixedRotation'], param: Any = None) → Self

constrain(id1: str, s1: Shape, id2: str, s2: Shape, kind: Literal['Plane', 'Point', 'Axis', 'PointInPlane', 'Fixed', 'FixedPoint', 'FixedAxis', 'PointOnLine', 'FixedRotation'], param: Any = None) → Self

constrain(id1: str, s1: Shape, kind: Literal['Plane', 'Point', 'Axis', 'PointInPlane', 'Fixed', 'FixedPoint', 'FixedAxis', 'PointOnLine', 'FixedRotation'], param: Any = None) → Self

Define a new constraint.

export(path: str, exportType: Optional[Literal['STEP', 'XML', 'XBF', 'GLTF', 'VTKJS', 'VRML', 'STL']] = None, mode: Literal['default', 'fused'] = 'default', tolerance: float = 0.1, angularTolerance: float = 0.1, **kwargs) → Self[ソース]

Save assembly to a file.

パラメータ:

-

path (str) -- Path and filename for writing.

-

exportType (Optional[Literal['STEP', 'XML', 'XBF', 'GLTF', 'VTKJS', 'VRML', 'STL']]) -- export format (default: None, results in format being inferred form the path)

-

mode (Literal['default', 'fused']) -- STEP only - See `exportAssembly()`.

-

tolerance (float) -- the deflection tolerance, in model units. Only used for glTF, VRML. Default 0.1.

-

angularTolerance (float) -- the angular tolerance, in radians. Only used for glTF, VRML. Default 0.1.

-

**kwargs -- Additional keyword arguments.  Only used for STEP, glTF and STL.
See `exportAssembly()`.

-

ascii (bool) -- STL only - Sets whether or not STL export should be text or binary

戻り値の型:

Self

classmethod importStep(path: str) → Self[ソース]

Reads an assembly from a STEP file.

パラメータ:

path (str) -- Path and filename for reading.

戻り値:

An Assembly object.

戻り値の型:

Self

classmethod load(path: str, importType: Optional[Literal['STEP', 'XML', 'XBF']] = None) → Self[ソース]

Load step, xbf or xml.

パラメータ:

-

path (str) --

-

importType (Optional[Literal['STEP', 'XML', 'XBF']]) --

戻り値の型:

Self

remove(name: str) → Assembly[ソース]

Remove a part/subassembly from the current assembly.

パラメータ:

name (str) -- Name of the part/subassembly to be removed

戻り値:

The modified assembly

戻り値の型:

Assembly

NOTE This method can cause problems with deeply nested assemblies and does not remove
constraints associated with the removed part/subassembly.

save(path: str, exportType: Optional[Literal['STEP', 'XML', 'XBF', 'GLTF', 'VTKJS', 'VRML', 'STL']] = None, mode: Literal['default', 'fused'] = 'default', tolerance: float = 0.1, angularTolerance: float = 0.1, **kwargs) → Self[ソース]

Save assembly to a file.

パラメータ:

-

path (str) -- Path and filename for writing.

-

exportType (Optional[Literal['STEP', 'XML', 'XBF', 'GLTF', 'VTKJS', 'VRML', 'STL']]) -- export format (default: None, results in format being inferred form the path)

-

mode (Literal['default', 'fused']) -- STEP only - See `exportAssembly()`.

-

tolerance (float) -- the deflection tolerance, in model units. Only used for glTF, VRML. Default 0.1.

-

angularTolerance (float) -- the angular tolerance, in radians. Only used for glTF, VRML. Default 0.1.

-

**kwargs -- Additional keyword arguments.  Only used for STEP, glTF and STL.
See `exportAssembly()`.

-

ascii (bool) -- STL only - Sets whether or not STL export should be text or binary

戻り値の型:

Self

property shapes: List[Shape]

List of Shape objects in the .obj field

solve(verbosity: int = 0) → Self[ソース]

Solve the constraints.

パラメータ:

verbosity (int) --

戻り値の型:

Self

toCompound() → Compound[ソース]

Returns a Compound made from this Assembly (including all children) with the
current Locations applied. Usually this method would only be used after solving.

戻り値の型:

Compound

traverse() → Iterator[Tuple[str, Assembly]][ソース]

Yield (name, child) pairs in a bottom-up manner

戻り値の型:

Iterator[Tuple[str, Assembly]]

class cadquery.BoundBox(bb: Bnd_Box)[ソース]

ベースクラス: `object`

A BoundingBox for an object or set of objects. Wraps the OCP one

パラメータ:

bb (Bnd_Box) --

__init__(bb: Bnd_Box) → None[ソース]

パラメータ:

bb (Bnd_Box) --

戻り値の型:

None

__weakref__

list of weak references to the object (if defined)

add(obj: Union[Tuple[float, float, float], Vector, BoundBox], tol: Optional[float] = None) → BoundBox[ソース]

Returns a modified (expanded) bounding box

obj can be one of several things:

-

a 3-tuple corresponding to x,y, and z amounts to add

-

a vector, containing the x,y,z values to add

-

another bounding box, where a new box will be created that
encloses both.

This bounding box is not changed.

パラメータ:

-

obj (Union[Tuple[float, float, float], Vector, BoundBox]) --

-

tol (Optional[float]) --

戻り値の型:

BoundBox

enlarge(tol: float) → BoundBox[ソース]

Returns a modified (expanded) bounding box, expanded in all
directions by the tolerance value.

This means that the minimum values of its X, Y and Z intervals
of the bounding box are reduced by the absolute value of tol, while
the maximum values are increased by the same amount.

パラメータ:

tol (float) --

戻り値の型:

BoundBox

static findOutsideBox2D(bb1: BoundBox, bb2: BoundBox) → Optional[BoundBox][ソース]

Compares bounding boxes

Compares bounding boxes. Returns none if neither is inside the other.
Returns the outer one if either is outside the other.

BoundBox.isInside works in 3d, but this is a 2d bounding box, so it
doesn't work correctly plus, there was all kinds of rounding error in
the built-in implementation i do not understand.

パラメータ:

-

bb1 (BoundBox) --

-

bb2 (BoundBox) --

戻り値の型:

Optional[BoundBox]

isInside(b2: BoundBox) → bool[ソース]

Is the provided bounding box inside this one?

パラメータ:

b2 (BoundBox) --

戻り値の型:

bool

cadquery.CQ

:py:class:`~cadquery.cq.Workplane`の別名です。

class cadquery.Color(name: str)[ソース]

class cadquery.Color(r: float, g: float, b: float, a: float = 0, srgb: bool = True)

class cadquery.Color

ベースクラス: `object`

Wrapper for the OCCT color object Quantity_ColorRGBA.

__eq__(other)[ソース]

Return self==value.

__hash__()[ソース]

Return hash(self).

__init__(name: str)[ソース]

__init__(r: float, g: float, b: float, a: float = 0, srgb: bool = True)

__init__()

__weakref__

list of weak references to the object (if defined)

toTuple() → Tuple[float, float, float, float][ソース]

Convert Color to RGB tuple.

戻り値の型:

Tuple[float, float, float, float]

class cadquery.Compound(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin3D`

切断された固体の集合体

パラメータ:

obj (TopoDS_Shape) --

__bool__() → bool[ソース]

Check if empty.

戻り値の型:

bool

ancestors(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) → Compound[ソース]

Iterate over ancestors, i.e. shapes of same kind within shape that contain elements of self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

戻り値の型:

Compound

cut(*toCut: Shape, tol: Optional[float] = None) → Compound[ソース]

Remove the positional arguments from this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toCut (Shape) --

戻り値の型:

Compound

fuse(*toFuse: Shape, glue: bool = False, tol: Optional[float] = None) → Compound[ソース]

Fuse shapes together

パラメータ:

-

toFuse (Shape) --

-

glue (bool) --

-

tol (Optional[float]) --

戻り値の型:

Compound

intersect(*toIntersect: Shape, tol: Optional[float] = None) → Compound[ソース]

Intersection of the positional arguments and this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toIntersect (Shape) --

戻り値の型:

Compound

classmethod makeCompound(listOfShapes: Iterable[Shape]) → Compound[ソース]

Create a compound out of a list of shapes

パラメータ:

listOfShapes (Iterable[Shape]) --

戻り値の型:

Compound

classmethod makeText(text: str, size: float, height: float, font: str = 'Arial', fontPath: Optional[str] = None, kind: Literal['regular', 'bold', 'italic'] = 'regular', halign: Literal['center', 'left', 'right'] = 'center', valign: Literal['center', 'top', 'bottom'] = 'center', position: Plane = Plane(origin=(0.0, 0.0, 0.0), xDir=(1.0, 0.0, 0.0), normal=(0.0, 0.0, 1.0))) → Shape[ソース]

Create a 3D text

パラメータ:

-

text (str) --

-

size (float) --

-

height (float) --

-

font (str) --

-

fontPath (Optional[str]) --

-

kind (Literal['regular', 'bold', 'italic']) --

-

halign (Literal['center', 'left', 'right']) --

-

valign (Literal['center', 'top', 'bottom']) --

-

position (Plane) --

戻り値の型:

Shape

remove(*shape: Shape)[ソース]

Remove the specified shapes.

パラメータ:

shape (Shape) --

siblings(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound'], level: int = 1) → Compound[ソース]

Iterate over siblings, i.e. shapes within shape that share subshapes of kind with the elements of self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

-

level (int) --

戻り値の型:

Compound

cadquery.Constraint

:py:class:`~cadquery.occ_impl.solver.ConstraintSpec`の別名です。

class cadquery.DirectionMinMaxSelector(vector: Vector, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `CenterNthSelector`

指定した方向に最も近い、または最も遠いオブジェクトを選択します。

Applicability:

All object types. for a vertex, its point is used. for all other kinds
of objects, the center of mass of the object is used.

You can use the string shortcuts >(X|Y|Z) or <(X|Y|Z) if you want to select
based on a cardinal direction.

For example this:

```python
CQ(aCube).faces(DirectionMinMaxSelector((0, 0, 1), True))

```

Means to select the face having the center of mass farthest in the positive
z direction, and is the same as:

```python
CQ(aCube).faces(">Z")

```

パラメータ:

-

vector (Vector) --

-

directionMax (bool) --

-

tolerance (float) --

__init__(vector: Vector, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

パラメータ:

-

vector (Vector) --

-

directionMax (bool) --

-

tolerance (float) --

class cadquery.DirectionSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `BaseDirSelector`

指定した方向に並んだオブジェクトを選択します。

Applicability:

Linear Edges
Planar Faces

Use the string syntax shortcut +/-(X|Y|Z) if you want to select based on a cardinal direction.

Example:

```python
CQ(aCube).faces(DirectionSelector((0, 0, 1)))

```

selects faces with the normal in the z direction, and is equivalent to:

```python
CQ(aCube).faces("+Z")

```

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.Edge(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin1D`

面の境界を表すトリミングされた曲線

パラメータ:

obj (TopoDS_Shape) --

arcCenter() → Vector[ソース]

Center of an underlying circle or ellipse geometry.

戻り値の型:

Vector

close() → Union[Edge, Wire][ソース]

Close an Edge

戻り値の型:

Union[Edge, Wire]

hasPCurve(f: Face) → bool[ソース]

Check if self has a pcurve defined on f.

パラメータ:

f (Face) --

戻り値の型:

bool

classmethod makeBezier(points: List[Vector]) → Edge[ソース]

Create a cubic Bézier Curve from the points.

パラメータ:

points (List[Vector]) -- a list of Vectors that represent the points.
The edge will pass through the first and the last point,
and the inner points are Bézier control points.

戻り値:

An edge

戻り値の型:

Edge

classmethod makeEllipse(x_radius: float, y_radius: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), xdir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (1.0, 0.0, 0.0), angle1: float = 360.0, angle2: float = 360.0, sense: ~typing.Literal[-1, 1] = 1) → Edge[ソース]

Makes an Ellipse centered at the provided point, having normal in the provided direction.

パラメータ:

-

cls --

-

x_radius (float) -- x radius of the ellipse (along the x-axis of plane the ellipse should lie in)

-

y_radius (float) -- y radius of the ellipse (along the y-axis of plane the ellipse should lie in)

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the center of the ellipse

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the direction of the plane the ellipse should lie in

-

angle1 (float) -- start angle of arc

-

angle2 (float) -- end angle of arc (angle2 == angle1 return closed ellipse = default)

-

sense (Literal[-1, 1]) -- clockwise (-1) or counter clockwise (1)

-

xdir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値:

an Edge

戻り値の型:

Edge

classmethod makeLine(v1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Edge[ソース]

Create a line between two points

パラメータ:

-

v1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Vector that represents the first point

-

v2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Vector that represents the second point

戻り値:

A linear edge between the two provided points

戻り値の型:

Edge

classmethod makeSpline(listOfVector: List[Vector], tangents: Optional[Sequence[Vector]] = None, periodic: bool = False, parameters: Optional[Sequence[float]] = None, scale: bool = True, tol: float = 1e-06) → Edge[ソース]

Interpolate a spline through the provided points.

パラメータ:

-

listOfVector (List[Vector]) -- a list of Vectors that represent the points

-

tangents (Optional[Sequence[Vector]]) -- tuple of Vectors specifying start and finish tangent

-

periodic (bool) -- creation of periodic curves

-

parameters (Optional[Sequence[float]]) -- the value of the parameter at each interpolation point. (The interpolated
curve is represented as a vector-valued function of a scalar parameter.) If periodic ==
True, then len(parameters) must be len(intepolation points) + 1, otherwise len(parameters)
must be equal to len(interpolation points).

-

scale (bool) -- whether to scale the specified tangent vectors before interpolating. Each
tangent is scaled, so it's length is equal to the derivative of the Lagrange interpolated
curve. I.e., set this to True, if you want to use only the direction of the tangent
vectors specified by `tangents`, but not their magnitude.

-

tol (float) -- tolerance of the algorithm (consult OCC documentation). Used to check that the
specified points are not too close to each other, and that tangent vectors are not too
short. (In either case interpolation may fail.)

戻り値:

an Edge

戻り値の型:

Edge

classmethod makeSplineApprox(listOfVector: List[Vector], tol: float = 0.001, smoothing: Optional[Tuple[float, float, float]] = None, minDeg: int = 1, maxDeg: int = 6) → Edge[ソース]

Approximate a spline through the provided points.

パラメータ:

-

listOfVector (List[Vector]) -- a list of Vectors that represent the points

-

tol (float) -- tolerance of the algorithm (consult OCC documentation).

-

smoothing (Optional[Tuple[float, float, float]]) -- optional tuple of 3 weights use for variational smoothing (default: None)

-

minDeg (int) -- minimum spline degree. Enforced only when smothing is None (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 6)

戻り値:

an Edge

戻り値の型:

Edge

classmethod makeTangentArc(v1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v3: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Edge[ソース]

Makes a tangent arc from point v1, in the direction of v2 and ends at v3.

パラメータ:

-

cls --

-

v1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- start vector

-

v2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- tangent vector

-

v3 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- end vector

戻り値:

an edge

戻り値の型:

Edge

classmethod makeThreePointArc(v1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v3: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Edge[ソース]

Makes a three point arc through the provided points

パラメータ:

-

cls --

-

v1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- start vector

-

v2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- middle vector

-

v3 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- end vector

戻り値:

an edge object through the three points

戻り値の型:

Edge

trim(u0: Union[float, int], u1: Union[float, int]) → Edge[ソース]

Trim the edge in the parametric space to (u0, u1).

NB: this operation is done on the base geometry.

パラメータ:

-

u0 (Union[float, int]) --

-

u1 (Union[float, int]) --

戻り値の型:

Edge

class cadquery.Face(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`

固体の境界の一部を表す有界面

パラメータ:

obj (TopoDS_Shape) --

Center() → Vector[ソース]

戻り値:

The point of the center of mass of this Shape

戻り値の型:

Vector

addHole(*inner: cadquery.occ_impl.shapes.Wire | cadquery.occ_impl.shapes.Edge) → Self[ソース]

Add one or more holes.

パラメータ:

inner (cadquery.occ_impl.shapes.Wire | cadquery.occ_impl.shapes.Edge) --

戻り値の型:

Self

chamfer2D(d: float, vertices: Iterable[Vertex]) → Face[ソース]

Apply 2D chamfer to a face

パラメータ:

-

d (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Face

extend(d: float, umin: bool = True, umax: bool = True, vmin: bool = True, vmax: bool = True) → Face[ソース]

Extend a face. Does not work well in periodic directions.

パラメータ:

-

d (float) -- length of the extension.

-

umin (bool) -- extend along the umin isoline.

-

umax (bool) -- extend along the umax isoline.

-

vmin (bool) -- extend along the vmin isoline.

-

vmax (bool) -- extend along the vmax isoline.

戻り値の型:

Face

fillet2D(radius: float, vertices: Iterable[Vertex]) → Face[ソース]

Apply 2D fillet to a face

パラメータ:

-

radius (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Face

isoline(param: Union[float, int], direction: Literal['u', 'v'] = 'v') → Edge[ソース]

Construct an isoline.

パラメータ:

-

param (Union[float, int]) --

-

direction (Literal['u', 'v']) --

戻り値の型:

Edge

isolines(params: Iterable[Union[float, int]], direction: Literal['u', 'v'] = 'v') → List[Edge][ソース]

Construct multiple isolines.

パラメータ:

-

params (Iterable[Union[float, int]]) --

-

direction (Literal['u', 'v']) --

戻り値の型:

List[Edge]

classmethod makeFromWires(outerWire: Wire, innerWires: List[Wire] = []) → Face[ソース]

Makes a planar face from one or more wires

パラメータ:

-

outerWire (Wire) --

-

innerWires (List[Wire]) --

戻り値の型:

Face

classmethod makeNSidedSurface(edges: ~typing.Iterable[~typing.Union[~cadquery.occ_impl.shapes.Edge, ~cadquery.occ_impl.shapes.Wire]], constraints: ~typing.Iterable[~typing.Union[~cadquery.occ_impl.shapes.Edge, ~cadquery.occ_impl.shapes.Wire, ~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]], ~OCP.gp.gp_Pnt]], continuity: ~OCP.GeomAbs.GeomAbs_Shape = <GeomAbs_Shape.GeomAbs_C0: 0>, degree: int = 3, nbPtsOnCur: int = 15, nbIter: int = 2, anisotropy: bool = False, tol2d: float = 1e-05, tol3d: float = 0.0001, tolAng: float = 0.01, tolCurv: float = 0.1, maxDeg: int = 8, maxSegments: int = 9) → Face[ソース]

Returns a surface enclosed by a closed polygon defined by 'edges' and 'constraints'.

パラメータ:

-

edges (list of edges or wires) -- edges

-

constraints (list of points or edges) -- constraints

-

continuity (GeomAbs_Shape) -- OCC.Core.GeomAbs continuity condition

-

degree (int) -- >=2

-

nbPtsOnCur (int) -- number of points on curve >= 15

-

nbIter (int) -- number of iterations >= 2

-

anisotropy (bool) -- bool Anisotropy

-

tol2d (float) -- 2D tolerance >0

-

tol3d (float) -- 3D tolerance >0

-

tolAng (float) -- angular tolerance

-

tolCurv (float) -- tolerance for curvature >0

-

maxDeg (int) -- highest polynomial degree >= 2

-

maxSegments (int) -- greatest number of segments >= 2

戻り値の型:

Face

classmethod makeRuledSurface(edgeOrWire1: Edge, edgeOrWire2: Edge) → Face[ソース]

classmethod makeRuledSurface(edgeOrWire1: Wire, edgeOrWire2: Wire) → Face

makeRuledSurface(Edge|Wire,Edge|Wire) -- Make a ruled surface
Create a ruled surface out of two edges or wires. If wires are used then
these must have the same number of edges

classmethod makeSplineApprox(points: List[List[Vector]], tol: float = 0.01, smoothing: Optional[Tuple[float, float, float]] = None, minDeg: int = 1, maxDeg: int = 3) → Face[ソース]

Approximate a spline surface through the provided points.

パラメータ:

-

points (List[List[Vector]]) -- a 2D list of Vectors that represent the points

-

tol (float) -- tolerance of the algorithm (consult OCC documentation).

-

smoothing (Optional[Tuple[float, float, float]]) -- optional tuple of 3 weights use for variational smoothing (default: None)

-

minDeg (int) -- minimum spline degree. Enforced only when smothing is None (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 6)

戻り値の型:

Face

normalAt(locationVector: Optional[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]] = None) → Vector[ソース]

normalAt(u: Union[float, int], v: Union[float, int]) → Tuple[Vector, Vector]

Computes the normal vector at the desired location on the face.

戻り値:

a vector representing the direction

パラメータ:

locationVector (a vector that lies on the surface.) -- the location to compute the normal at. If none, the center of the face is used.

戻り値の型:

Vector

Computes the normal vector at the desired location in the u,v parameter space.

戻り値:

a vector representing the normal direction and the position

パラメータ:

-

u -- the u parametric location to compute the normal at.

-

v -- the v parametric location to compute the normal at.

-

locationVector (Optional[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) --

戻り値の型:

Vector

normals(us: Iterable[Union[float, int]], vs: Iterable[Union[float, int]]) → Tuple[List[Vector], List[Vector]][ソース]

Computes the normal vectors at the desired locations in the u,v parameter space.

戻り値:

a tuple of list of vectors representing the normal directions and the positions

パラメータ:

-

us (Iterable[Union[float, int]]) -- the u parametric locations to compute the normal at.

-

vs (Iterable[Union[float, int]]) -- the v parametric locations to compute the normal at.

戻り値の型:

Tuple[List[Vector], List[Vector]]

paramAt(pt: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Tuple[float, float][ソース]

Computes the (u,v) pair closest to a given vector.

戻り値:

(u, v) tuple

パラメータ:

pt (a vector that lies on or close to the surface.) -- the location to compute the normal at.

戻り値の型:

Tuple[float, float]

params(pts: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]], tol: float = 1e-09) → Tuple[List[float], List[float]][ソース]

Computes (u,v) pairs closest to given vectors.

戻り値:

list of (u, v) tuples

パラメータ:

-

pts (a list of vectors that lie on the surface.) -- the points to compute the normals at.

-

tol (float) --

戻り値の型:

Tuple[List[float], List[float]]

positionAt(u: Union[float, int], v: Union[float, int]) → Vector[ソース]

Computes the position vector at the desired location in the u,v parameter space.

戻り値:

a vector representing the position

パラメータ:

-

u (Union[float, int]) -- the u parametric location to compute the normal at.

-

v (Union[float, int]) -- the v parametric location to compute the normal at.

戻り値の型:

Vector

positions(uvs: Iterable[Tuple[Union[int, float], Union[int, float]]]) → List[Vector][ソース]

Computes position vectors at the desired locations in the u,v parameter space.

戻り値:

list of vectors corresponding to the requested u,v positions

パラメータ:

uvs (Iterable[Tuple[Union[int, float], Union[int, float]]]) -- iterable of u,v pairs.

戻り値の型:

List[Vector]

thicken(thickness: float) → Solid[ソース]

Return a thickened face

パラメータ:

thickness (float) --

戻り値の型:

Solid

toArcs(tolerance: float = 0.001) → Face[ソース]

Approximate planar face with arcs and straight line segments.

パラメータ:

tolerance (float) -- Approximation tolerance.

戻り値の型:

Face

toPln() → gp_Pln[ソース]

Convert this face to a gp_Pln.

Note the Location of the resulting plane may not equal the center of this face,
however the resulting plane will still contain the center of this face.

戻り値の型:

gp_Pln

trim(outer: Wire, *inner: Wire) → Self[ソース]

trim(u0: Union[float, int], u1: Union[float, int], v0: Union[float, int], v1: Union[float, int], tol: Union[float, int] = 1e-06) → Self

trim(pt1: Tuple[Union[int, float], Union[int, float]], pt2: Tuple[Union[int, float], Union[int, float]], pt3: Tuple[Union[int, float], Union[int, float]], *pts: Tuple[Union[int, float], Union[int, float]]) → Self

Trim the face in the (u,v) space to (u0, u1)x(v1, v2).

NB: this operation is done on the base geometry.

Trim the face using a polyline defined in the (u,v) space.

Trim using wires. The provided wires need to have a pcurve on self.

パラメータ:

-

u0 (Union[float, int]) --

-

u1 (Union[float, int]) --

-

v0 (Union[float, int]) --

-

v1 (Union[float, int]) --

-

tol (Union[float, int]) --

戻り値の型:

Self

uvBounds() → Tuple[float, float, float, float][ソース]

Parametric bounds (u_min, u_max, v_min, v_max).

戻り値の型:

Tuple[float, float, float, float]

class cadquery.Location(t: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]])[ソース]

ベースクラス: `object`

Location in 3D space. Depending on usage can be absolute or relative.

This class wraps the TopLoc_Location class from OCCT. It can be used to move Shape
objects in both relative and absolute manner. It is the preferred type to locate objects
in CQ.

パラメータ:

t (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

__init__(t: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], ax: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angle: Union[int, float]) → None[ソース]

__init__(T: gp_Trsf) → None

__init__(t: Plane) → None

__init__(t: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angles: Tuple[Union[int, float], Union[int, float], Union[int, float]]) → None

__init__(t: Plane, v: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → None

__init__(x: Union[int, float] = 0, y: Union[int, float] = 0, z: Union[int, float] = 0, rx: Union[int, float] = 0, ry: Union[int, float] = 0, rz: Union[int, float] = 0) → None

__init__(t: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → None

__init__(T: TopLoc_Location) → None

Location with translation t with respect to the original location.

Location with translation (x,y,z) and 3 rotation angles.

Location corresponding to the location of the Plane t.

Location corresponding to the angular location of the Plane t with translation v.

Location wrapping the low-level TopLoc_Location object t

Location wrapping the low-level gp_Trsf object t

Location with translation t and rotation around ax by angle

with respect to the original location.

Location with translation t and 3 rotation angles.

パラメータ:

t (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

None

__weakref__

list of weak references to the object (if defined)

toTuple() → Tuple[Tuple[float, float, float], Tuple[float, float, float]][ソース]

Convert the location to a translation, rotation tuple.

戻り値の型:

Tuple[Tuple[float, float, float], Tuple[float, float, float]]

class cadquery.Material(name: Optional[str] = None, **kwargs)[ソース]

ベースクラス: `object`

Wrapper for the OCCT material classes XCAFDoc_Material and XCAFDoc_VisMaterial.
XCAFDoc_Material is focused on physical material properties and
XCAFDoc_VisMaterial is for visual properties to be used when rendering.

パラメータ:

name (str | None) --

__eq__(other)[ソース]

Check equality of this material against another via its tuple.

__getstate__() → Tuple[str, str, float, str][ソース]

Allows pickling.

戻り値の型:

Tuple[str, str, float, str]

__hash__()[ソース]

Create a unique hash for this material via its tuple.

__init__(name: Optional[str] = None, **kwargs)[ソース]

Can be passed an arbitrary string name for the material along with keyword
arguments defining some other characteristics of the material. If nothing is
passed, arbitrary defaults are used.

パラメータ:

name (Optional[str]) --

__setstate__(data: Tuple[str, str, float, str])[ソース]

Allows pickling.

パラメータ:

data (Tuple[str, str, float, str]) --

__weakref__

list of weak references to the object (if defined)

property density: float

Get the density value of the material.

property densityUnit: str

Get the units that the material density is defined in.

property description: str

Get the string description of the material.

property name: str

Get the string name of the material.

toTuple() → Tuple[str, str, float, str][ソース]

Convert Material to a tuple.

戻り値の型:

Tuple[str, str, float, str]

class cadquery.Matrix[ソース]

class cadquery.Matrix(matrix: Union[gp_GTrsf, gp_Trsf])

class cadquery.Matrix(matrix: Sequence[Sequence[float]])

ベースクラス: `object`

3d , 4x4 の変換行列。

Used to move geometry in space.

The provided "matrix" parameter may be None, a gp_GTrsf, or a nested list of
values.

If given a nested list, it is expected to be of the form:

[[m11, m12, m13, m14],

[m21, m22, m23, m24],
[m31, m32, m33, m34]]

A fourth row may be given, but it is expected to be: [0.0, 0.0, 0.0, 1.0]
since this is a transform matrix.

__getitem__(rc: Tuple[int, int]) → float[ソース]

Provide Matrix[r, c] syntax for accessing individual values. The row
and column parameters start at zero, which is consistent with most
python libraries, but is counter to gp_GTrsf(), which is 1-indexed.

パラメータ:

rc (Tuple[int, int]) --

戻り値の型:

float

__init__() → None[ソース]

__init__(matrix: Union[gp_GTrsf, gp_Trsf]) → None

__init__(matrix: Sequence[Sequence[float]]) → None

__repr__() → str[ソース]

Generate a valid python expression representing this Matrix

戻り値の型:

str

__weakref__

list of weak references to the object (if defined)

transposed_list() → Sequence[float][ソース]

Needed by the cqparts gltf exporter

戻り値の型:

Sequence[float]

class cadquery.NearestToPointSelector(pnt)[ソース]

ベースクラス: `Selector`

指定された点に最も近いオブジェクトを選択します。

If the object is a vertex or point, the distance
is used. For other kinds of shapes, the center of mass
is used to to compute which is closest.

Applicability: All Types of Shapes

Example:

```python
CQ(aCube).vertices(NearestToPointSelector((0, 1, 0)))

```

returns the vertex of the unit cube closest to the point x=0,y=1,z=0

__init__(pnt)[ソース]

filter(objectList: Sequence[Shape])[ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

class cadquery.ParallelDirSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `BaseDirSelector`

指定した方向と平行なオブジェクトを選択します。

Applicability:

Linear Edges
Planar Faces

Use the string syntax shortcut |(X|Y|Z) if you want to select based on a cardinal direction.

Example:

```python
CQ(aCube).faces(ParallelDirSelector((0, 0, 1)))

```

selects faces with the normal parallel to the z direction, and is equivalent to:

```python
CQ(aCube).faces("|Z")

```

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.PerpendicularDirSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `BaseDirSelector`

指定した方向と直交するオブジェクトを選択します。

Applicability:

Linear Edges
Planar Faces

Use the string syntax shortcut #(X|Y|Z) if you want to select based on a
cardinal direction.

Example:

```python
CQ(aCube).faces(PerpendicularDirSelector((0, 0, 1)))

```

selects faces with the normal perpendicular to the z direction, and is equivalent to:

```python
CQ(aCube).faces("#Z")

```

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.Plane(origin: Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector], xDir: Optional[Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]] = None, normal: Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector] = (0, 0, 1))[ソース]

ベースクラス: `object`

空間における2次元座標系

A 2D coordinate system in space, with the x-y axes on the plane, and a
particular point as the origin.

A plane allows the use of 2D coordinates, which are later converted to
global, 3d coordinates when the operations are complete.

Frequently, it is not necessary to create work planes, as they can be
created automatically from faces.

パラメータ:

-

origin (Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]) --

-

xDir (Vector) --

-

normal (Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]) --

__eq__(other)[ソース]

Return self==value.

__hash__ = None

__init__(origin: Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector], xDir: Optional[Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]] = None, normal: Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector] = (0, 0, 1))[ソース]

__init__(loc: Location)

Create a Plane from origin in global coordinates, vector xDir, and normal direction for the plane.

Create a Plane from Location loc.

パラメータ:

-

origin (Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]) --

-

xDir (Optional[Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]]) --

-

normal (Union[Tuple[Union[int, float], Union[int, float], Union[int, float]], Vector]) --

__ne__(other)[ソース]

Return self!=value.

__repr__()[ソース]

Return repr(self).

__weakref__

list of weak references to the object (if defined)

classmethod named(stdName: str, origin=(0, 0, 0)) → Plane[ソース]

Create a predefined Plane based on the conventional names.

パラメータ:

-

stdName (string) -- one of (XY|YZ|ZX|XZ|YX|ZY|front|back|left|right|top|bottom)

-

origin (3-tuple of the origin of the new plane, in global coordinates.) -- the desired origin, specified in global coordinates

戻り値の型:

Plane

Available named planes are as follows. Direction references refer to
the global directions.

Name

xDir

yDir

zDir

XY

+x

+y

+z

YZ

+y

+z

+x

ZX

+z

+x

+y

XZ

+x

+z

-y

YX

+y

+x

-z

ZY

+z

+y

-x

front

+x

+y

+z

back

-x

+y

-z

left

+z

+y

-x

right

-z

+y

+x

top

+x

-z

+y

bottom

+x

+z

-y

rotated(rotate=(0, 0, 0))[ソース]

Returns a copy of this plane, rotated about the specified axes

Since the z axis is always normal the plane, rotating around Z will
always produce a plane that is parallel to this one.

The origin of the workplane is unaffected by the rotation.

Rotations are done in order x, y, z. If you need a different order,
manually chain together multiple rotate() commands.

パラメータ:

rotate -- Vector [xDegrees, yDegrees, zDegrees]

戻り値:

a copy of this plane rotated as requested.

setOrigin2d(x, y)[ソース]

Set a new origin in the plane itself

Set a new origin in the plane itself. The plane's orientation and
xDrection are unaffected.

パラメータ:

-

x (float) -- offset in the x direction

-

y (float) -- offset in the y direction

戻り値:

void

The new coordinates are specified in terms of the current 2D system.
As an example:

p = Plane.XY()
p.setOrigin2d(2, 2)
p.setOrigin2d(2, 2)

results in a plane with its origin at (x, y) = (4, 4) in global
coordinates. Both operations were relative to local coordinates of the
plane.

toLocalCoords(obj)[ソース]

Project the provided coordinates onto this plane

パラメータ:

obj -- an object or vector to convert

戻り値:

an object of the same type, but converted to local coordinates

Most of the time, the z-coordinate returned will be zero, because most
operations based on a plane are all 2D. Occasionally, though, 3D
points outside of the current plane are transformed. One such example is
`Workplane.box()`, where 3D corners of a box are transformed to
orient the box in space correctly.

toWorldCoords(tuplePoint) → Vector[ソース]

Convert a point in local coordinates to global coordinates

パラメータ:

tuplePoint (a 2 or three tuple of float. The third value is taken to be zero if not supplied.) -- point in local coordinates to convert.

戻り値:

a Vector in global coordinates

戻り値の型:

Vector

class cadquery.Selector[ソース]

ベースクラス: `object`

オブジェクトのリストにフィルタをかける。

Filters must provide a single method that filters objects.

__weakref__

list of weak references to the object (if defined)

filter(objectList: Sequence[Shape]) → List[Shape][ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

戻り値の型:

List[Shape]

class cadquery.Shape(obj: TopoDS_Shape)[ソース]

ベースクラス: `object`

Represents a shape in the system. Wraps TopoDS_Shape.

パラメータ:

obj (TopoDS_Shape) --

Area() → float[ソース]

戻り値:

The surface area of all faces in this Shape

戻り値の型:

float

BoundingBox(tolerance: Optional[float] = None) → BoundBox[ソース]

Create a bounding box for this Shape.

パラメータ:

tolerance (Optional[float]) -- Tolerance value passed to `BoundBox`

戻り値:

A `BoundBox` object for this Shape

戻り値の型:

BoundBox

Center() → Vector[ソース]

戻り値:

The point of the center of mass of this Shape

戻り値の型:

Vector

CenterOfBoundBox(tolerance: Optional[float] = None) → Vector[ソース]

パラメータ:

tolerance (Optional[float]) -- Tolerance passed to the `BoundingBox()` method

戻り値:

Center of the bounding box of this shape

戻り値の型:

Vector

Closed() → bool[ソース]

戻り値:

The closedness flag

戻り値の型:

bool

static CombinedCenter(objects: Iterable[Shape]) → Vector[ソース]

Calculates the center of mass of multiple objects.

パラメータ:

objects (Iterable[Shape]) -- A list of objects with mass

戻り値の型:

Vector

static CombinedCenterOfBoundBox(objects: List[Shape]) → Vector[ソース]

Calculates the center of a bounding box of multiple objects.

パラメータ:

objects (List[Shape]) -- A list of objects

戻り値の型:

Vector

CompSolids() → List[CompSolid][ソース]

戻り値:

All the compsolids in this Shape

戻り値の型:

List[CompSolid]

Compounds() → List[Compound][ソース]

戻り値:

All the compounds in this Shape

戻り値の型:

List[Compound]

Edges() → List[Edge][ソース]

戻り値:

All the edges in this Shape

戻り値の型:

List[Edge]

Faces() → List[Face][ソース]

戻り値:

All the faces in this Shape

戻り値の型:

List[Face]

Shells() → List[Shell][ソース]

戻り値:

All the shells in this Shape

戻り値の型:

List[Shell]

Solids() → List[Solid][ソース]

戻り値:

All the solids in this Shape

戻り値の型:

List[Solid]

Vertices() → List[Vertex][ソース]

戻り値:

All the vertices in this Shape

戻り値の型:

List[Vertex]

Volume(tol: Optional[float] = None) → float[ソース]

戻り値:

The volume of this Shape

パラメータ:

tol (Optional[float]) --

戻り値の型:

float

Wires() → List[Wire][ソース]

戻り値:

All the wires in this Shape

戻り値の型:

List[Wire]

__add__(other: Shape) → Shape[ソース]

Fuse self and other.

パラメータ:

other (Shape) --

戻り値の型:

Shape

__eq__(other) → bool[ソース]

Return self==value.

戻り値の型:

bool

__hash__() → int[ソース]

Return hash(self).

戻り値の型:

int

__init__(obj: TopoDS_Shape)[ソース]

パラメータ:

obj (TopoDS_Shape) --

__iter__() → Iterator[Shape][ソース]

Iterate over subshapes.

戻り値の型:

Iterator[Shape]

__mul__(other: Shape) → Shape[ソース]

Intersect self and other.

パラメータ:

other (Shape) --

戻り値の型:

Shape

__sub__(other: Shape) → Shape[ソース]

Subtract other from self.

パラメータ:

other (Shape) --

戻り値の型:

Shape

__truediv__(other: Shape) → Shape[ソース]

Split self with other.

パラメータ:

other (Shape) --

戻り値の型:

Shape

__weakref__

list of weak references to the object (if defined)

ancestors(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) → Compound[ソース]

Iterate over ancestors, i.e. shapes of same kind within shape that contain self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

戻り値の型:

Compound

classmethod cast(obj: TopoDS_Shape, forConstruction: bool = False) → Shape[ソース]

Returns the right type of wrapper, given a OCCT object

パラメータ:

-

obj (TopoDS_Shape) --

-

forConstruction (bool) --

戻り値の型:

Shape

static centerOfMass(obj: Shape) → Vector[ソース]

Calculates the center of 'mass' of an object.

パラメータ:

obj (Shape) -- Compute the center of mass of this object

戻り値の型:

Vector

clean() → T[ソース]

Experimental clean using ShapeUpgrade

パラメータ:

self (T) --

戻り値の型:

T

static computeMass(obj: Shape, tol: Optional[float] = None) → float[ソース]

Calculates the 'mass' of an object.

パラメータ:

-

obj (Shape) -- Compute the mass of this object

-

tol (Optional[float]) -- Numerical integration tolerance (optional).

戻り値の型:

float

copy(mesh: bool = False) → T[ソース]

Creates a new object that is a copy of this object.

パラメータ:

-

mesh (bool) -- should I copy the triangulation too (default: False)

-

self (T) --

戻り値:

a copy of the object

戻り値の型:

T

cut(*toCut: Shape, tol: Optional[float] = None) → Shape[ソース]

Remove the positional arguments from this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toCut (Shape) --

戻り値の型:

Shape

distance(other: Shape) → float[ソース]

Minimal distance between two shapes

パラメータ:

other (Shape) --

戻り値の型:

float

distances(*others: Shape) → Iterator[float][ソース]

Minimal distances to between self and other shapes

パラメータ:

others (Shape) --

戻り値の型:

Iterator[float]

edges(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select edges.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

export(fname: str, tolerance: float = 0.1, angularTolerance: float = 0.1, opt: Optional[Dict[str, Any]] = None)[ソース]

Export Shape to file.

パラメータ:

-

self (T) --

-

fname (str) --

-

tolerance (float) --

-

angularTolerance (float) --

-

opt (Optional[Dict[str, Any]]) --

exportBin(f: Union[str, BytesIO]) → bool[ソース]

Export this shape to a binary BREP file.

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

bool

exportBrep(f: Union[str, BytesIO]) → bool[ソース]

Export this shape to a BREP file

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

bool

exportStep(fileName: str, **kwargs) → IFSelect_ReturnStatus[ソース]

Export this shape to a STEP file.

kwargs is used to provide optional keyword arguments to configure the exporter.

パラメータ:

-

fileName (str) -- Path and filename for writing.

-

write_pcurves (bool) --

Enable or disable writing parametric curves to the STEP file. Default True.

If False, writes STEP file without pcurves. This decreases the size of the resulting STEP file.

-

precision_mode (int) -- Controls the uncertainty value for STEP entities. Specify -1, 0, or 1. Default 0.
See OCCT documentation.

戻り値の型:

IFSelect_ReturnStatus

exportStl(fileName: str, tolerance: float = 0.001, angularTolerance: float = 0.1, ascii: bool = False, relative: bool = True, parallel: bool = True) → bool[ソース]

Exports a shape to a specified STL file.

パラメータ:

-

fileName (str) -- The path and file name to write the STL output to.

-

tolerance (float) -- A linear deflection setting which limits the distance between a curve and its tessellation.
Setting this value too low will result in large meshes that can consume computing resources.
Setting the value too high can result in meshes with a level of detail that is too low.
Default is 1e-3, which is a good starting point for a range of cases.

-

angularTolerance (float) -- Angular deflection setting which limits the angle between subsequent segments in a polyline. Default is 0.1.

-

ascii (bool) -- Export the file as ASCII (True) or binary (False) STL format.  Default is binary.

-

relative (bool) -- If True, tolerance will be scaled by the size of the edge being meshed. Default is True.
Setting this value to True may cause large features to become faceted, or small features dense.

-

parallel (bool) -- If True, OCCT will use parallel processing to mesh the shape. Default is True.

戻り値の型:

bool

faces(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select faces.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

facesIntersectedByLine(point: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], axis: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], tol: float = 0.0001, direction: Optional[Literal['AlongAxis', 'Opposite']] = None)[ソース]

Computes the intersections between the provided line and the faces of this Shape

パラメータ:

-

point (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Base point for defining a line

-

axis (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Axis on which the line rests

-

tol (float) -- Intersection tolerance

-

direction (Optional[Literal['AlongAxis', 'Opposite']]) -- Valid values: "AlongAxis", "Opposite";
If specified, will ignore all faces that are not in the specified direction
including the face where the point lies if it is the case

戻り値:

A list of intersected faces sorted by distance from point

fix() → T[ソース]

Try to fix shape if not valid

パラメータ:

self (T) --

戻り値の型:

T

fuse(*toFuse: Shape, glue: bool = False, tol: Optional[float] = None) → Shape[ソース]

Fuse the positional arguments with this Shape.

パラメータ:

-

glue (bool) -- Sets the glue option for the algorithm, which allows
increasing performance of the intersection of the input shapes

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toFuse (Shape) --

戻り値の型:

Shape

geomType() → Literal['Vertex', 'Wire', 'Shell', 'Solid', 'Compound', 'PLANE', 'CYLINDER', 'CONE', 'SPHERE', 'TORUS', 'BEZIER', 'BSPLINE', 'REVOLUTION', 'EXTRUSION', 'OFFSET', 'OTHER', 'LINE', 'CIRCLE', 'ELLIPSE', 'HYPERBOLA', 'PARABOLA'][ソース]

Gets the underlying geometry type.

Implementations can return any values desired, but the values the user
uses in type filters should correspond to these.

As an example, if a user does:

```python
CQ(object).faces("%mytype")

```

The expectation is that the geomType attribute will return 'mytype'

The return values depend on the type of the shape:

Vertex:  always 'Vertex'
Edge:   LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER,

BSPLINE, OFFSET, OTHER

Face:   PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE,

REVOLUTION, EXTRUSION, OFFSET, OTHER

Solid:  'Solid'
Shell:  'Shell'
Compound: 'Compound'
Wire:   'Wire'

戻り値:

A string according to the geometry type

戻り値の型:

Literal['Vertex', 'Wire', 'Shell', 'Solid', 'Compound', 'PLANE', 'CYLINDER', 'CONE', 'SPHERE', 'TORUS', 'BEZIER', 'BSPLINE', 'REVOLUTION', 'EXTRUSION', 'OFFSET', 'OTHER', 'LINE', 'CIRCLE', 'ELLIPSE', 'HYPERBOLA', 'PARABOLA']

hashCode() → int[ソース]

Returns a hashed value denoting this shape. It is computed from the
TShape and the Location. The Orientation is not used.

戻り値の型:

int

classmethod importBin(f: Union[str, BytesIO]) → Shape[ソース]

Import shape from a binary BREP file.

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

Shape

classmethod importBrep(f: Union[str, BytesIO]) → Shape[ソース]

Import shape from a BREP file

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

Shape

intersect(*toIntersect: Shape, tol: Optional[float] = None) → Shape[ソース]

Intersection of the positional arguments and this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toIntersect (Shape) --

戻り値の型:

Shape

isEqual(other: Shape) → bool[ソース]

Returns True if two shapes are equal, i.e. if they share the same
TShape with the same Locations and Orientations. Also see
`isSame()`.

パラメータ:

other (Shape) --

戻り値の型:

bool

isNull() → bool[ソース]

Returns true if this shape is null. In other words, it references no
underlying shape with the potential to be given a location and an
orientation.

戻り値の型:

bool

isSame(other: Shape) → bool[ソース]

Returns True if other and this shape are same, i.e. if they share the
same TShape with the same Locations. Orientations may differ. Also see
`isEqual()`

パラメータ:

other (Shape) --

戻り値の型:

bool

isValid() → bool[ソース]

Returns True if no defect is detected on the shape S or any of its
subshapes. See the OCCT docs on BRepCheck_Analyzer::IsValid for a full
description of what is checked.

戻り値の型:

bool

locate(loc: Location) → T[ソース]

Apply a location in absolute sense to self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

located(loc: Location) → T[ソース]

Apply a location in absolute sense to a copy of self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

location() → Location[ソース]

Return the current location

戻り値の型:

Location

static matrixOfInertia(obj: Shape) → List[List[float]][ソース]

Calculates the matrix of inertia of an object.
Since the part's density is unknown, this result is inertia/density with units of [1/length].
:param obj: Compute the matrix of inertia of this object

パラメータ:

obj (Shape) --

戻り値の型:

List[List[float]]

mesh(tolerance: float, angularTolerance: float = 0.1)[ソース]

Generate triangulation if none exists.

パラメータ:

-

tolerance (float) --

-

angularTolerance (float) --

mirror(mirrorPlane: Union[Literal['XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'], Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]] = 'XY', basePointVector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]] = (0, 0, 0)) → Shape[ソース]

Applies a mirror transform to this Shape. Does not duplicate objects
about the plane.

パラメータ:

-

mirrorPlane (Union[Literal['XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'], Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- The direction of the plane to mirror about - one of
'XY', 'XZ' or 'YZ'

-

basePointVector (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- The origin of the plane to mirror about

戻り値:

The mirrored shape

戻り値の型:

Shape

move(loc: Location) → T[ソース]

move(x: Union[float, int] = 0, y: Union[float, int] = 0, z: Union[float, int] = 0, rx: Union[float, int] = 0, ry: Union[float, int] = 0, rz: Union[float, int] = 0) → T

move(loc: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

Apply a location in relative sense (i.e. update current location) to self.

Apply translation and rotation in relative sense (i.e. update current location) to self.

Apply a VectorLike in relative sense (i.e. update current location) to self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

moved(loc: Sequence[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) → T[ソース]

moved(x: Union[float, int] = 0, y: Union[float, int] = 0, z: Union[float, int] = 0, rx: Union[float, int] = 0, ry: Union[float, int] = 0, rz: Union[float, int] = 0) → T

moved(loc1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], loc2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], *locs: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

moved(locs: Sequence[Location]) → T

moved(loc: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

moved(loc: Location) → T

moved(loc1: Location, loc2: Location, *locs: Location) → T

Apply a location in relative sense (i.e. update current location) to a copy of self.

Apply multiple locations.

Apply multiple locations.

Apply translation and rotation in relative sense to a copy of self.

Apply a VectorLike in relative sense to a copy of self.

Apply multiple VectorLikes in relative sense to a copy of self.

Apply multiple VectorLikes in relative sense to a copy of self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

remove(*subshape: Shape) → Self[ソース]

Remove subshapes.

パラメータ:

subshape (Shape) --

戻り値の型:

Self

replace(old: Shape, *new: Shape) → Self[ソース]

Replace old subshape with new subshapes.

パラメータ:

-

old (Shape) --

-

new (Shape) --

戻り値の型:

Self

rotate(startVector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], endVector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angleDegrees: float) → T[ソース]

Rotates a shape around an axis.

パラメータ:

-

startVector (either a 3-tuple or a Vector) -- start point of rotation axis

-

endVector (either a 3-tuple or a Vector) -- end point of rotation axis

-

angleDegrees (float) -- angle to rotate, in degrees

-

self (T) --

戻り値:

a copy of the shape, rotated

戻り値の型:

T

scale(factor: float) → Shape[ソース]

Scales this shape through a transformation.

パラメータ:

factor (float) --

戻り値の型:

Shape

shells(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select shells.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

siblings(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound'], level: int = 1) → Compound[ソース]

Iterate over siblings, i.e. shapes within shape that share subshapes of kind with self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

-

level (int) --

戻り値の型:

Compound

solids(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select solids.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

split(*splitters: Shape) → Shape[ソース]

Split this shape with the positional arguments.

パラメータ:

splitters (Shape) --

戻り値の型:

Shape

toNURBS() → T[ソース]

Return a NURBS representation of a given shape.

パラメータ:

self (T) --

戻り値の型:

T

toSplines(degree: int = 3, tolerance: float = 0.001, nurbs: bool = False) → T[ソース]

Approximate shape with b-splines of the specified degree.

パラメータ:

-

degree (int) -- Maximum degree.

-

tolerance (float) -- Approximation tolerance.

-

nurbs (bool) -- Use rational splines.

-

self (T) --

戻り値の型:

T

toVtkPolyData(tolerance: Optional[float] = None, angularTolerance: Optional[float] = None, normals: bool = False) → vtkPolyData[ソース]

Convert shape to vtkPolyData

パラメータ:

-

tolerance (Optional[float]) --

-

angularTolerance (Optional[float]) --

-

normals (bool) --

戻り値の型:

vtkPolyData

transformGeometry(tMatrix: Matrix) → Shape[ソース]

Transforms this shape by tMatrix.

WARNING: transformGeometry will sometimes convert lines and circles to
splines, but it also has the ability to handle skew and stretching
transformations.

If your transformation is only translation and rotation, it is safer to
use `transformShape()`, which doesn't change the underlying type
of the geometry, but cannot handle skew transformations.

パラメータ:

tMatrix (Matrix) -- The transformation matrix

戻り値:

a copy of the object, but with geometry transformed instead
of just rotated.

戻り値の型:

Shape

transformShape(tMatrix: Matrix) → Shape[ソース]

Transforms this Shape by tMatrix. Also see `transformGeometry()`.

パラメータ:

tMatrix (Matrix) -- The transformation matrix

戻り値:

a copy of the object, transformed by the provided matrix,
with all objects keeping their type

戻り値の型:

Shape

translate(vector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T[ソース]

Translates this shape through a transformation.

パラメータ:

-

self (T) --

-

vector (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

T

vertices(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select vertices.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

wires(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select wires.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

class cadquery.Shell(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`

サーフェスの外側の境界線

パラメータ:

obj (TopoDS_Shape) --

classmethod makeShell(listOfFaces: Iterable[Face]) → Shell[ソース]

Makes a shell from faces.

パラメータ:

listOfFaces (Iterable[Face]) --

戻り値の型:

Shell

class cadquery.Sketch(parent: ~typing.Optional[~typing.Any] = None, locs: ~typing.Iterable[~cadquery.occ_impl.geom.Location] = (<cadquery.occ_impl.geom.Location object>, ), obj: ~typing.Optional[~cadquery.occ_impl.shapes.Compound] = None)[ソース]

ベースクラス: `object`

2D sketch. Supports faces, edges and edges with constraints based construction.

パラメータ:

-

parent (Any) --

-

locs (List[Location]) --

-

obj (Optional[Compound]) --

__add__(other: Sketch) → T[ソース]

Fuse self and other.

パラメータ:

-

self (T) --

-

other (Sketch) --

戻り値の型:

T

__init__(parent: ~typing.Optional[~typing.Any] = None, locs: ~typing.Iterable[~cadquery.occ_impl.geom.Location] = (<cadquery.occ_impl.geom.Location object>, ), obj: ~typing.Optional[~cadquery.occ_impl.shapes.Compound] = None)[ソース]

Construct an empty sketch.

パラメータ:

-

self (T) --

-

parent (Optional[Any]) --

-

locs (Iterable[Location]) --

-

obj (Optional[Compound]) --

__iter__() → Iterator[Face][ソース]

Iterate over faces-locations combinations. If not faces are present
iterate over edges:

戻り値の型:

Iterator[Face]

__mul__(other: Sketch) → T[ソース]

Intersect self and other.

パラメータ:

-

self (T) --

-

other (Sketch) --

戻り値の型:

T

__sub__(other: Sketch) → T[ソース]

Subtract other from self.

パラメータ:

-

self (T) --

-

other (Sketch) --

戻り値の型:

T

__truediv__(other: Sketch) → T[ソース]

Split self with other.

パラメータ:

-

self (T) --

-

other (Sketch) --

戻り値の型:

T

__weakref__

list of weak references to the object (if defined)

add() → T[ソース]

Add selection to the underlying faces.

パラメータ:

self (T) --

戻り値の型:

T

apply(f: Callable[[Iterable[Union[Shape, Location]]], Iterable[Union[Shape, Location]]])[ソース]

Apply a callable to all items at once.

パラメータ:

-

f (Callable[[Iterable[Union[Shape, Location]]], Iterable[Union[Shape, Location]]]) -- Callable to be applied.

-

self (T) --

戻り値:

Sketch object with f applied to all items.

arc(c: Union[Vector, Tuple[Union[int, float], Union[int, float]]], r: Union[int, float], a: Union[int, float], da: Union[int, float], tag: Optional[str] = None, forConstruction: bool = False) → T[ソース]

arc(p1: Union[Vector, Tuple[Union[int, float], Union[int, float]]], p2: Union[Vector, Tuple[Union[int, float], Union[int, float]]], p3: Union[Vector, Tuple[Union[int, float], Union[int, float]]], tag: Optional[str] = None, forConstruction: bool = False) → T

arc(p2: Union[Vector, Tuple[Union[int, float], Union[int, float]]], p3: Union[Vector, Tuple[Union[int, float], Union[int, float]]], tag: Optional[str] = None, forConstruction: bool = False) → T

Construct an arc.

パラメータ:

-

self (T) --

-

p1 (Union[Vector, Tuple[Union[int, float], Union[int, float]]]) --

-

p2 (Union[Vector, Tuple[Union[int, float], Union[int, float]]]) --

-

p3 (Union[Vector, Tuple[Union[int, float], Union[int, float]]]) --

-

tag (Optional[str]) --

-

forConstruction (bool) --

戻り値の型:

T

assemble(mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Assemble edges into faces.

パラメータ:

-

self (T) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

bezier(pts: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]], tag: Optional[str] = None, forConstruction: bool = False) → T[ソース]

Construct an bezier curve.

The edge will pass through the last points, and the inner points
are bezier control points.

パラメータ:

-

self (T) --

-

pts (Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]]) --

-

tag (Optional[str]) --

-

forConstruction (bool) --

戻り値の型:

T

chamfer(d: Union[int, float]) → T[ソース]

Add a chamfer based on current selection.

パラメータ:

-

self (T) --

-

d (Union[int, float]) --

戻り値の型:

T

circle(r: Union[int, float], mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct a circular face.

パラメータ:

-

self (T) --

-

r (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

clean() → T[ソース]

Remove internal wires.

パラメータ:

self (T) --

戻り値の型:

T

close(tag: Optional[str] = None) → T[ソース]

Connect last edge to the first one.

パラメータ:

-

self (T) --

-

tag (Optional[str]) --

戻り値の型:

T

constrain(tag: str, constraint: Literal['Fixed', 'FixedPoint', 'Coincident', 'Angle', 'Length', 'Distance', 'Radius', 'Orientation', 'ArcAngle'], arg: Any) → T[ソース]

constrain(tag1: str, tag2: str, constraint: Literal['Fixed', 'FixedPoint', 'Coincident', 'Angle', 'Length', 'Distance', 'Radius', 'Orientation', 'ArcAngle'], arg: Any) → T

Add a constraint.

パラメータ:

-

self (T) --

-

tag (str) --

-

constraint (Literal['Fixed', 'FixedPoint', 'Coincident', 'Angle', 'Length', 'Distance', 'Radius', 'Orientation', 'ArcAngle']) --

-

arg (Any) --

戻り値の型:

T

copy() → T[ソース]

Create a partial copy of the sketch.

パラメータ:

self (T) --

戻り値の型:

T

delete() → T[ソース]

Delete selected object.

パラメータ:

self (T) --

戻り値の型:

T

distribute(n: int, start: Union[int, float] = 0, stop: Union[int, float] = 1, rotate: bool = True) → T[ソース]

Distribute locations along selected edges or wires.

パラメータ:

-

self (T) --

-

n (int) --

-

start (Union[int, float]) --

-

stop (Union[int, float]) --

-

rotate (bool) --

戻り値の型:

T

each(callback: Callable[[Location], Union[Face, Sketch, Compound]], mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None, ignore_selection: bool = False) → T[ソース]

Apply a callback on all applicable entities.

パラメータ:

-

self (T) --

-

callback (Callable[[Location], Union[Face, Sketch, Compound]]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

-

ignore_selection (bool) --

戻り値の型:

T

edge(val: Edge, tag: Optional[str] = None, forConstruction: bool = False) → T[ソース]

Add an edge to the sketch.

パラメータ:

-

self (T) --

-

val (Edge) --

-

tag (Optional[str]) --

-

forConstruction (bool) --

戻り値の型:

T

edges(s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select edges.

パラメータ:

-

self (T) --

-

s (Optional[Union[str, Selector]]) --

-

tag (Optional[str]) --

戻り値の型:

T

ellipse(a1: Union[int, float], a2: Union[int, float], angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct an elliptical face.

パラメータ:

-

self (T) --

-

a1 (Union[int, float]) --

-

a2 (Union[int, float]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

export(fname: str, tolerance: float = 0.1, angularTolerance: float = 0.1, opt: Optional[Dict[str, Any]] = None) → T[ソース]

Export Sketch to file.

パラメータ:

-

path -- Filename.

-

tolerance (float) -- the deflection tolerance, in model units. Default 0.1.

-

angularTolerance (float) -- the angular tolerance, in radians. Default 0.1.

-

opt (Optional[Dict[str, Any]]) -- additional options passed to the specific exporter. Default None.

-

self (T) --

-

fname (str) --

戻り値:

Self.

戻り値の型:

T

face(b: Union[Wire, Iterable[Edge], Shape, T], angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None, ignore_selection: bool = False) → T[ソース]

Construct a face from a wire or edges.

パラメータ:

-

self (T) --

-

b (Union[Wire, Iterable[Edge], Shape, T]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

-

ignore_selection (bool) --

戻り値の型:

T

faces(s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select faces.

パラメータ:

-

self (T) --

-

s (Optional[Union[str, Selector]]) --

-

tag (Optional[str]) --

戻り値の型:

T

fillet(d: Union[int, float]) → T[ソース]

Add a fillet based on current selection.

パラメータ:

-

self (T) --

-

d (Union[int, float]) --

戻り値の型:

T

filter(f: Callable[[Union[Shape, Location]], bool]) → T[ソース]

Filter items using a boolean predicate.

パラメータ:

-

f (Callable[[Union[Shape, Location]], bool]) -- Callable to be used for filtering.

-

self (T) --

戻り値:

Sketch object with filtered items.

戻り値の型:

T

finalize() → Any[ソース]

Finish sketch construction and return the parent.

戻り値の型:

Any

hull(mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Generate a convex hull from current selection or all objects.

パラメータ:

-

self (T) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

importDXF(filename: str, tol: float = 1e-06, exclude: List[str] = [], include: List[str] = [], angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Import a DXF file and construct face(s)

パラメータ:

-

self (T) --

-

filename (str) --

-

tol (float) --

-

exclude (List[str]) --

-

include (List[str]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

invoke(f: Union[Callable[[T], T], Callable[[T], None], Callable[[], None]])[ソース]

Invoke a callable mapping Sketch to Sketch or None. Supports also
callables that take no arguments such as breakpoint. Returns self if callable
returns None.

パラメータ:

-

f (Union[Callable[[T], T], Callable[[T], None], Callable[[], None]]) -- Callable to be invoked.

-

self (T) --

戻り値:

Sketch object.

located(loc: Location) → T[ソース]

Create a partial copy of the sketch with a new location.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

map(f: Callable[[Union[Shape, Location]], Union[Shape, Location]])[ソース]

Apply a callable to every item separately.

パラメータ:

-

f (Callable[[Union[Shape, Location]], Union[Shape, Location]]) -- Callable to be applied to every item separately.

-

self (T) --

戻り値:

Sketch object with f applied to all items.

moved(loc: Location) → T[ソース]

moved(loc1: Location, loc2: Location, *locs: Location) → T

moved(locs: Sequence[Location]) → T

moved(x: Union[int, float] = 0, y: Union[int, float] = 0, z: Union[int, float] = 0, rx: Union[int, float] = 0, ry: Union[int, float] = 0, rz: Union[int, float] = 0) → T

moved(loc: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

moved(loc1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], loc2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], *locs: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

moved(loc: Sequence[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) → T

Create a partial copy of the sketch with moved _faces.

offset(d: Union[int, float], mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Offset selected wires or edges.

パラメータ:

-

self (T) --

-

d (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

parray(r: Union[int, float], a1: Union[int, float], da: Union[int, float], n: int, rotate: bool = True) → T[ソース]

Generate a polar array of locations.

パラメータ:

-

self (T) --

-

r (Union[int, float]) --

-

a1 (Union[int, float]) --

-

da (Union[int, float]) --

-

n (int) --

-

rotate (bool) --

戻り値の型:

T

polygon(pts: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]], angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct a polygonal face.

パラメータ:

-

self (T) --

-

pts (Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

push(locs: Iterable[Union[Location, Vector, Tuple[Union[int, float], Union[int, float]]]], tag: Optional[str] = None) → T[ソース]

Set current selection to given locations or points.

パラメータ:

-

self (T) --

-

locs (Iterable[Union[Location, Vector, Tuple[Union[int, float], Union[int, float]]]]) --

-

tag (Optional[str]) --

戻り値の型:

T

rarray(xs: Union[int, float], ys: Union[int, float], nx: int, ny: int) → T[ソース]

Generate a rectangular array of locations.

パラメータ:

-

self (T) --

-

xs (Union[int, float]) --

-

ys (Union[int, float]) --

-

nx (int) --

-

ny (int) --

戻り値の型:

T

rect(w: Union[int, float], h: Union[int, float], angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct a rectangular face.

パラメータ:

-

self (T) --

-

w (Union[int, float]) --

-

h (Union[int, float]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

regularPolygon(r: Union[int, float], n: int, angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct a regular polygonal face.

パラメータ:

-

self (T) --

-

r (Union[int, float]) --

-

n (int) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

replace() → T[ソース]

Replace the underlying faces with the selection.

パラメータ:

self (T) --

戻り値の型:

T

reset() → T[ソース]

Reset current selection.

パラメータ:

self (T) --

戻り値の型:

T

segment(p1: Union[Vector, Tuple[Union[int, float], Union[int, float]]], p2: Union[Vector, Tuple[Union[int, float], Union[int, float]]], tag: Optional[str] = None, forConstruction: bool = False) → T[ソース]

segment(p2: Union[Vector, Tuple[Union[int, float], Union[int, float]]], tag: Optional[str] = None, forConstruction: bool = False) → T

segment(l: Union[int, float], a: Union[int, float], tag: Optional[str] = None, forConstruction: bool = False) → T

Construct a segment.

パラメータ:

-

self (T) --

-

p1 (Union[Vector, Tuple[Union[int, float], Union[int, float]]]) --

-

p2 (Union[Vector, Tuple[Union[int, float], Union[int, float]]]) --

-

tag (Optional[str]) --

-

forConstruction (bool) --

戻り値の型:

T

select(*tags: str) → T[ソース]

Select based on tags.

パラメータ:

-

self (T) --

-

tags (str) --

戻り値の型:

T

slot(w: Union[int, float], h: Union[int, float], angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct a slot-shaped face.

パラメータ:

-

self (T) --

-

w (Union[int, float]) --

-

h (Union[int, float]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

solve() → T[ソース]

Solve current constraints and update edge positions.

パラメータ:

self (T) --

戻り値の型:

T

sort(key: Callable[[Union[Shape, Location]], Any]) → T[ソース]

Sort items using a callable.

パラメータ:

-

key (Callable[[Union[Shape, Location]], Any]) -- Callable to be used for sorting.

-

self (T) --

戻り値:

Sketch object with items sorted.

戻り値の型:

T

spline(pts: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]], tangents: Optional[Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]]], periodic: bool, tag: Optional[str] = None, forConstruction: bool = False) → T[ソース]

spline(pts: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]], tag: Optional[str] = None, forConstruction: bool = False) → T

Construct a spline edge.

パラメータ:

-

self (T) --

-

pts (Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]]) --

-

tangents (Optional[Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]]]]]) --

-

periodic (bool) --

-

tag (Optional[str]) --

-

forConstruction (bool) --

戻り値の型:

T

subtract() → T[ソース]

Subtract selection from the underlying faces.

パラメータ:

self (T) --

戻り値の型:

T

tag(tag: str) → T[ソース]

Tag current selection.

パラメータ:

-

self (T) --

-

tag (str) --

戻り値の型:

T

trapezoid(w: Union[int, float], h: Union[int, float], a1: Union[int, float], a2: Optional[float] = None, angle: Union[int, float] = 0, mode: Literal['a', 's', 'i', 'c', 'r'] = 'a', tag: Optional[str] = None) → T[ソース]

Construct a trapezoidal face.

パラメータ:

-

self (T) --

-

w (Union[int, float]) --

-

h (Union[int, float]) --

-

a1 (Union[int, float]) --

-

a2 (Optional[float]) --

-

angle (Union[int, float]) --

-

mode (Literal['a', 's', 'i', 'c', 'r']) --

-

tag (Optional[str]) --

戻り値の型:

T

val() → Union[Shape, Location][ソース]

Return the first selected item, underlying compound or first edge.

パラメータ:

self (T) --

戻り値の型:

Union[Shape, Location]

vals() → List[Union[Shape, Location]][ソース]

Return all selected items, underlying compound or all edges.

パラメータ:

self (T) --

戻り値の型:

List[Union[Shape, Location]]

vertices(s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select vertices.

パラメータ:

-

self (T) --

-

s (Optional[Union[str, Selector]]) --

-

tag (Optional[str]) --

戻り値の型:

T

wires(s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select wires.

パラメータ:

-

self (T) --

-

s (Optional[Union[str, Selector]]) --

-

tag (Optional[str]) --

戻り値の型:

T

class cadquery.Solid(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin3D`

単体

パラメータ:

obj (TopoDS_Shape) --

addCavity(*shells: Union[Shell, Solid]) → Self[ソース]

Add one or more cavities.

パラメータ:

shells (Union[Shell, Solid]) --

戻り値の型:

Self

classmethod extrudeLinear(outerWire: Wire, innerWires: List[Wire], vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], taper: Union[float, int] = 0) → Solid[ソース]

classmethod extrudeLinear(face: Face, vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], taper: Union[float, int] = 0) → Solid

Attempt to extrude the list of wires into a prismatic solid in the provided direction

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

vecNormal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- a vector along which to extrude the wires

-

taper (Union[float, int]) -- taper angle, default=0

戻り値:

a Solid object

戻り値の型:

Solid

The wires must not intersect

Extruding wires is very non-trivial.  Nested wires imply very different geometry, and
there are many geometries that are invalid. In general, the following conditions must be met:

-

all wires must be closed

-

there cannot be any intersecting or self-intersecting wires

-

wires must be listed from outside in

-

more than one levels of nesting is not supported reliably

This method will attempt to sort the wires, but there is much work remaining to make this method
reliable.

classmethod extrudeLinearWithRotation(outerWire: Wire, innerWires: List[Wire], vecCenter: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angleDegrees: Union[float, int]) → Solid[ソース]

classmethod extrudeLinearWithRotation(face: Face, vecCenter: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angleDegrees: Union[float, int]) → Solid

Creates a 'twisted prism' by extruding, while simultaneously rotating around the extrusion vector.

Though the signature may appear to be similar enough to extrudeLinear to merit combining them, the
construction methods used here are different enough that they should be separate.

At a high level, the steps followed are:

-

accept a set of wires

-

create another set of wires like this one, but which are transformed and rotated

-

create a ruledSurface between the sets of wires

-

create a shell and compute the resulting object

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

vecCenter (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- the center point about which to rotate.  the axis of rotation is defined by
vecNormal, located at vecCenter.

-

vecNormal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- a vector along which to extrude the wires

-

angleDegrees (Union[float, int]) -- the angle to rotate through while extruding

戻り値:

a Solid object

戻り値の型:

Solid

innerShells() → List[Shell][ソース]

Returns inner shells.

戻り値の型:

List[Shell]

classmethod interpPlate(surf_edges, surf_pts, thickness, degree=3, nbPtsOnCur=15, nbIter=2, anisotropy=False, tol2d=1e-05, tol3d=0.0001, tolAng=0.01, tolCurv=0.1, maxDeg=8, maxSegments=9) → Union[Solid, Face][ソース]

Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points, and going through 'surf_pts' points.

パラメータ:

-

surf_edges -- list of [x,y,z] float ordered coordinates
or list of ordered or unordered wires

-

surf_pts -- list of [x,y,z] float coordinates (uses only edges if [])

-

thickness -- thickness may be negative or positive depending on direction, (returns 2D surface if 0)

-

degree -- >=2

-

nbPtsOnCur -- number of points on curve >= 15

-

nbIter -- number of iterations >= 2

-

anisotropy -- bool Anisotropy

-

tol2d -- 2D tolerance >0

-

tol3d -- 3D tolerance >0

-

tolAng -- angular tolerance

-

tolCurv -- tolerance for curvature >0

-

maxDeg -- highest polynomial degree >= 2

-

maxSegments -- greatest number of segments >= 2

戻り値の型:

Union[Solid, Face]

static isSolid(obj: Shape) → bool[ソース]

Returns true if the object is a solid, false otherwise

パラメータ:

obj (Shape) --

戻り値の型:

bool

classmethod makeBox(length,width,height,[pnt,dir]) -- Make a box located in pnt with the dimensions (length,width,height)[ソース]

By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)

パラメータ:

-

length (float) --

-

width (float) --

-

height (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Solid

classmethod makeCone(radius1: float, radius2: float, height: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees: float = 360) → Solid[ソース]

Make a cone with given radii and height
By default pnt=Vector(0,0,0),
dir=Vector(0,0,1) and angle=360

パラメータ:

-

radius1 (float) --

-

radius2 (float) --

-

height (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees (float) --

戻り値の型:

Solid

classmethod makeCylinder(radius: float, height: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees: float = 360) → Solid[ソース]

makeCylinder(radius,height,[pnt,dir,angle]) --
Make a cylinder with a given radius and height
By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360

パラメータ:

-

radius (float) --

-

height (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees (float) --

戻り値の型:

Solid

classmethod makeLoft(listOfWire: List[Wire], ruled: bool = False) → Solid[ソース]

makes a loft from a list of wires
The wires will be converted into faces when possible-- it is presumed that nobody ever actually
wants to make an infinitely thin shell for a real FreeCADPart.

パラメータ:

-

listOfWire (List[Wire]) --

-

ruled (bool) --

戻り値の型:

Solid

classmethod makeSolid(shell: Shell) → Solid[ソース]

Makes a solid from a single shell.

パラメータ:

shell (Shell) --

戻り値の型:

Solid

classmethod makeSphere(radius: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees1: float = 0, angleDegrees2: float = 90, angleDegrees3: float = 360) → Shape[ソース]

Make a sphere with a given radius
By default pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0, angle2=90 and angle3=360

パラメータ:

-

radius (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees1 (float) --

-

angleDegrees2 (float) --

-

angleDegrees3 (float) --

戻り値の型:

Shape

classmethod makeTorus(radius1: float, radius2: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees1: float = 0, angleDegrees2: float = 360) → Solid[ソース]

makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
Make a torus with a given radii and angles
By default pnt=Vector(0,0,0),dir=Vector(0,0,1),angle1=0
,angle1=360 and angle=360

パラメータ:

-

radius1 (float) --

-

radius2 (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees1 (float) --

-

angleDegrees2 (float) --

戻り値の型:

Solid

classmethod makeWedge(dx: float, dy: float, dz: float, xmin: float, zmin: float, xmax: float, zmax: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0)) → Solid[ソース]

Make a wedge located in pnt
By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)

パラメータ:

-

dx (float) --

-

dy (float) --

-

dz (float) --

-

xmin (float) --

-

zmin (float) --

-

xmax (float) --

-

zmax (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Solid

outerShell() → Shell[ソース]

Returns outer shell.

戻り値の型:

Shell

classmethod revolve(outerWire: Wire, innerWires: List[Wire], angleDegrees: Union[float, int], axisStart: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], axisEnd: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Solid[ソース]

classmethod revolve(face: Face, angleDegrees: Union[float, int], axisStart: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], axisEnd: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Solid

Attempt to revolve the list of wires into a solid in the provided direction

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

angleDegrees (float, anything less than 360 degrees will leave the shape open) -- the angle to revolve through.

-

axisStart (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- the start point of the axis of rotation

-

axisEnd (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- the end point of the axis of rotation

戻り値:

a Solid object

戻り値の型:

Solid

The wires must not intersect

-

all wires must be closed

-

there cannot be any intersecting or self-intersecting wires

-

wires must be listed from outside in

-

more than one levels of nesting is not supported reliably

-

the wire(s) that you're revolving cannot be centered

This method will attempt to sort the wires, but there is much work remaining to make this method
reliable.

classmethod sweep(outerWire: Wire, innerWires: List[Wire], path: Union[Wire, Edge], makeSolid: bool = True, isFrenet: bool = False, mode: Optional[Union[Vector, Wire, Edge]] = None, transitionMode: Literal['transformed', 'round', 'right'] = 'transformed') → Shape[ソース]

classmethod sweep(face: Face, path: Union[Wire, Edge], makeSolid: bool = True, isFrenet: bool = False, mode: Optional[Union[Vector, Wire, Edge]] = None, transitionMode: Literal['transformed', 'round', 'right'] = 'transformed') → Shape

Attempt to sweep the list of wires into a prismatic solid along the provided path

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

path (Union[Wire, Edge]) -- The wire to sweep the face resulting from the wires over

-

makeSolid (bool) -- return Solid or Shell (default True)

-

isFrenet (bool) -- Frenet mode (default False)

-

mode (Optional[Union[Vector, Wire, Edge]]) -- additional sweep mode parameters

-

transitionMode (Literal['transformed', 'round', 'right']) -- handling of profile orientation at C1 path discontinuities.
Possible values are {'transformed','round', 'right'} (default: 'right').

戻り値:

a Solid object

戻り値の型:

Shape

classmethod sweep_multi(profiles: Iterable[Union[Wire, Face]], path: Union[Wire, Edge], makeSolid: bool = True, isFrenet: bool = False, mode: Optional[Union[Vector, Wire, Edge]] = None) → Solid[ソース]

Multi section sweep. Only single outer profile per section is allowed.

パラメータ:

-

profiles (Iterable[Union[Wire, Face]]) -- list of profiles

-

path (Union[Wire, Edge]) -- The wire to sweep the face resulting from the wires over

-

mode (Optional[Union[Vector, Wire, Edge]]) -- additional sweep mode parameters.

-

makeSolid (bool) --

-

isFrenet (bool) --

戻り値:

a Solid object

戻り値の型:

Solid

class cadquery.StringSyntaxSelector(selectorString)[ソース]

ベースクラス: `Selector`

Filter lists objects using a simple string syntax. All of the filters available in the string syntax
are also available ( usually with more functionality ) through the creation of full-fledged
selector objects. see `Selector` and its subclasses

Filtering works differently depending on the type of object list being filtered.

パラメータ:

selectorString -- A two-part selector string, [selector][axis]

戻り値:

objects that match the specified selector

*Modifiers* are `('|','+','-','<','>','%')`

|:

parallel to ( same as `ParallelDirSelector` ). Can return multiple objects.

#:

perpendicular to (same as `PerpendicularDirSelector` )

+:

positive direction (same as `DirectionSelector` )

-:

negative direction (same as `DirectionSelector`  )

>:

maximize (same as `DirectionMinMaxSelector` with directionMax=True)

<:

minimize (same as `DirectionMinMaxSelector` with directionMax=False )

%:

curve/surface type (same as `TypeSelector`)

*axisStrings* are: `X,Y,Z,XY,YZ,XZ` or `(x,y,z)` which defines an arbitrary direction

It is possible to combine simple selectors together using logical operations.
The following operations are supported

and:

Logical AND, e.g. >X and >Y

or:

Logical OR, e.g. |X or |Y

not:

Logical NOT, e.g. not #XY

exc(ept):

Set difference (equivalent to AND NOT): |X exc >Z

Finally, it is also possible to use even more complex expressions with nesting
and arbitrary number of terms, e.g.

(not >X[0] and #XY) or >XY[0]

Selectors are a complex topic: see Selectors Reference for more information

__init__(selectorString)[ソース]

Feed the input string through the parser and construct an relevant complex selector object

filter(objectList: Sequence[Shape])[ソース]

Filter give object list through th already constructed complex selector object

パラメータ:

objectList (Sequence[Shape]) --

class cadquery.TypeSelector(typeString: str)[ソース]

ベースクラス: `Selector`

所定のジオメトリタイプを持つオブジェクトを選択します。

Applicability:

Faces: PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE, REVOLUTION, EXTRUSION, OFFSET, OTHER
Edges: LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER, BSPLINE, OFFSET, OTHER

You can use the string selector syntax. For example this:

```python
CQ(aCube).faces(TypeSelector("PLANE"))

```

will select 6 faces, and is equivalent to:

```python
CQ(aCube).faces("%PLANE")

```

パラメータ:

typeString (str) --

__init__(typeString: str)[ソース]

パラメータ:

typeString (str) --

filter(objectList: Sequence[Shape]) → List[Shape][ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

戻り値の型:

List[Shape]

class cadquery.Vector(x: float, y: float, z: float)[ソース]

class cadquery.Vector(x: float, y: float)

class cadquery.Vector(v: Vector)

class cadquery.Vector(v: Sequence[float])

class cadquery.Vector(v: Union[gp_Vec, gp_Pnt, gp_Dir, gp_XYZ])

class cadquery.Vector

ベースクラス: `object`

3次元ベクトルを作成する

パラメータ:

args -- a 3D vector, with x-y-z parts.

you can either provide:

-

nothing (in which case the null vector is return)

-

a gp_Vec

-

a vector ( in which case it is copied )

-

a 3-tuple

-

a 2-tuple (z assumed to be 0)

-

three float values: x, y, and z

-

two float values: x,y

Center() → Vector[ソース]

Return the vector itself

The center of myself is myself.
Provided so that vectors, vertices, and other shapes all support a
common interface, when Center() is requested for all objects on the
stack.

戻り値の型:

Vector

__eq__(other: Vector) → bool[ソース]

Return self==value.

パラメータ:

other (Vector) --

戻り値の型:

bool

__hash__ = None

__init__(x: float, y: float, z: float) → None[ソース]

__init__(x: float, y: float) → None

__init__(v: Vector) → None

__init__(v: Sequence[float]) → None

__init__(v: Union[gp_Vec, gp_Pnt, gp_Dir, gp_XYZ]) → None

__init__() → None

__repr__() → str[ソース]

Return repr(self).

戻り値の型:

str

__str__() → str[ソース]

Return str(self).

戻り値の型:

str

__weakref__

list of weak references to the object (if defined)

multiply(scale: float) → Vector[ソース]

Return a copy multiplied by the provided scalar

パラメータ:

scale (float) --

戻り値の型:

Vector

normalized() → Vector[ソース]

Return a normalized version of this vector

戻り値の型:

Vector

projectToLine(line: Vector) → Vector[ソース]

Returns a new vector equal to the projection of this Vector onto the line
represented by Vector <line>

パラメータ:

-

args -- Vector

-

line (Vector) --

戻り値の型:

Vector

Returns the projected vector.

projectToPlane(plane: Plane) → Vector[ソース]

Vector is projected onto the plane provided as input.

パラメータ:

-

args -- Plane object

-

plane (Plane) --

戻り値の型:

Vector

Returns the projected vector.

class cadquery.Vertex(obj: TopoDS_Shape, forConstruction: bool = False)[ソース]

ベースクラス: `Shape`

空間の中の一点

パラメータ:

-

obj (TopoDS_Shape) --

-

forConstruction (bool) --

Center() → Vector[ソース]

The center of a vertex is itself!

戻り値の型:

Vector

__init__(obj: TopoDS_Shape, forConstruction: bool = False)[ソース]

Create a vertex

パラメータ:

-

obj (TopoDS_Shape) --

-

forConstruction (bool) --

class cadquery.Wire(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin1D`

接続され、順序付けられた一連のEdgeで、通常、Faceを囲みます。

パラメータ:

obj (TopoDS_Shape) --

Vertices() → List[Vertex][ソース]

Ordered list of vertices of the wire.

戻り値の型:

List[Vertex]

__iter__() → Iterator[Edge][ソース]

Iterate over edges in an ordered way.

戻り値の型:

Iterator[Edge]

classmethod assembleEdges(listOfEdges: Iterable[Edge]) → Wire[ソース]

Attempts to build a wire that consists of the edges in the provided list

パラメータ:

-

cls --

-

listOfEdges (Iterable[Edge]) -- a list of Edge objects. The edges are not to be consecutive.

戻り値:

a wire with the edges assembled

戻り値の型:

Wire

BRepBuilderAPI_MakeWire::Error() values:

-

BRepBuilderAPI_WireDone = 0

-

BRepBuilderAPI_EmptyWire = 1

-

BRepBuilderAPI_DisconnectedWire = 2

-

BRepBuilderAPI_NonManifoldWire = 3

chamfer2D(d: float, vertices: Iterable[Vertex]) → Wire[ソース]

Apply 2D chamfer to a wire

パラメータ:

-

d (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Wire

close() → Wire[ソース]

Close a Wire

戻り値の型:

Wire

classmethod combine(listOfWires: Iterable[Union[Wire, Edge]], tol: float = 1e-09) → List[Wire][ソース]

Attempt to combine a list of wires and edges into a new wire.

パラメータ:

-

cls --

-

listOfWires (Iterable[Union[Wire, Edge]]) --

-

tol (float) -- default 1e-9

戻り値:

List[Wire]

戻り値の型:

List[Wire]

fillet(radius: float, vertices: Optional[Iterable[Vertex]] = None) → Wire[ソース]

Apply 2D or 3D fillet to a wire

パラメータ:

-

radius (float) -- the radius of the fillet, must be > zero

-

vertices (Optional[Iterable[Vertex]]) -- the vertices to delete (where the fillet will be applied).  By default
all vertices are deleted except ends of open wires.

戻り値:

A wire with filleted corners

戻り値の型:

Wire

fillet2D(radius: float, vertices: Iterable[Vertex]) → Wire[ソース]

Apply 2D fillet to a wire

パラメータ:

-

radius (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Wire

classmethod makeCircle(radius: float, center: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], normal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Wire[ソース]

Makes a Circle centered at the provided point, having normal in the provided direction

パラメータ:

-

radius (float) -- floating point radius of the circle, must be > 0

-

center (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the center of the circle

-

normal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the direction of the plane the circle should lie in

戻り値の型:

Wire

classmethod makeEllipse(x_radius: float, y_radius: float, center: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], normal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], xDir: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angle1: float = 360.0, angle2: float = 360.0, rotation_angle: float = 0.0, closed: bool = True) → Wire[ソース]

Makes an Ellipse centered at the provided point, having normal in the provided direction

パラメータ:

-

x_radius (float) -- floating point major radius of the ellipse (x-axis), must be > 0

-

y_radius (float) -- floating point minor radius of the ellipse (y-axis), must be > 0

-

center (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the center of the circle

-

normal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the direction of the plane the circle should lie in

-

angle1 (float) -- start angle of arc

-

angle2 (float) -- end angle of arc

-

rotation_angle (float) -- angle to rotate the created ellipse / arc

-

xDir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

closed (bool) --

戻り値の型:

Wire

classmethod makeHelix(pitch: float, height: float, radius: float, center: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angle: float = 360.0, lefthand: bool = False) → Wire[ソース]

Make a helix with a given pitch, height and radius
By default a cylindrical surface is used to create the helix. If
the fourth parameter is set (the apex given in degree) a conical surface is used instead'

パラメータ:

-

pitch (float) --

-

height (float) --

-

radius (float) --

-

center (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angle (float) --

-

lefthand (bool) --

戻り値の型:

Wire

classmethod makePolygon(listOfVertices: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]], forConstruction: bool = False, close: bool = False) → Wire[ソース]

Construct a polygonal wire from points.

パラメータ:

-

listOfVertices (Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) --

-

forConstruction (bool) --

-

close (bool) --

戻り値の型:

Wire

offset2D(d: float, kind: Literal['arc', 'intersection', 'tangent'] = 'arc') → List[Wire][ソース]

Offsets a planar wire

パラメータ:

-

d (float) --

-

kind (Literal['arc', 'intersection', 'tangent']) --

戻り値の型:

List[Wire]

stitch(other: Wire) → Wire[ソース]

Attempt to stitch wires

パラメータ:

other (Wire) --

戻り値の型:

Wire

class cadquery.Workplane(obj: Union[Vector, Location, Shape, Sketch])[ソース]

class cadquery.Workplane(inPlane: Union[Plane, str] = 'XY', origin: Union[Tuple[float, float], Tuple[float, float, float], Vector] = (0, 0, 0), obj: Optional[Union[Vector, Location, Shape, Sketch]] = None)

ベースクラス: `object`

2次元座標を使用できる空間上の座標系を定義します。

パラメータ:

-

plane (a Plane object, or a string in (XY|YZ|XZ|front|back|top|bottom|left|right)) -- the plane in which the workplane will be done

-

origin (a 3-tuple in global coordinates, or None to default to the origin) -- the desired origin of the new workplane

-

obj (a CAD primitive, or None to use the centerpoint of the plane as the initial
stack value.) -- an object to use initially for the stack

Raises:

ValueError if the provided plane is not a plane, a valid named workplane

戻り値:

A Workplane object, with coordinate system matching the supplied plane.

The most common use is:

```python
s = Workplane("XY")

```

After creation, the stack contains a single point, the origin of the underlying plane,
and the current point is on the origin.

注釈

You can also create workplanes on the surface of existing faces using
`workplane()`

__add__(other: Union[Workplane, Solid, Compound]) → T[ソース]

Syntactic sugar for union.

Notice that `r = a + b` is equivalent to `r = a.union(b)` and `r = a | b`.

パラメータ:

-

self (T) --

-

other (Union[Workplane, Solid, Compound]) --

戻り値の型:

T

__and__(other: Union[Workplane, Solid, Compound]) → T[ソース]

Syntactic sugar for intersect.

Notice that `r = a & b` is equivalent to `r = a.intersect(b)`.

Example:

```python
Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
Sphere = Workplane("XY").sphere(1)
result = Box & Sphere

```

パラメータ:

-

self (T) --

-

other (Union[Workplane, Solid, Compound]) --

戻り値の型:

T

__init__(obj: Union[Vector, Location, Shape, Sketch]) → None[ソース]

__init__(inPlane: Union[Plane, str] = 'XY', origin: Union[Tuple[float, float], Tuple[float, float, float], Vector] = (0, 0, 0), obj: Optional[Union[Vector, Location, Shape, Sketch]] = None) → None

make a workplane from a particular plane

パラメータ:

-

inPlane (a Plane object, or a string in (XY|YZ|XZ|front|back|top|bottom|left|right)) -- the plane in which the workplane will be done

-

origin (a 3-tuple in global coordinates, or None to default to the origin) -- the desired origin of the new workplane

-

obj (a CAD primitive, or None to use the centerpoint of the plane as the initial
stack value.) -- an object to use initially for the stack

Raises:

ValueError if the provided plane is not a plane, or one of XY|YZ|XZ

戻り値:

A Workplane object, with coordinate system matching the supplied plane.

The most common use is:

```python
s = Workplane("XY")

```

After creation, the stack contains a single point, the origin of the underlying plane, and
the current point is on the origin.

__iter__() → Iterator[Shape][ソース]

Special method for iterating over Shapes in objects

パラメータ:

self (T) --

戻り値の型:

Iterator[Shape]

__mul__(other: Union[Workplane, Solid, Compound]) → T[ソース]

Syntactic sugar for intersect.

Notice that `r = a * b` is equivalent to `r = a.intersect(b)`.

Example:

```python
Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
Sphere = Workplane("XY").sphere(1)
result = Box * Sphere

```

パラメータ:

-

self (T) --

-

other (Union[Workplane, Solid, Compound]) --

戻り値の型:

T

__or__(other: Union[Workplane, Solid, Compound]) → T[ソース]

Syntactic sugar for union.

Notice that `r = a | b` is equivalent to `r = a.union(b)` and `r = a + b`.

Example:

```python
Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
Sphere = Workplane("XY").sphere(1)
result = Box | Sphere

```

パラメータ:

-

self (T) --

-

other (Union[Workplane, Solid, Compound]) --

戻り値の型:

T

__sub__(other: Union[Workplane, Solid, Compound]) → T[ソース]

Syntactic sugar for cut.

Notice that `r = a - b` is equivalent to `r = a.cut(b)`.

Example:

```python
Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
Sphere = Workplane("XY").sphere(1)
result = Box - Sphere

```

パラメータ:

-

self (T) --

-

other (Union[Workplane, Solid, Compound]) --

戻り値の型:

T

__truediv__(other: Union[Workplane, Solid, Compound]) → T[ソース]

Syntactic sugar for intersect.

Notice that `r = a / b` is equivalent to `r = a.split(b)`.

Example:

```python
Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
Sphere = Workplane("XY").sphere(1)
result = Box / Sphere

```

パラメータ:

-

self (T) --

-

other (Union[Workplane, Solid, Compound]) --

戻り値の型:

T

__weakref__

list of weak references to the object (if defined)

add(obj: Workplane) → T[ソース]

add(obj: Union[Vector, Location, Shape, Sketch]) → T

add(obj: Iterable[Union[Vector, Location, Shape, Sketch]]) → T

Adds an object or a list of objects to the stack

パラメータ:

obj (a Workplane, CAD primitive, or list of CAD primitives) -- an object to add

戻り値:

a Workplane with the requested operation performed

If a Workplane object, the values of that object's stack are added. If
a list of cad primitives, they are all added. If a single CAD primitive
then it is added.

Used in rare cases when you need to combine the results of several CQ
results into a single Workplane object.

all() → List[T][ソース]

Return a list of all CQ objects on the stack.

useful when you need to operate on the elements
individually.

Contrast with vals, which returns the underlying
objects for all of the items on the stack

パラメータ:

self (T) --

戻り値の型:

List[T]

ancestors(kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound'], tag: Optional[str] = None) → T[ソース]

Select topological ancestors.

パラメータ:

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) -- kind of ancestor, e.g. "Face" or "Edge"

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a Workplane object whose stack contains selected ancestors.

戻り値の型:

T

apply(f: Callable[[Iterable[Union[Vector, Location, Shape, Sketch]]], Iterable[Union[Vector, Location, Shape, Sketch]]]) → T[ソース]

Apply a callable to all items at once.

パラメータ:

-

f (Callable[[Iterable[Union[Vector, Location, Shape, Sketch]]], Iterable[Union[Vector, Location, Shape, Sketch]]]) -- Callable to be applied.

-

self (T) --

戻り値:

Workplane object with f applied to all items.

戻り値の型:

T

bezier(listOfXYTuple: Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector]], forConstruction: bool = False, includeCurrent: bool = False, makeWire: bool = False) → T[ソース]

Make a cubic Bézier curve by the provided points (2D or 3D).

パラメータ:

-

listOfXYTuple (Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- Bezier control points and end point.
All points except the last point are Bezier control points,
and the last point is the end point

-

includeCurrent (bool) -- Use the current point as a starting point of the curve

-

makeWire (bool) -- convert the resulting bezier edge to a wire

-

self (T) --

-

forConstruction (bool) --

戻り値:

a Workplane object with the current point at the end of the bezier

戻り値の型:

T

The Bézier Will begin at either current point or the first point
of listOfXYTuple, and end with the last point of listOfXYTuple

box(length: float, width: float, height: float, centered: Union[bool, Tuple[bool, bool, bool]] = True, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Return a 3d box with specified dimensions for each object on the stack.

パラメータ:

-

length (float) -- box size in X direction

-

width (float) -- box size in Y direction

-

height (float) -- box size in Z direction

-

centered (Union[bool, Tuple[bool, bool, bool]]) -- If True, the box will be centered around the reference point.
If False, the corner of the box will be on the reference point and it will
extend in the positive x, y and z directions. Can also use a 3-tuple to
specify centering along each axis.

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- should the results be combined with other solids on the stack
(and each other)?

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値の型:

T

One box is created for each item on the current stack. If no items are on the stack, one box
using the current workplane center is created.

If combine is true, the result will be a single object on the stack. If a solid was found
in the chain, the result is that solid with all boxes produced fused onto it otherwise, the
result is the combination of all the produced boxes.

If combine is false, the result will be a list of the boxes produced.

Most often boxes form the basis for a part:

```python
# make a single box with lower left corner at origin
s = Workplane().box(1, 2, 3, centered=False)

```

But sometimes it is useful to create an array of them:

```python
# create 4 small square bumps on a larger base plate:
s = (
    Workplane()
    .box(4, 4, 0.5)
    .faces(">Z")
    .workplane()
    .rect(3, 3, forConstruction=True)
    .vertices()
    .box(0.25, 0.25, 0.25, combine=True)
)

```

cboreHole(diameter: float, cboreDiameter: float, cboreDepth: float, depth: Optional[float] = None, clean: bool = True) → T[ソース]

Makes a counterbored hole for each item on the stack.

パラメータ:

-

diameter (float) -- the diameter of the hole

-

cboreDiameter (float) -- the diameter of the cbore, must be greater than hole diameter

-

cboreDepth (float > 0) -- depth of the counterbore

-

depth (float > 0 or None to drill thru the entire part) -- the depth of the hole

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値の型:

T

The surface of the hole is at the current workplane plane.

One hole is created for each item on the stack.  A very common use case is to use a
construction rectangle to define the centers of a set of holes, like so:

```python
s = (
    Workplane()
    .box(2, 4, 0.5)
    .faces(">Z")
    .workplane()
    .rect(1.5, 3.5, forConstruction=True)
    .vertices()
    .cboreHole(0.125, 0.25, 0.125, depth=None)
)

```

This sample creates a plate with a set of holes at the corners.

Plugin Note: this is one example of the power of plugins. Counterbored holes are quite
time consuming to create, but are quite easily defined by users.

see `cskHole()` to make countersinks instead of counterbores

center(x: float, y: float) → T[ソース]

Shift local coordinates to the specified location.

The location is specified in terms of local coordinates.

パラメータ:

-

x (float) -- the new x location

-

y (float) -- the new y location

-

self (T) --

戻り値:

the Workplane object, with the center adjusted.

戻り値の型:

T

The current point is set to the new center.
This method is useful to adjust the center point after it has been created automatically on
a face, but not where you'd like it to be.

In this example, we adjust the workplane center to be at the corner of a cube, instead of
the center of a face, which is the default:

```python
# this workplane is centered at x=0.5,y=0.5, the center of the upper face
s = Workplane().box(1, 1, 1).faces(">Z").workplane()

s = s.center(-0.5, -0.5)  # move the center to the corner
t = s.circle(0.25).extrude(0.2)
assert t.faces().size() == 9  # a cube with a cylindrical nub at the top right corner

```

The result is a cube with a round boss on the corner

chamfer(length: float, length2: Optional[float] = None) → T[ソース]

Chamfers a solid on the selected edges.

The edges on the stack are chamfered. The solid to which the
edges belong must be in the parent chain of the selected
edges.

Optional parameter length2 can be supplied with a different
value than length for a chamfer that is shorter on one side
longer on the other side.

パラメータ:

-

length (float) -- the length of the chamfer, must be greater than zero

-

length2 (Optional[float]) -- optional parameter for asymmetrical chamfer

-

self (T) --

例外:

-

ValueError -- if at least one edge is not selected

-

ValueError -- if the solid containing the edge is not in the chain

戻り値:

CQ object with the resulting solid selected.

戻り値の型:

T

This example will create a unit cube, with the top edges chamfered:

```python
s = Workplane("XY").box(1, 1, 1).faces("+Z").chamfer(0.1)

```

This example will create chamfers longer on the sides:

```python
s = Workplane("XY").box(1, 1, 1).faces("+Z").chamfer(0.2, 0.1)

```

circle(radius: float, forConstruction: bool = False) → T[ソース]

Make a circle for each item on the stack.

パラメータ:

-

radius (float) -- radius of the circle

-

forConstruction (true if the wires are for reference, false if they are creating
part geometry) -- should the new wires be reference geometry only?

-

self (T) --

戻り値:

a new CQ object with the created wires on the stack

戻り値の型:

T

A common use case is to use a for-construction rectangle to define the centers of a
hole pattern:

```python
s = Workplane().rect(4.0, 4.0, forConstruction=True).vertices().circle(0.25)

```

Creates 4 circles at the corners of a square centered on the origin. Another common case is
to use successive circle() calls to create concentric circles.  This works because the
center of a circle is its reference point:

```python
s = Workplane().circle(2.0).circle(1.0)

```

Creates two concentric circles, which when extruded will form a ring.

Future Enhancements:

better way to handle forConstruction
project points not in the workplane plane onto the workplane plane

clean() → T[ソース]

Cleans the current solid by removing unwanted edges from the
faces.

Normally you don't have to call this function. It is
automatically called after each related operation. You can
disable this behavior with clean=False parameter if method
has any. In some cases this can improve performance
drastically but is generally dis-advised since it may break
some operations such as fillet.

Note that in some cases where lots of solid operations are
chained, clean() may actually improve performance since
the shape is 'simplified' at each step and thus next operation
is easier.

Also note that, due to limitation of the underlying engine,
clean may fail to produce a clean output in some cases such as
spherical faces.

パラメータ:

self (T) --

戻り値の型:

T

close() → T[ソース]

End construction, and attempt to build a closed wire.

戻り値:

a CQ object with a completed wire on the stack, if possible.

パラメータ:

self (T) --

戻り値の型:

T

After 2D (or 3D) drafting with methods such as lineTo, threePointArc,
tangentArcPoint and polyline, it is necessary to convert the edges
produced by these into one or more wires.

When a set of edges is closed, CadQuery assumes it is safe to build
the group of edges into a wire. This example builds a simple triangular
prism:

```python
s = Workplane().lineTo(1, 0).lineTo(1, 1).close().extrude(0.2)

```

combine(clean: bool = True, glue: bool = False, tol: Optional[float] = None) → T[ソース]

Attempts to combine all of the items on the stack into a single item.

WARNING: all of the items must be of the same type!

パラメータ:

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

glue (bool) -- use a faster gluing mode for non-overlapping shapes (default False)

-

tol (Optional[float]) -- tolerance value for fuzzy bool operation mode (default None)

-

self (T) --

Raises:

ValueError if there are no items on the stack, or if they cannot be combined

戻り値:

a CQ object with the resulting object selected

戻り値の型:

T

combineSolids(otherCQToCombine: Optional[Workplane] = None) → Workplane[ソース]

!!!DEPRECATED!!! use union()
Combines all solids on the current stack, and any context object, together
into a single object.

After the operation, the returned solid is also the context solid.

パラメータ:

otherCQToCombine (Optional[Workplane]) -- another CadQuery to combine.

戻り値:

a CQ object with the resulting combined solid on the stack.

戻り値の型:

Workplane

Most of the time, both objects will contain a single solid, which is
combined and returned on the stack of the new object.

compounds(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select compounds on the stack, optionally filtering the selection. If there are multiple
objects on the stack, they are collected and a list of all the distinct compounds
is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains all of the distinct compounds of all objects on
the current stack, filtered by the provided selector.

戻り値の型:

T

A compound contains multiple CAD primitives that resulted from a single operation, such as
a union, cut, split, or fillet.  Compounds can contain multiple edges, wires, or solids.

consolidateWires() → T[ソース]

Attempt to consolidate wires on the stack into a single.
If possible, a new object with the results are returned.
if not possible, the wires remain separated

パラメータ:

self (T) --

戻り値の型:

T

copyWorkplane(obj: T) → T[ソース]

Copies the workplane from obj.

パラメータ:

obj (a CQ object) -- an object to copy the workplane from

戻り値:

a CQ object with obj's workplane

戻り値の型:

T

cskHole(diameter: float, cskDiameter: float, cskAngle: float, depth: Optional[float] = None, clean: bool = True) → T[ソース]

Makes a countersunk hole for each item on the stack.

パラメータ:

-

diameter (float > 0) -- the diameter of the hole

-

cskDiameter (float) -- the diameter of the countersink, must be greater than hole diameter

-

cskAngle (float > 0) -- angle of the countersink, in degrees ( 82 is common )

-

depth (float > 0 or None to drill thru the entire part.) -- the depth of the hole

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値の型:

T

The surface of the hole is at the current workplane.

One hole is created for each item on the stack.  A very common use case is to use a
construction rectangle to define the centers of a set of holes, like so:

```python
s = (
    Workplane()
    .box(2, 4, 0.5)
    .faces(">Z")
    .workplane()
    .rect(1.5, 3.5, forConstruction=True)
    .vertices()
    .cskHole(0.125, 0.25, 82, depth=None)
)

```

This sample creates a plate with a set of holes at the corners.

Plugin Note: this is one example of the power of plugins. CounterSunk holes are quite
time consuming to create, but are quite easily defined by users.

see `cboreHole()` to make counterbores instead of countersinks

cut(toCut: Union[Workplane, Solid, Compound], clean: bool = True, tol: Optional[float] = None) → T[ソース]

Cuts the provided solid from the current solid, IE, perform a solid subtraction.

パラメータ:

-

toCut (Union[Workplane, Solid, Compound]) -- a solid object, or a Workplane object having a solid

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

tol (Optional[float]) -- tolerance value for fuzzy bool operation mode (default None)

-

self (T) --

例外:

ValueError -- if there is no solid to subtract from in the chain

戻り値:

a Workplane object with the resulting object selected

戻り値の型:

T

cutBlind(until: Union[float, Literal['next', 'last'], Face], clean: bool = True, both: bool = False, taper: Optional[float] = None) → T[ソース]

Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.

Specify either a distance value, or one of "next", "last" to indicate a face to cut to.

Similar to extrude, except that a solid in the parent chain is required to remove material
from. cutBlind always removes material from a part.

パラメータ:

-

until (Union[float, Literal['next', 'last'], Face]) -- The distance to cut to, normal to the workplane plane. When a negative float
is passed the cut extends this far in the opposite direction to the normal of the plane
(i.e in the solid). The string "next" cuts until the next face orthogonal to the wire
normal.  "last" cuts to the last face. If an object of type Face is passed, then the cut
will extend until this face.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

both (bool) -- cut in both directions symmetrically

-

taper (Optional[float]) -- angle for optional tapered extrusion

-

self (T) --

例外:

ValueError -- if there is no solid to subtract from in the chain

戻り値:

a CQ object with the resulting object selected

戻り値の型:

T

see `cutThruAll()` to cut material from the entire part

cutEach(fcn: Callable[[Location], Shape], useLocalCoords: bool = False, clean: bool = True) → T[ソース]

Evaluates the provided function at each point on the stack (ie, eachpoint)
and then cuts the result from the context solid.

パラメータ:

-

fcn (Callable[[Location], Shape]) -- a function suitable for use in the eachpoint method: ie, that accepts a vector

-

useLocalCoords (bool) -- same as for `eachpoint()`

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

例外:

ValueError -- if no solids or compounds are found in the stack or parent chain

戻り値:

a CQ object that contains the resulting solid

戻り値の型:

T

cutThruAll(clean: bool = True, taper: float = 0) → T[ソース]

Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.
Cuts through all material in both normal directions of workplane.

Similar to extrude, except that a solid in the parent chain is required to remove material
from. cutThruAll always removes material from a part.

パラメータ:

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

-

taper (float) --

例外:

-

ValueError -- if there is no solid to subtract from in the chain

-

ValueError -- if there are no pending wires to cut with

戻り値:

a CQ object with the resulting object selected

戻り値の型:

T

see `cutBlind()` to cut material to a limited depth

cylinder(height: float, radius: float, direct: ~typing.Union[~typing.Tuple[float, float, float], ~cadquery.occ_impl.geom.Vector] = Vector: (0.0, 0.0, 1.0), angle: float = 360, centered: ~typing.Union[bool, ~typing.Tuple[bool, bool, bool]] = True, combine: ~typing.Union[bool, ~typing.Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Returns a cylinder with the specified radius and height for each point on the stack

パラメータ:

-

height (float) -- The height of the cylinder

-

radius (float) -- The radius of the cylinder

-

direct (A three-tuple) -- The direction axis for the creation of the cylinder

-

angle (float > 0) -- The angle to sweep the cylinder arc through

-

centered (Union[bool, Tuple[bool, bool, bool]]) -- If True, the cylinder will be centered around the reference point. If False,
the corner of a bounding box around the cylinder will be on the reference point and it
will extend in the positive x, y and z directions. Can also use a 3-tuple to specify
centering along each axis.

-

combine (true to combine shapes, false otherwise) -- Whether the results should be combined with other solids on the stack
(and each other)

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値:

A cylinder object for each point on the stack

戻り値の型:

T

One cylinder is created for each item on the current stack. If no items are on the stack, one
cylinder is created using the current workplane center.

If combine is true, the result will be a single object on the stack. If a solid was found
in the chain, the result is that solid with all cylinders produced fused onto it otherwise,
the result is the combination of all the produced cylinders.

If combine is false, the result will be a list of the cylinders produced.

each(callback: Callable[[Union[Vector, Location, Shape, Sketch]], Shape], useLocalCoordinates: bool = False, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Runs the provided function on each value in the stack, and collects the return values into
a new CQ object.

Special note: a newly created workplane always has its center point as its only stack item

パラメータ:

-

callBackFunction -- the function to call for each item on the current stack.

-

useLocalCoordinates (bool) -- should  values be converted from local coordinates first?

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

-

callback (Callable[[Union[Vector, Location, Shape, Sketch]], Shape]) --

戻り値の型:

T

The callback function must accept one argument, which is the item on the stack, and return
one object, which is collected. If the function returns None, nothing is added to the stack.
The object passed into the callBackFunction is potentially transformed to local coordinates,
if useLocalCoordinates is true

useLocalCoordinates is very useful for plugin developers.

If false, the callback function is assumed to be working in global coordinates.  Objects
created are added as-is, and objects passed into the function are sent in using global
coordinates

If true, the calling function is assumed to be  working in local coordinates.  Objects are
transformed to local coordinates before they are passed into the callback method, and result
objects are transformed to global coordinates after they are returned.

This allows plugin developers to create objects in local coordinates, without worrying
about the fact that the working plane is different than the global coordinate system.

TODO: wrapper object for Wire will clean up forConstruction flag everywhere

eachpoint(arg: Union[Shape, Workplane, Callable[[Location], Shape]], useLocalCoordinates: bool = False, combine: Union[bool, Literal['cut', 'a', 's']] = False, clean: bool = True) → T[ソース]

Same as each(), except arg is translated by the positions on the stack. If arg is a callback function, then the function is called for each point on the stack, and the resulting shape is used.
:return: CadQuery object which contains a list of  vectors (points ) on its stack.

パラメータ:

-

useLocalCoordinates (bool) -- should points be in local or global coordinates

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

-

arg (Union[Shape, Workplane, Callable[[Location], Shape]]) --

戻り値の型:

T

The resulting object has a point on the stack for each object on the original stack.
Vertices and points remain a point.  Faces, Wires, Solids, Edges, and Shells are converted
to a point by using their center of mass.

If the stack has zero length, a single point is returned, which is the center of the current
workplane/coordinate system

edges(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select the edges of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the edges of all objects are collected and a list of all the
distinct edges is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains all of the distinct edges of all objects on
the current stack, filtered by the provided selector.

戻り値の型:

T

If there are no edges for any objects on the current stack, an empty CQ object is returned

The typical use is to select the edges of a single object on the stack. For example:

```python
Workplane().box(1, 1, 1).faces("+Z").edges().size()

```

returns 4, because the topmost face of a cube will contain four edges. Similarly:

```python
Workplane().box(1, 1, 1).edges().size()

```

returns 12, because a cube has a total of 12 edges, And:

```python
Workplane().box(1, 1, 1).edges("|Z").size()

```

returns 4, because a cube has 4 edges parallel to the z direction

ellipse(x_radius: float, y_radius: float, rotation_angle: float = 0.0, forConstruction: bool = False) → T[ソース]

Make an ellipse for each item on the stack.

パラメータ:

-

x_radius (float) -- x radius of the ellipse (x-axis of plane the ellipse should lie in)

-

y_radius (float) -- y radius of the ellipse (y-axis of plane the ellipse should lie in)

-

rotation_angle (float) -- angle to rotate the ellipse

-

forConstruction (true if the wires are for reference, false if they are creating
part geometry) -- should the new wires be reference geometry only?

-

self (T) --

戻り値:

a new CQ object with the created wires on the stack

戻り値の型:

T

NOTE Due to a bug in opencascade (https://tracker.dev.opencascade.org/view.php?id=31290)
the center of mass (equals center for next shape) is shifted. To create concentric ellipses
use:

```python
Workplane("XY").center(10, 20).ellipse(100, 10).center(0, 0).ellipse(50, 5)

```

ellipseArc(x_radius: float, y_radius: float, angle1: float = 360, angle2: float = 360, rotation_angle: float = 0.0, sense: Literal[- 1, 1] = 1, forConstruction: bool = False, startAtCurrent: bool = True, makeWire: bool = False) → T[ソース]

Draw an elliptical arc with x and y radiuses either with start point at current point or
or current point being the center of the arc

パラメータ:

-

x_radius (float) -- x radius of the ellipse (along the x-axis of plane the ellipse should lie in)

-

y_radius (float) -- y radius of the ellipse (along the y-axis of plane the ellipse should lie in)

-

angle1 (float) -- start angle of arc

-

angle2 (float) -- end angle of arc (angle2 == angle1 return closed ellipse = default)

-

rotation_angle (float) -- angle to rotate the created ellipse / arc

-

sense (Literal[-1, 1]) -- clockwise (-1) or counter clockwise (1)

-

startAtCurrent (bool) -- True: start point of arc is moved to current point; False: center of
arc is on current point

-

makeWire (bool) -- convert the resulting arc edge to a wire

-

self (T) --

-

forConstruction (bool) --

戻り値の型:

T

end(n: int = 1) → Workplane[ソース]

Return the nth parent of this CQ element

パラメータ:

n (int) -- number of ancestor to return (default: 1)

戻り値の型:

a CQ object

Raises:

ValueError if there are no more parents in the chain.

For example:

```python
CQ(obj).faces("+Z").vertices().end()

```

will return the same as:

```python
CQ(obj).faces("+Z")

```

export(fname: str, tolerance: float = 0.1, angularTolerance: float = 0.1, opt: Optional[Dict[str, Any]] = None) → T[ソース]

Export Workplane to file.

パラメータ:

-

path -- Filename.

-

tolerance (float) -- the deflection tolerance, in model units. Default 0.1.

-

angularTolerance (float) -- the angular tolerance, in radians. Default 0.1.

-

opt (Optional[Dict[str, Any]]) -- additional options passed to the specific exporter. Default None.

-

self (T) --

-

fname (str) --

戻り値:

Self.

戻り値の型:

T

exportSvg(fileName: str) → None[ソース]

Exports the first item on the stack as an SVG file

For testing purposes mainly.

パラメータ:

fileName (str) -- the filename to export, absolute path to the file

戻り値の型:

None

extrude(until: Union[float, Literal['next', 'last'], Face], combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True, both: bool = False, taper: Optional[float] = None) → T[ソース]

Use all un-extruded wires in the parent chain to create a prismatic solid.

パラメータ:

-

until (Union[float, Literal['next', 'last'], Face]) -- The distance to extrude, normal to the workplane plane. When a float is
passed, the extrusion extends this far and a negative value is in the opposite direction
to the normal of the plane. The string "next" extrudes until the next face orthogonal to
the wire normal. "last" extrudes to the last face. If a object of type Face is passed then
the extrusion will extend until this face. Note that the Workplane must contain a Solid for extruding to a given face.

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

both (bool) -- extrude in both directions symmetrically

-

taper (Optional[float]) -- angle for optional tapered extrusion

-

self (T) --

戻り値:

a CQ object with the resulting solid selected.

戻り値の型:

T

The returned object is always a CQ object, and depends on whether combine is True, and
whether a context solid is already defined:

-
if combine is False, the new value is pushed onto the stack. Note that when extruding

until a specified face, combine can not be False

-
if combine is true, the value is combined with the context solid if it exists,

and the resulting solid becomes the new context solid.

faces(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select the faces of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the faces of all objects are collected and a list of all the
distinct faces is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains all of the distinct faces of all objects on
the current stack, filtered by the provided selector.

戻り値の型:

T

If there are no faces for any objects on the current stack, an empty CQ object
is returned.

The typical use is to select the faces of a single object on the stack. For example:

```python
Workplane().box(1, 1, 1).faces("+Z").size()

```

returns 1, because a cube has one face with a normal in the +Z direction. Similarly:

```python
Workplane().box(1, 1, 1).faces().size()

```

returns 6, because a cube has a total of 6 faces, And:

```python
Workplane().box(1, 1, 1).faces("|Z").size()

```

returns 2, because a cube has 2 faces having normals parallel to the z direction

fillet(radius: float) → T[ソース]

Fillets a solid on the selected edges.

The edges on the stack are filleted. The solid to which the edges belong must be in the
parent chain of the selected edges.

パラメータ:

-

radius (float) -- the radius of the fillet, must be > zero

-

self (T) --

例外:

-

ValueError -- if at least one edge is not selected

-

ValueError -- if the solid containing the edge is not in the chain

戻り値:

CQ object with the resulting solid selected.

戻り値の型:

T

This example will create a unit cube, with the top edges filleted:

```python
s = Workplane().box(1, 1, 1).faces("+Z").edges().fillet(0.1)

```

filter(f: Callable[[Union[Vector, Location, Shape, Sketch]], bool]) → T[ソース]

Filter items using a boolean predicate.

パラメータ:

-

f (Callable[[Union[Vector, Location, Shape, Sketch]], bool]) -- Callable to be used for filtering.

-

self (T) --

戻り値:

Workplane object with filtered items.

戻り値の型:

T

findFace(searchStack: bool = True, searchParents: bool = True) → Face[ソース]

Finds the first face object in the chain, searching from the current node
backwards through parents until one is found.

パラメータ:

-

searchStack (bool) -- should objects on the stack be searched first.

-

searchParents (bool) -- should parents be searched?

戻り値:

A face or None if no face is found.

戻り値の型:

Face

findSolid(searchStack: bool = True, searchParents: bool = True) → Union[Solid, Compound][ソース]

Finds the first solid object in the chain, searching from the current node
backwards through parents until one is found.

パラメータ:

-

searchStack (bool) -- should objects on the stack be searched first?

-

searchParents (bool) -- should parents be searched?

例外:

ValueError -- if no solid is found

戻り値の型:

Union[Solid, Compound]

This function is very important for chains that are modifying a single parent object,
most often a solid.

Most of the time, a chain defines or selects a solid, and then modifies it using workplanes
or other operations.

Plugin Developers should make use of this method to find the solid that should be modified,
if the plugin implements a unary operation, or if the operation will automatically merge its
results with an object already on the stack.

first() → T[ソース]

Return the first item on the stack

戻り値:

the first item on the stack.

戻り値の型:

a CQ object

パラメータ:

self (T) --

hLine(distance: float, forConstruction: bool = False) → T[ソース]

Make a horizontal line from the current point the provided distance

パラメータ:

-

distance (float) --

-

distance from current point

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

hLineTo(xCoord: float, forConstruction: bool = False) → T[ソース]

Make a horizontal line from the current point to the provided x coordinate.

Useful if it is more convenient to specify the end location rather than distance,
as in `hLine()`

パラメータ:

-

xCoord (float) -- x coordinate for the end of the line

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

hole(diameter: float, depth: Optional[float] = None, clean: bool = True) → T[ソース]

Makes a hole for each item on the stack.

パラメータ:

-

diameter (float) -- the diameter of the hole

-

depth (float > 0 or None to drill thru the entire part.) -- the depth of the hole

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値の型:

T

The surface of the hole is at the current workplane.

One hole is created for each item on the stack.  A very common use case is to use a
construction rectangle to define the centers of a set of holes, like so:

```python
s = (
    Workplane()
    .box(2, 4, 0.5)
    .faces(">Z")
    .workplane()
    .rect(1.5, 3.5, forConstruction=True)
    .vertices()
    .hole(0.125, 82)
)

```

This sample creates a plate with a set of holes at the corners.

Plugin Note: this is one example of the power of plugins. CounterSunk holes are quite
time consuming to create, but are quite easily defined by users.

see `cboreHole()` and `cskHole()` to make counterbores or countersinks

interpPlate(surf_edges: Union[Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]], Sequence[Union[Edge, Wire]], Workplane], surf_pts: Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]] = [], thickness: float = 0, combine: Union[bool, Literal['cut', 'a', 's']] = False, clean: bool = True, degree: int = 3, nbPtsOnCur: int = 15, nbIter: int = 2, anisotropy: bool = False, tol2d: float = 1e-05, tol3d: float = 0.0001, tolAng: float = 0.01, tolCurv: float = 0.1, maxDeg: int = 8, maxSegments: int = 9) → T[ソース]

Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points, and going
through 'surf_pts' points.  Using pushPoints directly with interpPlate and combine=True, can be
very resource intensive depending on the complexity of the shape. In this case set combine=False.

パラメータ:

-

surf_edges (Union[Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]], Sequence[Union[Edge, Wire]], Workplane]) -- list of [x,y,z] ordered coordinates or list of ordered or unordered edges, wires

-

surf_pts (Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- list of points (uses only edges if [])

-

thickness (float) -- value may be negative or positive depending on thickening direction (2D surface if 0)

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- should the results be combined with other solids on the stack (and each other)?

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

degree (int) -- >= 2

-

nbPtsOnCur (int) -- number of points on curve >= 15

-

nbIter (int) -- number of iterations >= 2

-

anisotropy (bool) -- = bool Anisotropy

-

tol2d (float) -- 2D tolerance

-

tol3d (float) -- 3D tolerance

-

tolAng (float) -- angular tolerance

-

tolCurv (float) -- tolerance for curvature

-

maxDeg (int) -- highest polynomial degree >= 2

-

maxSegments (int) -- greatest number of segments >= 2

-

self (T) --

戻り値の型:

T

intersect(toIntersect: Union[Workplane, Solid, Compound], clean: bool = True, tol: Optional[float] = None) → T[ソース]

Intersects the provided solid from the current solid.

パラメータ:

-

toIntersect (Union[Workplane, Solid, Compound]) -- a solid object, or a Workplane object having a solid

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

tol (Optional[float]) -- tolerance value for fuzzy bool operation mode (default None)

-

self (T) --

例外:

ValueError -- if there is no solid to intersect with in the chain

戻り値:

a Workplane object with the resulting object selected

戻り値の型:

T

invoke(f: Union[Callable[[T], T], Callable[[T], None], Callable[[], None]]) → T[ソース]

Invoke a callable mapping Workplane to Workplane or None. Supports also
callables that take no arguments such as breakpoint. Returns self if callable
returns None.

パラメータ:

-

f (Union[Callable[[T], T], Callable[[T], None], Callable[[], None]]) -- Callable to be invoked.

-

self (T) --

戻り値:

Workplane object.

戻り値の型:

T

item(i: int) → T[ソース]

Return the ith item on the stack.

戻り値の型:

a CQ object

パラメータ:

-

self (T) --

-

i (int) --

largestDimension() → float[ソース]

Finds the largest dimension in the stack.

Used internally to create thru features, this is how you can compute
how long or wide a feature must be to make sure to cut through all of the material

例外:

ValueError -- if no solids or compounds are found

戻り値:

A value representing the largest dimension of the first solid on the stack

戻り値の型:

float

last() → T[ソース]

Return the last item on the stack.

戻り値の型:

a CQ object

パラメータ:

self (T) --

line(xDist: float, yDist: float, forConstruction: bool = False) → T[ソース]

Make a line from the current point to the provided point, using
dimensions relative to the current point

パラメータ:

-

xDist (float) -- x distance from current point

-

yDist (float) -- y distance from current point

-

self (T) --

-

forConstruction (bool) --

戻り値:

the workplane object with the current point at the end of the new line

戻り値の型:

T

see `lineTo()` if you want to use absolute coordinates to make a line instead.

lineTo(x: float, y: float, forConstruction: bool = False) → T[ソース]

Make a line from the current point to the provided point

パラメータ:

-

x (float) -- the x point, in workplane plane coordinates

-

y (float) -- the y point, in workplane plane coordinates

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

See `line()` if you want to use relative dimensions to make a line instead.

loft(ruled: bool = False, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Make a lofted solid, through the set of wires.

パラメータ:

-

ruled (bool) -- When set to True connects each section linearly and without continuity

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値:

a Workplane object containing the created loft

戻り値の型:

T

map(f: Callable[[Union[Vector, Location, Shape, Sketch]], Union[Vector, Location, Shape, Sketch]]) → T[ソース]

Apply a callable to every item separately.

パラメータ:

-

f (Callable[[Union[Vector, Location, Shape, Sketch]], Union[Vector, Location, Shape, Sketch]]) -- Callable to be applied to every item separately.

-

self (T) --

戻り値:

Workplane object with f applied to all items.

戻り値の型:

T

mirror(mirrorPlane: Union[Literal['XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'], Tuple[float, float], Tuple[float, float, float], Vector, Face, Workplane] = 'XY', basePointVector: Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]] = None, union: bool = False) → T[ソース]

Mirror a single CQ object.

パラメータ:

-

mirrorPlane (string, one of "XY", "YX", "XZ", "ZX", "YZ", "ZY" the planes
or the normal vector of the plane eg (1,0,0) or a Face object) -- the plane to mirror about

-

basePointVector (Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- the base point to mirror about (this is overwritten if a Face is passed)

-

union (bool) -- If true will perform a union operation on the mirrored object

-

self (T) --

戻り値の型:

T

mirrorX() → T[ソース]

Mirror entities around the x axis of the workplane plane.

戻り値:

a new object with any free edges consolidated into as few wires as possible.

パラメータ:

self (T) --

戻り値の型:

T

All free edges are collected into a wire, and then the wire is mirrored,
and finally joined into a new wire

Typically used to make creating wires with symmetry easier.

mirrorY() → T[ソース]

Mirror entities around the y axis of the workplane plane.

戻り値:

a new object with any free edges consolidated into as few wires as possible.

パラメータ:

self (T) --

戻り値の型:

T

All free edges are collected into a wire, and then the wire is mirrored,
and finally joined into a new wire

Typically used to make creating wires with symmetry easier. This line of code:

```python
s = Workplane().lineTo(2, 2).threePointArc((3, 1), (2, 0)).mirrorX().extrude(0.25)

```

Produces a flat, heart shaped object

move(xDist: float = 0, yDist: float = 0) → T[ソース]

Move the specified distance from the current point, without drawing.

パラメータ:

-

xDist (float, or none for zero) -- desired x distance, in local coordinates

-

yDist (float, or none for zero.) -- desired y distance, in local coordinates

-

self (T) --

戻り値の型:

T

Not to be confused with `center()`, which moves the center of the entire
workplane, this method only moves the current point ( and therefore does not affect objects
already drawn ).

See `moveTo()` to do the same thing but using absolute coordinates

moveTo(x: float = 0, y: float = 0) → T[ソース]

Move to the specified point, without drawing.

パラメータ:

-

x (float, or none for zero) -- desired x location, in local coordinates

-

y (float, or none for zero.) -- desired y location, in local coordinates

-

self (T) --

戻り値の型:

T

Not to be confused with `center()`, which moves the center of the entire
workplane, this method only moves the current point ( and therefore does not affect objects
already drawn ).

See `move()` to do the same thing but using relative dimensions

newObject(objlist: Iterable[Union[Vector, Location, Shape, Sketch]]) → T[ソース]

Create a new workplane object from this one.

Overrides CQ.newObject, and should be used by extensions, plugins, and
subclasses to create new objects.

パラメータ:

-

objlist (a list of CAD primitives) -- new objects to put on the stack

-

self (T) --

戻り値:

a new Workplane object with the current workplane as a parent.

戻り値の型:

T

offset2D(d: float, kind: Literal['arc', 'intersection', 'tangent'] = 'arc', forConstruction: bool = False) → T[ソース]

Creates a 2D offset wire.

パラメータ:

-

d (float) -- thickness. Negative thickness denotes offset to inside.

-

kind (Literal['arc', 'intersection', 'tangent']) -- offset kind. Use "arc" for rounded and "intersection" for sharp edges (default: "arc")

-

forConstruction (bool) -- Should the result be added to pending wires?

-

self (T) --

戻り値:

CQ object with resulting wire(s).

戻り値の型:

T

parametricCurve(func: Callable[[float], Union[Tuple[float, float], Tuple[float, float, float], Vector]], N: int = 400, start: float = 0, stop: float = 1, tol: float = 1e-06, minDeg: int = 1, maxDeg: int = 6, smoothing: Optional[Tuple[float, float, float]] = (1, 1, 1), makeWire: bool = True) → T[ソース]

Create a spline curve approximating the provided function.

パラメータ:

-

func (float --> (float,float,float)) -- function f(t) that will generate (x,y,z) pairs

-

N (int) -- number of points for discretization

-

start (float) -- starting value of the parameter t

-

stop (float) -- final value of the parameter t

-

tol (float) -- tolerance of the algorithm (default: 1e-6)

-

minDeg (int) -- minimum spline degree (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 6)

-

smoothing (Optional[Tuple[float, float, float]]) -- optional parameters for the variational smoothing algorithm (default: (1,1,1))

-

makeWire (bool) -- convert the resulting spline edge to a wire

-

self (T) --

戻り値:

a Workplane object with the current point unchanged

戻り値の型:

T

parametricSurface(func: Callable[[float, float], Union[Tuple[float, float], Tuple[float, float, float], Vector]], N: int = 20, start: float = 0, stop: float = 1, tol: float = 0.01, minDeg: int = 1, maxDeg: int = 6, smoothing: Optional[Tuple[float, float, float]] = (1, 1, 1)) → T[ソース]

Create a spline surface approximating the provided function.

パラメータ:

-

func ((float,float) --> (float,float,float)) -- function f(u,v) that will generate (x,y,z) pairs

-

N (int) -- number of points for discretization in one direction

-

start (float) -- starting value of the parameters u,v

-

stop (float) -- final value of the parameters u,v

-

tol (float) -- tolerance used by the approximation algorithm (default: 1e-3)

-

minDeg (int) -- minimum spline degree (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 3)

-

smoothing (Optional[Tuple[float, float, float]]) -- optional parameters for the variational smoothing algorithm (default: (1,1,1))

-

self (T) --

戻り値:

a Workplane object with the current point unchanged

戻り値の型:

T

This method might be unstable and may require tuning of the tol parameter.

placeSketch(*sketches: Sketch) → T[ソース]

Place the provided sketch(es) based on the current items on the stack.

戻り値:

Workplane object with the sketch added.

パラメータ:

-

self (T) --

-

sketches (Sketch) --

戻り値の型:

T

polarArray(radius: float, startAngle: float, angle: float, count: int, fill: bool = True, rotate: bool = True) → T[ソース]

Creates a polar array of points and pushes them onto the stack.
The zero degree reference angle is located along the local X-axis.

パラメータ:

-

radius (float) -- Radius of the array.

-

startAngle (float) -- Starting angle (degrees) of array. Zero degrees is
situated along the local X-axis.

-

angle (float) -- The angle (degrees) to fill with elements. A positive
value will fill in the counter-clockwise direction. If fill is
False, angle is the angle between elements.

-

count (int) -- Number of elements in array. (count >= 1)

-

fill (bool) -- Interpret the angle as total if True (default: True).

-

rotate (bool) -- Rotate every item (default: True).

-

self (T) --

戻り値の型:

T

polarLine(distance: float, angle: float, forConstruction: bool = False) → T[ソース]

Make a line of the given length, at the given angle from the current point

パラメータ:

-

distance (float) -- distance of the end of the line from the current point

-

angle (float) -- angle of the vector to the end of the line with the x-axis

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

polarLineTo(distance: float, angle: float, forConstruction: bool = False) → T[ソース]

Make a line from the current point to the given polar coordinates

Useful if it is more convenient to specify the end location rather than
the distance and angle from the current point

パラメータ:

-

distance (float) -- distance of the end of the line from the origin

-

angle (float) -- angle of the vector to the end of the line with the x-axis

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

polygon(nSides: int, diameter: float, forConstruction: bool = False, circumscribed: bool = False) → T[ソース]

Make a polygon for each item on the stack.

By default, each polygon is created by inscribing it in a circle of the
specified diameter, such that the first vertex is oriented in the x direction.
Alternatively, each polygon can be created by circumscribing it around
a circle of the specified diameter, such that the midpoint of the first edge
is oriented in the x direction. Circumscribed polygons are thus rotated by
pi/nSides radians relative to the inscribed polygon. This ensures the extent
of the polygon along the positive x-axis is always known.
This has the advantage of not requiring additional formulae for purposes such as
tiling on the x-axis (at least for even sided polygons).

パラメータ:

-

nSides (int) -- number of sides, must be >= 3

-

diameter (float) -- the diameter of the circle for constructing the polygon

-

circumscribed (true to create the polygon by circumscribing it about a circle,
false to create the polygon by inscribing it in a circle) -- circumscribe the polygon about a circle

-

self (T) --

-

forConstruction (bool) --

戻り値:

a polygon wire

戻り値の型:

T

polyline(listOfXYTuple: Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]], forConstruction: bool = False, includeCurrent: bool = False) → T[ソース]

Create a polyline from a list of points

パラメータ:

-

listOfXYTuple (Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- a list of points in Workplane coordinates (2D or 3D)

-

forConstruction (true if the edges are for reference, false if they are for creating geometry
part geometry) -- whether or not the edges are used for reference

-

includeCurrent (bool) -- use current point as a starting point of the polyline

-

self (T) --

戻り値:

a new CQ object with a list of edges on the stack

戻り値の型:

T

NOTE most commonly, the resulting wire should be closed.

pushPoints(pntList: Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector, Location]]) → T[ソース]

Pushes a list of points onto the stack as vertices.
The points are in the 2D coordinate space of the workplane face

パラメータ:

-

pntList (list of 2-tuples, in local coordinates) -- a list of points to push onto the stack

-

self (T) --

戻り値:

a new workplane with the desired points on the stack.

戻り値の型:

T

A common use is to provide a list of points for a subsequent operation, such as creating
circles or holes. This example creates a cube, and then drills three holes through it,
based on three points:

```python
s = (
    Workplane()
    .box(1, 1, 1)
    .faces(">Z")
    .workplane()
    .pushPoints([(-0.3, 0.3), (0.3, 0.3), (0, 0)])
)
body = s.circle(0.05).cutThruAll()

```

Here the circle function operates on all three points, and is then extruded to create three
holes. See `circle()` for how it works.

radiusArc(endPoint: Union[Tuple[float, float], Tuple[float, float, float], Vector], radius: float, forConstruction: bool = False) → T[ソース]

Draw an arc from the current point to endPoint with an arc defined by the radius.

パラメータ:

-

endPoint (2-tuple, in workplane coordinates) -- end point for the arc

-

radius (float, the radius of the arc between start point and end point.) -- the radius of the arc

-

self (T) --

-

forConstruction (bool) --

戻り値:

a workplane with the current point at the end of the arc

戻り値の型:

T

Given that a closed contour is drawn clockwise;
A positive radius means convex arc and negative radius means concave arc.

rarray(xSpacing: float, ySpacing: float, xCount: int, yCount: int, center: Union[bool, Tuple[bool, bool]] = True) → T[ソース]

Creates an array of points and pushes them onto the stack.
If you want to position the array at another point, create another workplane
that is shifted to the position you would like to use as a reference

パラメータ:

-

xSpacing (float) -- spacing between points in the x direction ( must be >= 0)

-

ySpacing (float) -- spacing between points in the y direction ( must be >= 0)

-

xCount (int) -- number of points ( > 0 )

-

yCount (int) -- number of points ( > 0 )

-

center (Union[bool, Tuple[bool, bool]]) -- If True, the array will be centered around the workplane center.
If False, the lower corner will be on the reference point and the array will
extend in the positive x and y directions. Can also use a 2-tuple to specify
centering along each axis.

-

self (T) --

戻り値の型:

T

rect(xLen: float, yLen: float, centered: Union[bool, Tuple[bool, bool]] = True, forConstruction: bool = False) → T[ソース]

Make a rectangle for each item on the stack.

パラメータ:

-

xLen (float) -- length in the x direction (in workplane coordinates)

-

yLen (float) -- length in the y direction (in workplane coordinates)

-

centered (Union[bool, Tuple[bool, bool]]) -- If True, the rectangle will be centered around the reference
point. If False, the corner of the rectangle will be on the reference point and
it will extend in the positive x and y directions. Can also use a 2-tuple to
specify centering along each axis.

-

forConstruction (true if the wires are for reference, false if they are creating part
geometry) -- should the new wires be reference geometry only?

-

self (T) --

戻り値:

a new CQ object with the created wires on the stack

戻り値の型:

T

A common use case is to use a for-construction rectangle to define the centers of a hole
pattern:

```python
s = Workplane().rect(4.0, 4.0, forConstruction=True).vertices().circle(0.25)

```

Creates 4 circles at the corners of a square centered on the origin.

Negative values for xLen and yLen are permitted, although they only have an effect when
centered is False.

Future Enhancements:

-

project points not in the workplane plane onto the workplane plane

revolve(angleDegrees: float = 360.0, axisStart: Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]] = None, axisEnd: Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]] = None, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Use all un-revolved wires in the parent chain to create a solid.

パラメータ:

-

angleDegrees (float, anything less than 360 degrees will leave the shape open) -- the angle to revolve through.

-

axisStart (Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- the start point of the axis of rotation

-

axisEnd (Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- the end point of the axis of rotation

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値:

a CQ object with the resulting solid selected.

戻り値の型:

T

The returned object is always a CQ object, and depends on whether combine is True, and
whether a context solid is already defined:

-

if combine is False, the new value is pushed onto the stack.

-

if combine is true, the value is combined with the context solid if it exists,
and the resulting solid becomes the new context solid.

注釈

Keep in mind that axisStart and axisEnd are defined relative to the current Workplane center position.
So if for example you want to revolve a circle centered at (10,0,0) around the Y axis, be sure to either `move()` (or `moveTo()`)
the current Workplane position or specify axisStart and axisEnd with the correct vector position.
In this example (0,0,0), (0,1,0) as axis coords would fail.

rotate(axisStartPoint: Union[Tuple[float, float], Tuple[float, float, float], Vector], axisEndPoint: Union[Tuple[float, float], Tuple[float, float, float], Vector], angleDegrees: float) → T[ソース]

Returns a copy of all of the items on the stack rotated through and angle around the axis
of rotation.

パラメータ:

-

axisStartPoint (a 3-tuple of floats) -- The first point of the axis of rotation

-

axisEndPoint (a 3-tuple of floats) -- The second point of the axis of rotation

-

angleDegrees (float) -- the rotation angle, in degrees

-

self (T) --

戻り値:

a CQ object

戻り値の型:

T

rotateAboutCenter(axisEndPoint: Union[Tuple[float, float], Tuple[float, float, float], Vector], angleDegrees: float) → T[ソース]

Rotates all items on the stack by the specified angle, about the specified axis

The center of rotation is a vector starting at the center of the object on the stack,
and ended at the specified point.

パラメータ:

-

axisEndPoint (a three-tuple in global coordinates) -- the second point of axis of rotation

-

angleDegrees (float) -- the rotation angle, in degrees

-

self (T) --

戻り値:

a CQ object, with all items rotated.

戻り値の型:

T

WARNING: This version returns the same CQ object instead of a new one-- the
old object is not accessible.

Future Enhancements:

-

A version of this method that returns a transformed copy, rather than modifying
the originals

-

This method doesn't expose a very good interface, because the axis of rotation
could be inconsistent between multiple objects.  This is because the beginning
of the axis is variable, while the end is fixed. This is fine when operating on
one object, but is not cool for multiple.

sagittaArc(endPoint: Union[Tuple[float, float], Tuple[float, float, float], Vector], sag: float, forConstruction: bool = False) → T[ソース]

Draw an arc from the current point to endPoint with an arc defined by the sag (sagitta).

パラメータ:

-

endPoint (2-tuple, in workplane coordinates) -- end point for the arc

-

sag (float, perpendicular distance from arc center to arc baseline.) -- the sagitta of the arc

-

self (T) --

-

forConstruction (bool) --

戻り値:

a workplane with the current point at the end of the arc

戻り値の型:

T

The sagitta is the distance from the center of the arc to the arc base.
Given that a closed contour is drawn clockwise;
A positive sagitta means convex arc and negative sagitta means concave arc.
See https://en.wikipedia.org/wiki/Sagitta_(geometry) for more information.

section(height: float = 0.0) → T[ソース]

Slices current solid at the given height.

パラメータ:

-

height (float) -- height to slice at (default: 0)

-

self (T) --

例外:

ValueError -- if no solids or compounds are found

戻り値:

a CQ object with the resulting face(s).

戻り値の型:

T

shell(thickness: float, kind: Literal['arc', 'intersection'] = 'arc') → T[ソース]

Remove the selected faces to create a shell of the specified thickness.

To shell, first create a solid, and in the same chain select the faces you wish to remove.

パラメータ:

-

thickness (float) -- thickness of the desired shell.
Negative values shell inwards, positive values shell outwards.

-

kind (Literal['arc', 'intersection']) -- kind of join, arc or intersection (default: arc).

-

self (T) --

例外:

ValueError -- if the current stack contains objects that are not faces of a solid
further up in the chain.

戻り値:

a CQ object with the resulting shelled solid selected.

戻り値の型:

T

This example will create a hollowed out unit cube, where the top most face is open,
and all other walls are 0.2 units thick:

```python
Workplane().box(1, 1, 1).faces("+Z").shell(0.2)

```

You can also select multiple faces at once. Here is an example that creates a three-walled
corner, by removing three faces of a cube:

```python
Workplane().box(10, 10, 10).faces(">Z or >X or <Y").shell(1)

```

Note:  When sharp edges are shelled inwards, they remain sharp corners, but outward
shells are automatically filleted (unless kind="intersection"), because an outward offset
from a corner generates a radius.

shells(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select the shells of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the shells of all objects are collected and a list of all the
distinct shells is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains all of the distinct shells of all objects on
the current stack, filtered by the provided selector.

戻り値の型:

T

If there are no shells for any objects on the current stack, an empty CQ object is returned

Most solids will have a single shell, which represents the outer surface. A shell will
typically be composed of multiple faces.

siblings(kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound'], level: int = 1, tag: Optional[str] = None) → T[ソース]

Select topological siblings.

パラメータ:

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) -- kind of linking element, e.g. "Vertex" or "Edge"

-

level (int) -- level of relation - how many elements of kind are in the link

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a Workplane object whose stack contains selected siblings.

戻り値の型:

T

size() → int[ソース]

Return the number of objects currently on the stack

戻り値の型:

int

sketch() → Sketch[ソース]

Initialize and return a sketch

戻り値:

Sketch object with the current workplane as a parent.

パラメータ:

self (T) --

戻り値の型:

Sketch

slot2D(length: float, diameter: float, angle: float = 0) → T[ソース]

Creates a rounded slot for each point on the stack.

パラメータ:

-

diameter (float) -- desired diameter, or width, of slot

-

length (float) -- desired end to end length of slot

-

angle (float) -- angle of slot in degrees, with 0 being along x-axis

-

self (T) --

戻り値:

a new CQ object with the created wires on the stack

戻り値の型:

T

Can be used to create arrays of slots, such as in cooling applications:

```python
Workplane().box(10, 25, 1).rarray(1, 2, 1, 10).slot2D(8, 1, 0).cutThruAll()

```

solids(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select the solids of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the solids of all objects are collected and a list of all the
distinct solids is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains all of the distinct solids of all objects on
the current stack, filtered by the provided selector.

戻り値の型:

T

If there are no solids for any objects on the current stack, an empty CQ object is returned

The typical use is to select a single object on the stack. For example:

```python
Workplane().box(1, 1, 1).solids().size()

```

returns 1, because a cube consists of one solid.

It is possible for a single CQ object ( or even a single CAD primitive ) to contain
multiple solids.

sort(key: Callable[[Union[Vector, Location, Shape, Sketch]], Any]) → T[ソース]

Sort items using a callable.

パラメータ:

-

key (Callable[[Union[Vector, Location, Shape, Sketch]], Any]) -- Callable to be used for sorting.

-

self (T) --

戻り値:

Workplane object with items sorted.

戻り値の型:

T

sphere(radius: float, direct: Union[Tuple[float, float], Tuple[float, float, float], Vector] = (0, 0, 1), angle1: float = - 90, angle2: float = 90, angle3: float = 360, centered: Union[bool, Tuple[bool, bool, bool]] = True, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Returns a 3D sphere with the specified radius for each point on the stack.

パラメータ:

-

radius (float) -- The radius of the sphere

-

direct (A three-tuple) -- The direction axis for the creation of the sphere

-

angle1 (float > 0) -- The first angle to sweep the sphere arc through

-

angle2 (float > 0) -- The second angle to sweep the sphere arc through

-

angle3 (float > 0) -- The third angle to sweep the sphere arc through

-

centered (Union[bool, Tuple[bool, bool, bool]]) -- If True, the sphere will be centered around the reference point. If False,
the corner of a bounding box around the sphere will be on the reference point and it
will extend in the positive x, y and z directions. Can also use a 3-tuple to specify
centering along each axis.

-

combine (true to combine shapes, false otherwise) -- Whether the results should be combined with other solids on the stack
(and each other)

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

戻り値:

A sphere object for each point on the stack

戻り値の型:

T

One sphere is created for each item on the current stack. If no items are on the stack, one
box using the current workplane center is created.

If combine is true, the result will be a single object on the stack. If a solid was found
in the chain, the result is that solid with all spheres produced fused onto it otherwise,
the result is the combination of all the produced spheres.

If combine is false, the result will be a list of the spheres produced.

spline(listOfXYTuple: Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector]], tangents: Optional[Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]]] = None, periodic: bool = False, parameters: Optional[Sequence[float]] = None, scale: bool = True, tol: Optional[float] = None, forConstruction: bool = False, includeCurrent: bool = False, makeWire: bool = False) → T[ソース]

Create a spline interpolated through the provided points (2D or 3D).

パラメータ:

-

listOfXYTuple (Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- points to interpolate through

-

tangents (Optional[Sequence[Union[Tuple[float, float], Tuple[float, float, float], Vector]]]) --

vectors specifying the direction of the tangent to the
curve at each of the specified interpolation points.

If only 2 tangents are given, they will be used as the initial and
final tangent.

If some tangents are not specified (i.e., are None), no tangent
constraint will be applied to the corresponding interpolation point.

The spline will be C2 continuous at the interpolation points where
no tangent constraint is specified, and C1 continuous at the points
where a tangent constraint is specified.

-

periodic (bool) -- creation of periodic curves

-

parameters (Optional[Sequence[float]]) --

the value of the parameter at each interpolation point.
(The interpolated curve is represented as a vector-valued function of a
scalar parameter.)

If periodic == True, then len(parameters) must be
len(interpolation points) + 1, otherwise len(parameters) must be equal to
len(interpolation points).

-

scale (bool) --

whether to scale the specified tangent vectors before
interpolating.

Each tangent is scaled, so it's length is equal to the derivative of
the Lagrange interpolated curve.

I.e., set this to True, if you want to use only the direction of
the tangent vectors specified by `tangents`, but not their magnitude.

-

tol (Optional[float]) --

tolerance of the algorithm (consult OCC documentation)

Used to check that the specified points are not too close to each
other, and that tangent vectors are not too short. (In either case
interpolation may fail.)

Set to None to use the default tolerance.

-

includeCurrent (bool) -- use current point as a starting point of the curve

-

makeWire (bool) -- convert the resulting spline edge to a wire

-

self (T) --

-

forConstruction (bool) --

戻り値:

a Workplane object with the current point at the end of the spline

戻り値の型:

T

The spline will begin at the current point, and end with the last point in the
XY tuple list.

This example creates a block with a spline for one side:

```python
s = Workplane(Plane.XY())
sPnts = [
    (2.75, 1.5),
    (2.5, 1.75),
    (2.0, 1.5),
    (1.5, 1.0),
    (1.0, 1.25),
    (0.5, 1.0),
    (0, 1.0),
]
r = s.lineTo(3.0, 0).lineTo(3.0, 1.0).spline(sPnts).close()
r = r.extrude(0.5)

```

WARNING  It is fairly easy to create a list of points
that cannot be correctly interpreted as a spline.

splineApprox(points: Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector]], tol: Optional[float] = 1e-06, minDeg: int = 1, maxDeg: int = 6, smoothing: Optional[Tuple[float, float, float]] = (1, 1, 1), forConstruction: bool = False, includeCurrent: bool = False, makeWire: bool = False) → T[ソース]

Create a spline interpolated through the provided points (2D or 3D).

パラメータ:

-

points (Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- points to interpolate through

-

tol (Optional[float]) -- tolerance of the algorithm (default: 1e-6)

-

minDeg (int) -- minimum spline degree (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 6)

-

smoothing (Optional[Tuple[float, float, float]]) -- optional parameters for the variational smoothing algorithm (default: (1,1,1))

-

includeCurrent (bool) -- use current point as a starting point of the curve

-

makeWire (bool) -- convert the resulting spline edge to a wire

-

self (T) --

-

forConstruction (bool) --

戻り値:

a Workplane object with the current point at the end of the spline

戻り値の型:

T

WARNING  for advanced users.

split(keepTop: bool = False, keepBottom: bool = False) → T[ソース]

split(splitter: Union[Workplane, Shape]) → T

Splits a solid on the stack into two parts, optionally keeping the separate parts.

パラメータ:

-

keepTop (bool) -- True to keep the top, False or None to discard it

-

keepBottom (bool) -- True to keep the bottom, False or None to discard it

例外:

-

ValueError -- if keepTop and keepBottom are both false.

-

ValueError -- if there is no solid in the current stack or parent chain

戻り値:

CQ object with the desired objects on the stack.

The most common operation splits a solid and keeps one half. This sample creates
a split bushing:

```python
# drill a hole in the side
c = Workplane().box(1, 1, 1).faces(">Z").workplane().circle(0.25).cutThruAll()

# now cut it in half sideways
c = c.faces(">Y").workplane(-0.5).split(keepTop=True)

```

sweep(path: Union[Workplane, Wire, Edge], multisection: bool = False, sweepAlongWires: Optional[bool] = None, makeSolid: bool = True, isFrenet: bool = False, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True, transition: Literal['right', 'round', 'transformed'] = 'right', normal: Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]] = None, auxSpine: Optional[Workplane] = None) → T[ソース]

Use all un-extruded wires in the parent chain to create a swept solid.

パラメータ:

-

path (Union[Workplane, Wire, Edge]) -- A wire along which the pending wires will be swept

-

multiSection -- False to create multiple swept from wires on the chain along path.
True to create only one solid swept along path with shape following the list of wires on the chain

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

transition (Literal['right', 'round', 'transformed']) -- handling of profile orientation at C1 path discontinuities. Possible values are {'transformed','round', 'right'} (default: 'right').

-

normal (Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- optional fixed normal for extrusion

-

auxSpine (Optional[Workplane]) -- a wire defining the binormal along the extrusion path

-

self (T) --

-

multisection (bool) --

-

sweepAlongWires (Optional[bool]) --

-

makeSolid (bool) --

-

isFrenet (bool) --

戻り値:

a CQ object with the resulting solid selected.

戻り値の型:

T

tag(name: str) → T[ソース]

Tags the current CQ object for later reference.

パラメータ:

-

name (str) -- the name to tag this object with

-

self (T) --

戻り値:

self, a CQ object with tag applied

戻り値の型:

T

tangentArcPoint(endpoint: Union[Tuple[float, float], Tuple[float, float, float], Vector], forConstruction: bool = False, relative: bool = True) → T[ソース]

Draw an arc as a tangent from the end of the current edge to endpoint.

パラメータ:

-

endpoint (2-tuple, 3-tuple or Vector) -- point for the arc to end at

-

relative (bool) -- True if endpoint is specified relative to the current point, False if endpoint is in workplane coordinates

-

self (T) --

-

forConstruction (bool) --

戻り値:

a Workplane object with an arc on the stack

戻り値の型:

T

Requires the the current first object on the stack is an Edge, as would
be the case after a lineTo operation or similar.

text(txt: str, fontsize: float, distance: float, cut: bool = True, combine: Union[bool, Literal['cut', 'a', 's']] = False, clean: bool = True, font: str = 'Arial', fontPath: Optional[str] = None, kind: Literal['regular', 'bold', 'italic'] = 'regular', halign: Literal['center', 'left', 'right'] = 'center', valign: Literal['center', 'top', 'bottom'] = 'center') → T[ソース]

Returns a 3D text.

パラメータ:

-

txt (str) -- text to be rendered

-

fontsize (float) -- size of the font in model units

-

distance (float, negative means opposite the normal direction) -- the distance to extrude or cut, normal to the workplane plane

-

cut (bool) -- True to cut the resulting solid from the parent solids if found

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

font (str) -- font name

-

fontPath (Optional[str]) -- path to font file

-

kind (Literal['regular', 'bold', 'italic']) -- font type

-

halign (Literal['center', 'left', 'right']) -- horizontal alignment

-

valign (Literal['center', 'top', 'bottom']) -- vertical alignment

-

self (T) --

戻り値:

a CQ object with the resulting solid selected

戻り値の型:

T

The returned object is always a Workplane object, and depends on whether combine is True, and
whether a context solid is already defined:

-

if combine is False, the new value is pushed onto the stack.

-

if combine is true, the value is combined with the context solid if it exists,
and the resulting solid becomes the new context solid.

Examples:

```python
cq.Workplane().text("CadQuery", 5, 1)

```

Specify the font (name), and kind to use an installed system font:

```python
cq.Workplane().text("CadQuery", 5, 1, font="Liberation Sans Narrow", kind="italic")

```

Specify fontPath to use a font from a given file:

```python
cq.Workplane().text("CadQuery", 5, 1, fontPath="/opt/fonts/texgyrecursor-bold.otf")

```

Cutting text into a solid:

```python
cq.Workplane().box(8, 8, 8).faces(">Z").workplane().text("Z", 5, -1.0)

```

threePointArc(point1: Union[Tuple[float, float], Tuple[float, float, float], Vector], point2: Union[Tuple[float, float], Tuple[float, float, float], Vector], forConstruction: bool = False) → T[ソース]

Draw an arc from the current point, through point1, and ending at point2

パラメータ:

-

point1 (2-tuple, in workplane coordinates) -- point to draw through

-

point2 (2-tuple, in workplane coordinates) -- end point for the arc

-

self (T) --

-

forConstruction (bool) --

戻り値:

a workplane with the current point at the end of the arc

戻り値の型:

T

Future Enhancements:

provide a version that allows an arc using relative measures
provide a centerpoint arc
provide tangent arcs

toOCC() → Any[ソース]

Directly returns the wrapped OCCT object.

戻り値:

The wrapped OCCT object

戻り値の型:

TopoDS_Shape or a subclass

toPending() → T[ソース]

Adds wires/edges to pendingWires/pendingEdges.

戻り値:

same CQ object with updated context.

パラメータ:

self (T) --

戻り値の型:

T

toSvg(opts: Optional[Any] = None) → str[ソース]

Returns svg text that represents the first item on the stack.

for testing purposes.

パラメータ:

opts (dictionary, width and height) -- svg formatting options

戻り値:

a string that contains SVG that represents this item.

戻り値の型:

str

transformed(rotate: Union[Tuple[float, float], Tuple[float, float, float], Vector] = (0, 0, 0), offset: Union[Tuple[float, float], Tuple[float, float, float], Vector] = (0, 0, 0)) → T[ソース]

Create a new workplane based on the current one.
The origin of the new plane is located at the existing origin+offset vector, where offset is
given in coordinates local to the current plane
The new plane is rotated through the angles specified by the components of the rotation
vector.

パラメータ:

-

rotate (Union[Tuple[float, float], Tuple[float, float, float], Vector]) -- 3-tuple of angles to rotate, in degrees relative to work plane coordinates

-

offset (Union[Tuple[float, float], Tuple[float, float, float], Vector]) -- 3-tuple to offset the new plane, in local work plane coordinates

-

self (T) --

戻り値:

a new work plane, transformed as requested

戻り値の型:

T

translate(vec: Union[Tuple[float, float], Tuple[float, float, float], Vector]) → T[ソース]

Returns a copy of all of the items on the stack moved by the specified translation vector.

パラメータ:

-

tupleDistance (a 3-tuple of float) -- distance to move, in global coordinates

-

self (T) --

-

vec (Union[Tuple[float, float], Tuple[float, float, float], Vector]) --

戻り値:

a CQ object

戻り値の型:

T

twistExtrude(distance: float, angleDegrees: float, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Extrudes a wire in the direction normal to the plane, but also twists by the specified
angle over the length of the extrusion.

The center point of the rotation will be the center of the workplane.

See extrude for more details, since this method is the same except for the the addition
of the angle. In fact, if angle=0, the result is the same as a linear extrude.

NOTE  This method can create complex calculations, so be careful using it with
complex geometries

パラメータ:

-

distance (float) -- the distance to extrude normal to the workplane

-

angle -- angle (in degrees) to rotate through the extrusion

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- True or "a" to combine the resulting solid with parent solids if found,
"cut" or "s" to remove the resulting solid from the parent solids if found.
False to keep the resulting solid separated from the parent solids.

-

clean (bool) -- call `clean()` afterwards to have a clean shape

-

self (T) --

-

angleDegrees (float) --

戻り値:

a CQ object with the resulting solid selected.

戻り値の型:

T

union(toUnion: Optional[Union[Workplane, Solid, Compound]] = None, clean: bool = True, glue: bool = False, tol: Optional[float] = None) → T[ソース]

Unions all of the items on the stack of toUnion with the current solid.
If there is no current solid, the items in toUnion are unioned together.

パラメータ:

-

toUnion (Optional[Union[Workplane, Solid, Compound]]) -- a solid object, or a Workplane object having a solid

-

clean (bool) -- call `clean()` afterwards to have a clean shape (default True)

-

glue (bool) -- use a faster gluing mode for non-overlapping shapes (default False)

-

tol (Optional[float]) -- tolerance value for fuzzy bool operation mode (default None)

-

self (T) --

Raises:

ValueError if there is no solid to add to in the chain

戻り値:

a Workplane object with the resulting object selected

戻り値の型:

T

vLine(distance: float, forConstruction: bool = False) → T[ソース]

Make a vertical line from the current point the provided distance

パラメータ:

-

distance (float) --

-

distance from current point

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

vLineTo(yCoord: float, forConstruction: bool = False) → T[ソース]

Make a vertical line from the current point to the provided y coordinate.

Useful if it is more convenient to specify the end location rather than distance,
as in `vLine()`

パラメータ:

-

yCoord (float) -- y coordinate for the end of the line

-

self (T) --

-

forConstruction (bool) --

戻り値:

the Workplane object with the current point at the end of the new line

戻り値の型:

T

val() → Union[Vector, Location, Shape, Sketch][ソース]

Return the first value on the stack. If no value is present, current plane origin is returned.

戻り値:

the first value on the stack.

戻り値の型:

A CAD primitive

vals() → List[Union[Vector, Location, Shape, Sketch]][ソース]

get the values in the current list

戻り値の型:

list of occ_impl objects

戻り値:

the values of the objects on the stack.

Contrast with `all()`, which returns CQ objects for all of the items on the stack

vertices(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select the vertices of objects on the stack, optionally filtering the selection. If there
are multiple objects on the stack, the vertices of all objects are collected and a list of
all the distinct vertices is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains  the distinct vertices of all objects on the
current stack, after being filtered by the selector, if provided

戻り値の型:

T

If there are no vertices for any objects on the current stack, an empty CQ object
is returned

The typical use is to select the vertices of a single object on the stack. For example:

```python
Workplane().box(1, 1, 1).faces("+Z").vertices().size()

```

returns 4, because the topmost face of a cube will contain four vertices. While this:

```python
Workplane().box(1, 1, 1).faces().vertices().size()

```

returns 8, because a cube has a total of 8 vertices

Note Circles are peculiar, they have a single vertex at the center!

wedge(dx: float, dy: float, dz: float, xmin: float, zmin: float, xmax: float, zmax: float, pnt: ~typing.Union[~typing.Tuple[float, float], ~typing.Tuple[float, float, float], ~cadquery.occ_impl.geom.Vector] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~typing.Tuple[float, float], ~typing.Tuple[float, float, float], ~cadquery.occ_impl.geom.Vector] = Vector: (0.0, 0.0, 1.0), centered: ~typing.Union[bool, ~typing.Tuple[bool, bool, bool]] = True, combine: ~typing.Union[bool, ~typing.Literal['cut', 'a', 's']] = True, clean: bool = True) → T[ソース]

Returns a 3D wedge with the specified dimensions for each point on the stack.

パラメータ:

-

dx (float) -- Distance along the X axis

-

dy (float) -- Distance along the Y axis

-

dz (float) -- Distance along the Z axis

-

xmin (float) -- The minimum X location

-

zmin (float) -- The minimum Z location

-

xmax (float) -- The maximum X location

-

zmax (float) -- The maximum Z location

-

pnt (Union[Tuple[float, float], Tuple[float, float, float], Vector]) -- A vector (or tuple) for the origin of the direction for the wedge

-

dir (Union[Tuple[float, float], Tuple[float, float, float], Vector]) -- The direction vector (or tuple) for the major axis of the wedge

-

centered (Union[bool, Tuple[bool, bool, bool]]) -- If True, the wedge will be centered around the reference point.
If False, the corner of the wedge will be on the reference point and it will
extend in the positive x, y and z directions. Can also use a 3-tuple to
specify centering along each axis.

-

combine (Union[bool, Literal['cut', 'a', 's']]) -- Whether the results should be combined with other solids on the stack
(and each other)

-

clean (bool) -- True to attempt to have the kernel clean up the geometry, False otherwise

-

self (T) --

戻り値:

A wedge object for each point on the stack

戻り値の型:

T

One wedge is created for each item on the current stack. If no items are on the stack, one
wedge using the current workplane center is created.

If combine is True, the result will be a single object on the stack. If a solid was found
in the chain, the result is that solid with all wedges produced fused onto it otherwise,
the result is the combination of all the produced wedges.

If combine is False, the result will be a list of the wedges produced.

wire(forConstruction: bool = False) → T[ソース]

Returns a CQ object with all pending edges connected into a wire.

All edges on the stack that can be combined will be combined into a single wire object,
and other objects will remain on the stack unmodified. If there are no pending edges,
this method will just return self.

パラメータ:

-

forConstruction (bool) -- whether the wire should be used to make a solid, or if it is just
for reference

-

self (T) --

戻り値の型:

T

This method is primarily of use to plugin developers making utilities for 2D construction.
This method should be called when a user operation implies that 2D construction is
finished, and we are ready to begin working in 3d.

SEE '2D construction concepts' for a more detailed explanation of how CadQuery handles
edges, wires, etc.

Any non edges will still remain.

wires(selector: Optional[Union[str, Selector]] = None, tag: Optional[str] = None) → T[ソース]

Select the wires of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the wires of all objects are collected and a list of all the
distinct wires is returned.

パラメータ:

-

selector (Optional[Union[str, Selector]]) -- optional Selector object, or string selector expression
(see `StringSyntaxSelector`)

-

tag (Optional[str]) -- if set, search the tagged object instead of self

-

self (T) --

戻り値:

a CQ object whose stack contains all of the distinct wires of all objects on
the current stack, filtered by the provided selector.

戻り値の型:

T

If there are no wires for any objects on the current stack, an empty CQ object is returned

The typical use is to select the wires of a single object on the stack. For example:

```python
Workplane().box(1, 1, 1).faces("+Z").wires().size()

```

returns 1, because a face typically only has one outer wire

workplane(offset: float = 0.0, invert: bool = False, centerOption: Literal['CenterOfMass', 'ProjectedOrigin', 'CenterOfBoundBox'] = 'ProjectedOrigin', origin: Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]] = None) → T[ソース]

Creates a new 2D workplane, located relative to the first face on the stack.

パラメータ:

-

offset (float) -- offset for the workplane in its normal direction . Default

-

invert (bool) -- invert the normal direction from that of the face.

-

centerOption (string or None='ProjectedOrigin') -- how local origin of workplane is determined.

-

origin (Optional[Union[Tuple[float, float], Tuple[float, float, float], Vector]]) -- origin for plane center, requires 'ProjectedOrigin' centerOption.

-

self (T) --

戻り値の型:

Workplane object

The first element on the stack must be a face, a set of
co-planar faces or a vertex.  If a vertex, then the parent
item on the chain immediately before the vertex must be a
face.

The result will be a 2D working plane
with a new coordinate system set up as follows:

-

The centerOption parameter sets how the center is defined.
Options are 'CenterOfMass', 'CenterOfBoundBox', or 'ProjectedOrigin'.
'CenterOfMass' and 'CenterOfBoundBox' are in relation to the selected
face(s) or vertex (vertices). 'ProjectedOrigin' uses by default the current origin
or the optional origin parameter (if specified) and projects it onto the plane
defined by the selected face(s).

-

The Z direction will be the normal of the face, computed
at the center point.

-

The X direction will be parallel to the x-y plane. If the workplane is  parallel to
the global x-y plane, the x direction of the workplane will co-incide with the
global x direction.

Most commonly, the selected face will be planar, and the workplane lies in the same plane
of the face ( IE, offset=0). Occasionally, it is useful to define a face offset from
an existing surface, and even more rarely to define a workplane based on a face that is
not planar.

workplaneFromTagged(name: str) → Workplane[ソース]

Copies the workplane from a tagged parent.

パラメータ:

name (str) -- tag to search for

戻り値:

a CQ object with name's workplane

戻り値の型:

Workplane

cadquery.sortWiresByBuildOrder(wireList: List[Wire]) → List[List[Wire]][ソース]

Tries to determine how wires should be combined into faces.

Assume:

The wires make up one or more faces, which could have 'holes'
Outer wires are listed ahead of inner wires
there are no wires inside wires inside wires
( IE, islands -- we can deal with that later on )
none of the wires are construction wires

Compute:

one or more sets of wires, with the outer wire listed first, and inner
ones

Returns, list of lists.

パラメータ:

wireList (List[Wire]) --

戻り値の型:

List[List[Wire]]

class cadquery.occ_impl.shapes.CompSolid(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin3D`

a single compsolid

パラメータ:

obj (TopoDS_Shape) --

class cadquery.occ_impl.shapes.Compound(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin3D`

切断された固体の集合体

パラメータ:

obj (TopoDS_Shape) --

ancestors(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) → Compound[ソース]

Iterate over ancestors, i.e. shapes of same kind within shape that contain elements of self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

戻り値の型:

Compound

cut(*toCut: Shape, tol: Optional[float] = None) → Compound[ソース]

Remove the positional arguments from this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toCut (Shape) --

戻り値の型:

Compound

fuse(*toFuse: Shape, glue: bool = False, tol: Optional[float] = None) → Compound[ソース]

Fuse shapes together

パラメータ:

-

toFuse (Shape) --

-

glue (bool) --

-

tol (Optional[float]) --

戻り値の型:

Compound

intersect(*toIntersect: Shape, tol: Optional[float] = None) → Compound[ソース]

Intersection of the positional arguments and this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toIntersect (Shape) --

戻り値の型:

Compound

classmethod makeCompound(listOfShapes: Iterable[Shape]) → Compound[ソース]

Create a compound out of a list of shapes

パラメータ:

listOfShapes (Iterable[Shape]) --

戻り値の型:

Compound

classmethod makeText(text: str, size: float, height: float, font: str = 'Arial', fontPath: Optional[str] = None, kind: Literal['regular', 'bold', 'italic'] = 'regular', halign: Literal['center', 'left', 'right'] = 'center', valign: Literal['center', 'top', 'bottom'] = 'center', position: Plane = Plane(origin=(0.0, 0.0, 0.0), xDir=(1.0, 0.0, 0.0), normal=(0.0, 0.0, 1.0))) → Shape[ソース]

Create a 3D text

パラメータ:

-

text (str) --

-

size (float) --

-

height (float) --

-

font (str) --

-

fontPath (Optional[str]) --

-

kind (Literal['regular', 'bold', 'italic']) --

-

halign (Literal['center', 'left', 'right']) --

-

valign (Literal['center', 'top', 'bottom']) --

-

position (Plane) --

戻り値の型:

Shape

remove(*shape: Shape)[ソース]

Remove the specified shapes.

パラメータ:

shape (Shape) --

siblings(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound'], level: int = 1) → Compound[ソース]

Iterate over siblings, i.e. shapes within shape that share subshapes of kind with the elements of self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

-

level (int) --

戻り値の型:

Compound

class cadquery.occ_impl.shapes.Edge(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin1D`

面の境界を表すトリミングされた曲線

パラメータ:

obj (TopoDS_Shape) --

arcCenter() → Vector[ソース]

Center of an underlying circle or ellipse geometry.

戻り値の型:

Vector

close() → Union[Edge, Wire][ソース]

Close an Edge

戻り値の型:

Union[Edge, Wire]

hasPCurve(f: Face) → bool[ソース]

Check if self has a pcurve defined on f.

パラメータ:

f (Face) --

戻り値の型:

bool

classmethod makeBezier(points: List[Vector]) → Edge[ソース]

Create a cubic Bézier Curve from the points.

パラメータ:

points (List[Vector]) -- a list of Vectors that represent the points.
The edge will pass through the first and the last point,
and the inner points are Bézier control points.

戻り値:

An edge

戻り値の型:

Edge

classmethod makeEllipse(x_radius: float, y_radius: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), xdir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (1.0, 0.0, 0.0), angle1: float = 360.0, angle2: float = 360.0, sense: ~typing.Literal[-1, 1] = 1) → Edge[ソース]

Makes an Ellipse centered at the provided point, having normal in the provided direction.

パラメータ:

-

cls --

-

x_radius (float) -- x radius of the ellipse (along the x-axis of plane the ellipse should lie in)

-

y_radius (float) -- y radius of the ellipse (along the y-axis of plane the ellipse should lie in)

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the center of the ellipse

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the direction of the plane the ellipse should lie in

-

angle1 (float) -- start angle of arc

-

angle2 (float) -- end angle of arc (angle2 == angle1 return closed ellipse = default)

-

sense (Literal[-1, 1]) -- clockwise (-1) or counter clockwise (1)

-

xdir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値:

an Edge

戻り値の型:

Edge

classmethod makeLine(v1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Edge[ソース]

Create a line between two points

パラメータ:

-

v1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Vector that represents the first point

-

v2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Vector that represents the second point

戻り値:

A linear edge between the two provided points

戻り値の型:

Edge

classmethod makeSpline(listOfVector: List[Vector], tangents: Optional[Sequence[Vector]] = None, periodic: bool = False, parameters: Optional[Sequence[float]] = None, scale: bool = True, tol: float = 1e-06) → Edge[ソース]

Interpolate a spline through the provided points.

パラメータ:

-

listOfVector (List[Vector]) -- a list of Vectors that represent the points

-

tangents (Optional[Sequence[Vector]]) -- tuple of Vectors specifying start and finish tangent

-

periodic (bool) -- creation of periodic curves

-

parameters (Optional[Sequence[float]]) -- the value of the parameter at each interpolation point. (The interpolated
curve is represented as a vector-valued function of a scalar parameter.) If periodic ==
True, then len(parameters) must be len(intepolation points) + 1, otherwise len(parameters)
must be equal to len(interpolation points).

-

scale (bool) -- whether to scale the specified tangent vectors before interpolating. Each
tangent is scaled, so it's length is equal to the derivative of the Lagrange interpolated
curve. I.e., set this to True, if you want to use only the direction of the tangent
vectors specified by `tangents`, but not their magnitude.

-

tol (float) -- tolerance of the algorithm (consult OCC documentation). Used to check that the
specified points are not too close to each other, and that tangent vectors are not too
short. (In either case interpolation may fail.)

戻り値:

an Edge

戻り値の型:

Edge

classmethod makeSplineApprox(listOfVector: List[Vector], tol: float = 0.001, smoothing: Optional[Tuple[float, float, float]] = None, minDeg: int = 1, maxDeg: int = 6) → Edge[ソース]

Approximate a spline through the provided points.

パラメータ:

-

listOfVector (List[Vector]) -- a list of Vectors that represent the points

-

tol (float) -- tolerance of the algorithm (consult OCC documentation).

-

smoothing (Optional[Tuple[float, float, float]]) -- optional tuple of 3 weights use for variational smoothing (default: None)

-

minDeg (int) -- minimum spline degree. Enforced only when smothing is None (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 6)

戻り値:

an Edge

戻り値の型:

Edge

classmethod makeTangentArc(v1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v3: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Edge[ソース]

Makes a tangent arc from point v1, in the direction of v2 and ends at v3.

パラメータ:

-

cls --

-

v1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- start vector

-

v2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- tangent vector

-

v3 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- end vector

戻り値:

an edge

戻り値の型:

Edge

classmethod makeThreePointArc(v1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], v3: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Edge[ソース]

Makes a three point arc through the provided points

パラメータ:

-

cls --

-

v1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- start vector

-

v2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- middle vector

-

v3 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- end vector

戻り値:

an edge object through the three points

戻り値の型:

Edge

trim(u0: Union[float, int], u1: Union[float, int]) → Edge[ソース]

Trim the edge in the parametric space to (u0, u1).

NB: this operation is done on the base geometry.

パラメータ:

-

u0 (Union[float, int]) --

-

u1 (Union[float, int]) --

戻り値の型:

Edge

class cadquery.occ_impl.shapes.Face(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`

固体の境界の一部を表す有界面

パラメータ:

obj (TopoDS_Shape) --

Center() → Vector[ソース]

戻り値:

The point of the center of mass of this Shape

戻り値の型:

Vector

addHole(*inner: cadquery.occ_impl.shapes.Wire | cadquery.occ_impl.shapes.Edge) → Self[ソース]

Add one or more holes.

パラメータ:

inner (cadquery.occ_impl.shapes.Wire | cadquery.occ_impl.shapes.Edge) --

戻り値の型:

Self

chamfer2D(d: float, vertices: Iterable[Vertex]) → Face[ソース]

Apply 2D chamfer to a face

パラメータ:

-

d (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Face

extend(d: float, umin: bool = True, umax: bool = True, vmin: bool = True, vmax: bool = True) → Face[ソース]

Extend a face. Does not work well in periodic directions.

パラメータ:

-

d (float) -- length of the extension.

-

umin (bool) -- extend along the umin isoline.

-

umax (bool) -- extend along the umax isoline.

-

vmin (bool) -- extend along the vmin isoline.

-

vmax (bool) -- extend along the vmax isoline.

戻り値の型:

Face

fillet2D(radius: float, vertices: Iterable[Vertex]) → Face[ソース]

Apply 2D fillet to a face

パラメータ:

-

radius (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Face

isoline(param: Union[float, int], direction: Literal['u', 'v'] = 'v') → Edge[ソース]

Construct an isoline.

パラメータ:

-

param (Union[float, int]) --

-

direction (Literal['u', 'v']) --

戻り値の型:

Edge

isolines(params: Iterable[Union[float, int]], direction: Literal['u', 'v'] = 'v') → List[Edge][ソース]

Construct multiple isolines.

パラメータ:

-

params (Iterable[Union[float, int]]) --

-

direction (Literal['u', 'v']) --

戻り値の型:

List[Edge]

classmethod makeFromWires(outerWire: Wire, innerWires: List[Wire] = []) → Face[ソース]

Makes a planar face from one or more wires

パラメータ:

-

outerWire (Wire) --

-

innerWires (List[Wire]) --

戻り値の型:

Face

classmethod makeNSidedSurface(edges: ~typing.Iterable[~typing.Union[~cadquery.occ_impl.shapes.Edge, ~cadquery.occ_impl.shapes.Wire]], constraints: ~typing.Iterable[~typing.Union[~cadquery.occ_impl.shapes.Edge, ~cadquery.occ_impl.shapes.Wire, ~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]], ~OCP.gp.gp_Pnt]], continuity: ~OCP.GeomAbs.GeomAbs_Shape = <GeomAbs_Shape.GeomAbs_C0: 0>, degree: int = 3, nbPtsOnCur: int = 15, nbIter: int = 2, anisotropy: bool = False, tol2d: float = 1e-05, tol3d: float = 0.0001, tolAng: float = 0.01, tolCurv: float = 0.1, maxDeg: int = 8, maxSegments: int = 9) → Face[ソース]

Returns a surface enclosed by a closed polygon defined by 'edges' and 'constraints'.

パラメータ:

-

edges (list of edges or wires) -- edges

-

constraints (list of points or edges) -- constraints

-

continuity (GeomAbs_Shape) -- OCC.Core.GeomAbs continuity condition

-

degree (int) -- >=2

-

nbPtsOnCur (int) -- number of points on curve >= 15

-

nbIter (int) -- number of iterations >= 2

-

anisotropy (bool) -- bool Anisotropy

-

tol2d (float) -- 2D tolerance >0

-

tol3d (float) -- 3D tolerance >0

-

tolAng (float) -- angular tolerance

-

tolCurv (float) -- tolerance for curvature >0

-

maxDeg (int) -- highest polynomial degree >= 2

-

maxSegments (int) -- greatest number of segments >= 2

戻り値の型:

Face

classmethod makeRuledSurface(edgeOrWire1: Edge, edgeOrWire2: Edge) → Face[ソース]

classmethod makeRuledSurface(edgeOrWire1: Wire, edgeOrWire2: Wire) → Face

makeRuledSurface(Edge|Wire,Edge|Wire) -- Make a ruled surface
Create a ruled surface out of two edges or wires. If wires are used then
these must have the same number of edges

classmethod makeSplineApprox(points: List[List[Vector]], tol: float = 0.01, smoothing: Optional[Tuple[float, float, float]] = None, minDeg: int = 1, maxDeg: int = 3) → Face[ソース]

Approximate a spline surface through the provided points.

パラメータ:

-

points (List[List[Vector]]) -- a 2D list of Vectors that represent the points

-

tol (float) -- tolerance of the algorithm (consult OCC documentation).

-

smoothing (Optional[Tuple[float, float, float]]) -- optional tuple of 3 weights use for variational smoothing (default: None)

-

minDeg (int) -- minimum spline degree. Enforced only when smothing is None (default: 1)

-

maxDeg (int) -- maximum spline degree (default: 6)

戻り値の型:

Face

normalAt(locationVector: Optional[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]] = None) → Vector[ソース]

normalAt(u: Union[float, int], v: Union[float, int]) → Tuple[Vector, Vector]

Computes the normal vector at the desired location on the face.

戻り値:

a vector representing the direction

パラメータ:

locationVector (a vector that lies on the surface.) -- the location to compute the normal at. If none, the center of the face is used.

戻り値の型:

Vector

Computes the normal vector at the desired location in the u,v parameter space.

戻り値:

a vector representing the normal direction and the position

パラメータ:

-

u -- the u parametric location to compute the normal at.

-

v -- the v parametric location to compute the normal at.

-

locationVector (Optional[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) --

戻り値の型:

Vector

normals(us: Iterable[Union[float, int]], vs: Iterable[Union[float, int]]) → Tuple[List[Vector], List[Vector]][ソース]

Computes the normal vectors at the desired locations in the u,v parameter space.

戻り値:

a tuple of list of vectors representing the normal directions and the positions

パラメータ:

-

us (Iterable[Union[float, int]]) -- the u parametric locations to compute the normal at.

-

vs (Iterable[Union[float, int]]) -- the v parametric locations to compute the normal at.

戻り値の型:

Tuple[List[Vector], List[Vector]]

paramAt(pt: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Tuple[float, float][ソース]

Computes the (u,v) pair closest to a given vector.

戻り値:

(u, v) tuple

パラメータ:

pt (a vector that lies on or close to the surface.) -- the location to compute the normal at.

戻り値の型:

Tuple[float, float]

params(pts: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]], tol: float = 1e-09) → Tuple[List[float], List[float]][ソース]

Computes (u,v) pairs closest to given vectors.

戻り値:

list of (u, v) tuples

パラメータ:

-

pts (a list of vectors that lie on the surface.) -- the points to compute the normals at.

-

tol (float) --

戻り値の型:

Tuple[List[float], List[float]]

positionAt(u: Union[float, int], v: Union[float, int]) → Vector[ソース]

Computes the position vector at the desired location in the u,v parameter space.

戻り値:

a vector representing the position

パラメータ:

-

u (Union[float, int]) -- the u parametric location to compute the normal at.

-

v (Union[float, int]) -- the v parametric location to compute the normal at.

戻り値の型:

Vector

positions(uvs: Iterable[Tuple[Union[int, float], Union[int, float]]]) → List[Vector][ソース]

Computes position vectors at the desired locations in the u,v parameter space.

戻り値:

list of vectors corresponding to the requested u,v positions

パラメータ:

uvs (Iterable[Tuple[Union[int, float], Union[int, float]]]) -- iterable of u,v pairs.

戻り値の型:

List[Vector]

thicken(thickness: float) → Solid[ソース]

Return a thickened face

パラメータ:

thickness (float) --

戻り値の型:

Solid

toArcs(tolerance: float = 0.001) → Face[ソース]

Approximate planar face with arcs and straight line segments.

パラメータ:

tolerance (float) -- Approximation tolerance.

戻り値の型:

Face

toPln() → gp_Pln[ソース]

Convert this face to a gp_Pln.

Note the Location of the resulting plane may not equal the center of this face,
however the resulting plane will still contain the center of this face.

戻り値の型:

gp_Pln

trim(outer: Wire, *inner: Wire) → Self[ソース]

trim(u0: Union[float, int], u1: Union[float, int], v0: Union[float, int], v1: Union[float, int], tol: Union[float, int] = 1e-06) → Self

trim(pt1: Tuple[Union[int, float], Union[int, float]], pt2: Tuple[Union[int, float], Union[int, float]], pt3: Tuple[Union[int, float], Union[int, float]], *pts: Tuple[Union[int, float], Union[int, float]]) → Self

Trim the face in the (u,v) space to (u0, u1)x(v1, v2).

NB: this operation is done on the base geometry.

Trim the face using a polyline defined in the (u,v) space.

Trim using wires. The provided wires need to have a pcurve on self.

パラメータ:

-

u0 (Union[float, int]) --

-

u1 (Union[float, int]) --

-

v0 (Union[float, int]) --

-

v1 (Union[float, int]) --

-

tol (Union[float, int]) --

戻り値の型:

Self

uvBounds() → Tuple[float, float, float, float][ソース]

Parametric bounds (u_min, u_max, v_min, v_max).

戻り値の型:

Tuple[float, float, float, float]

class cadquery.occ_impl.shapes.Mixin1DProtocol(*args, **kwargs)[ソース]

ベースクラス: `ShapeProtocol`, `Protocol`

class cadquery.occ_impl.shapes.Shape(obj: TopoDS_Shape)[ソース]

ベースクラス: `object`

Represents a shape in the system. Wraps TopoDS_Shape.

パラメータ:

obj (TopoDS_Shape) --

Area() → float[ソース]

戻り値:

The surface area of all faces in this Shape

戻り値の型:

float

BoundingBox(tolerance: Optional[float] = None) → BoundBox[ソース]

Create a bounding box for this Shape.

パラメータ:

tolerance (Optional[float]) -- Tolerance value passed to `BoundBox`

戻り値:

A `BoundBox` object for this Shape

戻り値の型:

BoundBox

Center() → Vector[ソース]

戻り値:

The point of the center of mass of this Shape

戻り値の型:

Vector

CenterOfBoundBox(tolerance: Optional[float] = None) → Vector[ソース]

パラメータ:

tolerance (Optional[float]) -- Tolerance passed to the `BoundingBox()` method

戻り値:

Center of the bounding box of this shape

戻り値の型:

Vector

Closed() → bool[ソース]

戻り値:

The closedness flag

戻り値の型:

bool

static CombinedCenter(objects: Iterable[Shape]) → Vector[ソース]

Calculates the center of mass of multiple objects.

パラメータ:

objects (Iterable[Shape]) -- A list of objects with mass

戻り値の型:

Vector

static CombinedCenterOfBoundBox(objects: List[Shape]) → Vector[ソース]

Calculates the center of a bounding box of multiple objects.

パラメータ:

objects (List[Shape]) -- A list of objects

戻り値の型:

Vector

CompSolids() → List[CompSolid][ソース]

戻り値:

All the compsolids in this Shape

戻り値の型:

List[CompSolid]

Compounds() → List[Compound][ソース]

戻り値:

All the compounds in this Shape

戻り値の型:

List[Compound]

Edges() → List[Edge][ソース]

戻り値:

All the edges in this Shape

戻り値の型:

List[Edge]

Faces() → List[Face][ソース]

戻り値:

All the faces in this Shape

戻り値の型:

List[Face]

Shells() → List[Shell][ソース]

戻り値:

All the shells in this Shape

戻り値の型:

List[Shell]

Solids() → List[Solid][ソース]

戻り値:

All the solids in this Shape

戻り値の型:

List[Solid]

Vertices() → List[Vertex][ソース]

戻り値:

All the vertices in this Shape

戻り値の型:

List[Vertex]

Volume(tol: Optional[float] = None) → float[ソース]

戻り値:

The volume of this Shape

パラメータ:

tol (Optional[float]) --

戻り値の型:

float

Wires() → List[Wire][ソース]

戻り値:

All the wires in this Shape

戻り値の型:

List[Wire]

ancestors(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) → Compound[ソース]

Iterate over ancestors, i.e. shapes of same kind within shape that contain self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

戻り値の型:

Compound

classmethod cast(obj: TopoDS_Shape, forConstruction: bool = False) → Shape[ソース]

Returns the right type of wrapper, given a OCCT object

パラメータ:

-

obj (TopoDS_Shape) --

-

forConstruction (bool) --

戻り値の型:

Shape

static centerOfMass(obj: Shape) → Vector[ソース]

Calculates the center of 'mass' of an object.

パラメータ:

obj (Shape) -- Compute the center of mass of this object

戻り値の型:

Vector

clean() → T[ソース]

Experimental clean using ShapeUpgrade

パラメータ:

self (T) --

戻り値の型:

T

static computeMass(obj: Shape, tol: Optional[float] = None) → float[ソース]

Calculates the 'mass' of an object.

パラメータ:

-

obj (Shape) -- Compute the mass of this object

-

tol (Optional[float]) -- Numerical integration tolerance (optional).

戻り値の型:

float

copy(mesh: bool = False) → T[ソース]

Creates a new object that is a copy of this object.

パラメータ:

-

mesh (bool) -- should I copy the triangulation too (default: False)

-

self (T) --

戻り値:

a copy of the object

戻り値の型:

T

cut(*toCut: Shape, tol: Optional[float] = None) → Shape[ソース]

Remove the positional arguments from this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toCut (Shape) --

戻り値の型:

Shape

distance(other: Shape) → float[ソース]

Minimal distance between two shapes

パラメータ:

other (Shape) --

戻り値の型:

float

distances(*others: Shape) → Iterator[float][ソース]

Minimal distances to between self and other shapes

パラメータ:

others (Shape) --

戻り値の型:

Iterator[float]

edges(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select edges.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

export(fname: str, tolerance: float = 0.1, angularTolerance: float = 0.1, opt: Optional[Dict[str, Any]] = None)[ソース]

Export Shape to file.

パラメータ:

-

self (T) --

-

fname (str) --

-

tolerance (float) --

-

angularTolerance (float) --

-

opt (Optional[Dict[str, Any]]) --

exportBin(f: Union[str, BytesIO]) → bool[ソース]

Export this shape to a binary BREP file.

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

bool

exportBrep(f: Union[str, BytesIO]) → bool[ソース]

Export this shape to a BREP file

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

bool

exportStep(fileName: str, **kwargs) → IFSelect_ReturnStatus[ソース]

Export this shape to a STEP file.

kwargs is used to provide optional keyword arguments to configure the exporter.

パラメータ:

-

fileName (str) -- Path and filename for writing.

-

write_pcurves (bool) --

Enable or disable writing parametric curves to the STEP file. Default True.

If False, writes STEP file without pcurves. This decreases the size of the resulting STEP file.

-

precision_mode (int) -- Controls the uncertainty value for STEP entities. Specify -1, 0, or 1. Default 0.
See OCCT documentation.

戻り値の型:

IFSelect_ReturnStatus

exportStl(fileName: str, tolerance: float = 0.001, angularTolerance: float = 0.1, ascii: bool = False, relative: bool = True, parallel: bool = True) → bool[ソース]

Exports a shape to a specified STL file.

パラメータ:

-

fileName (str) -- The path and file name to write the STL output to.

-

tolerance (float) -- A linear deflection setting which limits the distance between a curve and its tessellation.
Setting this value too low will result in large meshes that can consume computing resources.
Setting the value too high can result in meshes with a level of detail that is too low.
Default is 1e-3, which is a good starting point for a range of cases.

-

angularTolerance (float) -- Angular deflection setting which limits the angle between subsequent segments in a polyline. Default is 0.1.

-

ascii (bool) -- Export the file as ASCII (True) or binary (False) STL format.  Default is binary.

-

relative (bool) -- If True, tolerance will be scaled by the size of the edge being meshed. Default is True.
Setting this value to True may cause large features to become faceted, or small features dense.

-

parallel (bool) -- If True, OCCT will use parallel processing to mesh the shape. Default is True.

戻り値の型:

bool

faces(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select faces.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

facesIntersectedByLine(point: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], axis: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], tol: float = 0.0001, direction: Optional[Literal['AlongAxis', 'Opposite']] = None)[ソース]

Computes the intersections between the provided line and the faces of this Shape

パラメータ:

-

point (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Base point for defining a line

-

axis (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- Axis on which the line rests

-

tol (float) -- Intersection tolerance

-

direction (Optional[Literal['AlongAxis', 'Opposite']]) -- Valid values: "AlongAxis", "Opposite";
If specified, will ignore all faces that are not in the specified direction
including the face where the point lies if it is the case

戻り値:

A list of intersected faces sorted by distance from point

fix() → T[ソース]

Try to fix shape if not valid

パラメータ:

self (T) --

戻り値の型:

T

fuse(*toFuse: Shape, glue: bool = False, tol: Optional[float] = None) → Shape[ソース]

Fuse the positional arguments with this Shape.

パラメータ:

-

glue (bool) -- Sets the glue option for the algorithm, which allows
increasing performance of the intersection of the input shapes

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toFuse (Shape) --

戻り値の型:

Shape

geomType() → Literal['Vertex', 'Wire', 'Shell', 'Solid', 'Compound', 'PLANE', 'CYLINDER', 'CONE', 'SPHERE', 'TORUS', 'BEZIER', 'BSPLINE', 'REVOLUTION', 'EXTRUSION', 'OFFSET', 'OTHER', 'LINE', 'CIRCLE', 'ELLIPSE', 'HYPERBOLA', 'PARABOLA'][ソース]

Gets the underlying geometry type.

Implementations can return any values desired, but the values the user
uses in type filters should correspond to these.

As an example, if a user does:

```python
CQ(object).faces("%mytype")

```

The expectation is that the geomType attribute will return 'mytype'

The return values depend on the type of the shape:

Vertex:  always 'Vertex'
Edge:   LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER,

BSPLINE, OFFSET, OTHER

Face:   PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE,

REVOLUTION, EXTRUSION, OFFSET, OTHER

Solid:  'Solid'
Shell:  'Shell'
Compound: 'Compound'
Wire:   'Wire'

戻り値:

A string according to the geometry type

戻り値の型:

Literal['Vertex', 'Wire', 'Shell', 'Solid', 'Compound', 'PLANE', 'CYLINDER', 'CONE', 'SPHERE', 'TORUS', 'BEZIER', 'BSPLINE', 'REVOLUTION', 'EXTRUSION', 'OFFSET', 'OTHER', 'LINE', 'CIRCLE', 'ELLIPSE', 'HYPERBOLA', 'PARABOLA']

hashCode() → int[ソース]

Returns a hashed value denoting this shape. It is computed from the
TShape and the Location. The Orientation is not used.

戻り値の型:

int

classmethod importBin(f: Union[str, BytesIO]) → Shape[ソース]

Import shape from a binary BREP file.

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

Shape

classmethod importBrep(f: Union[str, BytesIO]) → Shape[ソース]

Import shape from a BREP file

パラメータ:

f (Union[str, BytesIO]) --

戻り値の型:

Shape

intersect(*toIntersect: Shape, tol: Optional[float] = None) → Shape[ソース]

Intersection of the positional arguments and this Shape.

パラメータ:

-

tol (Optional[float]) -- Fuzzy mode tolerance

-

toIntersect (Shape) --

戻り値の型:

Shape

isEqual(other: Shape) → bool[ソース]

Returns True if two shapes are equal, i.e. if they share the same
TShape with the same Locations and Orientations. Also see
`isSame()`.

パラメータ:

other (Shape) --

戻り値の型:

bool

isNull() → bool[ソース]

Returns true if this shape is null. In other words, it references no
underlying shape with the potential to be given a location and an
orientation.

戻り値の型:

bool

isSame(other: Shape) → bool[ソース]

Returns True if other and this shape are same, i.e. if they share the
same TShape with the same Locations. Orientations may differ. Also see
`isEqual()`

パラメータ:

other (Shape) --

戻り値の型:

bool

isValid() → bool[ソース]

Returns True if no defect is detected on the shape S or any of its
subshapes. See the OCCT docs on BRepCheck_Analyzer::IsValid for a full
description of what is checked.

戻り値の型:

bool

locate(loc: Location) → T[ソース]

Apply a location in absolute sense to self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

located(loc: Location) → T[ソース]

Apply a location in absolute sense to a copy of self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

location() → Location[ソース]

Return the current location

戻り値の型:

Location

static matrixOfInertia(obj: Shape) → List[List[float]][ソース]

Calculates the matrix of inertia of an object.
Since the part's density is unknown, this result is inertia/density with units of [1/length].
:param obj: Compute the matrix of inertia of this object

パラメータ:

obj (Shape) --

戻り値の型:

List[List[float]]

mesh(tolerance: float, angularTolerance: float = 0.1)[ソース]

Generate triangulation if none exists.

パラメータ:

-

tolerance (float) --

-

angularTolerance (float) --

mirror(mirrorPlane: Union[Literal['XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'], Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]] = 'XY', basePointVector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]] = (0, 0, 0)) → Shape[ソース]

Applies a mirror transform to this Shape. Does not duplicate objects
about the plane.

パラメータ:

-

mirrorPlane (Union[Literal['XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'], Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- The direction of the plane to mirror about - one of
'XY', 'XZ' or 'YZ'

-

basePointVector (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- The origin of the plane to mirror about

戻り値:

The mirrored shape

戻り値の型:

Shape

move(loc: Location) → T[ソース]

move(x: Union[float, int] = 0, y: Union[float, int] = 0, z: Union[float, int] = 0, rx: Union[float, int] = 0, ry: Union[float, int] = 0, rz: Union[float, int] = 0) → T

move(loc: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

Apply a location in relative sense (i.e. update current location) to self.

Apply translation and rotation in relative sense (i.e. update current location) to self.

Apply a VectorLike in relative sense (i.e. update current location) to self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

moved(loc: Sequence[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) → T[ソース]

moved(x: Union[float, int] = 0, y: Union[float, int] = 0, z: Union[float, int] = 0, rx: Union[float, int] = 0, ry: Union[float, int] = 0, rz: Union[float, int] = 0) → T

moved(loc1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], loc2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], *locs: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

moved(locs: Sequence[Location]) → T

moved(loc: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T

moved(loc: Location) → T

moved(loc1: Location, loc2: Location, *locs: Location) → T

Apply a location in relative sense (i.e. update current location) to a copy of self.

Apply multiple locations.

Apply multiple locations.

Apply translation and rotation in relative sense to a copy of self.

Apply a VectorLike in relative sense to a copy of self.

Apply multiple VectorLikes in relative sense to a copy of self.

Apply multiple VectorLikes in relative sense to a copy of self.

パラメータ:

-

self (T) --

-

loc (Location) --

戻り値の型:

T

remove(*subshape: Shape) → Self[ソース]

Remove subshapes.

パラメータ:

subshape (Shape) --

戻り値の型:

Self

replace(old: Shape, *new: Shape) → Self[ソース]

Replace old subshape with new subshapes.

パラメータ:

-

old (Shape) --

-

new (Shape) --

戻り値の型:

Self

rotate(startVector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], endVector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angleDegrees: float) → T[ソース]

Rotates a shape around an axis.

パラメータ:

-

startVector (either a 3-tuple or a Vector) -- start point of rotation axis

-

endVector (either a 3-tuple or a Vector) -- end point of rotation axis

-

angleDegrees (float) -- angle to rotate, in degrees

-

self (T) --

戻り値:

a copy of the shape, rotated

戻り値の型:

T

scale(factor: float) → Shape[ソース]

Scales this shape through a transformation.

パラメータ:

factor (float) --

戻り値の型:

Shape

shells(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select shells.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

siblings(shape: Shape, kind: Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound'], level: int = 1) → Compound[ソース]

Iterate over siblings, i.e. shapes within shape that share subshapes of kind with self.

パラメータ:

-

shape (Shape) --

-

kind (Literal['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound']) --

-

level (int) --

戻り値の型:

Compound

solids(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select solids.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

split(*splitters: Shape) → Shape[ソース]

Split this shape with the positional arguments.

パラメータ:

splitters (Shape) --

戻り値の型:

Shape

toNURBS() → T[ソース]

Return a NURBS representation of a given shape.

パラメータ:

self (T) --

戻り値の型:

T

toSplines(degree: int = 3, tolerance: float = 0.001, nurbs: bool = False) → T[ソース]

Approximate shape with b-splines of the specified degree.

パラメータ:

-

degree (int) -- Maximum degree.

-

tolerance (float) -- Approximation tolerance.

-

nurbs (bool) -- Use rational splines.

-

self (T) --

戻り値の型:

T

toVtkPolyData(tolerance: Optional[float] = None, angularTolerance: Optional[float] = None, normals: bool = False) → vtkPolyData[ソース]

Convert shape to vtkPolyData

パラメータ:

-

tolerance (Optional[float]) --

-

angularTolerance (Optional[float]) --

-

normals (bool) --

戻り値の型:

vtkPolyData

transformGeometry(tMatrix: Matrix) → Shape[ソース]

Transforms this shape by tMatrix.

WARNING: transformGeometry will sometimes convert lines and circles to
splines, but it also has the ability to handle skew and stretching
transformations.

If your transformation is only translation and rotation, it is safer to
use `transformShape()`, which doesn't change the underlying type
of the geometry, but cannot handle skew transformations.

パラメータ:

tMatrix (Matrix) -- The transformation matrix

戻り値:

a copy of the object, but with geometry transformed instead
of just rotated.

戻り値の型:

Shape

transformShape(tMatrix: Matrix) → Shape[ソース]

Transforms this Shape by tMatrix. Also see `transformGeometry()`.

パラメータ:

tMatrix (Matrix) -- The transformation matrix

戻り値:

a copy of the object, transformed by the provided matrix,
with all objects keeping their type

戻り値の型:

Shape

translate(vector: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → T[ソース]

Translates this shape through a transformation.

パラメータ:

-

self (T) --

-

vector (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

T

vertices(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select vertices.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

wires(selector: Optional[Union[str, Selector]] = None) → Shape[ソース]

Select wires.

パラメータ:

selector (Optional[Union[str, Selector]]) --

戻り値の型:

Shape

class cadquery.occ_impl.shapes.ShapeProtocol(*args, **kwargs)[ソース]

ベースクラス: `Protocol`

class cadquery.occ_impl.shapes.Shell(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`

サーフェスの外側の境界線

パラメータ:

obj (TopoDS_Shape) --

classmethod makeShell(listOfFaces: Iterable[Face]) → Shell[ソース]

Makes a shell from faces.

パラメータ:

listOfFaces (Iterable[Face]) --

戻り値の型:

Shell

class cadquery.occ_impl.shapes.Solid(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin3D`

単体

パラメータ:

obj (TopoDS_Shape) --

addCavity(*shells: Union[Shell, Solid]) → Self[ソース]

Add one or more cavities.

パラメータ:

shells (Union[Shell, Solid]) --

戻り値の型:

Self

classmethod extrudeLinear(outerWire: Wire, innerWires: List[Wire], vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], taper: Union[float, int] = 0) → Solid[ソース]

classmethod extrudeLinear(face: Face, vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], taper: Union[float, int] = 0) → Solid

Attempt to extrude the list of wires into a prismatic solid in the provided direction

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

vecNormal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- a vector along which to extrude the wires

-

taper (Union[float, int]) -- taper angle, default=0

戻り値:

a Solid object

戻り値の型:

Solid

The wires must not intersect

Extruding wires is very non-trivial.  Nested wires imply very different geometry, and
there are many geometries that are invalid. In general, the following conditions must be met:

-

all wires must be closed

-

there cannot be any intersecting or self-intersecting wires

-

wires must be listed from outside in

-

more than one levels of nesting is not supported reliably

This method will attempt to sort the wires, but there is much work remaining to make this method
reliable.

classmethod extrudeLinearWithRotation(outerWire: Wire, innerWires: List[Wire], vecCenter: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angleDegrees: Union[float, int]) → Solid[ソース]

classmethod extrudeLinearWithRotation(face: Face, vecCenter: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], vecNormal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angleDegrees: Union[float, int]) → Solid

Creates a 'twisted prism' by extruding, while simultaneously rotating around the extrusion vector.

Though the signature may appear to be similar enough to extrudeLinear to merit combining them, the
construction methods used here are different enough that they should be separate.

At a high level, the steps followed are:

-

accept a set of wires

-

create another set of wires like this one, but which are transformed and rotated

-

create a ruledSurface between the sets of wires

-

create a shell and compute the resulting object

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

vecCenter (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- the center point about which to rotate.  the axis of rotation is defined by
vecNormal, located at vecCenter.

-

vecNormal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- a vector along which to extrude the wires

-

angleDegrees (Union[float, int]) -- the angle to rotate through while extruding

戻り値:

a Solid object

戻り値の型:

Solid

innerShells() → List[Shell][ソース]

Returns inner shells.

戻り値の型:

List[Shell]

classmethod interpPlate(surf_edges, surf_pts, thickness, degree=3, nbPtsOnCur=15, nbIter=2, anisotropy=False, tol2d=1e-05, tol3d=0.0001, tolAng=0.01, tolCurv=0.1, maxDeg=8, maxSegments=9) → Union[Solid, Face][ソース]

Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points, and going through 'surf_pts' points.

パラメータ:

-

surf_edges -- list of [x,y,z] float ordered coordinates
or list of ordered or unordered wires

-

surf_pts -- list of [x,y,z] float coordinates (uses only edges if [])

-

thickness -- thickness may be negative or positive depending on direction, (returns 2D surface if 0)

-

degree -- >=2

-

nbPtsOnCur -- number of points on curve >= 15

-

nbIter -- number of iterations >= 2

-

anisotropy -- bool Anisotropy

-

tol2d -- 2D tolerance >0

-

tol3d -- 3D tolerance >0

-

tolAng -- angular tolerance

-

tolCurv -- tolerance for curvature >0

-

maxDeg -- highest polynomial degree >= 2

-

maxSegments -- greatest number of segments >= 2

戻り値の型:

Union[Solid, Face]

static isSolid(obj: Shape) → bool[ソース]

Returns true if the object is a solid, false otherwise

パラメータ:

obj (Shape) --

戻り値の型:

bool

classmethod makeBox(length,width,height,[pnt,dir]) -- Make a box located in pnt with the dimensions (length,width,height)[ソース]

By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)

パラメータ:

-

length (float) --

-

width (float) --

-

height (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Solid

classmethod makeCone(radius1: float, radius2: float, height: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees: float = 360) → Solid[ソース]

Make a cone with given radii and height
By default pnt=Vector(0,0,0),
dir=Vector(0,0,1) and angle=360

パラメータ:

-

radius1 (float) --

-

radius2 (float) --

-

height (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees (float) --

戻り値の型:

Solid

classmethod makeCylinder(radius: float, height: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees: float = 360) → Solid[ソース]

makeCylinder(radius,height,[pnt,dir,angle]) --
Make a cylinder with a given radius and height
By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360

パラメータ:

-

radius (float) --

-

height (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees (float) --

戻り値の型:

Solid

classmethod makeLoft(listOfWire: List[Wire], ruled: bool = False) → Solid[ソース]

makes a loft from a list of wires
The wires will be converted into faces when possible-- it is presumed that nobody ever actually
wants to make an infinitely thin shell for a real FreeCADPart.

パラメータ:

-

listOfWire (List[Wire]) --

-

ruled (bool) --

戻り値の型:

Solid

classmethod makeSolid(shell: Shell) → Solid[ソース]

Makes a solid from a single shell.

パラメータ:

shell (Shell) --

戻り値の型:

Solid

classmethod makeSphere(radius: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees1: float = 0, angleDegrees2: float = 90, angleDegrees3: float = 360) → Shape[ソース]

Make a sphere with a given radius
By default pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0, angle2=90 and angle3=360

パラメータ:

-

radius (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees1 (float) --

-

angleDegrees2 (float) --

-

angleDegrees3 (float) --

戻り値の型:

Shape

classmethod makeTorus(radius1: float, radius2: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angleDegrees1: float = 0, angleDegrees2: float = 360) → Solid[ソース]

makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
Make a torus with a given radii and angles
By default pnt=Vector(0,0,0),dir=Vector(0,0,1),angle1=0
,angle1=360 and angle=360

パラメータ:

-

radius1 (float) --

-

radius2 (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angleDegrees1 (float) --

-

angleDegrees2 (float) --

戻り値の型:

Solid

classmethod makeWedge(dx: float, dy: float, dz: float, xmin: float, zmin: float, xmax: float, zmax: float, pnt: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0)) → Solid[ソース]

Make a wedge located in pnt
By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)

パラメータ:

-

dx (float) --

-

dy (float) --

-

dz (float) --

-

xmin (float) --

-

zmin (float) --

-

xmax (float) --

-

zmax (float) --

-

pnt (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Solid

outerShell() → Shell[ソース]

Returns outer shell.

戻り値の型:

Shell

classmethod revolve(outerWire: Wire, innerWires: List[Wire], angleDegrees: Union[float, int], axisStart: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], axisEnd: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Solid[ソース]

classmethod revolve(face: Face, angleDegrees: Union[float, int], axisStart: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], axisEnd: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Solid

Attempt to revolve the list of wires into a solid in the provided direction

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

angleDegrees (float, anything less than 360 degrees will leave the shape open) -- the angle to revolve through.

-

axisStart (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- the start point of the axis of rotation

-

axisEnd (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- the end point of the axis of rotation

戻り値:

a Solid object

戻り値の型:

Solid

The wires must not intersect

-

all wires must be closed

-

there cannot be any intersecting or self-intersecting wires

-

wires must be listed from outside in

-

more than one levels of nesting is not supported reliably

-

the wire(s) that you're revolving cannot be centered

This method will attempt to sort the wires, but there is much work remaining to make this method
reliable.

classmethod sweep(outerWire: Wire, innerWires: List[Wire], path: Union[Wire, Edge], makeSolid: bool = True, isFrenet: bool = False, mode: Optional[Union[Vector, Wire, Edge]] = None, transitionMode: Literal['transformed', 'round', 'right'] = 'transformed') → Shape[ソース]

classmethod sweep(face: Face, path: Union[Wire, Edge], makeSolid: bool = True, isFrenet: bool = False, mode: Optional[Union[Vector, Wire, Edge]] = None, transitionMode: Literal['transformed', 'round', 'right'] = 'transformed') → Shape

Attempt to sweep the list of wires into a prismatic solid along the provided path

パラメータ:

-

outerWire (Wire) -- the outermost wire

-

innerWires (List[Wire]) -- a list of inner wires

-

path (Union[Wire, Edge]) -- The wire to sweep the face resulting from the wires over

-

makeSolid (bool) -- return Solid or Shell (default True)

-

isFrenet (bool) -- Frenet mode (default False)

-

mode (Optional[Union[Vector, Wire, Edge]]) -- additional sweep mode parameters

-

transitionMode (Literal['transformed', 'round', 'right']) -- handling of profile orientation at C1 path discontinuities.
Possible values are {'transformed','round', 'right'} (default: 'right').

戻り値:

a Solid object

戻り値の型:

Shape

classmethod sweep_multi(profiles: Iterable[Union[Wire, Face]], path: Union[Wire, Edge], makeSolid: bool = True, isFrenet: bool = False, mode: Optional[Union[Vector, Wire, Edge]] = None) → Solid[ソース]

Multi section sweep. Only single outer profile per section is allowed.

パラメータ:

-

profiles (Iterable[Union[Wire, Face]]) -- list of profiles

-

path (Union[Wire, Edge]) -- The wire to sweep the face resulting from the wires over

-

mode (Optional[Union[Vector, Wire, Edge]]) -- additional sweep mode parameters.

-

makeSolid (bool) --

-

isFrenet (bool) --

戻り値:

a Solid object

戻り値の型:

Solid

class cadquery.occ_impl.shapes.Vertex(obj: TopoDS_Shape, forConstruction: bool = False)[ソース]

ベースクラス: `Shape`

空間の中の一点

パラメータ:

-

obj (TopoDS_Shape) --

-

forConstruction (bool) --

Center() → Vector[ソース]

The center of a vertex is itself!

戻り値の型:

Vector

class cadquery.occ_impl.shapes.Wire(obj: TopoDS_Shape)[ソース]

ベースクラス: `Shape`, `Mixin1D`

接続され、順序付けられた一連のEdgeで、通常、Faceを囲みます。

パラメータ:

obj (TopoDS_Shape) --

Vertices() → List[Vertex][ソース]

Ordered list of vertices of the wire.

戻り値の型:

List[Vertex]

classmethod assembleEdges(listOfEdges: Iterable[Edge]) → Wire[ソース]

Attempts to build a wire that consists of the edges in the provided list

パラメータ:

-

cls --

-

listOfEdges (Iterable[Edge]) -- a list of Edge objects. The edges are not to be consecutive.

戻り値:

a wire with the edges assembled

戻り値の型:

Wire

BRepBuilderAPI_MakeWire::Error() values:

-

BRepBuilderAPI_WireDone = 0

-

BRepBuilderAPI_EmptyWire = 1

-

BRepBuilderAPI_DisconnectedWire = 2

-

BRepBuilderAPI_NonManifoldWire = 3

chamfer2D(d: float, vertices: Iterable[Vertex]) → Wire[ソース]

Apply 2D chamfer to a wire

パラメータ:

-

d (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Wire

close() → Wire[ソース]

Close a Wire

戻り値の型:

Wire

classmethod combine(listOfWires: Iterable[Union[Wire, Edge]], tol: float = 1e-09) → List[Wire][ソース]

Attempt to combine a list of wires and edges into a new wire.

パラメータ:

-

cls --

-

listOfWires (Iterable[Union[Wire, Edge]]) --

-

tol (float) -- default 1e-9

戻り値:

List[Wire]

戻り値の型:

List[Wire]

fillet(radius: float, vertices: Optional[Iterable[Vertex]] = None) → Wire[ソース]

Apply 2D or 3D fillet to a wire

パラメータ:

-

radius (float) -- the radius of the fillet, must be > zero

-

vertices (Optional[Iterable[Vertex]]) -- the vertices to delete (where the fillet will be applied).  By default
all vertices are deleted except ends of open wires.

戻り値:

A wire with filleted corners

戻り値の型:

Wire

fillet2D(radius: float, vertices: Iterable[Vertex]) → Wire[ソース]

Apply 2D fillet to a wire

パラメータ:

-

radius (float) --

-

vertices (Iterable[Vertex]) --

戻り値の型:

Wire

classmethod makeCircle(radius: float, center: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], normal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Wire[ソース]

Makes a Circle centered at the provided point, having normal in the provided direction

パラメータ:

-

radius (float) -- floating point radius of the circle, must be > 0

-

center (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the center of the circle

-

normal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the direction of the plane the circle should lie in

戻り値の型:

Wire

classmethod makeEllipse(x_radius: float, y_radius: float, center: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], normal: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], xDir: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], angle1: float = 360.0, angle2: float = 360.0, rotation_angle: float = 0.0, closed: bool = True) → Wire[ソース]

Makes an Ellipse centered at the provided point, having normal in the provided direction

パラメータ:

-

x_radius (float) -- floating point major radius of the ellipse (x-axis), must be > 0

-

y_radius (float) -- floating point minor radius of the ellipse (y-axis), must be > 0

-

center (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the center of the circle

-

normal (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- vector representing the direction of the plane the circle should lie in

-

angle1 (float) -- start angle of arc

-

angle2 (float) -- end angle of arc

-

rotation_angle (float) -- angle to rotate the created ellipse / arc

-

xDir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

closed (bool) --

戻り値の型:

Wire

classmethod makeHelix(pitch: float, height: float, radius: float, center: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 0.0), dir: ~typing.Union[~cadquery.occ_impl.geom.Vector, ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float]], ~typing.Tuple[~typing.Union[int, float], ~typing.Union[int, float], ~typing.Union[int, float]]] = Vector: (0.0, 0.0, 1.0), angle: float = 360.0, lefthand: bool = False) → Wire[ソース]

Make a helix with a given pitch, height and radius
By default a cylindrical surface is used to create the helix. If
the fourth parameter is set (the apex given in degree) a conical surface is used instead'

パラメータ:

-

pitch (float) --

-

height (float) --

-

radius (float) --

-

center (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

dir (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

angle (float) --

-

lefthand (bool) --

戻り値の型:

Wire

classmethod makePolygon(listOfVertices: Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]], forConstruction: bool = False, close: bool = False) → Wire[ソース]

Construct a polygonal wire from points.

パラメータ:

-

listOfVertices (Iterable[Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) --

-

forConstruction (bool) --

-

close (bool) --

戻り値の型:

Wire

offset2D(d: float, kind: Literal['arc', 'intersection', 'tangent'] = 'arc') → List[Wire][ソース]

Offsets a planar wire

パラメータ:

-

d (float) --

-

kind (Literal['arc', 'intersection', 'tangent']) --

戻り値の型:

List[Wire]

stitch(other: Wire) → Wire[ソース]

Attempt to stitch wires

パラメータ:

other (Wire) --

戻り値の型:

Wire

cadquery.occ_impl.shapes.box(w: float, l: float, h: float) → Shape[ソース]

Construct a solid box.

パラメータ:

-

w (float) --

-

l (float) --

-

h (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.cap(s: Shape, ctx: Shape, constraints: Sequence[Union[Shape, Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]] = ()) → Shape[ソース]

Fill edges/wire possibly obeying constraints and try to connect smoothly to the context shape.

パラメータ:

-

s (Shape) --

-

ctx (Shape) --

-

constraints (Sequence[Union[Shape, Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.chamfer(s: Shape, e: Shape, d: float) → Shape[ソース]

Chamfer selected edges in a given shell or solid.

パラメータ:

-

s (Shape) --

-

e (Shape) --

-

d (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.check(s: Shape, results: Optional[List[Tuple[List[Shape], Any]]] = None, tol: Optional[float] = None) → bool[ソース]

Check if a shape is valid.

パラメータ:

-

s (Shape) --

-

results (Optional[List[Tuple[List[Shape], Any]]]) --

-

tol (Optional[float]) --

戻り値の型:

bool

cadquery.occ_impl.shapes.circle(r: float) → Shape[ソース]

Construct a circle.

パラメータ:

r (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.clean(s: Shape) → Shape[ソース]

Clean superfluous edges and faces.

パラメータ:

s (Shape) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.closest(s1: Shape, s2: Shape) → Tuple[Vector, Vector][ソース]

Closest points between two shapes.

パラメータ:

-

s1 (Shape) --

-

s2 (Shape) --

戻り値の型:

Tuple[Vector, Vector]

cadquery.occ_impl.shapes.compound(*s: cadquery.occ_impl.shapes.Shape) → cadquery.occ_impl.shapes.Shape[ソース]

Build compound from shapes.

compound(s: Sequence[cadquery.occ_impl.shapes.Shape]) -> cadquery.occ_impl.shapes.Shape

Build compound from a sequence of shapes.

パラメータ:

s (Shape) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.cone(d1: Union[float, int], d2: Union[float, int], h: Union[float, int]) → cadquery.occ_impl.shapes.Shape[ソース]

Construct a partial solid cone.

cone(d: Union[float, int], h: Union[float, int]) -> cadquery.occ_impl.shapes.Shape

Construct a full solid cone.

パラメータ:

-

d1 (Union[float, int]) --

-

d2 (Union[float, int]) --

-

h (Union[float, int]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.cut(s1: Shape, s2: Shape, tol: float = 0.0, glue: Optional[Literal['partial', 'full', None]] = None) → Shape[ソース]

Subtract two shapes.

パラメータ:

-

s1 (Shape) --

-

s2 (Shape) --

-

tol (float) --

-

glue (Optional[Literal['partial', 'full', None]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.cylinder(d: float, h: float) → Shape[ソース]

Construct a solid cylinder.

パラメータ:

-

d (float) --

-

h (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.downcast(obj: TopoDS_Shape) → TopoDS_Shape[ソース]

Downcasts a TopoDS object to suitable specialized type

パラメータ:

obj (TopoDS_Shape) --

戻り値の型:

TopoDS_Shape

cadquery.occ_impl.shapes.edgeOn(base: cadquery.occ_impl.shapes.Shape, pts: Sequence[Tuple[Union[int, float], Union[int, float]]], periodic: bool = False, tol: float = 1e-06) → cadquery.occ_impl.shapes.Shape[ソース]

Build an edge on a face from points in (u,v) space.

_(fbase: cadquery.occ_impl.shapes.Shape, edg: cadquery.occ_impl.shapes.Shape, *edgs: cadquery.occ_impl.shapes.Shape, tol: float = 1e-06, N: int = 20)

Map one or more edges onto a base face in the u,v space.

パラメータ:

-

base (Shape) --

-

pts (Sequence[Tuple[Union[int, float], Union[int, float]]]) --

-

periodic (bool) --

-

tol (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.edgesToWires(edges: Iterable[Edge], tol: float = 1e-06) → List[Wire][ソース]

Convert edges to a list of wires.

パラメータ:

-

edges (Iterable[Edge]) --

-

tol (float) --

戻り値の型:

List[Wire]

cadquery.occ_impl.shapes.ellipse(r1: float, r2: float) → Shape[ソース]

Construct an ellipse.

パラメータ:

-

r1 (float) --

-

r2 (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.extrude(s: Shape, d: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Shape[ソース]

Extrude a shape.

パラメータ:

-

s (Shape) --

-

d (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.face(*s: cadquery.occ_impl.shapes.Shape) → cadquery.occ_impl.shapes.Shape[ソース]

Build face from edges or wires.

face(s: Sequence[cadquery.occ_impl.shapes.Shape]) -> cadquery.occ_impl.shapes.Shape

Build face from a sequence of edges or wires.

パラメータ:

s (Shape) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.faceOn(base: Shape, *fcs: Shape, tol=1e-06, N=20) → Shape[ソース]

Build face(s) on base by mapping planar face(s) onto the (u,v) space of base.

パラメータ:

-

base (Shape) --

-

fcs (Shape) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.fill(s: Shape, constraints: Sequence[Union[Shape, Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]] = ()) → Shape[ソース]

Fill edges/wire possibly obeying constraints.

パラメータ:

-

s (Shape) --

-

constraints (Sequence[Union[Shape, Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.fillet(s: Shape, e: Shape, r: float) → Shape[ソース]

Fillet selected edges in a given shell or solid.

パラメータ:

-

s (Shape) --

-

e (Shape) --

-

r (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.fix(obj: TopoDS_Shape) → TopoDS_Shape[ソース]

Fix a TopoDS object to suitable specialized type

パラメータ:

obj (TopoDS_Shape) --

戻り値の型:

TopoDS_Shape

cadquery.occ_impl.shapes.fuse(s1: Shape, s2: Shape, *shapes: Shape, tol: float = 0.0, glue: Optional[Literal['partial', 'full', None]] = None) → Shape[ソース]

Fuse at least two shapes.

パラメータ:

-

s1 (Shape) --

-

s2 (Shape) --

-

shapes (Shape) --

-

tol (float) --

-

glue (Optional[Literal['partial', 'full', None]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.imprint(*shapes: Shape, tol: float = 0.0, glue: Literal['partial', 'full', None] = 'full', history: Optional[Dict[Union[Shape, str], Shape]] = None) → Shape[ソース]

Imprint arbitrary number of shapes.

パラメータ:

-

shapes (Shape) --

-

tol (float) --

-

glue (Literal['partial', 'full', None]) --

-

history (Optional[Dict[Union[Shape, str], Shape]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.intersect(s1: Shape, s2: Shape, tol: float = 0.0, glue: Optional[Literal['partial', 'full', None]] = None) → Shape[ソース]

Intersect two shapes.

パラメータ:

-

s1 (Shape) --

-

s2 (Shape) --

-

tol (float) --

-

glue (Optional[Literal['partial', 'full', None]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.isSubshape(s1: Shape, s2: Shape) → bool[ソース]

Check if s1 is a subshape of s2.

パラメータ:

-

s1 (Shape) --

-

s2 (Shape) --

戻り値の型:

bool

cadquery.occ_impl.shapes.loft(s: Sequence[cadquery.occ_impl.shapes.Shape], cap: bool = False, ruled: bool = False, continuity: Literal['C1', 'C2', 'C3'] = 'C2', parametrization: Literal['uniform', 'chordal', 'centripetal'] = 'uniform', degree: int = 3, compat: bool = True, smoothing: bool = False, weights: Tuple[float, float, float] = (1, 1, 1)) → cadquery.occ_impl.shapes.Shape[ソース]

Loft edges, wires or faces. For faces cap has no effect. Do not mix faces with other types.

loft(*s: cadquery.occ_impl.shapes.Shape, cap: bool = False, ruled: bool = False, continuity: Literal['C1', 'C2', 'C3'] = 'C2', parametrization: Literal['uniform', 'chordal', 'centripetal'] = 'uniform', degree: int = 3, compat: bool = True, smoothing: bool = False, weights: Tuple[float, float, float] = (1, 1, 1)) -> cadquery.occ_impl.shapes.Shape

Variadic loft overload.

パラメータ:

-

s (Sequence[Shape]) --

-

cap (bool) --

-

ruled (bool) --

-

continuity (Literal['C1', 'C2', 'C3']) --

-

parametrization (Literal['uniform', 'chordal', 'centripetal']) --

-

degree (int) --

-

compat (bool) --

-

smoothing (bool) --

-

weights (Tuple[float, float, float]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.offset(s: Shape, t: float, cap=True, both: bool = False, tol: float = 1e-06) → Shape[ソース]

Offset or thicken faces or shells.

パラメータ:

-

s (Shape) --

-

t (float) --

-

both (bool) --

-

tol (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.plane(w: Union[float, int], l: Union[float, int]) → cadquery.occ_impl.shapes.Shape[ソース]

Construct a finite planar face.

plane() -> cadquery.occ_impl.shapes.Shape

Construct an infinite planar face.

This is a crude approximation. Truly infinite faces in OCCT do not work as
expected in all contexts.

パラメータ:

-

w (Union[float, int]) --

-

l (Union[float, int]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.polygon(*pts: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Shape[ソース]

Construct a polygon (closed polyline) from points.

パラメータ:

pts (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.polyline(*pts: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Shape[ソース]

Construct a polyline from points.

パラメータ:

pts (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.project(s: Shape, base: Shape, continuity: Literal['C1', 'C2', 'C3'] = 'C2', degree: int = 3, maxseg: int = 30, tol: float = 0.0001)[ソース]

Project s onto base using normal projection.

パラメータ:

-

s (Shape) --

-

base (Shape) --

-

continuity (Literal['C1', 'C2', 'C3']) --

-

degree (int) --

-

maxseg (int) --

-

tol (float) --

cadquery.occ_impl.shapes.rect(w: float, h: float) → Shape[ソース]

Construct a rectangle.

パラメータ:

-

w (float) --

-

h (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.revolve(s: Shape, p: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], d: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], a: float = 360)[ソース]

Revolve a shape.

パラメータ:

-

s (Shape) --

-

p (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

d (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

a (float) --

cadquery.occ_impl.shapes.segment(p1: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], p2: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) → Shape[ソース]

Construct a segment from two points.

パラメータ:

-

p1 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

p2 (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.setThreads(n: int)[ソース]

Set number of threads to be used by boolean operations.

パラメータ:

n (int) --

cadquery.occ_impl.shapes.shell(*s: cadquery.occ_impl.shapes.Shape, tol: float = 1e-06, manifold: bool = True, ctx: Union[Sequence[cadquery.occ_impl.shapes.Shape], cadquery.occ_impl.shapes.Shape, NoneType] = None, history: Optional[Dict[Union[cadquery.occ_impl.shapes.Shape, str], cadquery.occ_impl.shapes.Shape]] = None) → cadquery.occ_impl.shapes.Shape[ソース]

Build shell from faces. If ctx is specified, local sewing is performed.

shell(s: Sequence[cadquery.occ_impl.shapes.Shape], tol: float = 1e-06, manifold: bool = True, ctx: Union[Sequence[cadquery.occ_impl.shapes.Shape], cadquery.occ_impl.shapes.Shape, NoneType] = None, history: Optional[Dict[Union[cadquery.occ_impl.shapes.Shape, str], cadquery.occ_impl.shapes.Shape]] = None) -> cadquery.occ_impl.shapes.Shape

Build shell from a sequence of faces. If ctx is specified, local sewing is performed.

パラメータ:

-

s (Shape) --

-

tol (float) --

-

manifold (bool) --

-

ctx (Optional[Union[Sequence[Shape], Shape]]) --

-

history (Optional[Dict[Union[Shape, str], Shape]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.solid(s1: cadquery.occ_impl.shapes.Shape, *sn: cadquery.occ_impl.shapes.Shape, tol: float = 1e-06, history: Optional[Dict[Union[cadquery.occ_impl.shapes.Shape, str], cadquery.occ_impl.shapes.Shape]] = None) → cadquery.occ_impl.shapes.Shape[ソース]

Build solid from faces or shells.

solid(s: Sequence[cadquery.occ_impl.shapes.Shape], inner: Optional[Sequence[cadquery.occ_impl.shapes.Shape]] = None, tol: float = 1e-06, history: Optional[Dict[Union[cadquery.occ_impl.shapes.Shape, str], cadquery.occ_impl.shapes.Shape]] = None) -> cadquery.occ_impl.shapes.Shape

Build solid from a sequence of faces.

パラメータ:

-

s1 (Shape) --

-

sn (Shape) --

-

tol (float) --

-

history (Optional[Dict[Union[Shape, str], Shape]]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.sortWiresByBuildOrder(wireList: List[Wire]) → List[List[Wire]][ソース]

Tries to determine how wires should be combined into faces.

Assume:

The wires make up one or more faces, which could have 'holes'
Outer wires are listed ahead of inner wires
there are no wires inside wires inside wires
( IE, islands -- we can deal with that later on )
none of the wires are construction wires

Compute:

one or more sets of wires, with the outer wire listed first, and inner
ones

Returns, list of lists.

パラメータ:

wireList (List[Wire]) --

戻り値の型:

List[List[Wire]]

cadquery.occ_impl.shapes.sphere(d: float) → Shape[ソース]

Construct a solid sphere.

パラメータ:

d (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.spline(*pts: Union[ForwardRef('Vector'), Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], tol: float = 1e-06, periodic: bool = False) → cadquery.occ_impl.shapes.Shape[ソース]

Construct a spline from points.

spline(pts: Sequence[Union[ForwardRef('Vector'), Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]], tgts: Optional[Sequence[Union[ForwardRef('Vector'), Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]]] = None, params: Optional[Sequence[float]] = None, tol: float = 1e-06, periodic: bool = False, scale: bool = True) -> cadquery.occ_impl.shapes.Shape

Construct a spline from a sequence points.

パラメータ:

-

pts (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

tol (float) --

-

periodic (bool) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.split(s1: Shape, s2: Shape, tol: float = 0.0) → Shape[ソース]

Split one shape with another.

パラメータ:

-

s1 (Shape) --

-

s2 (Shape) --

-

tol (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.sweep(s: cadquery.occ_impl.shapes.Shape, path: cadquery.occ_impl.shapes.Shape, aux: Optional[cadquery.occ_impl.shapes.Shape] = None, cap: bool = False) → cadquery.occ_impl.shapes.Shape[ソース]

Sweep edge, wire or face along a path. For faces cap has no effect.
Do not mix faces with other types.

sweep(s: Sequence[cadquery.occ_impl.shapes.Shape], path: cadquery.occ_impl.shapes.Shape, aux: Optional[cadquery.occ_impl.shapes.Shape] = None, cap: bool = False) -> cadquery.occ_impl.shapes.Shape

Sweep edges, wires or faces along a path, multiple sections are supported.
For faces cap has no effect. Do not mix faces with other types.

パラメータ:

-

s (Shape) --

-

path (Shape) --

-

aux (Optional[Shape]) --

-

cap (bool) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.text(txt: str, size: Union[float, int], font: str = 'Arial', path: Optional[str] = None, kind: Literal['regular', 'bold', 'italic'] = 'regular', halign: Literal['center', 'left', 'right'] = 'center', valign: Literal['center', 'top', 'bottom'] = 'center') → cadquery.occ_impl.shapes.Shape[ソース]

Create a flat text.

text(txt: str, size: Union[float, int], spine: cadquery.occ_impl.shapes.Shape, planar: bool = False, font: str = 'Arial', path: Optional[str] = None, kind: Literal['regular', 'bold', 'italic'] = 'regular', halign: Literal['center', 'left', 'right'] = 'center', valign: Literal['center', 'top', 'bottom'] = 'center') -> cadquery.occ_impl.shapes.Shape

Create a text on a spine.

text(txt: str, size: Union[float, int], spine: cadquery.occ_impl.shapes.Shape, base: cadquery.occ_impl.shapes.Shape, font: str = 'Arial', path: Optional[str] = None, kind: Literal['regular', 'bold', 'italic'] = 'regular', halign: Literal['center', 'left', 'right'] = 'center', valign: Literal['center', 'top', 'bottom'] = 'center') -> cadquery.occ_impl.shapes.Shape

Create a text on a spine and a base surface.

パラメータ:

-

txt (str) --

-

size (Union[float, int]) --

-

font (str) --

-

path (Optional[str]) --

-

kind (Literal['regular', 'bold', 'italic']) --

-

halign (Literal['center', 'left', 'right']) --

-

valign (Literal['center', 'top', 'bottom']) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.torus(d1: float, d2: float) → Shape[ソース]

Construct a solid torus.

パラメータ:

-

d1 (float) --

-

d2 (float) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.vertex(x: Union[float, int], y: Union[float, int], z: Union[float, int]) → cadquery.occ_impl.shapes.Shape[ソース]

Construct a vertex from coordinates.

vertex(p: Union[ForwardRef('Vector'), Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]])

Construct a vertex from VectorLike.

パラメータ:

-

x (Union[float, int]) --

-

y (Union[float, int]) --

-

z (Union[float, int]) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.wire(*s: cadquery.occ_impl.shapes.Shape) → cadquery.occ_impl.shapes.Shape[ソース]

Build wire from edges.

パラメータ:

s (Shape) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.wireOn(base: Shape, w: Shape, tol=1e-06, N=20) → Shape[ソース]

Map a wire onto a base face in the u,v space.

パラメータ:

-

base (Shape) --

-

w (Shape) --

戻り値の型:

Shape

cadquery.occ_impl.shapes.wiresToFaces(wireList: List[Wire]) → List[Face][ソース]

Convert wires to a list of faces.

パラメータ:

wireList (List[Wire]) --

戻り値の型:

List[Face]

class cadquery.occ_impl.shapes.Mixin1D[ソース]

ベースクラス: `object`

bounds() → Tuple[float, float][ソース]

Parametric bounds of the curve.

パラメータ:

self (Mixin1DProtocol) --

戻り値の型:

Tuple[float, float]

curvatureAt(d: float, mode: Literal['length', 'parameter'] = 'length', resolution: float = 1e-06) → float[ソース]

Calculate mean curvature along the underlying curve.

パラメータ:

-

d (float) -- distance or parameter value

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

resolution (float) -- resolution of the calculation (default: 1e-6)

-

self (Mixin1DProtocol) --

戻り値:

mean curvature value at the specified d value.

戻り値の型:

float

curvatures(ds: Iterable[float], mode: Literal['length', 'parameter'] = 'length', resolution: float = 1e-06) → List[float][ソース]

Calculate mean curvatures along the underlying curve.

パラメータ:

-

d -- distance or parameter values

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

resolution (float) -- resolution of the calculation (default: 1e-6)

-

self (Mixin1DProtocol) --

-

ds (Iterable[float]) --

戻り値:

mean curvature value at the specified d value.

戻り値の型:

List[float]

endPoint() → Vector[ソース]

戻り値:

a vector representing the end point of this edge.

パラメータ:

self (Mixin1DProtocol) --

戻り値の型:

Vector

Note, circles may have the start and end points the same

locationAt(d: float, mode: Literal['length', 'parameter'] = 'length', frame: Literal['frenet', 'corrected'] = 'frenet', planar: bool = False) → Location[ソース]

Generate a location along the underlying curve.

パラメータ:

-

d (float) -- distance or parameter value

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

frame (Literal['frenet', 'corrected']) -- moving frame calculation method (default: frenet)

-

planar (bool) -- planar mode

-

self (Mixin1DProtocol) --

戻り値:

A Location object representing local coordinate system at the specified distance.

戻り値の型:

Location

locations(ds: Iterable[float], mode: Literal['length', 'parameter'] = 'length', frame: Literal['frenet', 'corrected'] = 'frenet', planar: bool = False) → List[Location][ソース]

Generate locations along the curve.

パラメータ:

-

ds (Iterable[float]) -- distance or parameter values

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

frame (Literal['frenet', 'corrected']) -- moving frame calculation method (default: frenet)

-

planar (bool) -- planar mode

-

self (Mixin1DProtocol) --

戻り値:

A list of Location objects representing local coordinate systems at the specified distances.

戻り値の型:

List[Location]

normal() → Vector[ソース]

Calculate the normal Vector. Only possible for planar curves.

戻り値:

normal vector

パラメータ:

self (Mixin1DProtocol) --

戻り値の型:

Vector

paramAt(d: Union[float, int, Vector]) → float[ソース]

Compute parameter value at the specified normalized distance or a point.

パラメータ:

-

d (Union[float, int, Vector]) -- normalized distance [0, 1] or a point

-

self (Mixin1DProtocol) --

戻り値:

parameter value

戻り値の型:

float

params(pts: Iterable[Vector], tol=1e-06) → List[float][ソース]

Computes u values closest to given vectors.

パラメータ:

-

pts (Iterable[Vector]) -- the points to compute the parameters at.

-

self (Mixin1DProtocol) --

戻り値:

list of u values.

戻り値の型:

List[float]

paramsLength(locations: Iterable[float]) → List[float][ソース]

Computes u values at given relative lengths.

パラメータ:

-

locations (Iterable[float]) -- list of distances.

-

pts -- the points to compute the parameters at.

-

self (Mixin1DProtocol) --

戻り値:

list of u values.

戻り値の型:

List[float]

positionAt(d: float, mode: Literal['length', 'parameter'] = 'length') → Vector[ソース]

Generate a position along the underlying curve.

パラメータ:

-

d (float) -- distance or parameter value

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

self (Mixin1DProtocol) --

戻り値:

A Vector on the underlying curve located at the specified d value.

戻り値の型:

Vector

positions(ds: Iterable[float], mode: Literal['length', 'parameter'] = 'length') → List[Vector][ソース]

Generate positions along the underlying curve.

パラメータ:

-

ds (Iterable[float]) -- distance or parameter values

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

self (Mixin1DProtocol) --

戻り値:

A list of Vector objects.

戻り値の型:

List[Vector]

project(face: Face, d: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], closest: bool = True) → Union[T1D, List[T1D]][ソース]

Project onto a face along the specified direction.

パラメータ:

-

self (T1D) --

-

face (Face) --

-

d (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) --

-

closest (bool) --

戻り値の型:

Union[T1D, List[T1D]]

radius() → float[ソース]

Calculate the radius.

Note that when applied to a Wire, the radius is simply the radius of the first edge.

戻り値:

radius

例外:

ValueError -- if kernel can not reduce the shape to a circular edge

パラメータ:

self (Mixin1DProtocol) --

戻り値の型:

float

sample(n: Union[int, float]) → Tuple[List[Vector], List[float]][ソース]

Sample a curve based on a number of points or deflection.

パラメータ:

-

n (Union[int, float]) -- Number of positions or deflection

-

self (Mixin1DProtocol) --

戻り値:

A list of Vectors and a list of parameters.

戻り値の型:

Tuple[List[Vector], List[float]]

startPoint() → Vector[ソース]

戻り値:

a vector representing the start point of this edge

パラメータ:

self (Mixin1DProtocol) --

戻り値の型:

Vector

Note, circles may have the start and end points the same

tangentAt(locationParam: float = 0.5, mode: Literal['length', 'parameter'] = 'length') → Vector[ソース]

Compute tangent vector at the specified location.

パラメータ:

-

locationParam (float) -- distance or parameter value (default: 0.5)

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length)

-

self (Mixin1DProtocol) --

戻り値:

tangent vector

戻り値の型:

Vector

tangents(locations: Iterable[float], mode: Literal['length', 'parameter'] = 'length') → List[Vector][ソース]

Compute tangent vectors at the specified locations.

パラメータ:

-

locations (Iterable[float]) -- list of distances or parameters.

-

mode (Literal['length', 'parameter']) -- position calculation mode (default: length).

-

self (Mixin1DProtocol) --

戻り値:

list of tangent vectors

戻り値の型:

List[Vector]

class cadquery.occ_impl.shapes.Mixin3D[ソース]

ベースクラス: `object`

chamfer(length: float, length2: Optional[float], edgeList: Iterable[Edge]) → Any[ソース]

Chamfers the specified edges of this solid.

パラメータ:

-

length (float) -- length > 0, the length (length) of the chamfer

-

length2 (Optional[float]) -- length2 > 0, optional parameter for asymmetrical chamfer. Should be None if not required.

-

edgeList (Iterable[Edge]) -- a list of Edge objects, which must belong to this solid

-

self (Any) --

戻り値:

Chamfered solid

戻り値の型:

Any

dprism(basis: Optional[Face], profiles: List[Wire], depth: Optional[Union[float, int]] = None, taper: Union[float, int] = 0, upToFace: Optional[Face] = None, thruAll: bool = True, additive: bool = True) → Solid[ソース]

dprism(basis: Optional[Face], faces: List[Face], depth: Optional[Union[float, int]] = None, taper: Union[float, int] = 0, upToFace: Optional[Face] = None, thruAll: bool = True, additive: bool = True) → Solid

Make a prismatic feature (additive or subtractive)

パラメータ:

-

basis (Optional[Face]) -- face to perform the operation on

-

profiles (List[Wire]) -- list of profiles

-

depth (Optional[Union[float, int]]) -- depth of the cut or extrusion

-

upToFace (Optional[Face]) -- a face to extrude until

-

thruAll (bool) -- cut thruAll

-

self (TS) --

-

taper (Union[float, int]) --

-

additive (bool) --

戻り値:

a Solid object

戻り値の型:

Solid

fillet(radius: float, edgeList: Iterable[Edge]) → Any[ソース]

Fillets the specified edges of this solid.

パラメータ:

-

radius (float) -- float > 0, the radius of the fillet

-

edgeList (Iterable[Edge]) -- a list of Edge objects, which must belong to this solid

-

self (Any) --

戻り値:

Filleted solid

戻り値の型:

Any

isInside(point: Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]], tolerance: float = 1e-06) → bool[ソース]

Returns whether or not the point is inside a solid or compound
object within the specified tolerance.

パラメータ:

-

point (Union[Vector, Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float], Union[int, float]]]) -- tuple or Vector representing 3D point to be tested

-

tolerance (float) -- tolerance for inside determination, default=1.0e-6

-

self (ShapeProtocol) --

戻り値:

bool indicating whether or not point is within solid

戻り値の型:

bool

shell(faceList: Optional[Iterable[Face]], thickness: float, tolerance: float = 0.0001, kind: Literal['arc', 'intersection'] = 'arc') → Any[ソース]

Make a shelled solid of self.

パラメータ:

-

faceList (Optional[Iterable[Face]]) -- List of faces to be removed, which must be part of the solid. Can
be an empty list.

-

thickness (float) -- Floating point thickness. Positive shells outwards, negative
shells inwards.

-

tolerance (float) -- Modelling tolerance of the method, default=0.0001.

-

self (Any) --

-

kind (Literal['arc', 'intersection']) --

戻り値:

A shelled solid.

戻り値の型:

Any

class cadquery.selectors.AndSelector(left, right)[ソース]

ベースクラス: `BinarySelector`

Intersection selector. Returns objects that is selected by both selectors.

class cadquery.selectors.AreaNthSelector(n: int, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `_NthSelector`

Selects the object(s) with Nth area

Applicability:

-

Faces, Shells, Solids - Shape.Area() is used to compute area

-

closed planar Wires - a temporary face is created to compute area

Will ignore non-planar or non-closed wires.

Among other things can be used to select one of
the nested coplanar wires or faces.

For example to create a fillet on a shank:

```python
result = (
    cq.Workplane("XY")
    .circle(5)
    .extrude(2)
    .circle(2)
    .extrude(10)
    .faces(">Z[-2]")
    .wires(AreaNthSelector(0))
    .fillet(2)
)

```

Or to create a lip on a case seam:

```python
result = (
    cq.Workplane("XY")
    .rect(20, 20)
    .extrude(10)
    .edges("|Z or <Z")
    .fillet(2)
    .faces(">Z")
    .shell(2)
    .faces(">Z")
    .wires(AreaNthSelector(-1))
    .toPending()
    .workplane()
    .offset2D(-1)
    .extrude(1)
    .faces(">Z[-2]")
    .wires(AreaNthSelector(0))
    .toPending()
    .workplane()
    .cutBlind(2)
)

```

パラメータ:

-

n (int) --

-

directionMax (bool) --

-

tolerance (float) --

key(obj: Shape) → float[ソース]

Return the key for ordering. Can raise a ValueError if obj can not be
used to create a key, which will result in obj being dropped by the
clustering method.

パラメータ:

obj (Shape) --

戻り値の型:

float

class cadquery.selectors.BaseDirSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `Selector`

単一の方向ベクトルに基づく選択を処理するセレクタ。

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

filter(objectList: Sequence[Shape]) → List[Shape][ソース]

There are lots of kinds of filters, but for planes they are always
based on the normal of the plane, and for edges on the tangent vector
along the edge

パラメータ:

objectList (Sequence[Shape]) --

戻り値の型:

List[Shape]

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.selectors.BinarySelector(left, right)[ソース]

ベースクラス: `Selector`

Base class for selectors that operates with two other
selectors. Subclass must implement the :filterResults(): method.

filter(objectList: Sequence[Shape])[ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

class cadquery.selectors.BoxSelector(point0, point1, boundingbox=False)[ソース]

ベースクラス: `Selector`

2点で定義された3Dボックス内のオブジェクトを選択します。

If boundingbox is True only the objects that have their bounding
box inside the given box is selected. Otherwise only center point
of the object is tested.

Applicability: all types of shapes

Example:

```python
CQ(aCube).edges(BoxSelector((0, 1, 0), (1, 2, 1)))

```

filter(objectList: Sequence[Shape])[ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

class cadquery.selectors.CenterNthSelector(vector: Vector, n: int, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `_NthSelector`

オブジェクトを、指定された方向に投影された中心からの距離によって決まる順序でリストにソートします。

Applicability:

All Shapes.

パラメータ:

-

vector (Vector) --

-

n (int) --

-

directionMax (bool) --

-

tolerance (float) --

key(obj: Shape) → float[ソース]

Return the key for ordering. Can raise a ValueError if obj can not be
used to create a key, which will result in obj being dropped by the
clustering method.

パラメータ:

obj (Shape) --

戻り値の型:

float

class cadquery.selectors.DirectionMinMaxSelector(vector: Vector, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `CenterNthSelector`

指定した方向に最も近い、または最も遠いオブジェクトを選択します。

Applicability:

All object types. for a vertex, its point is used. for all other kinds
of objects, the center of mass of the object is used.

You can use the string shortcuts >(X|Y|Z) or <(X|Y|Z) if you want to select
based on a cardinal direction.

For example this:

```python
CQ(aCube).faces(DirectionMinMaxSelector((0, 0, 1), True))

```

Means to select the face having the center of mass farthest in the positive
z direction, and is the same as:

```python
CQ(aCube).faces(">Z")

```

パラメータ:

-

vector (Vector) --

-

directionMax (bool) --

-

tolerance (float) --

class cadquery.selectors.DirectionNthSelector(vector: Vector, n: int, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `ParallelDirSelector`, `CenterNthSelector`

Filters for objects parallel (or normal) to the specified direction then returns the Nth one.

Applicability:

Linear Edges
Planar Faces

パラメータ:

-

vector (Vector) --

-

n (int) --

-

directionMax (bool) --

-

tolerance (float) --

filter(objectlist: Sequence[Shape]) → List[Shape][ソース]

There are lots of kinds of filters, but for planes they are always
based on the normal of the plane, and for edges on the tangent vector
along the edge

パラメータ:

objectlist (Sequence[Shape]) --

戻り値の型:

List[Shape]

class cadquery.selectors.DirectionSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `BaseDirSelector`

指定した方向に並んだオブジェクトを選択します。

Applicability:

Linear Edges
Planar Faces

Use the string syntax shortcut +/-(X|Y|Z) if you want to select based on a cardinal direction.

Example:

```python
CQ(aCube).faces(DirectionSelector((0, 0, 1)))

```

selects faces with the normal in the z direction, and is equivalent to:

```python
CQ(aCube).faces("+Z")

```

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.selectors.InverseSelector(selector)[ソース]

ベースクラス: `Selector`

Inverts the selection of given selector. In other words, selects
all objects that is not selected by given selector.

filter(objectList: Sequence[Shape])[ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

class cadquery.selectors.LengthNthSelector(n: int, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `_NthSelector`

Select the object(s) with the Nth length

Applicability:

All Edge and Wire objects

パラメータ:

-

n (int) --

-

directionMax (bool) --

-

tolerance (float) --

key(obj: Shape) → float[ソース]

Return the key for ordering. Can raise a ValueError if obj can not be
used to create a key, which will result in obj being dropped by the
clustering method.

パラメータ:

obj (Shape) --

戻り値の型:

float

class cadquery.selectors.NearestToPointSelector(pnt)[ソース]

ベースクラス: `Selector`

指定された点に最も近いオブジェクトを選択します。

If the object is a vertex or point, the distance
is used. For other kinds of shapes, the center of mass
is used to to compute which is closest.

Applicability: All Types of Shapes

Example:

```python
CQ(aCube).vertices(NearestToPointSelector((0, 1, 0)))

```

returns the vertex of the unit cube closest to the point x=0,y=1,z=0

filter(objectList: Sequence[Shape])[ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

class cadquery.selectors.ParallelDirSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `BaseDirSelector`

指定した方向と平行なオブジェクトを選択します。

Applicability:

Linear Edges
Planar Faces

Use the string syntax shortcut |(X|Y|Z) if you want to select based on a cardinal direction.

Example:

```python
CQ(aCube).faces(ParallelDirSelector((0, 0, 1)))

```

selects faces with the normal parallel to the z direction, and is equivalent to:

```python
CQ(aCube).faces("|Z")

```

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.selectors.PerpendicularDirSelector(vector: Vector, tolerance: float = 0.0001)[ソース]

ベースクラス: `BaseDirSelector`

指定した方向と直交するオブジェクトを選択します。

Applicability:

Linear Edges
Planar Faces

Use the string syntax shortcut #(X|Y|Z) if you want to select based on a
cardinal direction.

Example:

```python
CQ(aCube).faces(PerpendicularDirSelector((0, 0, 1)))

```

selects faces with the normal perpendicular to the z direction, and is equivalent to:

```python
CQ(aCube).faces("#Z")

```

パラメータ:

-

vector (Vector) --

-

tolerance (float) --

test(vec: Vector) → bool[ソース]

Test a specified vector. Subclasses override to provide other implementations

パラメータ:

vec (Vector) --

戻り値の型:

bool

class cadquery.selectors.RadiusNthSelector(n: int, directionMax: bool = True, tolerance: float = 0.0001)[ソース]

ベースクラス: `_NthSelector`

N 番目の半径を持つオブジェクトを選択します。

Applicability:

All Edge and Wires.

Will ignore any shape that can not be represented as a circle or an arc of
a circle.

パラメータ:

-

n (int) --

-

directionMax (bool) --

-

tolerance (float) --

key(obj: Shape) → float[ソース]

Return the key for ordering. Can raise a ValueError if obj can not be
used to create a key, which will result in obj being dropped by the
clustering method.

パラメータ:

obj (Shape) --

戻り値の型:

float

class cadquery.selectors.Selector[ソース]

ベースクラス: `object`

オブジェクトのリストにフィルタをかける。

Filters must provide a single method that filters objects.

filter(objectList: Sequence[Shape]) → List[Shape][ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

戻り値の型:

List[Shape]

class cadquery.selectors.StringSyntaxSelector(selectorString)[ソース]

ベースクラス: `Selector`

Filter lists objects using a simple string syntax. All of the filters available in the string syntax
are also available ( usually with more functionality ) through the creation of full-fledged
selector objects. see `Selector` and its subclasses

Filtering works differently depending on the type of object list being filtered.

パラメータ:

selectorString -- A two-part selector string, [selector][axis]

戻り値:

objects that match the specified selector

*Modifiers* are `('|','+','-','<','>','%')`

|:

parallel to ( same as `ParallelDirSelector` ). Can return multiple objects.

#:

perpendicular to (same as `PerpendicularDirSelector` )

+:

positive direction (same as `DirectionSelector` )

-:

negative direction (same as `DirectionSelector`  )

>:

maximize (same as `DirectionMinMaxSelector` with directionMax=True)

<:

minimize (same as `DirectionMinMaxSelector` with directionMax=False )

%:

curve/surface type (same as `TypeSelector`)

*axisStrings* are: `X,Y,Z,XY,YZ,XZ` or `(x,y,z)` which defines an arbitrary direction

It is possible to combine simple selectors together using logical operations.
The following operations are supported

and:

Logical AND, e.g. >X and >Y

or:

Logical OR, e.g. |X or |Y

not:

Logical NOT, e.g. not #XY

exc(ept):

Set difference (equivalent to AND NOT): |X exc >Z

Finally, it is also possible to use even more complex expressions with nesting
and arbitrary number of terms, e.g.

(not >X[0] and #XY) or >XY[0]

Selectors are a complex topic: see Selectors Reference for more information

filter(objectList: Sequence[Shape])[ソース]

Filter give object list through th already constructed complex selector object

パラメータ:

objectList (Sequence[Shape]) --

class cadquery.selectors.SubtractSelector(left, right)[ソース]

ベースクラス: `BinarySelector`

Difference selector. Subtract results of a selector from another
selectors results.

class cadquery.selectors.SumSelector(left, right)[ソース]

ベースクラス: `BinarySelector`

Union selector. Returns the sum of two selectors results.

class cadquery.selectors.TypeSelector(typeString: str)[ソース]

ベースクラス: `Selector`

所定のジオメトリタイプを持つオブジェクトを選択します。

Applicability:

Faces: PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE, REVOLUTION, EXTRUSION, OFFSET, OTHER
Edges: LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER, BSPLINE, OFFSET, OTHER

You can use the string selector syntax. For example this:

```python
CQ(aCube).faces(TypeSelector("PLANE"))

```

will select 6 faces, and is equivalent to:

```python
CQ(aCube).faces("%PLANE")

```

パラメータ:

typeString (str) --

filter(objectList: Sequence[Shape]) → List[Shape][ソース]

Filter the provided list.

The default implementation returns the original list unfiltered.

パラメータ:

objectList (list of OCCT primitives) -- list to filter

戻り値:

filtered list

戻り値の型:

List[Shape]

cadquery.occ_impl.exporters.assembly.exportAssembly(assy: AssemblyProtocol, path: str, mode: Literal['default', 'fused'] = 'default', **kwargs) → bool[ソース]

Export an assembly to a STEP file.

kwargs is used to provide optional keyword arguments to configure the exporter.

パラメータ:

-

assy (AssemblyProtocol) -- assembly

-

path (str) -- Path and filename for writing

-

mode (Literal['default', 'fused']) -- STEP export mode. The options are "default", and "fused" (a single fused compound).
It is possible that fused mode may exhibit low performance.

-

fuzzy_tol (float) -- OCCT fuse operation tolerance setting used only for fused assembly export.

-

glue (bool) -- Enable gluing mode for improved performance during fused assembly export.
This option should only be used for non-intersecting shapes or those that are only touching or partially overlapping.
Note that when glue is enabled, the resulting fused shape may be invalid if shapes are intersecting in an incompatible way.
Defaults to False.

-

write_pcurves (bool) -- Enable or disable writing parametric curves to the STEP file. Default True.
If False, writes STEP file without pcurves. This decreases the size of the resulting STEP file.

-

precision_mode (int) -- Controls the uncertainty value for STEP entities. Specify -1, 0, or 1. Default 0.
See OCCT documentation.

戻り値の型:

bool

cadquery.occ_impl.exporters.assembly.exportCAF(assy: AssemblyProtocol, path: str, binary: bool = False) → bool[ソース]

Export an assembly to an XCAF xml or xbf file (internal OCCT formats).

パラメータ:

-

assy (AssemblyProtocol) --

-

path (str) --

-

binary (bool) --

戻り値の型:

bool

cadquery.occ_impl.exporters.assembly.exportGLTF(assy: AssemblyProtocol, path: str, binary: Optional[bool] = None, tolerance: float = 0.001, angularTolerance: float = 0.1)[ソース]

Export an assembly to a gltf file.

パラメータ:

-

assy (AssemblyProtocol) --

-

path (str) --

-

binary (Optional[bool]) --

-

tolerance (float) --

-

angularTolerance (float) --

cadquery.occ_impl.exporters.assembly.exportStepMeta(assy: AssemblyProtocol, path: str, write_pcurves: bool = True, precision_mode: int = 0) → bool[ソース]

Export an assembly to a STEP file with faces tagged with names and colors. This is done as a
separate method from the main STEP export because this is not compatible with the fused mode
and also flattens the hierarchy of the STEP.

Layers are used because some software does not understand the ADVANCED_FACE entity and needs
names attached to layers instead.

パラメータ:

-

assy (AssemblyProtocol) -- assembly

-

path (str) -- Path and filename for writing

-

write_pcurves (bool) -- Enable or disable writing parametric curves to the STEP file. Default True.
If False, writes STEP file without pcurves. This decreases the size of the resulting STEP file.

-

precision_mode (int) -- Controls the uncertainty value for STEP entities. Specify -1, 0, or 1. Default 0.
See OCCT documentation.

戻り値の型:

bool

cadquery.occ_impl.exporters.assembly.exportVRML(assy: AssemblyProtocol, path: str, tolerance: float = 0.001, angularTolerance: float = 0.1)[ソース]

Export an assembly to a vrml file using vtk.

パラメータ:

-

assy (AssemblyProtocol) --

-

path (str) --

-

tolerance (float) --

-

angularTolerance (float) --

cadquery.occ_impl.exporters.assembly.exportVTKJS(assy: AssemblyProtocol, path: str)[ソース]

Export an assembly to a zipped vtkjs. NB: .zip extensions is added to path.

パラメータ:

-

assy (AssemblyProtocol) --

-

path (str) --

cadquery.occ_impl.assembly.toJSON(assy: AssemblyProtocol, color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0), tolerance: float = 0.001) → List[Dict[str, Any]][ソース]

Export an object to a structure suitable for converting to VTK.js JSON.

パラメータ:

-

assy (AssemblyProtocol) --

-

color (Tuple[float, float, float, float]) --

-

tolerance (float) --

戻り値の型:

List[Dict[str, Any]]

class cadquery.occ_impl.exporters.dxf.DxfDocument(dxfversion: str = 'AC1027', setup: Union[bool, List[str]] = False, doc_units: int = 4, *, metadata: Optional[Dict[str, str]] = None, approx: Optional[Literal['spline', 'arc']] = None, tolerance: float = 0.001)[ソース]

Create DXF document from CadQuery objects.

A wrapper for ezdxf providing methods for
converting `cadquery.Workplane` objects to DXF entities.

The ezdxf document is available as the property `document`, allowing most
features of ezdxf to be utilised directly.

Example usage

Single layer DXF document

```python
rectangle = cq.Workplane().rect(10, 20)

dxf = DxfDocument()
dxf.add_shape(rectangle)
dxf.document.saveas("rectangle.dxf")

```

Multilayer DXF document

```python
rectangle = cq.Workplane().rect(10, 20)
circle = cq.Workplane().circle(3)

dxf = DxfDocument()
dxf = (
    dxf.add_layer("layer_1", color=2)
    .add_layer("layer_2", color=3)
    .add_shape(rectangle, "layer_1")
    .add_shape(circle, "layer_2")
)
dxf.document.saveas("rectangle-with-hole.dxf")

```

パラメータ:

-

dxfversion (str) --

-

setup (Union[bool, List[str]]) --

-

doc_units (int) --

-

metadata (Optional[Dict[str, str]]) --

-

approx (Optional[Literal['spline', 'arc']]) --

-

tolerance (float) --

__init__(dxfversion: str = 'AC1027', setup: Union[bool, List[str]] = False, doc_units: int = 4, *, metadata: Optional[Dict[str, str]] = None, approx: Optional[Literal['spline', 'arc']] = None, tolerance: float = 0.001)[ソース]

Initialize DXF document.

パラメータ:

-

dxfversion (str) -- `DXF version specifier`
as string, default is "AC1027" respectively "R2013"

-

setup (Union[bool, List[str]]) -- setup default styles, `False` for no setup, `True` to set up
everything or a list of topics as strings, e.g. `["linetypes", "styles"]`
refer to `ezdxf.new()`.

-

doc_units (int) -- ezdxf document/modelspace units

-

metadata (Optional[Dict[str, str]]) -- document metadata a dictionary of name value pairs

-

approx (Optional[Literal['spline', 'arc']]) --

Approximation strategy for converting `cadquery.Workplane` objects to DXF entities:

`None`

no approximation applied

`"spline"`

all splines approximated as cubic splines

`"arc"`

all curves approximated as arcs and straight segments

-

tolerance (float) -- Approximation tolerance for converting `cadquery.Workplane` objects to DXF entities.

add_layer(name: str, *, color: int = 7, linetype: str = 'CONTINUOUS') → Self[ソース]

Create a layer definition

Refer to ezdxf layers and
ezdxf layer tutorial.

パラメータ:

-

name (str) -- layer definition name

-

color (int) -- color index. Standard colors include:
1 red, 2 yellow, 3 green, 4 cyan, 5 blue, 6 magenta, 7 white/black

-

linetype (str) -- ezdxf line type

戻り値の型:

Self

add_shape(shape: Union[WorkplaneLike, Shape], layer: str = '') → Self[ソース]

Add CadQuery shape to a DXF layer.

パラメータ:

-

s -- CadQuery Workplane or Shape

-

layer (str) -- layer definition name

-

shape (Union[WorkplaneLike, Shape]) --

戻り値の型:

Self