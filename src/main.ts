import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js';
import { Octree } from 'three/examples/jsm/math/Octree.js';
import { Capsule } from 'three/examples/jsm/math/Capsule.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { Lighting } from './lighting';
import { PostFX } from './postfx';

// --- STAN APLIKACJI ---
let isFlyMode = false;
const clock = new THREE.Clock();

// --- INICJALIZACJA SCENY I RENDERERA ---
const canvas = document.getElementById('stage') as HTMLCanvasElement;
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: 'high-performance'
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); // MSAA 4x przy DPR 2 to 16 próbek/piksel CSS

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.2, 2000);

// --- OŚWIETLENIE I POSTPROCESSING (src/lighting.ts, src/postfx.ts) ---
const lighting = new Lighting(scene, renderer);
lighting.loadSky('/assets/env/overcast_soil_puresky_2k.hdr');
const postfx = new PostFX(renderer, scene, camera);

// --- PUNKTY WIDOKOWE (TELEPORTACJA) ---
interface Viewpoint {
  name: string;
  pos: THREE.Vector3;
  target: THREE.Vector3;
}

const viewpoints: Viewpoint[] = [
  {
    name: "Środek Murawy (Widok na Trybunę Główną)",
    pos: new THREE.Vector3(0, 1.8, 0),
    target: new THREE.Vector3(-60, 8, 0)
  },
  {
    name: "Korona Trybuny Głównej (Rząd 33)",
    pos: new THREE.Vector3(-81, 20.3, 1.64), // przejście w osi przęsła 7 (nad tunelem)
    target: new THREE.Vector3(0, 4, 1.64)
  },
  {
    name: "Trybuna Główna — Sektor VIP & Daszek",
    pos: new THREE.Vector3(-49, 3.6, -12),
    target: new THREE.Vector3(0, 2, 0)
  },
  {
    name: "Łuk Południowy — Historyczny Zegar",
    pos: new THREE.Vector3(0, 2.2, 40),
    target: new THREE.Vector3(0, 10.5, 110.5)
  },
  {
    name: "Galera (Al. Unii Lubelskiej)",
    pos: new THREE.Vector3(64, 7.2, 3.5), // rząd 16, sekcja przy linii środkowej (siatka na Y = 0)
    target: new THREE.Vector3(-55, 7, 3.5)
  },
  {
    name: "Jupiter NW — Szczyt Masztu Oświetleniowego",
    pos: new THREE.Vector3(-45, 26, -55),
    target: new THREE.Vector3(-68, 48.2, -82)
  },
  {
    name: "Bramka Południowa — Biało-Czerwono-Biała Siatka",
    pos: new THREE.Vector3(0, 1.6, 44),
    target: new THREE.Vector3(0, 1.2, 53.5)
  },
  {
    name: "Tunel pod Trybuną Główną — Schody na Widownię",
    pos: new THREE.Vector3(-74.5, 1.7, -16.9),
    target: new THREE.Vector3(-55, 6, -16.9)
  }
];

// --- FIZYKA, KOLIZJE I SCHODY (OCTREE & CAPSULE CONTROLLER) ---
const worldOctree = new Octree();
const COLLIDER_LAYER = 1;
let octreeReady = false;

const CAPSULE_RADIUS = 0.35;
const playerCollider = new Capsule(
  new THREE.Vector3(0, CAPSULE_RADIUS, 0),
  new THREE.Vector3(0, 1.40, 0),
  CAPSULE_RADIUS
);

const playerVelocity = new THREE.Vector3();
const playerDirection = new THREE.Vector3();
let playerOnFloor = false;
const GRAVITY = 25.0;
const STEPS_PER_FRAME = 5;
const MAX_STEP_HEIGHT = 0.48; // Umożliwia wchodzenie po stopniach trybun (do 48 cm)
const CAMERA_EYE_OFFSET = new THREE.Vector3(0, 0.25, 0); // Oczy 25 cm ponad środkiem górnej sfery (1.65 m nad gruntem)
const STEP_PROBE = CAPSULE_RADIUS * 0.5; // min. wysunięcie kapsuły nad krawędź stopnia
const STEP_DOWN_SLICES = 12; // rozdzielczość opuszczania kapsuły na stopień (4 cm)
const JUMP_SPEED = 5.0; // v²/2g = 0.5 m wysokości skoku

