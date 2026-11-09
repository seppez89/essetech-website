/* Essetech landing: interactive Three.js hero scenes + rotatable 3D chart.
   Loaded lazily by landing.js only when the device can handle it. */
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

const C = {
  fire: 0xE84425, fire2: 0xf4633f, orange: 0xff7a3d, amber: 0xffb347, pink: 0xff4f8b, cyan: 0x38e1ff,
  blue: 0x4E6AAF, navy: 0x1e2b50, deep: 0x111a33, violet: 0x8b7bff, mint: 0x5effc9, white: 0xffffff, steel: 0xaab6d6,
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const TAU = Math.PI * 2;

/* ---------- shared helpers ---------- */
let _glowTex = null;
function glowTex() {
  if (_glowTex) return _glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,.55)');
  gr.addColorStop(0.6, 'rgba(255,255,255,.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  _glowTex = new THREE.CanvasTexture(c); _glowTex.colorSpace = THREE.SRGBColorSpace;
  return _glowTex;
}
function glow(color, size = 1, opacity = 0.9) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex(), color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false }));
  s.scale.setScalar(size);
  return s;
}
const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, flatShading: true, roughness: 0.42, metalness: 0.18, emissive: color, emissiveIntensity: o.ei ?? 0.14, ...o.extra });
const lit = (color, opacity = 1) => new THREE.MeshBasicMaterial({ color, transparent: opacity < 1, opacity });
function at(o, x, y, z) { o.position.set(x, y, z); return o; }
function mesh(geo, mat, x = 0, y = 0, z = 0) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); return m; }

function stars(n, r, colors) {
  const g = new THREE.BufferGeometry(), pos = new Float32Array(n * 3), col = new Float32Array(n * 3), c = new THREE.Color();
  for (let i = 0; i < n; i++) {
    const u = Math.random() * TAU, v = Math.acos(2 * Math.random() - 1), rr = r * (0.55 + Math.random() * 0.45);
    pos.set([rr * Math.sin(v) * Math.cos(u), rr * Math.cos(v) * 0.7, rr * Math.sin(v) * Math.sin(u)], i * 3);
    c.set(colors[i % colors.length]); col.set([c.r, c.g, c.b], i * 3);
  }
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return new THREE.Points(g, new THREE.PointsMaterial({ size: 0.06, vertexColors: true, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false, map: glowTex() }));
}

/* curved link with travelling packets */
function link(a, b, color, lift = 1.2, packets = 2, packetFactory) {
  const mid = a.clone().add(b).multiplyScalar(0.5);
  mid.y += lift;
  const curve = new THREE.QuadraticBezierCurve3(a.clone(), mid, b.clone());
  const pts = curve.getPoints(40);
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false }));
  const g = new THREE.Group(); g.add(line);
  const ps = [];
  for (let i = 0; i < packets; i++) {
    const p = packetFactory ? packetFactory() : glow(color, 0.42, 1);
    p.userData.off = i / packets + Math.random() * 0.2;
    p.userData.speed = 0.18 + Math.random() * 0.12;
    g.add(p); ps.push(p);
  }
  g.userData.tick = (t) => {
    for (const p of ps) {
      const k = (t * p.userData.speed + p.userData.off) % 1;
      curve.getPointAt(k, p.position);
      if (p.isMesh) { p.rotation.x = t * 3; p.rotation.y = t * 2; }
    }
  };
  return g;
}

/* ---------- gyro (shared, permission requested once on iOS) ---------- */
const gyro = { x: 0, y: 0, on: false };
function enableGyro() {
  if (gyro.on) return; gyro.on = true;
  addEventListener('deviceorientation', (e) => {
    if (e.gamma == null || e.beta == null) return;
    gyro.x = clamp(e.gamma / 35, -1, 1);
    gyro.y = clamp((e.beta - 50) / 35, -1, 1);
  }, { passive: true });
}
function wireGyro(el, mobile) {
  if (typeof DeviceOrientationEvent === 'undefined') return;
  if (typeof DeviceOrientationEvent.requestPermission === 'function') {
    const req = () => {
      el.removeEventListener('touchend', req);
      try { DeviceOrientationEvent.requestPermission().then((s) => { if (s === 'granted') enableGyro(); }).catch(() => {}); } catch (e) { /* denied or unsupported */ }
    };
    el.addEventListener('touchend', req, { passive: true });
  } else if (mobile) enableGyro();
}

