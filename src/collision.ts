import * as THREE from 'three';
import { Octree } from 'three/examples/jsm/math/Octree.js';
import { Capsule } from 'three/examples/jsm/math/Capsule.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { MeshBVH } from 'three-mesh-bvh';

/**
 * Kolizje kapsuły gracza ze statyczną geometrią stadionu.
 *
 * Wcześniej Octree z three.js budował drzewo z ok. 120 tys. trójkątów przez ok. 26 s na głównym wątku
 * (przeglądarka zgłaszała, że strona nie odpowiada): wielkie płaskie trójkąty terenu i placu oraz
 * pręty kratownic masztów trafiały do tysięcy komórek. MeshBVH buduje się w ułamku sekundy.
 * Test kapsuła–trójkąt i rozwiązywanie kolejnych kontaktów są identyczne jak w Octree.capsuleIntersect,
 * więc kontroler gracza (src/main.ts) zachowuje się tak samo.
 */
export class WorldCollider {
  private bvh: MeshBVH | null = null;
  // Octree służy tu tylko jako dostawca testu triangleCapsuleIntersect (nie budujemy drzewa)
  private readonly narrowPhase = new Octree();
  private readonly capsule = new Capsule();
  private readonly box = new THREE.Box3();
  private readonly candidates: THREE.Triangle[] = [];

  get ready() {
    return this.bvh !== null;
  }

  /** Scala w jedną geometrię (współrzędne świata) wszystkie siatki z warstwy layer pod root. */
  build(root: THREE.Object3D, layer: number) {
    root.updateMatrixWorld(true);
    const parts: THREE.BufferGeometry[] = [];
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || !mesh.layers.isEnabled(layer)) return;
      // Pozycje w GLB są skwantyzowane (meshopt, int16): kopia do Float32 przed przejściem do świata
      const pos = mesh.geometry.getAttribute('position');
      const xyz = new Float32Array(pos.count * 3);
      for (let i = 0; i < pos.count; i++) {
        xyz[3 * i] = pos.getX(i);
        xyz[3 * i + 1] = pos.getY(i);
        xyz[3 * i + 2] = pos.getZ(i);
      }
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(xyz, 3));
      g.setIndex(mesh.geometry.index ? mesh.geometry.index.clone() : Array.from({ length: pos.count }, (_, i) => i));
      g.applyMatrix4(mesh.matrixWorld);
      parts.push(g);
    });
    const merged = mergeGeometries(parts, false);
    parts.forEach((g) => g.dispose());
    this.bvh = new MeshBVH(merged);
  }

  /** Jak Octree.capsuleIntersect: wypadkowa korekta po rozwiązaniu kontaktów z trójkątami w otoczeniu kapsuły. */
  capsuleIntersect(capsule: Capsule): { normal: THREE.Vector3; depth: number } | false {
    if (!this.bvh) return false;
    const c = this.capsule.copy(capsule);
    const r = c.radius;
    this.box.min.set(Math.min(c.start.x, c.end.x) - r, Math.min(c.start.y, c.end.y) - r, Math.min(c.start.z, c.end.z) - r);
    this.box.max.set(Math.max(c.start.x, c.end.x) + r, Math.max(c.start.y, c.end.y) + r, Math.max(c.start.z, c.end.z) + r);

    const tris = this.candidates;
    tris.length = 0;
    this.bvh.shapecast({
      intersectsBounds: (b) => b.intersectsBox(this.box),
      intersectsTriangle: (tri) => {
        tris.push(tri.clone());
        return false;
      }
    });

    let hit = false;
    for (const tri of tris) {
      const result = this.narrowPhase.triangleCapsuleIntersect(c, tri);
      if (result) {
        hit = true;
        c.translate(result.normal.multiplyScalar(result.depth));
      }
    }
    if (!hit) return false;
    const v = c.getCenter(new THREE.Vector3()).sub(capsule.getCenter(new THREE.Vector3()));
    const depth = v.length();
    return { normal: v.normalize(), depth };
  }
}
