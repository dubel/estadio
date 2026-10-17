import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js';

// --- STAN APLIKACJI ---
let isNight = false;
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
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x7da4c4); // Błękitne niebo dzienne
scene.fog = new THREE.FogExp2(0x7da4c4, 0.0035);

const camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.2, 500);

// --- OŚWIETLENIE ---
// Światło ambient
const ambientLight = new THREE.HemisphereLight(0xddeeff, 0x334433, 0.6);
scene.add(ambientLight);

// Słońce dzienne
const sunLight = new THREE.DirectionalLight(0xfffaed, 2.5);
sunLight.position.set(70, 120, -50);
sunLight.castShadow = true;
sunLight.shadow.mapSize.width = 2048;
sunLight.shadow.mapSize.height = 2048;
sunLight.shadow.camera.near = 10;
sunLight.shadow.camera.far = 300;
sunLight.shadow.camera.left = -100;
sunLight.shadow.camera.right = 100;
sunLight.shadow.camera.top = 100;
sunLight.shadow.camera.bottom = -100;
scene.add(sunLight);

// Jupitery (oświetlenie nocne - 4 potężne reflektory na szczycie masztów)
// Jupitery (oświetlenie nocne - 4 potężne reflektory na szczycie masztów)
const jupitersLights: THREE.SpotLight[] = [];
const jupiterPositions = [
  new THREE.Vector3(-68.0, 48.2,  82.0), // SW (południowo-zachodni)
  new THREE.Vector3(-68.0, 48.2, -82.0), // NW (północno-zachodni)
  new THREE.Vector3( 68.0, 48.2,  82.0), // SE (południowo-wschodni)
  new THREE.Vector3( 68.0, 48.2, -82.0)  // NE (północno-wschodni)
];

jupiterPositions.forEach((pos, idx) => {
  const spot = new THREE.SpotLight(0xfffae8, 0.0); // początkowo wyłączone w dzień
  spot.position.copy(pos);
  spot.target.position.set(0, 0, 0); // celują w środek murawy
  spot.angle = Math.PI / 3.8;
  spot.penumbra = 0.55;
  spot.distance = 260;
  spot.castShadow = (idx === 0); // cień z 1 masztu dla zachowania wysokiej płynności WebGL
  scene.add(spot);
  scene.add(spot.target);
  jupitersLights.push(spot);
});

// Świecące kule blasku (flesze optyczne) na szczycie jupiterów w nocy
const texLoader = new THREE.TextureLoader();
const glowTexture = texLoader.load('/assets/textures/floodlight_glow.png');
const glowSprites: THREE.Sprite[] = [];

jupiterPositions.forEach((pos) => {
  const spriteMat = new THREE.SpriteMaterial({
    map: glowTexture,
    color: 0xffffff,
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.position.copy(pos);
  sprite.scale.set(34, 34, 1);
  scene.add(sprite);
  glowSprites.push(sprite);
});

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
    name: "Korona Trybuny Głównej (Rząd 26)",
    pos: new THREE.Vector3(-69, 15.5, 0),
    target: new THREE.Vector3(0, 4, 0)
  },
  {
    name: "Trybuna Główna — Sektor VIP & Daszek",
    pos: new THREE.Vector3(-49, 2.5, -12),
    target: new THREE.Vector3(0, 2, 0)
  },
  {
    name: "Łuk Południowy — Historyczny Zegar",
    pos: new THREE.Vector3(0, 2.2, 40),
    target: new THREE.Vector3(0, 10.5, 110.5)
  },
  {
    name: "Galera (Al. Unii Lubelskiej)",
    pos: new THREE.Vector3(64, 8.5, 0),
    target: new THREE.Vector3(-55, 7, 0)
  },
  {
    name: "Jupiter NW — Szczyt Masztu Oświetleniowego",
    pos: new THREE.Vector3(-45, 26, -55),
    target: new THREE.Vector3(-68, 48.2, -82)
  }
];