/* ---------- stage: renderer, camera, drag + inertia, visibility pausing ---------- */
function makeStage(el, { mobile, fov = 40, onTap } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, mobile ? 1.5 : 2));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(fov, 1, 0.1, 100);
  const world = new THREE.Group(); scene.add(world);

  scene.add(new THREE.HemisphereLight(0x9fbaff, 0x2a0f22, 1.4));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(4, 7, 6); scene.add(key);
  const rim = new THREE.DirectionalLight(0x38e1ff, 1.3); rim.position.set(-6, 2, -4); scene.add(rim);
  const warm = new THREE.PointLight(0xff7a3d, 40, 14, 1.6); warm.position.set(0, 1.5, 2); scene.add(warm);

  const st = { yaw: 0, pitch: 0, vy: 0, vp: 0, drag: false, w: 1, h: 1, aspect: 1, touched: false };
  let sx = 0, sy = 0, lx = 0, ly = 0, moved = 0, pid = null;
  const cv = renderer.domElement;
  cv.addEventListener('pointerdown', (e) => {
    pid = e.pointerId; st.drag = true; moved = 0; sx = lx = e.clientX; sy = ly = e.clientY;
    if (e.pointerType === 'mouse') cv.setPointerCapture(pid);
    if (!st.touched) { st.touched = true; el.classList.add('is-touched'); }
  });
  cv.addEventListener('pointermove', (e) => {
    if (!st.drag || e.pointerId !== pid) return;
    const dx = e.clientX - lx, dy = e.clientY - ly; lx = e.clientX; ly = e.clientY;
    moved += Math.abs(dx) + Math.abs(dy);
    st.vy = dx * 0.0085; st.yaw += st.vy;
    if (e.pointerType === 'mouse') { st.vp = dy * 0.005; st.pitch = clamp(st.pitch + st.vp, -0.5, 0.6); }
  });
  const end = (e) => {
    if (!st.drag) return; st.drag = false;
    if (onTap && e.type === 'pointerup' && moved < 8) {
      const r = cv.getBoundingClientRect();
      onTap(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    }
  };
  cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end); cv.addEventListener('lostpointercapture', end);
  wireGyro(el, mobile);

  const resize = () => {
    const r = el.getBoundingClientRect(); st.w = Math.max(1, r.width); st.h = Math.max(1, r.height);
    st.aspect = st.w / st.h; camera.aspect = st.aspect; camera.updateProjectionMatrix();
    renderer.setSize(st.w, st.h, false);
  };
  resize();
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(el); else addEventListener('resize', resize);

  let visible = true, running = false, frameCb = null, first = true, last = performance.now(), t = 0;
  const loop = (now) => {
    const dt = Math.min(0.05, (now - last) / 1000); last = now; t += dt;
    if (!st.drag) { st.vy *= 0.94; st.vp *= 0.9; st.yaw += st.vy; st.pitch *= 0.985; }
    frameCb && frameCb(t, dt);
    renderer.render(scene, camera);
    if (first) { first = false; el.classList.add('is-live'); }
  };
  const sync = () => {
    const should = visible && !document.hidden;
    if (should && !running) { last = performance.now(); renderer.setAnimationLoop(loop); running = true; }
    else if (!should && running) { renderer.setAnimationLoop(null); running = false; }
  };
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; sync(); }, { rootMargin: '60px' }).observe(el);
  document.addEventListener('visibilitychange', sync);

  return { renderer, scene, camera, world, st, el, onFrame: (f) => { frameCb = f; sync(); }, warm };
}

/* scroll progress through an element, 0 at top of viewport, 1 when scrolled past */
function scrollProgress(sec) {
  const r = sec.getBoundingClientRect();
  return clamp(-r.top / Math.max(1, r.height), 0, 1);
}