function playerCollisions() {
  if (!octreeReady) return;
  playerOnFloor = false;
  for (let iter = 0; iter < 2; iter++) {
    const result = worldOctree.capsuleIntersect(playerCollider);
    // Styk o zerowej głębokości ma zerową normalną — liczony jako „ściana” gasił prędkość
    if (!result || result.depth < 1e-6) break;

    if (result.normal.y > 0.25) {
      playerOnFloor = true;
      if (playerVelocity.y < 0) playerVelocity.y = 0;
    } else {
      // Kolizja pionowa ze ścianą / barierką: ślizganie wzdłuż płaszczyzny
      playerVelocity.addScaledVector(result.normal, -result.normal.dot(playerVelocity));
    }

    playerCollider.translate(result.normal.multiplyScalar(result.depth));
  }
}

// Opuszcza kapsułę porcjami aż do pierwszego kontaktu z podłożem (max maxDrop).
// Zanurzenie o całe maxDrop naraz dawało głęboką penetrację, a zagregowana normalna z sąsiednich
// trójkątów (podstopnie, krawędzie) wypychała kapsułę w tył — postać stała w miejscu na schodach.
// Pozioma korekta przeciwna do ruchu jest odrzucana: normalne z pobliskich krawędzi cofały kapsułę o tyle,
// ile przeszła w sub-stepie (zacinanie przed pierwszym stopniem schodów tunelu). Korekta zgodna z ruchem
// zostaje — pomaga zsunąć się z krawędzi stopnia przy schodzeniu.
function lowerUntilFloor(maxDrop: number): boolean {
  const slice = new THREE.Vector3(0, -maxDrop / STEP_DOWN_SLICES, 0);
  playerOnFloor = false;
  for (let i = 0; i < STEP_DOWN_SLICES && !playerOnFloor; i++) {
    const x = playerCollider.start.x;
    const z = playerCollider.start.z;
    playerCollider.translate(slice);
    playerCollisions();
    const dx = playerCollider.start.x - x;
    const dz = playerCollider.start.z - z;
    if (dx * playerVelocity.x + dz * playerVelocity.z < 0) {
      playerCollider.translate(new THREE.Vector3(-dx, 0, -dz));
    }
  }
  return playerOnFloor;
}

function getForwardVector(): THREE.Vector3 {
  camera.getWorldDirection(playerDirection);
  playerDirection.y = 0;
  playerDirection.normalize();
  return playerDirection;
}

function getSideVector(): THREE.Vector3 {
  camera.getWorldDirection(playerDirection);
  playerDirection.y = 0;
  playerDirection.normalize();
  playerDirection.cross(camera.up);
  return playerDirection;
}

function respawnPlayer() {
  playerCollider.start.set(0, CAPSULE_RADIUS, 0);
  playerCollider.end.set(0, 1.40, 0);
  playerVelocity.set(0, 0, 0);
  camera.position.set(0, 1.65, 0);
  camera.lookAt(new THREE.Vector3(-60, 8, 0));
  playerOnFloor = true;
}

