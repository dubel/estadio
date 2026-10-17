import * as THREE from 'three';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';

// Oś długa stadionu jest odchylona od północy geograficznej o 24,92° na zachód (docs/zrodla.md).
// Układ sceny: x — wschód stadionu, -z — północ stadionu (Y w Blenderze).
const STADIUM_AXIS_DEG = 24.92;
const LODZ = { lat: 51.759, lon: 19.457 };
// Pochmurne popołudnie meczowe: 17.09.2011, 16:00 CEST
const AFTERNOON = new Date('2011-09-17T14:00:00Z');

const DAY = {
  fog: 0xaab2b9,
  fogDensity: 0.0012,          // bloki za torami (500–900 m) przebijają się przez lekką mgiełkę
  exposure: 0.85,
  environmentIntensity: 1.0,
  sunIntensity: 1.1,           // zachmurzenie: słońce rozproszone, cienie miękkie
  sunColor: 0xfff4e6
};
const NIGHT = {
  background: 0x070b12,
  fog: 0x070b12,
  fogDensity: 0.005,
  exposure: 1.0,
  environmentIntensity: 0.03,
  sunIntensity: 0.0,
  jupiterIntensity: 8000.0
};

/** Azymut (od północy, zgodnie z ruchem wskazówek) i wysokość słońca w stopniach — przybliżenie NOAA. */
export function solarAngles(date: Date, latDeg: number, lonDeg: number) {
  const rad = Math.PI / 180;
  const d = date.getTime() / 86400000 - 10957.5;                    // dni od J2000.0
  const g = (357.529 + 0.98560028 * d) * rad;
  const q = 280.459 + 0.98564736 * d;
  const L = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad;
  const e = (23.439 - 0.00000036 * d) * rad;
  const ra = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L));
  const dec = Math.asin(Math.sin(e) * Math.sin(L));
  const gmst = (18.697374558 + 24.06570982441908 * d) % 24;
  const H = (gmst * 15 + lonDeg) * rad - ra;
  const lat = latDeg * rad;
  const el = Math.asin(Math.sin(lat) * Math.sin(dec) + Math.cos(lat) * Math.cos(dec) * Math.cos(H));
  const az = Math.atan2(-Math.sin(H) * Math.cos(dec), Math.sin(dec) * Math.cos(lat) - Math.cos(dec) * Math.sin(lat) * Math.cos(H));
  return { azimuth: (az / rad + 360) % 360, elevation: el / rad };
}

/** Kierunek do słońca w układzie sceny (uwzględnia obrót osi stadionu względem północy). */
export function sunDirection(date: Date): THREE.Vector3 {
  const { azimuth, elevation } = solarAngles(date, LODZ.lat, LODZ.lon);
  const b = THREE.MathUtils.degToRad(azimuth + STADIUM_AXIS_DEG);
  const el = THREE.MathUtils.degToRad(elevation);
  return new THREE.Vector3(Math.sin(b) * Math.cos(el), Math.sin(el), -Math.cos(b) * Math.cos(el));
}

// Jupitery: głowice masztów (pozycje jak w tools/build_full_stadium.py, układ sceny)
export const JUPITER_POSITIONS = [
  new THREE.Vector3(-68.0, 48.2,  82.0), // SW
  new THREE.Vector3(-68.0, 48.2, -82.0), // NW
  new THREE.Vector3( 68.0, 48.2,  61.5), // SE — ortofotomapa
  new THREE.Vector3( 68.0, 48.2, -61.5)  // NE — ortofotomapa
];

interface TrackedEmissive {
  mat: THREE.MeshStandardMaterial;
  day: { color: THREE.Color; intensity: number };
  night: { color: THREE.Color; intensity: number };
  pulse: boolean;
}