/* ======================= HERO SCENES ======================= */
function tradesScene(world) {
  const g = new THREE.Group(); world.add(g);
  // job site platform
  const plat = mesh(new THREE.CylinderGeometry(2.3, 2.55, 0.32, 6), std(C.navy, { ei: 0.1 }), 0, -1.1, 0);
  g.add(plat);
  const edge = new THREE.LineSegments(new THREE.EdgesGeometry(plat.geometry), new THREE.LineBasicMaterial({ color: C.cyan, transparent: true, opacity: 0.8 }));
  edge.position.copy(plat.position); g.add(edge);
  const pad = mesh(new THREE.CylinderGeometry(1.2, 1.2, 0.04, 6), lit(C.orange, 0.35), 0, -0.92, 0); g.add(pad);
  // building blocks
  const blocks = [];
  [[-0.9, 0, -0.5, 0.9, 0.9, 0.9, C.blue], [-0.9, 0.9, -0.5, 0.75, 0.75, 0.75, C.amber], [0.15, -0.25, -0.95, 0.7, 0.4, 0.7, C.violet],
   [-1.55, -0.45, 0.55, 0.45, 0.45, 0.45, C.orange]].forEach(([x, y, z, w, h, d, c], i) => {
    const b = mesh(new THREE.BoxGeometry(w, h, d), std(c), x, y - 0.95 + h / 2 + 0.15 + (y > 0 ? 0.15 : 0), z);
    b.position.y = -0.94 + h / 2 + (i === 1 ? 0.9 : 0);
    g.add(b); blocks.push(b);
  });
  // window strips on the main block
  for (let i = 0; i < 3; i++) g.add(mesh(new THREE.BoxGeometry(0.92, 0.06, 0.06), lit(C.cyan), -0.9, -0.75 + i * 0.25, -0.04));
  // crane
  const crane = new THREE.Group(); crane.position.set(1.2, -0.94, -0.6); g.add(crane);
  crane.add(mesh(new THREE.BoxGeometry(0.12, 2.6, 0.12), std(C.amber, { ei: 0.25 }), 0, 1.3, 0));
  const jib = new THREE.Group(); jib.position.y = 2.55; crane.add(jib);
  jib.add(mesh(new THREE.BoxGeometry(2.2, 0.1, 0.1), std(C.amber, { ei: 0.25 }), -0.6, 0, 0));
  jib.add(mesh(new THREE.BoxGeometry(0.3, 0.25, 0.25), std(C.steel), 0.45, -0.05, 0));
  const cable = mesh(new THREE.BoxGeometry(0.015, 0.9, 0.015), lit(C.white, 0.7), -1.4, -0.45, 0); jib.add(cable);
  const hook = mesh(new THREE.BoxGeometry(0.3, 0.2, 0.3), std(C.fire), -1.4, -0.95, 0); jib.add(hook);
  jib.add(at(glow(C.amber, 0.5), -1.7, 0.08, 0));
  // ute
  const ute = new THREE.Group(); ute.position.set(0.55, -0.94, 0.95); ute.rotation.y = -0.5; g.add(ute);
  ute.add(mesh(new THREE.BoxGeometry(1.25, 0.28, 0.58), std(C.white, { ei: 0.05 }), 0, 0.24, 0));
  ute.add(mesh(new THREE.BoxGeometry(0.52, 0.28, 0.54), std(C.white, { ei: 0.05 }), 0.28, 0.5, 0));
  ute.add(mesh(new THREE.BoxGeometry(0.06, 0.2, 0.5), lit(C.cyan, 0.85), 0.55, 0.52, 0));
  ute.add(mesh(new THREE.BoxGeometry(0.6, 0.12, 0.6), std(C.fire), -0.32, 0.43, 0));
  const wheelG = new THREE.CylinderGeometry(0.14, 0.14, 0.1, 10), wheelM = std(0x0b1024, { ei: 0 });
  [[-0.38, 0.3], [0.4, 0.3], [-0.38, -0.3], [0.4, -0.3]].forEach(([x, z]) => { const w = mesh(wheelG, wheelM, x, 0.12, z); w.rotation.x = Math.PI / 2; ute.add(w); });
  ute.add(at(glow(C.amber, 0.35), 0.64, 0.25, 0.2), at(glow(C.amber, 0.35), 0.64, 0.25, -0.2));

  // floating tools + devices orbiting the site
  const orbit = new THREE.Group(); g.add(orbit);
  const tools = [];
  const mk = (build, ang, r, y, s = 1) => {
    const holder = new THREE.Group(); holder.position.set(Math.cos(ang) * r, y, Math.sin(ang) * r);
    const obj = build(); obj.scale.setScalar(s); holder.add(obj); orbit.add(holder);
    holder.add(glow(C.orange, 1.3, 0.25));
    tools.push({ holder, obj, y, ph: Math.random() * TAU, spin: 0.3 + Math.random() * 0.4 });
    return holder;
  };
  const wrench = () => {
    const o = new THREE.Group(), m = std(C.steel, { ei: 0.18 });
    o.add(mesh(new THREE.BoxGeometry(0.16, 1.1, 0.08), m, 0, 0, 0));
    const head = mesh(new THREE.TorusGeometry(0.24, 0.08, 6, 14, Math.PI * 1.55), m, 0, 0.68, 0); head.rotation.z = Math.PI * 0.72; o.add(head);
    o.add(mesh(new THREE.TorusGeometry(0.15, 0.06, 6, 12), m, 0, -0.66, 0));
    o.rotation.z = 0.6; return o;
  };
  const hammer = () => {
    const o = new THREE.Group();
    o.add(mesh(new THREE.CylinderGeometry(0.06, 0.075, 1.15, 7), std(C.amber, { ei: 0.2 }), 0, 0, 0));
    o.add(mesh(new THREE.BoxGeometry(0.62, 0.2, 0.2), std(C.steel, { ei: 0.15 }), 0.08, 0.6, 0));
    const claw = mesh(new THREE.ConeGeometry(0.1, 0.3, 4), std(C.steel), -0.32, 0.62, 0); claw.rotation.z = Math.PI / 2; o.add(claw);
    o.rotation.z = -0.5; return o;
  };
  const hat = () => {
    const o = new THREE.Group(), m = std(C.amber, { ei: 0.3 });
    o.add(mesh(new THREE.SphereGeometry(0.46, 12, 6, 0, TAU, 0, Math.PI / 2), m));
    o.add(mesh(new THREE.CylinderGeometry(0.64, 0.64, 0.05, 16), m, 0.08, 0, 0));
    o.add(mesh(new THREE.BoxGeometry(0.1, 0.12, 0.8), std(C.orange), 0, 0.42, 0));
    o.rotation.x = 0.3; return o;
  };
  const toolbox = () => {
    const o = new THREE.Group();
    o.add(mesh(new THREE.BoxGeometry(0.85, 0.42, 0.42), std(C.fire, { ei: 0.25 })));
    o.add(mesh(new THREE.BoxGeometry(0.9, 0.08, 0.46), std(0xc2341b), 0, 0.24, 0));
    const h = mesh(new THREE.TorusGeometry(0.18, 0.035, 6, 12, Math.PI), std(C.steel), 0, 0.28, 0); o.add(h);
    return o;
  };
  const laptop = () => {
    const o = new THREE.Group();
    o.add(mesh(new THREE.BoxGeometry(0.9, 0.05, 0.6), std(C.steel)));
    const scr = new THREE.Group(); scr.position.set(0, 0.02, -0.3); scr.rotation.x = -0.35; o.add(scr);
    scr.add(mesh(new THREE.BoxGeometry(0.9, 0.6, 0.04), std(C.deep), 0, 0.3, 0));
    scr.add(mesh(new THREE.PlaneGeometry(0.8, 0.5), lit(C.cyan, 0.9), 0, 0.3, 0.025));
    return o;
  };
  const phone = () => {
    const o = new THREE.Group();
    o.add(mesh(new THREE.BoxGeometry(0.36, 0.7, 0.05), std(C.deep)));
    o.add(mesh(new THREE.PlaneGeometry(0.3, 0.6), lit(C.violet, 0.95), 0, 0, 0.03));
    return o;
  };
  const tiles = () => { // abstract Microsoft 365 style tile block
    const o = new THREE.Group(), gq = new THREE.BoxGeometry(0.3, 0.3, 0.1);
    [[C.fire, -0.17, 0.17], [C.mint, 0.17, 0.17], [C.cyan, -0.17, -0.17], [C.amber, 0.17, -0.17]].forEach(([c, x, y]) => o.add(mesh(gq, std(c, { ei: 0.45 }), x, y, 0)));
    return o;
  };
  const lock = () => {
    const o = new THREE.Group();
    o.add(mesh(new THREE.BoxGeometry(0.5, 0.42, 0.2), std(C.pink, { ei: 0.3 })));
    o.add(mesh(new THREE.TorusGeometry(0.17, 0.05, 6, 12, Math.PI), std(C.steel), 0, 0.2, 0));
    o.add(mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.22, 8), lit(C.white), 0, -0.02, 0.1));
    return o;
  };
  const builders = [wrench, laptop, hat, tiles, hammer, phone, toolbox, lock];
  const holders = builders.map((b, i) => mk(b, (i / builders.length) * TAU, 3.3 + (i % 2) * 0.35, -0.2 + ((i * 37) % 10) / 10 * 1.6, 0.95));
  // links from the site hub to each floating item
  const hub = new THREE.Vector3(0, 0.9, 0);
  const hubCore = mesh(new THREE.IcosahedronGeometry(0.22, 0), lit(C.white)); hubCore.position.copy(hub); g.add(hubCore);
  const hubGlow = glow(C.orange, 2.2, 0.9); hubGlow.position.copy(hub); g.add(hubGlow);
  const links = holders.map((h, i) => { const l = link(hub, h.position, i % 2 ? C.cyan : C.amber, 0.9, 2); orbit.add(l); return l; });
  // ring line around the site
  const ringPts = []; for (let i = 0; i <= 96; i++) { const a = (i / 96) * TAU; ringPts.push(new THREE.Vector3(Math.cos(a) * 3.45, -0.95, Math.sin(a) * 3.45)); }
  g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ringPts), new THREE.LineDashedMaterial({ color: C.cyan, transparent: true, opacity: 0.35, dashSize: 0.15, gapSize: 0.12 })).computeLineDistances());
  g.position.y = -0.1;
  return {
    radius: 3.7,
    tick(t) {
      orbit.rotation.y = t * 0.12;
      tools.forEach((o, i) => { o.holder.position.y = o.y + Math.sin(t * 1.2 + o.ph) * 0.18; o.obj.rotation.y = t * o.spin; });
      links.forEach((l) => l.userData.tick(t));
      jib.rotation.y = Math.sin(t * 0.4) * 0.6;
      hook.position.y = -0.95 + Math.sin(t * 0.9) * 0.15; cable.scale.y = 1 + Math.sin(t * 0.9) * -0.15;
      hubGlow.material.opacity = 0.7 + Math.sin(t * 3) * 0.25;
      hubCore.rotation.y = t; hubCore.rotation.x = t * 0.7;
    },
  };
}