function updatePlayer(subDelta: number) {
  let damping = Math.exp(-4 * subDelta) - 1;

  if (!playerOnFloor) {
    playerVelocity.y -= GRAVITY * subDelta;
    damping *= 0.1; // mniejszy opór powietrza podczas skoku/spadania
  }

  playerVelocity.addScaledVector(playerVelocity, damping);

  const deltaPosition = playerVelocity.clone().multiplyScalar(subDelta);
  const horizDist = Math.hypot(deltaPosition.x, deltaPosition.z);
  const wasOnFloor = playerOnFloor;

  // Mechanika wchodzenia po schodach:
  if (playerOnFloor && horizDist > 1e-4) {
    const originalStart = playerCollider.start.clone();
    const originalEnd = playerCollider.end.clone();

    // Standardowa próba ruchu
    playerCollider.translate(deltaPosition);
    playerCollisions();

    // Sprawdzamy czy ruch został zablokowany przez pionowy stopień/mur
    const movedHoriz = Math.hypot(
      playerCollider.start.x - originalStart.x,
      playerCollider.start.z - originalStart.z
    );

    if (movedHoriz < horizDist * 0.65) {
      // Wykryto blokadę poziomą — próba pokonania stopnia (Step-Up):
      playerCollider.start.copy(originalStart);
      playerCollider.end.copy(originalEnd);

      // 1. Uniesienie kapsuły ponad krawędź stopnia
      playerCollider.translate(new THREE.Vector3(0, MAX_STEP_HEIGHT, 0));

      // 2. Przesunięcie poziome nad stopniem — co najmniej STEP_PROBE, bo przy przesunięciu
      // rzędu centymetrów zaokrąglony dół kapsuły trafia krawędź stopnia „równikiem” (normalna pozioma)
      const probe = Math.max(horizDist, STEP_PROBE) / horizDist;
      playerCollider.translate(new THREE.Vector3(deltaPosition.x * probe, 0, deltaPosition.z * probe));

      // Rozwiązanie ewentualnych kolizji na podwyższonym poziomie
      const wallCheck = worldOctree.capsuleIntersect(playerCollider);
      if (wallCheck) {
        playerCollider.translate(wallCheck.normal.multiplyScalar(wallCheck.depth));
      }

      // 3. Opuszczenie kapsuły na poziom stopnia (Step-Down)
      lowerUntilFloor(MAX_STEP_HEIGHT);

      // Jeżeli krok w górę nie znalazł podłoża lub trafił na wysoką ścianę, przywracamy ślizg
      if (!playerOnFloor) {
        playerCollider.start.copy(originalStart);
        playerCollider.end.copy(originalEnd);
        playerCollider.translate(deltaPosition);
        playerCollisions();
      }
    }
  } else {
    // Ruch w powietrzu lub stanie w miejscu
    playerCollider.translate(deltaPosition);
    playerCollisions();
  }

  // Płynne schodzenie w dół schodów (przyklejanie do niższego stopnia zamiast odbijania)
  if (wasOnFloor && !playerOnFloor && playerVelocity.y <= 0) {
    const start = playerCollider.start.clone();
    const end = playerCollider.end.clone();
    if (lowerUntilFloor(MAX_STEP_HEIGHT)) {
      playerVelocity.y = 0;
    } else {
      playerCollider.start.copy(start);
      playerCollider.end.copy(end);
    }
  }

  // Synchronizacja kamery
  camera.position.copy(playerCollider.end).add(CAMERA_EYE_OFFSET);

  // Bezpiecznik: powrót na murawę w razie wypadnięcia poza stadion
  if (playerCollider.start.y < -5.0) {
    respawnPlayer();
  }
}

// Jeden krok trybu Spacer: sterowanie, skok i sub-stepy fizyki
function stepWalk(delta: number) {
  const accel = keys.sprint ? 50.0 : 25.0;
  const fwd = getForwardVector();
  if (keys.forward) playerVelocity.addScaledVector(fwd, accel * delta);
  if (keys.backward) playerVelocity.addScaledVector(fwd, -accel * delta);
  const side = getSideVector();
  if (keys.left) playerVelocity.addScaledVector(side, -accel * delta);
  if (keys.right) playerVelocity.addScaledVector(side, accel * delta);

  if (keys.up && playerOnFloor) {
    playerVelocity.y = JUMP_SPEED;
    playerOnFloor = false;
  }

  // Podział kroku fizyki na sub-steps (dla stabilności i braku przenikania)
  const subDelta = delta / STEPS_PER_FRAME;
  for (let i = 0; i < STEPS_PER_FRAME; i++) {
    updatePlayer(subDelta);
  }
}