/** Pionowy gradient alfa dla stożków światła (u góry przy głowicy jasno, przy murawie zanika). */
function coneAlphaMap(): THREE.DataTexture {
  const n = 64;
  const data = new Uint8Array(n * 4);
  for (let i = 0; i < n; i++) {
    const v = Math.pow(i / (n - 1), 1.6) * 255;
    data.set([v, v, v, 255], i * 4);
  }
  const tex = new THREE.DataTexture(data, 1, n);
  tex.needsUpdate = true;
  return tex;
}

export class Lighting {
  isNight = false;

  private readonly sun = new THREE.DirectionalLight(DAY.sunColor, DAY.sunIntensity);
  private readonly spots: THREE.SpotLight[] = [];
  private readonly glows: THREE.Sprite[] = [];
  private readonly cones: THREE.Mesh[] = [];
  private readonly emissives: TrackedEmissive[] = [];
  private skyTexture: THREE.Texture | null = null;

  constructor(private readonly scene: THREE.Scene, private readonly renderer: THREE.WebGLRenderer) {
    renderer.toneMapping = THREE.NeutralToneMapping;   // AgX zbyt mocno odbarwiał pochmurną scenę
    renderer.toneMappingExposure = DAY.exposure;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.setupSun();
    this.setupJupiters();
    this.applyDay();
  }

  /** Niebo HDRI (Poly Haven „Overcast Soil”, CC0) jako tło i oświetlenie otoczenia (IBL). */
  loadSky(url: string): Promise<void> {
    return new HDRLoader().loadAsync(url).then((hdr) => {
      hdr.mapping = THREE.EquirectangularReflectionMapping;
      const pmrem = new THREE.PMREMGenerator(this.renderer);
      this.scene.environment = pmrem.fromEquirectangular(hdr).texture;
      pmrem.dispose();
      this.skyTexture = hdr;
      if (!this.isNight) this.applyDay();
    });
  }

  private setupSun() {
    const dir = sunDirection(AFTERNOON);
    const s = this.sun;
    s.position.copy(dir).multiplyScalar(250);
    s.target.position.set(-10, 0, 0);       // środek ciężaru stadionu z trybuną główną
    s.position.add(s.target.position);
    s.castShadow = true;
    s.shadow.mapSize.set(4096, 4096);
    s.shadow.camera.near = 50;
    s.shadow.camera.far = 500;
    const half = 135;                       // obejmuje trybunę główną (do x ≈ −87), podkowę i maszty
    Object.assign(s.shadow.camera, { left: -half, right: half, top: half, bottom: -half });
    s.shadow.bias = -0.0004;
    s.shadow.normalBias = 0.05;
    s.shadow.radius = 3;
    this.scene.add(s, s.target);
  }