function medicalScene(world) {
  const g = new THREE.Group(); world.add(g);
  // shield core
  const sh = new THREE.Shape();
  sh.moveTo(0, 1.05); sh.bezierCurveTo(0.45, 0.85, 0.75, 0.82, 0.85, 0.8); sh.lineTo(0.85, 0.05);
  sh.bezierCurveTo(0.85, -0.55, 0.45, -0.9, 0, -1.12); sh.bezierCurveTo(-0.45, -0.9, -0.85, -0.55, -0.85, 0.05);
  sh.lineTo(-0.85, 0.8); sh.bezierCurveTo(-0.75, 0.82, -0.45, 0.85, 0, 1.05);
  const shieldGeo = new THREE.ExtrudeGeometry(sh, { depth: 0.28, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.06, bevelSegments: 2, curveSegments: 10 });
  shieldGeo.center();
  const core = new THREE.Group(); g.add(core);
  core.add(new THREE.Mesh(shieldGeo, new THREE.MeshStandardMaterial({ color: 0x2a9cd6, emissive: 0x1a6fd0, emissiveIntensity: 0.45, roughness: 0.25, metalness: 0.35 })));
  const crossM = lit(C.white);
  core.add(mesh(new THREE.BoxGeometry(0.22, 0.8, 0.12), crossM, 0, 0.02, 0.24));
  core.add(mesh(new THREE.BoxGeometry(0.8, 0.22, 0.12), crossM, 0, 0.02, 0.24));
  const cg = glow(C.cyan, 4.2, 0.75); g.add(cg);
  const cg2 = glow(C.mint, 2, 0.5); g.add(cg2);
  // protective sphere (pulses)
  const sphere = new THREE.Mesh(new THREE.IcosahedronGeometry(2.05, 2), new THREE.MeshBasicMaterial({ color: C.cyan, wireframe: true, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false }));
  g.add(sphere);
  const shell = new THREE.Mesh(new THREE.IcosahedronGeometry(2.0, 3), new THREE.MeshBasicMaterial({ color: 0x1a6fd0, transparent: true, opacity: 0.08, side: THREE.BackSide, depthWrite: false }));
  g.add(shell);
  // hex badges on the sphere
  const hexG = new THREE.CircleGeometry(0.16, 6), hexM = new THREE.MeshBasicMaterial({ color: C.mint, transparent: true, opacity: 0.5, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false });
  const hexes = [];
  for (let i = 0; i < 14; i++) {
    const v = new THREE.Vector3().randomDirection().multiplyScalar(2.06), h = new THREE.Mesh(hexG, hexM.clone());
    h.position.copy(v); h.lookAt(0, 0, 0); g.add(h); hexes.push(h);
  }
  // devices on two tilted orbits
  const ringA = new THREE.Group(); ringA.rotation.set(0.35, 0, 0.18); g.add(ringA);
  const ringB = new THREE.Group(); ringB.rotation.set(-0.45, 0, -0.3); g.add(ringB);
  const circle = (r, color) => { const p = []; for (let i = 0; i <= 120; i++) { const a = (i / 120) * TAU; p.push(new THREE.Vector3(Math.cos(a) * r, 0, Math.sin(a) * r)); } return new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(p), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.35 })); };
  ringA.add(circle(3.25, C.cyan)); ringB.add(circle(3.7, C.violet));
  const pc = () => { const o = new THREE.Group(); o.add(mesh(new THREE.BoxGeometry(0.85, 0.55, 0.06), std(C.deep))); o.add(mesh(new THREE.PlaneGeometry(0.76, 0.46), lit(C.cyan, 0.9), 0, 0, 0.035)); o.add(mesh(new THREE.BoxGeometry(0.08, 0.3, 0.08), std(C.steel), 0, -0.4, 0)); o.add(mesh(new THREE.BoxGeometry(0.4, 0.04, 0.25), std(C.steel), 0, -0.55, 0)); return o; };
  const tablet = () => { const o = new THREE.Group(); o.add(mesh(new THREE.BoxGeometry(0.55, 0.75, 0.04), std(C.deep))); o.add(mesh(new THREE.PlaneGeometry(0.47, 0.66), lit(C.mint, 0.9), 0, 0, 0.025)); return o; };
  const server = () => { const o = new THREE.Group(); for (let i = 0; i < 3; i++) { o.add(mesh(new THREE.BoxGeometry(0.7, 0.2, 0.5), std(C.navy, { ei: 0.2 }), 0, i * 0.23 - 0.23, 0)); o.add(mesh(new THREE.BoxGeometry(0.4, 0.04, 0.02), lit(i === 1 ? C.mint : C.cyan), -0.08, i * 0.23 - 0.23, 0.26)); o.add(mesh(new THREE.BoxGeometry(0.05, 0.05, 0.02), lit(C.orange), 0.25, i * 0.23 - 0.23, 0.26)); } return o; };
  const phone = () => { const o = new THREE.Group(); o.add(mesh(new THREE.BoxGeometry(0.32, 0.62, 0.05), std(C.deep))); o.add(mesh(new THREE.PlaneGeometry(0.27, 0.54), lit(C.violet, 0.95), 0, 0, 0.03)); return o; };
  const laptop = () => { const o = new THREE.Group(); o.add(mesh(new THREE.BoxGeometry(0.8, 0.05, 0.55), std(C.steel))); const s = new THREE.Group(); s.position.set(0, 0.02, -0.27); s.rotation.x = -0.3; o.add(s); s.add(mesh(new THREE.BoxGeometry(0.8, 0.52, 0.04), std(C.deep), 0, 0.26, 0)); s.add(mesh(new THREE.PlaneGeometry(0.7, 0.44), lit(C.cyan, 0.9), 0, 0.26, 0.025)); return o; };
  const devs = [];
  const add = (ring, b, ang, r) => {
    const h = new THREE.Group(); h.position.set(Math.cos(ang) * r, 0, Math.sin(ang) * r); h.add(b()); h.add(glow(C.cyan, 1.4, 0.3)); ring.add(h);
    const l = link(new THREE.Vector3(0, 0, 0), h.position, C.mint, 0.6, 2, () => mesh(new THREE.BoxGeometry(0.12, 0.12, 0.12), lit(C.mint)));
    ring.add(l); devs.push({ h, l, ph: Math.random() * TAU });
  };
  add(ringA, pc, 0, 3.25); add(ringA, tablet, 2.1, 3.25); add(ringA, server, 4.2, 3.25);
  add(ringB, laptop, 1.0, 3.7); add(ringB, phone, 3.2, 3.7); add(ringB, server, 5.2, 3.7);
  // pulse ring wave
  const wave = new THREE.Mesh(new THREE.RingGeometry(0.98, 1, 64), new THREE.MeshBasicMaterial({ color: C.cyan, transparent: true, opacity: 0.6, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false }));
  wave.rotation.x = -Math.PI / 2; g.add(wave);
  return {
    radius: 4.0,
    tick(t) {
      core.rotation.y = Math.sin(t * 0.6) * 0.5; core.position.y = Math.sin(t * 1.3) * 0.08;
      const pulse = 1 + Math.sin(t * 2.2) * 0.035;
      sphere.scale.setScalar(pulse); sphere.rotation.y = t * 0.08; shell.scale.setScalar(pulse);
      cg.material.opacity = 0.55 + Math.sin(t * 2.2) * 0.2;
      hexes.forEach((h, i) => { h.material.opacity = 0.15 + 0.45 * Math.max(0, Math.sin(t * 1.5 + i)); });
      ringA.rotation.y = t * 0.18; ringB.rotation.y = -t * 0.13;
      devs.forEach((d) => { d.h.children[0].rotation.y = -d.h.parent.rotation.y + Math.sin(t + d.ph) * 0.3; d.h.position.y = Math.sin(t * 1.4 + d.ph) * 0.12; d.l.userData.tick(t); });
      const k = (t * 0.45) % 1; wave.scale.setScalar(0.6 + k * 4); wave.material.opacity = 0.6 * (1 - k);
    },
  };
}