function setViewpoint(idx: number) {
  if (idx < 0 || idx >= viewpoints.length) return;
  const vp = viewpoints[idx];
  camera.position.copy(vp.pos);
  controls.object.position.copy(vp.pos);
  camera.lookAt(vp.target);

  playerCollider.start.set(vp.pos.x, vp.pos.y - 1.30, vp.pos.z);
  playerCollider.end.set(vp.pos.x, vp.pos.y - 0.25, vp.pos.z);
  playerVelocity.set(0, 0, 0);
  playerOnFloor = true;

  const locBadge = document.getElementById('hud-location');
  if (locBadge) locBadge.textContent = vp.name;
}

// --- KONTROLA KAMERY (POINTER LOCK CONTROLS) ---
const controls = new PointerLockControls(camera, canvas);

canvas.addEventListener('click', () => {
  if (!controls.isLocked) {
    controls.lock();
  }
});

controls.addEventListener('lock', () => {
  const reticle = document.getElementById('reticle');
  if (reticle) reticle.hidden = false;
});

controls.addEventListener('unlock', () => {
  const reticle = document.getElementById('reticle');
  if (reticle) reticle.hidden = true;
  releaseKeys();
});

// Sterowanie klawiaturą
const keys = {
  forward: false,
  backward: false,
  left: false,
  right: false,
  up: false,
  down: false,
  sprint: false
};

// Po Alt+Tab / Esc keyup nie dociera — bez resetu postać idzie dalej sama
function releaseKeys() {
  for (const k of Object.keys(keys) as (keyof typeof keys)[]) keys[k] = false;
}
window.addEventListener('blur', releaseKeys);

window.addEventListener('keydown', (e) => {
  switch (e.code) {
    case 'KeyW': keys.forward = true; break;
    case 'KeyS': keys.backward = true; break;
    case 'KeyA': keys.left = true; break;
    case 'KeyD': keys.right = true; break;
    case 'Space': keys.up = true; break;
    case 'ShiftLeft':
    case 'ShiftRight': keys.sprint = true; break;
    case 'KeyC': keys.down = true; break;
    case 'KeyL': toggleLighting(); break;
    case 'KeyV': toggleMode(); break;
    case 'Digit1': setViewpoint(0); break;
    case 'Digit2': setViewpoint(1); break;
    case 'Digit3': setViewpoint(2); break;
    case 'Digit4': setViewpoint(3); break;
    case 'Digit5': setViewpoint(4); break;
    case 'Digit6': setViewpoint(5); break;
    case 'Digit7': setViewpoint(6); break;
    case 'Digit8': setViewpoint(7); break;
  }
});

window.addEventListener('keyup', (e) => {
  switch (e.code) {
    case 'KeyW': keys.forward = false; break;
    case 'KeyS': keys.backward = false; break;
    case 'KeyA': keys.left = false; break;
    case 'KeyD': keys.right = false; break;
    case 'Space': keys.up = false; break;
    case 'ShiftLeft':
    case 'ShiftRight': keys.sprint = false; break;
    case 'KeyC': keys.down = false; break;
  }
});

function toggleLighting() {
  lighting.setNight(!lighting.isNight);
  postfx.setNight(lighting.isNight);
  const icon = document.getElementById('light-icon');
  const label = document.getElementById('light-label');
  if (icon) icon.textContent = lighting.isNight ? '🌙' : '☁️';
  if (label) label.textContent = lighting.isNight ? 'Noc (Jupitery)' : 'Dzień';
}

