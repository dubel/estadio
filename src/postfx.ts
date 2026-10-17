import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { FilmPass } from 'three/examples/jsm/postprocessing/FilmPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';

/**
 * Łańcuch postprocessingu: render (MSAA) → bloom (tylko nocą, jupitery) → lekkie ziarno → mapowanie tonów i sRGB.
 * Bez GTAO: AO jest wypalone w Blenderze, a GTAO dokładało drugi pełny render sceny (normalne) co klatkę.
 */
export class PostFX {
  private readonly composer: EffectComposer;
  private readonly bloom: UnrealBloomPass;

  constructor(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera) {
    const size = renderer.getSize(new THREE.Vector2());
    const target = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
    this.composer = new EffectComposer(renderer, target);
    this.composer.addPass(new RenderPass(scene, camera));

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