function nfpScene(world) {
  const g = new THREE.Group(); world.add(g);
  const R = 1.75;
  const globe = new THREE.Group(); g.add(globe);
  globe.add(new THREE.Mesh(new THREE.IcosahedronGeometry(R, 3), new THREE.MeshStandardMaterial({ color: 0x2b3f86, emissive: 0x1e2b70, emissiveIntensity: 0.35, flatShading: true, roughness: 0.6, metalness: 0.1 })));
  globe.add(new THREE.Mesh(new THREE.IcosahedronGeometry(R * 1.01, 2), new THREE.MeshBasicMaterial({ color: C.violet, wireframe: true, transparent: true, opacity: 0.18, depthWrite: false })));
  g.add(glow(C.pink, 5.4, 0.35)); g.add(glow(C.violet, 4.2, 0.35));
  // sites (little houses on the surface)
  const ll = (lat, lon, r = R) => { const la = lat * Math.PI / 180, lo = lon * Math.PI / 180; return new THREE.Vector3(r * Math.cos(la) * Math.cos(lo), r * Math.sin(la), r * Math.cos(la) * Math.sin(lo)); };
  const sitesLL = [[28, 10], [-12, 60], [40, 120], [-30, 170], [10, 230], [52, 290], [-40, 300]];
  const sites = sitesLL.map(([la, lo], i) => {
    const p = ll(la, lo), h = new THREE.Group(); h.position.copy(p); h.lookAt(p.clone().multiplyScalar(2));
    const c = [C.amber, C.orange, C.pink][i % 3];
    const base = mesh(new THREE.BoxGeometry(0.26, 0.26, 0.24), std(c, { ei: 0.35 }), 0, 0, 0.12); h.add(base);
    const roof = mesh(new THREE.ConeGeometry(0.24, 0.18, 4), std(C.white, { ei: 0.2 }), 0, 0, 0.32); roof.rotation.x = Math.PI / 2; roof.rotation.y = Math.PI / 4; h.add(roof);
    const gl = glow(c, 0.9, 0.7); gl.position.z = 0.15; h.add(gl);
    globe.add(h); return p;
  });
  // glowing arcs between sites
  const arcs = [];
  [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 3], [1, 5], [2, 6], [6, 4]].forEach(([a, b], i) => {
    const A = sites[a], B = sites[b], mid = A.clone().add(B).normalize().multiplyScalar(R * (1.45 + A.distanceTo(B) * 0.12));
    const curve = new THREE.QuadraticBezierCurve3(A, mid, B), pts = curve.getPoints(48);
    const col = i % 2 ? C.pink : C.amber;
    globe.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false })));
    const p = glow(col, 0.45, 1); globe.add(p);
    arcs.push({ curve, p, off: Math.random(), sp: 0.16 + Math.random() * 0.1 });
  });
  // people orbiting the globe
  const people = new THREE.Group(); people.rotation.x = 0.25; g.add(people);
  const folk = [];
  const pcol = [C.amber, C.cyan, C.pink, C.mint, C.orange, C.violet, C.amber, C.pink, C.cyan];
  pcol.forEach((c, i) => {
    const a = (i / pcol.length) * TAU, f = new THREE.Group(); f.position.set(Math.cos(a) * 3, 0, Math.sin(a) * 3);
    f.add(mesh(new THREE.SphereGeometry(0.13, 10, 8), std(c, { ei: 0.4 }), 0, 0.3, 0));
    f.add(mesh(new THREE.CylinderGeometry(0.06, 0.2, 0.36, 8), std(c, { ei: 0.3 }), 0, 0.02, 0));
    f.add(glow(c, 0.9, 0.35)); people.add(f); folk.push({ f, ph: a });
  });
  // links between neighbouring people (community ring)
  const ring = []; for (let i = 0; i <= 120; i++) { const a = (i / 120) * TAU; ring.push(new THREE.Vector3(Math.cos(a) * 3, 0.05, Math.sin(a) * 3)); }
  people.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ring), new THREE.LineBasicMaterial({ color: C.amber, transparent: true, opacity: 0.3 })));
  // floating hearts
  const hs = new THREE.Shape(); hs.moveTo(0, 0.25); hs.bezierCurveTo(0, 0.5, -0.45, 0.55, -0.45, 0.2); hs.bezierCurveTo(-0.45, -0.05, -0.15, -0.2, 0, -0.4); hs.bezierCurveTo(0.15, -0.2, 0.45, -0.05, 0.45, 0.2); hs.bezierCurveTo(0.45, 0.55, 0, 0.5, 0, 0.25);
  const heartG = new THREE.ExtrudeGeometry(hs, { depth: 0.14, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.04, bevelSegments: 2, curveSegments: 8 }); heartG.center();
  const hearts = [[-2.6, 1.4, 0.6, 0.9], [2.5, 1.1, -0.8, 0.7], [0.4, -1.9, 2.2, 0.6], [-1.6, -1.3, -2, 0.5]].map(([x, y, z, s], i) => {
    const h = mesh(heartG, new THREE.MeshStandardMaterial({ color: C.pink, emissive: 0xff2a6a, emissiveIntensity: 0.55, roughness: 0.3, metalness: 0.1 }), x, y, z);
    h.scale.setScalar(s); h.userData = { y, ph: i * 1.7 }; g.add(h); const gl = glow(C.pink, 1.4 * s, 0.5); h.add(gl); return h;
  });
  return {
    radius: 3.7,
    tick(t) {
      globe.rotation.y = t * 0.16;
      arcs.forEach((a) => a.curve.getPointAt((t * a.sp + a.off) % 1, a.p.position));
      people.rotation.y = -t * 0.1;
      folk.forEach((o) => { o.f.position.y = Math.abs(Math.sin(t * 2 + o.ph)) * 0.18; });
      hearts.forEach((h) => { h.position.y = h.userData.y + Math.sin(t * 1.1 + h.userData.ph) * 0.2; h.rotation.y = Math.sin(t * 0.8 + h.userData.ph) * 0.7; const s = 1 + Math.max(0, Math.sin(t * 3 + h.userData.ph)) * 0.08; h.scale.setScalar(h.userData.base ?? (h.userData.base = h.scale.x)); h.scale.multiplyScalar(s); });
    },
  };
}

