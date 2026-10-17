// Generator drzew (EZ-Tree, MIT) uruchamiany w headless Chrome przez tools/generate_trees.mjs.
// Buduje kilka odmian, rozstawia je instancjami na pozycjach z ortofotomapy
// (tools/data/drzewa_ortofoto.json) i eksportuje jeden GLB z EXT_mesh_gpu_instancing.
import * as THREE from 'three';
import { Tree } from '@dgreenheck/ez-tree';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import ortho from '../data/drzewa_ortofoto.json';

// Odmiany: preset EZ-Tree, ziarno, kora, wysokość docelowa przy skali 1 z ortofotomapy [m],
// opcjonalnie odcień liści (presety osiki są jesienne, żółte — połowa września była jeszcze zielona).
// Wysokość korony z ortofotomapy nie wynika — 14–22 m to typowe drzewa parkowe i przyuliczne w Łodzi.
export const VARIANTS = [
  { name: 'Brzoza', preset: 'Aspen Medium', seed: 18020, bark: 'birch', height: 15, leafTint: 0x9fd070 },
  { name: 'Topola', preset: 'Aspen Large', seed: 4113, bark: 'willow', height: 21, leafTint: 0x8cc066 },
  { name: 'Jesion', preset: 'Ash Medium', seed: 2711, bark: 'oak', height: 16 },
  { name: 'Dab', preset: 'Oak Medium', seed: 905, bark: 'oak', height: 14 }
];
const GROUND_Y = -0.25;          // teren poza placem (build_surroundings.py: Teren_Trawa)

function hash(i) {
  const s = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
}

/**
 * Lżejsza wersja presetu (drzewa oglądane z trybun, z daleka): mniej ścianek i odcinków gałęzi,
 * mniej liści o większym rozmiarze — korona zostaje pełna. Ok. 3–9 tys. trójkątów na drzewo zamiast 7–20 tys.
 */
function lighten(o) {
  for (const k of Object.keys(o.branch.segments)) o.branch.segments[k] = Math.max(3, Math.round(o.branch.segments[k] * 0.5));
  for (const k of Object.keys(o.branch.sections)) o.branch.sections[k] = Math.max(2, Math.round(o.branch.sections[k] * 0.5));
  o.leaves.count = Math.max(3, Math.round(o.leaves.count * 0.6));
  o.leaves.size *= 1.6;
}

/** Phong z EZ-Tree → Standard (glTF eksportuje metal-roughness). */
function toStandard(m, leaves) {
  return new THREE.MeshStandardMaterial({
    name: leaves ? 'Mat_Liscie_EZTree' : 'Mat_Kora_EZTree',
    map: m.map,
    normalMap: leaves ? null : m.normalMap,
    color: m.color,
    roughness: leaves ? 0.75 : 0.95,
    side: leaves ? THREE.DoubleSide : THREE.FrontSide,
    alphaTest: leaves ? m.alphaTest : 0
  });
}

/** Normalne liści od środka korony: oświetlenie jak bryły, nie jak tysiąca płaskich kart. */
function crownNormals(geo) {
  geo.computeBoundingBox();
  const c = geo.boundingBox.getCenter(new THREE.Vector3());
  const pos = geo.getAttribute('position');
  const n = new Float32Array(pos.count * 3);
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i).sub(c);
    v.y *= 0.6;
    v.normalize();
    n.set([v.x, v.y, v.z], i * 3);
  }
  geo.setAttribute('normal', new THREE.BufferAttribute(n, 3));
}

const root = new THREE.Group();
root.name = 'Drzewa';
const stats = [];
// Instancje dzielone na ćwiartki wokół stadionu: InstancedMesh jest odrzucany poza kadrem tylko w całości,
// więc jedna siatka na odmianę rysowała też drzewa za plecami kamery
const SECTORS = 4;
const groups = VARIANTS.map(() => Array.from({ length: SECTORS }, () => []));
ortho.trees.forEach((t, i) => {
  const sector = Math.floor(((Math.atan2(t.y, t.x) + Math.PI) / (2 * Math.PI)) * SECTORS) % SECTORS;
  groups[Math.floor(hash(i) * VARIANTS.length)][sector].push({ ...t, i });
});

VARIANTS.forEach((variant, vi) => {
  const tree = new Tree();
  tree.loadPreset(variant.preset);
  tree.options.seed = variant.seed;
  tree.options.bark.type = variant.bark;
  if (variant.leafTint) tree.options.leaves.tint = variant.leafTint;
  lighten(tree.options);
  tree.generate();

  const box = new THREE.Box3().setFromObject(tree);
  const unit = variant.height / (box.max.y - box.min.y);
  const branches = tree.branchesMesh.geometry.clone().scale(unit, unit, unit);
  const leaves = tree.leavesMesh.geometry.clone().scale(unit, unit, unit);
  crownNormals(leaves);
  const barkMat = toStandard(tree.branchesMesh.material, false);
  const leafMat = toStandard(tree.leavesMesh.material, true);
  stats.push({ name: variant.name, branches: branches.index.count / 3, leaves: leaves.index.count / 3,
               count: groups[vi].reduce((n, g) => n + g.length, 0) });

  groups[vi].forEach((items, sector) => {
    if (!items.length) return;
    const meshB = new THREE.InstancedMesh(branches, barkMat, items.length);
    const meshL = new THREE.InstancedMesh(leaves, leafMat, items.length);
    meshB.name = `Drzewa_${variant.name}_${sector}_Kora`;
    meshL.name = `Drzewa_${variant.name}_${sector}_Liscie`;
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    items.forEach((t, k) => {
      const s = t.scale * (0.9 + 0.2 * hash(t.i + 1000));
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), hash(t.i + 2000) * Math.PI * 2);
      // stadion: X wschód, Y północ; Three.js: x = X, z = -Y
      m.compose(new THREE.Vector3(t.x, GROUND_Y, -t.y), q, new THREE.Vector3(s, s, s));
      meshB.setMatrixAt(k, m);
      meshL.setMatrixAt(k, m);
    });
    root.add(meshB, meshL);
  });
});

// Tekstury EZ-Tree ładują się asynchronicznie (TextureLoader z data URI) — eksport po ich wczytaniu
const textures = [];
root.traverse((o) => {
  if (o.material) for (const key of ['map', 'normalMap']) if (o.material[key]) textures.push(o.material[key]);
});
while (!textures.every((t) => t.image && t.image.complete && t.image.naturalWidth > 0)) {
  await new Promise((r) => setTimeout(r, 50));
}

new GLTFExporter().parse(
  root,
  (glb) => {
    const bytes = new Uint8Array(glb);
    let bin = '';
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    window.__result = { glb: btoa(bin), stats };
  },
  (err) => { window.__result = { error: String(err) }; },
  { binary: true }
);
