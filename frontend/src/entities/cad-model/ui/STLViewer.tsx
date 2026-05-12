"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, type ThreeEvent } from "@react-three/fiber";
import { Center, Grid, Html, OrbitControls } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";

import type { ParameterData } from "@/entities/cad-model/model/types";

interface StlViewerProps {
  url: string;
  highlightEdgePoints?: number[][] | null;
  parameters?: ParameterData[];
  selectedParamName?: string | null;
  onSelectParam?: (name: string | null) => void;
  onApplyParam?: (name: string, newValue: number) => void;
  disabled?: boolean;
}

const TYPE_COLOR: Record<string, string> = {
  length: "#06b6d4",      // cyan
  radius: "#f59e0b",      // amber
  bounding_x: "#f43f5e",  // rose
  bounding_y: "#f43f5e",
  bounding_z: "#f43f5e",
};

const TYPE_LABEL: Record<string, string> = {
  length: "長さ",
  radius: "半径",
  bounding_x: "X",
  bounding_y: "Y",
  bounding_z: "Z",
};

function centroid(points: number[][]): [number, number, number] | null {
  if (points.length === 0) return null;
  let x = 0, y = 0, z = 0;
  for (const [px, py, pz] of points) {
    x += px;
    y += py;
    z += pz;
  }
  const n = points.length;
  return [x / n, y / n, z / n];
}

function StlModel({ url }: { url: string }) {
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);

  useEffect(() => {
    const loader = new STLLoader();
    loader.load(url, (geo) => {
      geo.computeVertexNormals();
      setGeometry(geo);
    });
  }, [url]);

  if (!geometry) return null;
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#6b9bd2" metalness={0.3} roughness={0.6} />
    </mesh>
  );
}

function EdgeHighlight({ points }: { points: number[][] }) {
  const lineObj = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(points.length * 3);
    for (let i = 0; i < points.length; i++) {
      positions[i * 3] = points[i][0];
      positions[i * 3 + 1] = points[i][1];
      positions[i * 3 + 2] = points[i][2];
    }
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.LineBasicMaterial({
      color: 0xff4444,
      depthTest: false,
    });
    return new THREE.Line(geo, mat);
  }, [points]);

  return (
    <>
      <primitive object={lineObj} renderOrder={999} />
      {[points[0], points[points.length - 1]].map((p, i) => (
        <mesh key={i} position={[p[0], p[1], p[2]]} renderOrder={999}>
          <sphereGeometry args={[0.8, 8, 8]} />
          <meshBasicMaterial
            color="#ff4444"
            depthTest={false}
            transparent
            opacity={0.9}
          />
        </mesh>
      ))}
    </>
  );
}

function ParameterHotspot({
  param,
  isSelected,
  onSelect,
}: {
  param: ParameterData;
  isSelected: boolean;
  onSelect: (e: ThreeEvent<MouseEvent>) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const pos = useMemo(() => centroid(param.edge_points), [param.edge_points]);
  if (!pos) return null;

  const baseRadius = 1.2;
  const scale = isSelected ? 1.8 : hovered ? 1.4 : 1.0;
  const color = TYPE_COLOR[param.parameter_type] ?? "#22d3ee";

  return (
    <mesh
      position={pos}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(e);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = "auto";
      }}
      renderOrder={998}
    >
      <sphereGeometry args={[baseRadius * scale, 16, 16]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={isSelected || hovered ? 0.95 : 0.65}
        depthTest={false}
      />
    </mesh>
  );
}

