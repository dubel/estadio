import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { FilmPass } from 'three/examples/jsm/postprocessing/FilmPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';

/**
 * Łańcuch postprocessingu: render (MSAA) → GTAO (cienie kontaktowe, uzupełnia AO wypalone w Blenderze,
 * m.in. pod krzesełkami) → bloom (tylko nocą, jupitery) → lekkie ziarno → mapowanie tonów i sRGB.
 */
export class PostFX {
  private readonly composer: EffectComposer;
  private readonly gtao: GTAOPass;
  private readonly bloom: UnrealBloomPass;

  constructor(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera) {
    const size = renderer.getSize(new THREE.Vector2());
    const target = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
    this.composer = new EffectComposer(renderer, target);
    this.composer.addPass(new RenderPass(scene, camera));

    this.gtao = new GTAOPass(scene, camera, size.x, size.y);
    this.gtao.updateGtaoMaterial({ radius: 0.8, distanceExponent: 1.5, thickness: 1.0, scale: 1.0, samples: 12 });
    this.gtao.blendIntensity = 0.8;
    this.composer.addPass(this.gtao);

    this.bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), 0.9, 0.6, 0.85);
    this.bloom.enabled = false;
    this.composer.addPass(this.bloom);

    this.composer.addPass(new FilmPass(0.12, false));
    this.composer.addPass(new OutputPass());
  }

  setNight(night: boolean) {
    this.bloom.enabled = night;
  }

  setSize(width: number, height: number, pixelRatio: number) {
    this.composer.setPixelRatio(pixelRatio);
    this.composer.setSize(width, height);
  }

  render(delta: number) {
    this.composer.render(delta);
  }
}