const SCENES = {
  trades: { build: tradesScene, stars: [C.amber, C.white, C.cyan, C.orange], tilt: 0.42, warm: C.orange },
  medical: { build: medicalScene, stars: [C.cyan, C.white, C.mint, C.violet], tilt: 0.3, warm: C.cyan },
  nfp: { build: nfpScene, stars: [C.pink, C.amber, C.white, C.violet], tilt: 0.25, warm: C.pink },
};

export function mountHero(el, theme, opts = {}) {
  const cfg = SCENES[theme] || SCENES.trades;
  const S = makeStage(el, { mobile: opts.mobile, fov: 38 });
  const { camera, world, st, scene } = S;
  S.warm.color.set(cfg.warm);
  const sc = cfg.build(world);
  const sky = stars(opts.mobile ? 220 : 420, 11, cfg.stars); scene.add(sky);
  const hero = el.closest('section') || el;
  let mx = 0, my = 0, smx = 0, smy = 0, sgx = 0, sgy = 0, sp = 0;
  if (!opts.mobile) addEventListener('pointermove', (e) => { mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5; }, { passive: true });
  world.rotation.x = cfg.tilt;
  S.onFrame((t, dt) => {
    if (!st.drag) st.yaw += dt * 0.12; // gentle auto rotate
    const p = scrollProgress(hero); sp += (p - sp) * 0.12;
    smx += (mx - smx) * 0.05; smy += (my - smy) * 0.05; sgx += (gyro.x - sgx) * 0.08; sgy += (gyro.y - sgy) * 0.08;
    world.rotation.y = st.yaw + smx * 0.5 + sgx * 0.55 + sp * 1.4;
    world.rotation.x = cfg.tilt + st.pitch + smy * 0.25 + sgy * 0.3 + sp * 0.5;
    const fit = sc.radius * (opts.mobile ? 1 : 1.18) / Math.tan((camera.fov * Math.PI) / 360) / Math.min(1, st.aspect);
    camera.position.set(sgx * 0.6, 0.4 + sgy * 0.3, fit * (0.98 - sp * 0.35)); // scroll dollies the camera in
    camera.lookAt(0, -0.1, 0);
    sky.rotation.y = t * 0.02;
    sc.tick(t, dt);
  });
  return S;
}

