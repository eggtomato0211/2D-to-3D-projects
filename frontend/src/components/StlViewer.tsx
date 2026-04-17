"use client";

import { useRef, useEffect, useState, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Center, Grid } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";

interface StlViewerProps {
  url: string;
  highlightEdgePoints?: number[][] | null;
}

function StlModel({ url }: { url: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
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
    <Center>
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial color="#6b9bd2" metalness={0.3} roughness={0.6} />
      </mesh>
    </Center>
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
    <Center>
      <primitive object={lineObj} renderOrder={999} />
      {/* エッジの始点・終点に球を描画して視認性向上 */}
      {[points[0], points[points.length - 1]].map((p, i) => (
        <mesh key={i} position={[p[0], p[1], p[2]]} renderOrder={999}>
          <sphereGeometry args={[0.8, 8, 8]} />
          <meshBasicMaterial color="#ff4444" depthTest={false} transparent opacity={0.9} />
        </mesh>
      ))}
    </Center>
  );
}

export default function StlViewer({ url, highlightEdgePoints }: StlViewerProps) {
  return (
    <div className="absolute inset-0 rounded-lg border border-gray-200 bg-gray-50">
      <Canvas camera={{ position: [80, 80, 80], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 10]} intensity={0.8} />
        <directionalLight position={[-10, -5, -10]} intensity={0.3} />

        <StlModel url={url} />

        {highlightEdgePoints && highlightEdgePoints.length >= 2 && (
          <EdgeHighlight points={highlightEdgePoints} />
        )}

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