function HotspotPopover({
  param,
  onApply,
  onCancel,
  disabled,
}: {
  param: ParameterData;
  onApply: (value: number) => void;
  onCancel: () => void;
  disabled: boolean;
}) {
  const pos = useMemo(() => centroid(param.edge_points), [param.edge_points]);
  const [value, setValue] = useState(String(param.value));
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setValue(String(param.value));
  }, [param.name, param.value]);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [param.name]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  if (!pos) return null;

  const num = parseFloat(value);
  const isValid = !Number.isNaN(num) && num >= 0;
  const isChanged = isValid && num !== param.value;

  return (
    <Html
      position={pos}
      style={{
        // ホットスポット直上に出す。pointer-events を canvas に取られないように
        transform: "translate(-50%, calc(-100% - 18px))",
        pointerEvents: "auto",
        width: 220,
      }}
      zIndexRange={[100, 0]}
    >
      <div
        className="rounded-sm border border-cyan-500/40 bg-zinc-950/95 p-2.5 font-mono text-[11px] text-zinc-100 shadow-[0_8px_24px_-8px_rgba(0,0,0,0.6)] backdrop-blur"
        onPointerDown={(e) => e.stopPropagation()}
      >
        <div className="mb-1.5 flex items-baseline justify-between gap-2">
          <span className="truncate text-zinc-200">{param.name}</span>
          <span className="text-[9px] uppercase tracking-widest text-cyan-400/80">
            {TYPE_LABEL[param.parameter_type] ?? param.parameter_type}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <input
            ref={inputRef}
            type="number"
            step="any"
            min={0}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            disabled={disabled}
            onKeyDown={(e) => {
              if (e.key === "Enter" && isValid) onApply(num);
            }}
            className={`w-full rounded-sm border bg-zinc-950 px-2 py-1 font-mono text-xs outline-none transition-colors focus:ring-1 disabled:opacity-50 ${
              isChanged
                ? "border-cyan-500/60 text-cyan-100 focus:border-cyan-400 focus:ring-cyan-400/30"
                : "border-zinc-800 text-zinc-100 focus:border-zinc-600 focus:ring-zinc-600/30"
            }`}
          />
          <span className="text-[10px] text-zinc-600">mm</span>
        </div>

        <div className="mt-2 flex gap-1.5">
          <button
            type="button"
            disabled={!isChanged || !isValid || disabled}
            onClick={() => onApply(num)}
            className="flex-1 rounded-sm border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-[10px] uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-400 hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-transparent disabled:text-zinc-600"
          >
            {disabled ? "…" : "Apply"}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={disabled}
            className="rounded-sm border border-zinc-800 px-2 py-1 text-[10px] uppercase tracking-widest text-zinc-500 transition-colors hover:border-zinc-600 hover:text-zinc-300 disabled:opacity-40"
          >
            Esc
          </button>
        </div>
      </div>
    </Html>
  );
}

export default function StlViewer({
  url,
  highlightEdgePoints,
  parameters,
  selectedParamName,
  onSelectParam,
  onApplyParam,
  disabled = false,
}: StlViewerProps) {
  const selectedParam = useMemo(
    () =>
      parameters && selectedParamName
        ? parameters.find((p) => p.name === selectedParamName) ?? null
        : null,
    [parameters, selectedParamName],
  );

  const pickable = useMemo(
    () => (parameters ?? []).filter((p) => p.edge_points.length > 0),
    [parameters],
  );

  return (
    <div className="h-full w-full min-h-[400px] rounded-lg border border-gray-200 bg-gray-50">
      <Canvas
        camera={{ position: [80, 80, 80], fov: 50 }}
        onPointerMissed={() => onSelectParam?.(null)}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 10]} intensity={0.8} />
        <directionalLight position={[-10, -5, -10]} intensity={0.3} />

        <Center>
          <StlModel url={url} />

          {highlightEdgePoints && highlightEdgePoints.length >= 2 && (
            <EdgeHighlight points={highlightEdgePoints} />
          )}

          {pickable.map((p) => (
            <ParameterHotspot
              key={p.name}
              param={p}
              isSelected={p.name === selectedParamName}
              onSelect={() => onSelectParam?.(p.name)}
            />
          ))}

          {selectedParam && onApplyParam && (
            <HotspotPopover
              param={selectedParam}
              onApply={(v) => onApplyParam(selectedParam.name, v)}
              onCancel={() => onSelectParam?.(null)}
              disabled={disabled}
            />
          )}
        </Center>

        <Grid
          args={[200, 200]}
          cellSize={10}
          cellColor="#d1d5db"
          sectionSize={50}
          sectionColor="#9ca3af"
          fadeDistance={300}
          position={[0, -0.01, 0]}
        />

        <OrbitControls makeDefault />
      </Canvas>
    </div>
  );
}