/* ======================= 3D CHART ======================= */
const BAR_COLS = [[C.amber, C.fire], [C.cyan, C.blue], [C.orange, C.pink], [C.violet, C.blue], [C.pink, C.fire], [C.mint, C.cyan]];

export function mountChart(el, theme, opts = {}) {
  const labels = (el.getAttribute('data-labels') || '').split('|').filter(Boolean);
  const n = labels.length || 6;
  const bars = [], ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  let hot = -1, hotT = 0;
  const S = makeStage(el, {
    mobile: opts.mobile, fov: 36,
    onTap(x, y) {
      ndc.set(x, y); ray.setFromCamera(ndc, S.camera);
      const hit = ray.intersectObjects(bars.map((b) => b.m))[0];
      setHot(hit ? bars.findIndex((b) => b.m === hit.object) : -1);
    },
  });
  const { camera, world, st } = S;
  const R = 2.25;
  const base = mesh(new THREE.CylinderGeometry(3.25, 3.45, 0.24, 48), new THREE.MeshStandardMaterial({ color: 0x18224a, emissive: 0x0d1638, emissiveIntensity: 0.6, roughness: 0.3, metalness: 0.5 }), 0, -0.12, 0);
  world.add(base);
  [1.15, R, 3.25].forEach((r, i) => {
    const p = []; for (let k = 0; k <= 120; k++) { const a = (k / 120) * TAU; p.push(new THREE.Vector3(Math.cos(a) * r, 0.01, Math.sin(a) * r)); }
    world.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(p), new THREE.LineBasicMaterial({ color: i === 1 ? C.orange : C.cyan, transparent: true, opacity: i === 1 ? 0.5 : 0.35 })));
  });
  const hub = mesh(new THREE.IcosahedronGeometry(0.42, 1), std(C.orange, { ei: 0.6 }), 0, 0.6, 0); world.add(hub);
  const hubG = glow(C.orange, 2.4, 0.8); hubG.position.y = 0.6; world.add(hubG);
  const barGeo = new THREE.BoxGeometry(0.62, 1, 0.62); barGeo.translate(0, 0.5, 0);
  const capGeo = new THREE.BoxGeometry(0.66, 0.06, 0.66);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * TAU, [c1, c2] = BAR_COLS[i % BAR_COLS.length];
    const holder = new THREE.Group(); holder.position.set(Math.cos(a) * R, 0, Math.sin(a) * R); holder.rotation.y = -a; world.add(holder);
    const m = new THREE.Mesh(barGeo, new THREE.MeshStandardMaterial({ color: c2, emissive: c1, emissiveIntensity: 0.35, roughness: 0.3, metalness: 0.25, flatShading: true }));
    holder.add(m);
    const cap = mesh(capGeo, lit(c1), 0, 1, 0); holder.add(cap);
    const g = glow(c1, 1.1, 0.8); holder.add(g);
    // spoke from hub
    const sp = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0.02, 0), new THREE.Vector3(Math.cos(a) * R, 0.02, Math.sin(a) * R)]), new THREE.LineBasicMaterial({ color: c1, transparent: true, opacity: 0.5 }));
    world.add(sp);
    const pk = glow(c1, 0.35, 1); world.add(pk);
    let lab = null;
    if (labels[i]) {
      lab = document.createElement('span'); lab.className = 'lp-chart-label'; lab.textContent = labels[i];
      el.querySelector('.lp-chart-labels').appendChild(lab);
    }
    bars.push({ holder, m, cap, g, pk, a, lab, grow: 0, delay: i * 0.12, h: 1 });
  }
  S.scene.add(stars(opts.mobile ? 120 : 220, 9, [C.cyan, C.white, C.amber]));
  function setHot(i) {
    hot = i; hotT = 0;
    bars.forEach((b, k) => { b.lab && b.lab.classList.toggle('is-hot', k === i); b.m.material.emissiveIntensity = k === i ? 0.9 : 0.35; });
    opts.onHot && opts.onHot(i);
  }
  if (opts.mobile === false) {
    S.renderer.domElement.addEventListener('pointermove', (e) => {
      if (st.drag) return;
      const r = S.renderer.domElement.getBoundingClientRect();
      ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); ray.setFromCamera(ndc, camera);
      const hit = ray.intersectObjects(bars.map((b) => b.m))[0], i = hit ? bars.findIndex((b) => b.m === hit.object) : -1;
      if (i !== hot) setHot(i);
      S.renderer.domElement.style.cursor = i >= 0 ? 'pointer' : '';
    });
  }
  const sec = el.closest('section') || el;
  let started = -1, sp = 0, sg = 0;
  const v = new THREE.Vector3();
  S.onFrame((t, dt) => {
    if (started < 0) started = t;
    const gt = t - started;
    if (!st.drag) st.yaw += dt * 0.16;
    const r = sec.getBoundingClientRect(), p = clamp((innerHeight - r.top) / (innerHeight + r.height), 0, 1);
    sp += (p - sp) * 0.1; sg += (gyro.x - sg) * 0.08;
    world.rotation.y = st.yaw + sp * 2.2 + sg * 0.5;
    const elev = 0.62 - sp * 0.3 + st.pitch * 0.6, dist = (opts.mobile ? 11 : 7.4) / Math.min(1, st.aspect * 0.9) * (1.08 - sp * 0.12);
    camera.position.set(0, Math.sin(elev) * dist, Math.cos(elev) * dist); camera.lookAt(0, 1.05, 0);
    hub.rotation.y = t * 0.8; hub.rotation.x = t * 0.5; hubG.material.opacity = 0.6 + Math.sin(t * 2.5) * 0.25;
    hotT += dt;
    const camD = camera.position.length();
    const w = el.clientWidth, h = el.clientHeight;
    bars.forEach((b, i) => {
      b.grow = clamp((gt - b.delay) / 1.4, 0, 1);
      const e = 1 - Math.pow(1 - b.grow, 4);
      // decorative breathing heights, not data
      const target = (1.35 + 0.75 * (0.5 + 0.5 * Math.sin(t * 0.9 + i * 1.05))) * e * (i === hot ? 1.25 : 1);
      b.h += (target - b.h) * 0.15;
      b.m.scale.y = Math.max(0.001, b.h); b.cap.position.y = b.h; b.g.position.y = b.h + 0.05;
      const k = (t * 0.5 + i / bars.length) % 1;
      b.pk.position.set(Math.cos(b.a) * R * k, 0.05, Math.sin(b.a) * R * k);
      if (b.lab) {
        b.holder.localToWorld(v.set(0, b.h + 0.42, 0));
        const front = clamp(1 - (v.distanceTo(camera.position) - (camD - R)) / (2 * R), 0, 1);
        v.project(camera);
        b.lab.style.transform = `translate(${((v.x + 1) / 2 * w).toFixed(1)}px,${((1 - v.y) / 2 * h).toFixed(1)}px) translate(-50%,-50%)`;
        b.lab.style.opacity = ((0.3 + 0.7 * front) * e).toFixed(2);
        b.lab.style.zIndex = String(Math.round(front * 100));
      }
    });
  });
  return S;
}
