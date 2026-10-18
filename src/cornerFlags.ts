import * as THREE from 'three';

// Chorągiewki w narożnikach boiska 105 x 68 m (linie: tools/build_horseshoe_bowl.py, środek boiska w 0,0).
// Falowanie liczy vertex shader z jednego uniformu czasu: zero pracy CPU na klatkę.
// Flagi nie rzucają cieni: mapy cieni są statyczne (src/lighting.ts), cień zastygłby w jednej pozie.
const CORNERS: [number, number][] = [[34, 52.5], [-34, 52.5], [34, -52.5], [-34, -52.5]];
const POLE_H = 1.5;
const POLE_R = 0.018;
const FLAG_W = 0.5;
const FLAG_H = 0.4;
const WIND_ANGLE = 0.6; // kierunek wiatru wokół osi pionowej, wspólny dla wszystkich flag

export class CornerFlags {
  private time = { value: 0 };

  constructor(scene: THREE.Scene) {
    const poleGeo = new THREE.CylinderGeometry(POLE_R, POLE_R, POLE_H, 8);
    poleGeo.translate(0, POLE_H / 2, 0);
    const poleMat = new THREE.MeshStandardMaterial({ color: 0xf2c200, roughness: 0.5 });

    // Flaga zaczepiona lewą krawędzią o słupek, poziome pasy biało-czerwono-białe
    const flagGeo = new THREE.PlaneGeometry(FLAG_W, FLAG_H, 10, 1);
    flagGeo.translate(FLAG_W / 2, POLE_H - FLAG_H / 2, 0);
    const stripes = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255, 200, 16, 32, 255, 255, 255, 255, 255]), 1, 3);
    stripes.magFilter = THREE.NearestFilter;
    stripes.colorSpace = THREE.SRGBColorSpace;
    stripes.needsUpdate = true;
    const flagMat = new THREE.MeshStandardMaterial({ map: stripes, side: THREE.DoubleSide, roughness: 0.8 });
    flagMat.onBeforeCompile = (shader) => {
      shader.uniforms.uTime = this.time;
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nuniform float uTime;')
        // Fala biegnie od słupka; amplituda rośnie z odległością od niego (krawędź przy słupku nieruchoma)
        .replace('#include <beginnormal_vertex>', `#include <beginnormal_vertex>
          float fx = position.x / ${FLAG_W.toFixed(2)};
          float ph = position.x * 9.0 - uTime * 6.0 + position.y * 2.0;
          float amp = 0.06 * fx;
          objectNormal = normalize(vec3(-amp * 9.0 * cos(ph), 0.0, 1.0));`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          transformed.z += amp * sin(ph);
          transformed.y -= 0.03 * fx * fx;`);
    };

    for (const [x, y] of CORNERS) {
      // Blender (x, y, z) -> glTF/three (x, z, -y)
      const group = new THREE.Group();
      group.position.set(x, 0, -y);
      group.rotation.y = WIND_ANGLE;
      const pole = new THREE.Mesh(poleGeo, poleMat);
      pole.castShadow = true;
      pole.receiveShadow = true;
      const flag = new THREE.Mesh(flagGeo, flagMat);
      flag.receiveShadow = true;
      group.add(pole, flag);
      scene.add(group);
    }
  }

  update(time: number) {
    this.time.value = time;
  }
}