  private setupJupiters() {
    const glowTexture = new THREE.TextureLoader().load('/assets/textures/floodlight_glow.png');
    const alphaMap = coneAlphaMap();
    const aim = new THREE.Vector3(0, 0, 0);

    JUPITER_POSITIONS.forEach((pos, idx) => {
      const spot = new THREE.SpotLight(0xfffae8, 0.0);
      spot.position.copy(pos);
      spot.target.position.copy(aim);
      spot.angle = Math.PI / 3.8;
      spot.penumbra = 0.55;
      spot.distance = 260;
      spot.castShadow = idx === 0;          // cień z jednego masztu — koszt cieni punktowych
      this.scene.add(spot, spot.target);
      this.spots.push(spot);

      const glow = new THREE.Sprite(new THREE.SpriteMaterial({
        map: glowTexture, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false
      }));
      glow.position.copy(pos);
      glow.scale.set(34, 34, 1);
      this.scene.add(glow);
      this.glows.push(glow);

      // Smuga światła: otwarty stożek od głowicy w stronę murawy (addytywny, widoczny tylko nocą)
      const length = pos.distanceTo(aim) * 0.6;
      const cone = new THREE.Mesh(
        new THREE.ConeGeometry(11, length, 32, 1, true),
        new THREE.MeshBasicMaterial({
          color: 0xfff3dc, alphaMap, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending,
          depthWrite: false, side: THREE.DoubleSide, fog: false
        })
      );
      const dir = aim.clone().sub(pos).normalize();
      cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), dir);  // wierzchołek stożka w głowicy
      cone.position.copy(pos).addScaledVector(dir, length / 2);
      cone.visible = false;
      this.scene.add(cone);
      this.cones.push(cone);
    });
  }

  /** Materiały świecące z modelu: reflektory, światło ostrzegawcze, tablica wyników. */
  trackModel(model: THREE.Object3D) {
    const rules: [string, TrackedEmissive['day'], TrackedEmissive['night'], boolean][] = [
      ['Lamp_Glow', { color: new THREE.Color(0x222222), intensity: 0.0 }, { color: new THREE.Color(0xffffff), intensity: 25.0 }, false],
      ['Beacon', { color: new THREE.Color(0x220000), intensity: 0.2 }, { color: new THREE.Color(0xff1111), intensity: 8.0 }, true],
      ['Board_Historic', { color: new THREE.Color(0x000000), intensity: 0.0 }, { color: new THREE.Color(0xffffff), intensity: 2.2 }, false]
    ];
    const seen = new Set<THREE.Material>();
    model.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (!mesh.isMesh) return;
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        const std = m as THREE.MeshStandardMaterial;
        if (!std?.isMeshStandardMaterial || seen.has(std)) continue;
        seen.add(std);
        const rule = rules.find(([key]) => std.name.includes(key));
        if (rule) this.emissives.push({ mat: std, day: rule[1], night: rule[2], pulse: rule[3] });
      }
    });
    this.applyEmissives();
  }

  setNight(night: boolean) {
    this.isNight = night;
    if (night) this.applyNight(); else this.applyDay();
  }

  update(time: number) {
    if (!this.isNight) return;
    const pulse = 0.75 + 0.25 * Math.sin(time * 4.0);
    for (const e of this.emissives) if (e.pulse) e.mat.emissiveIntensity = e.night.intensity * pulse;
  }

  private applyDay() {
    const sc = this.scene;
    sc.background = this.skyTexture ?? new THREE.Color(DAY.fog);
    sc.environmentIntensity = DAY.environmentIntensity;
    sc.backgroundIntensity = 1.0;
    sc.fog = new THREE.FogExp2(DAY.fog, DAY.fogDensity);
    this.renderer.toneMappingExposure = DAY.exposure;
    this.sun.intensity = DAY.sunIntensity;
    this.spots.forEach((l) => (l.intensity = 0));
    // Ukryte, nie tylko przezroczyste: GTAO rysuje normalne wszystkich widocznych obiektów
    this.glows.forEach((g) => { g.material.opacity = 0; g.visible = false; });
    this.cones.forEach((c) => (c.visible = false));
    this.applyEmissives();
  }

  private applyNight() {
    const sc = this.scene;
    sc.background = new THREE.Color(NIGHT.background);
    sc.environmentIntensity = NIGHT.environmentIntensity;
    sc.fog = new THREE.FogExp2(NIGHT.fog, NIGHT.fogDensity);
    this.renderer.toneMappingExposure = NIGHT.exposure;
    this.sun.intensity = NIGHT.sunIntensity;
    this.spots.forEach((l) => (l.intensity = NIGHT.jupiterIntensity));
    this.glows.forEach((g) => { g.material.opacity = 0.95; g.visible = true; });
    this.cones.forEach((c) => {
      c.visible = true;
      (c.material as THREE.MeshBasicMaterial).opacity = 0.045;
    });
    this.applyEmissives();
  }

  private applyEmissives() {
    for (const e of this.emissives) {
      const s = this.isNight ? e.night : e.day;
      e.mat.emissive.copy(s.color);
      e.mat.emissiveIntensity = s.intensity;
    }
  }
}