function setViewpoint(idx: number) {
  if (idx < 0 || idx >= viewpoints.length) return;
  const vp = viewpoints[idx];
  camera.position.copy(vp.pos);
  controls.object.position.copy(vp.pos);
  camera.lookAt(vp.target);
  
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

interface TrackedEmissive {
  mat: THREE.MeshStandardMaterial;
  dayColor: THREE.Color;
  nightColor: THREE.Color;
  dayIntensity: number;
  nightIntensity: number;
}
const trackedEmissives: TrackedEmissive[] = [];

function toggleLighting() {
  isNight = !isNight;
  const icon = document.getElementById('light-icon');
  const label = document.getElementById('light-label');
  
  if (isNight) {
    scene.background = new THREE.Color(0x070b12);
    scene.fog = new THREE.FogExp2(0x070b12, 0.005);
    ambientLight.color.setHex(0x182438);
    ambientLight.groundColor.setHex(0x06090e);
    ambientLight.intensity = 0.35;
    sunLight.intensity = 0.02;
    jupitersLights.forEach(l => l.intensity = 8000.0);
    glowSprites.forEach(s => s.material.opacity = 0.95);
    trackedEmissives.forEach(e => {
      e.mat.emissive.copy(e.nightColor);
      e.mat.emissiveIntensity = e.nightIntensity;
    });
    if (icon) icon.textContent = '🌙';
    if (label) label.textContent = 'Noc (Jupitery)';
  } else {
    scene.background = new THREE.Color(0x7da4c4);
    scene.fog = new THREE.FogExp2(0x7da4c4, 0.0035);
    ambientLight.color.setHex(0xddeeff);
    ambientLight.groundColor.setHex(0x334433);
    ambientLight.intensity = 0.6;
    sunLight.intensity = 2.5;
    jupitersLights.forEach(l => l.intensity = 0.0);
    glowSprites.forEach(s => s.material.opacity = 0.0);
    trackedEmissives.forEach(e => {
      e.mat.emissive.copy(e.dayColor);
      e.mat.emissiveIntensity = e.dayIntensity;
    });
    if (icon) icon.textContent = '☀️';
    if (label) label.textContent = 'Dzień';
  }
}

function toggleMode() {
  isFlyMode = !isFlyMode;
  const icon = document.getElementById('mode-icon');
  const label = document.getElementById('mode-label');
  if (icon) icon.textContent = isFlyMode ? '🚁' : '🚶';
  if (label) label.textContent = isFlyMode ? 'Dron (Lot)' : 'Spacer';
}

(window as any).__toggleLighting = toggleLighting;
(window as any).__setViewpoint = setViewpoint;
(window as any).__toggleMode = toggleMode;
(window as any).__setCam = (x: number, y: number, z: number, tx: number, ty: number, tz: number) => {
  camera.position.set(x, y, z);
  controls.object.position.set(x, y, z);
  camera.lookAt(tx, ty, tz);
};

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
const loader = new GLTFLoader();
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
        mesh.castShadow = true;
        mesh.receiveShadow = true;

        const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        mats.forEach((m) => {
          if (m && (m as THREE.MeshStandardMaterial).isMeshStandardMaterial) {
            const std = m as THREE.MeshStandardMaterial;
            if (std.name.includes('Lamp_Glow')) {
              trackedEmissives.push({
                mat: std,
                dayColor: new THREE.Color(0x222222),
                nightColor: new THREE.Color(0xffffff),
                dayIntensity: 0.0,
                nightIntensity: 25.0
              });
              std.emissive = new THREE.Color(0x000000);
              std.emissiveIntensity = 0.0;
            } else if (std.name.includes('Beacon')) {
              trackedEmissives.push({
                mat: std,
                dayColor: new THREE.Color(0x220000),
                nightColor: new THREE.Color(0xff1111),
                dayIntensity: 0.2,
                nightIntensity: 8.0
              });
              std.emissive = new THREE.Color(0x220000);
              std.emissiveIntensity = 0.2;
            } else if (std.name.includes('Board_Historic')) {
              trackedEmissives.push({
                mat: std,
                dayColor: new THREE.Color(0x000000),
                nightColor: new THREE.Color(0xffffff),
                dayIntensity: 0.0,
                nightIntensity: 2.2
              });
              std.emissive = new THREE.Color(0x000000);
              std.emissiveIntensity = 0.0;
            }
          }
        });
      }
    });
    scene.add(model);

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
const velocity = new THREE.Vector3();
const direction = new THREE.Vector3();

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.1);

  if (controls.isLocked) {
    const speed = keys.sprint ? 32.0 : 12.0;

    direction.z = Number(keys.forward) - Number(keys.backward);
    direction.x = Number(keys.right) - Number(keys.left);
    direction.normalize();

    if (keys.forward || keys.backward) {
      velocity.z = direction.z * speed * delta;
    } else {
      velocity.z = 0;
    }

    if (keys.left || keys.right) {
      velocity.x = direction.x * speed * delta;
    } else {
      velocity.x = 0;
    }

    controls.moveRight(velocity.x);
    controls.moveForward(velocity.z);

    if (isFlyMode) {
      if (keys.up) controls.object.position.y += speed * delta;
      if (keys.down) controls.object.position.y -= speed * delta;
    } else {
      // Blokowanie grawitacji na poziomie gruntu murawy/schodków
      const currentPos = controls.object.position;
      // Prosty clamp wysokości oczu
      if (currentPos.y < 1.8) {
        currentPos.y = 1.8;
      }
    }
  }

  if (isNight && trackedEmissives.length > 0) {
    const time = clock.getElapsedTime();
    const pulse = 0.75 + 0.25 * Math.sin(time * 4.0);
    trackedEmissives.forEach((e) => {
      if (e.mat.name.includes('Beacon')) {
        e.mat.emissiveIntensity = e.nightIntensity * pulse;
      }
    });
  }

  renderer.render(scene, camera);
}

// Obsługa zmiany rozmiaru okna
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
