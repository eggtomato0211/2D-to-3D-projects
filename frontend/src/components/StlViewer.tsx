"use client";

import { useRef, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Center, Grid } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";

interface StlViewerProps {
  url: string;
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

export default function StlViewer({ url }: StlViewerProps) {
  return (
    <div className="h-full w-full min-h-[400px] rounded-lg border border-gray-200 bg-gray-50">
      <Canvas camera={{ position: [80, 80, 80], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 10]} intensity={0.8} />
        <directionalLight position={[-10, -5, -10]} intensity={0.3} />

        <StlModel url={url} />

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