function toggleMode() {
  isFlyMode = !isFlyMode;
  const icon = document.getElementById('mode-icon');
  const label = document.getElementById('mode-label');
  if (icon) icon.textContent = isFlyMode ? '🚁' : '🚶';
  if (label) label.textContent = isFlyMode ? 'Dron (Lot)' : 'Spacer';

  if (!isFlyMode) {
    playerCollider.start.set(camera.position.x, camera.position.y - 1.30, camera.position.z);
    playerCollider.end.set(camera.position.x, camera.position.y - 0.25, camera.position.z);
    playerVelocity.set(0, 0, 0);
    playerCollisions();
  }
}

// Haki dla zrzutów (tools/shot.mjs) i testu fizyki (tools/test_physics.mjs) — tylko w trybie dev
if (import.meta.env.DEV) {
  (window as any).__toggleLighting = toggleLighting;
  (window as any).__setViewpoint = setViewpoint;
  (window as any).__toggleMode = toggleMode;
  (window as any).__setCam = (x: number, y: number, z: number, tx: number, ty: number, tz: number) => {
    camera.position.set(x, y, z);
    controls.object.position.set(x, y, z);
    camera.lookAt(tx, ty, tz);
    playerCollider.start.set(x, y - 1.30, z);
    playerCollider.end.set(x, y - 0.25, z);
    playerVelocity.set(0, 0, 0);
    playerOnFloor = true;
  };
  (window as any).__simulateWalk = (seconds = 1.0, forward = true, sprint = false, jump = false) => {
    keys.forward = forward;
    keys.sprint = sprint;
    keys.up = jump;
    const steps = Math.max(1, Math.round(seconds * 60));
    for (let s = 0; s < steps; s++) {
      stepWalk(1.0 / 60);
      keys.up = false;
    }
    releaseKeys();
    return {
      pos: [camera.position.x, camera.position.y, camera.position.z],
      onFloor: playerOnFloor,
      vel: [playerVelocity.x, playerVelocity.y, playerVelocity.z]
    };
  };
  // Pomiar wydajności: średni czas klatki i liczba draw calli / trójkątów na klatkę (wszystkie przebiegi:
  // cienie, postprocessing), zliczane przy wyłączonym automatycznym zerowaniu renderer.info
  (window as any).__perf = (frames = 60) => new Promise((resolve) => {
    renderer.info.autoReset = false;
    renderer.info.reset();
    const t0 = performance.now();
    let n = 0;
    const tick = () => {
      if (++n < frames) { requestAnimationFrame(tick); return; }
      const r = renderer.info.render;
      const ms = (performance.now() - t0) / frames;
      resolve({ msPerFrame: ms, calls: Math.round(r.calls / frames), triangles: Math.round(r.triangles / frames) });
      renderer.info.autoReset = true;
    };
    requestAnimationFrame(tick);
  });
  (window as any).__getPlayerState = () => ({
    pos: [camera.position.x, camera.position.y, camera.position.z],
    onFloor: playerOnFloor,
    vel: [playerVelocity.x, playerVelocity.y, playerVelocity.z],
    octreeReady
  });
}

// Podpięcie przycisków HUD
document.getElementById('btn-light')?.addEventListener('click', toggleLighting);
document.getElementById('btn-mode')?.addEventListener('click', toggleMode);
document.querySelectorAll('.vp-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const target = e.currentTarget as HTMLElement;
    const vpIndex = parseInt(target.getAttribute('data-vp') || '0', 10);
    setViewpoint(vpIndex);
  });
});

// --- WCZYTYWANIE MODELU GLTF ---
const NO_SHADOW_CASTERS = /^(Teren|Plac|Murawa|Bieznia|Slad_Biezni|Al_Unii|Tory|Panorama)/;
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const fillBar = document.getElementById('progress-fill');
const statusText = document.getElementById('loading-status');
const loadingOverlay = document.getElementById('loading');
const hud = document.getElementById('hud');

loader.load(
  '/assets/estadio_da_gruz.glb',
  (gltf) => {
    const model = gltf.scene;
    model.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        // Płaskie i dalekie powierzchnie nie rzucają cieni (teren, plac, murawa, bloki na horyzoncie)
        mesh.castShadow = !NO_SHADOW_CASTERS.test(mesh.name);
        mesh.receiveShadow = true;

        const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        mats.forEach((m) => {
          if (m && (m as THREE.MeshStandardMaterial).isMeshStandardMaterial) {
            const std = m as THREE.MeshStandardMaterial;
            if (std.name.includes('Goal_Net') || std.name.includes('Fence') || mesh.name.includes('Siatka')) {
              std.side = THREE.DoubleSide;
              std.transparent = true;
              std.alphaTest = 0.25;
              std.depthWrite = true;
              mesh.castShadow = false;
              mesh.receiveShadow = true;
            }
          }
        });
      }
    });
    lighting.trackModel(model);
    scene.add(model);
    lighting.refreshShadows();
    model.updateMatrixWorld(true);
    // Kolizje tylko z warstwy COLLIDER_LAYER: bez instancji (krzesełka — Octree widziałby jedną kopię
    // w początku układu) i bez dalekiej panoramy bloków (rozdęłaby drzewo do kilometra).
    model.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (mesh.isMesh && !(mesh as THREE.InstancedMesh).isInstancedMesh && !mesh.name.startsWith('Panorama')) {
        mesh.layers.enable(COLLIDER_LAYER);
      }
    });
    worldOctree.layers.set(COLLIDER_LAYER);
    worldOctree.fromGraphNode(model);
    octreeReady = true;
    console.log('World Octree built successfully from stadium model!');

    // Gotowe
    if (fillBar) fillBar.style.width = '100%';
    if (statusText) statusText.textContent = 'Uruchamianie spaceru...';
    
    setTimeout(() => {
      loadingOverlay?.classList.add('hidden');
      if (hud) hud.hidden = false;
      setViewpoint(0); // Start na środku murawy
    }, 400);
  },
  (xhr) => {
    if (xhr.lengthComputable) {
      const percent = (xhr.loaded / xhr.total) * 100;
      if (fillBar) fillBar.style.width = `${percent.toFixed(0)}%`;
      if (statusText) statusText.textContent = `Wczytywanie stadionu: ${percent.toFixed(0)}%`;
    }
  },
  (err) => {
    console.error('Błąd ładowania modelu:', err);
    if (statusText) statusText.textContent = 'Błąd wczytywania modelu stadionu!';
  }
);

// --- PĘTLA RENDEROWANIA ---
function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.1);

  if (controls.isLocked) {
    if (isFlyMode) {
      const flySpeed = keys.sprint ? 40.0 : 16.0;
      const fwd = new THREE.Vector3();
      camera.getWorldDirection(fwd);
      const side = new THREE.Vector3();
      side.crossVectors(fwd, camera.up).normalize();

      if (keys.forward) camera.position.addScaledVector(fwd, flySpeed * delta);
      if (keys.backward) camera.position.addScaledVector(fwd, -flySpeed * delta);
      if (keys.left) camera.position.addScaledVector(side, -flySpeed * delta);
      if (keys.right) camera.position.addScaledVector(side, flySpeed * delta);
      if (keys.up) camera.position.y += flySpeed * delta;
      if (keys.down) camera.position.y -= flySpeed * delta;

      playerCollider.start.set(camera.position.x, camera.position.y - 1.30, camera.position.z);
      playerCollider.end.set(camera.position.x, camera.position.y - 0.25, camera.position.z);
      playerVelocity.set(0, 0, 0);
    } else {
      // Tryb Spacer: ruch z akceleracją, kolizjami, schodami i grawitacją
      stepWalk(delta);
    }
  }

  lighting.update(clock.getElapsedTime());
  postfx.render(delta);
}

// Obsługa zmiany rozmiaru okna
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  postfx.setSize(window.innerWidth, window.innerHeight, renderer.getPixelRatio());
});

animate();
