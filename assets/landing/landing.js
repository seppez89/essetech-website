/* Essetech niche landing pages: interactions, reveals and lazy 3D loader. Vanilla, no dependencies. */
(function () {
  'use strict';
  var doc = document, root = doc.documentElement, body = doc.body;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches;
  var isMobile = innerWidth < 768;
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); };
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };

  /* ---------- scroll progress bar ---------- */
  var bar = doc.createElement('div');
  bar.className = 'lp-progress';
  bar.setAttribute('aria-hidden', 'true');
  body.appendChild(bar);

  /* ---------- reveals + stagger ---------- */
  $$('[data-stagger]').forEach(function (g) {
    Array.prototype.forEach.call(g.children, function (c, i) { c.style.setProperty('--i', i); });
  });
  var targets = $$('.reveal, [data-stagger]');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    targets.forEach(function (el) { io.observe(el); });
  } else {
    targets.forEach(function (el) { el.classList.add('visible'); });
  }

  /* ---------- counters (only numbers already in the copy; final value is in the HTML) ---------- */
  var nums = $$('[data-count]');
  if (!reduce && nums.length && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        cio.unobserve(e.target);
        var el = e.target, end = parseInt(el.getAttribute('data-count'), 10), t0 = performance.now(), dur = 1200;
        (function tick(now) {
          var k = clamp((now - t0) / dur, 0, 1), eased = 1 - Math.pow(1 - k, 3);
          el.textContent = String(Math.round(end * eased));
          if (k < 1) requestAnimationFrame(tick); else el.textContent = String(end);
        })(t0);
      });
    }, { threshold: 0.6 });
    nums.forEach(function (n) { cio.observe(n); });
  }

  /* ---------- FAQ accordion ---------- */
  var faqs = $$('.faq-item');
  faqs.forEach(function (item) {
    var btn = item.querySelector('.faq-toggle'), ans = item.querySelector('.faq-answer');
    if (!btn || !ans) return;
    btn.addEventListener('click', function () {
      var open = ans.classList.contains('open');
      faqs.forEach(function (o) {
        var a = o.querySelector('.faq-answer'), b = o.querySelector('.faq-toggle'), ic = o.querySelector('.faq-icon');
        a.classList.remove('open'); a.style.maxHeight = ''; o.classList.remove('active');
        if (ic) ic.classList.remove('rotated');
        b.setAttribute('aria-expanded', 'false');
      });
      if (!open) {
        ans.classList.add('open');
        ans.style.maxHeight = ans.scrollHeight + 24 + 'px';
        item.classList.add('active');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  /* ---------- ripple + magnetic buttons ---------- */
  doc.addEventListener('pointerdown', function (e) {
    var b = e.target.closest && e.target.closest('.lp-btn');
    if (!b || reduce) return;
    var r = b.getBoundingClientRect(), d = Math.max(r.width, r.height) * 2.2, s = doc.createElement('span');
    s.className = 'lp-ripple';
    s.style.cssText = 'width:' + d + 'px;height:' + d + 'px;left:' + (e.clientX - r.left - d / 2) + 'px;top:' + (e.clientY - r.top - d / 2) + 'px';
    b.appendChild(s);
    setTimeout(function () { s.remove(); }, 750);
  }, { passive: true });
  if (finePointer && !reduce) {
    $$('.lp-btn').forEach(function (b) {
      b.addEventListener('pointermove', function (e) {
        var r = b.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width / 2) / r.width, y = (e.clientY - r.top - r.height / 2) / r.height;
        b.style.transform = 'translate(' + (x * 10).toFixed(1) + 'px,' + (y * 8 - 2).toFixed(1) + 'px)';
      });
      b.addEventListener('pointerleave', function () { b.style.transform = ''; });
    });
  }

  /* ---------- 3D tilt cards ---------- */
  if (!reduce) {
    $$('[data-tilt]').forEach(function (c) {
      var max = c.classList.contains('lp-tile') ? 6 : 8;
      if (finePointer) {
        c.addEventListener('pointermove', function (e) {
          var r = c.getBoundingClientRect(), px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
          c.style.transform = 'perspective(900px) rotateX(' + ((0.5 - py) * max).toFixed(2) + 'deg) rotateY(' + ((px - 0.5) * max).toFixed(2) + 'deg) translateY(-4px)';
          c.style.setProperty('--mx', (px * 100).toFixed(1) + '%');
          c.style.setProperty('--my', (py * 100).toFixed(1) + '%');
        });
        c.addEventListener('pointerleave', function () { c.style.transform = ''; });
      } else {
        // gentle press tilt on touch
        c.addEventListener('touchstart', function (e) {
          var t = e.touches[0], r = c.getBoundingClientRect(), px = (t.clientX - r.left) / r.width, py = (t.clientY - r.top) / r.height;
          c.style.transform = 'perspective(900px) rotateX(' + ((0.5 - py) * 5).toFixed(2) + 'deg) rotateY(' + ((px - 0.5) * 5).toFixed(2) + 'deg) scale(.985)';
        }, { passive: true });
        var reset = function () { c.style.transform = ''; };
        c.addEventListener('touchend', reset, { passive: true });
        c.addEventListener('touchcancel', reset, { passive: true });
      }
    });
  }

  /* ---------- steps timeline + parallax + progress (one rAF scroll loop) ---------- */
  var steps = doc.querySelector('[data-steps]'), stepItems = steps ? $$('.lp-step', steps) : [];
  var para = reduce ? [] : $$('[data-parallax]');
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var y = scrollY, h = innerHeight, max = root.scrollHeight - h;
      bar.style.transform = 'scaleX(' + (max > 0 ? clamp(y / max, 0, 1) : 0).toFixed(4) + ')';
      if (steps) {
        var r = steps.getBoundingClientRect();
        var p = reduce ? 1 : clamp((h * 0.72 - r.top) / r.height, 0, 1);
        steps.style.setProperty('--p', p.toFixed(3));
        stepItems.forEach(function (li) {
          var lr = li.getBoundingClientRect();
          li.classList.toggle('is-on', reduce || lr.top + 22 < h * 0.72);
        });
      }
      for (var i = 0; i < para.length; i++) {
        var el = para[i], pr = el.parentElement.getBoundingClientRect();
        if (pr.bottom < -200 || pr.top > h + 200) continue;
        var f = parseFloat(el.getAttribute('data-parallax')) || 0.2;
        el.style.translate = '0 ' + ((pr.top + pr.height / 2 - h / 2) * -f).toFixed(1) + 'px';
      }
      updateSticky();
    });
  }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll, { passive: true });

  /* ---------- sticky mobile CTA (built at runtime from the hero's own CTA labels) ---------- */
  var sticky = null, heroCtas = doc.querySelector('.lp-ctas'), contact = doc.getElementById('contact'), footer = doc.querySelector('footer');
  if (heroCtas) {
    var links = $$('a', heroCtas), tel = links.filter(function (a) { return /^tel:/.test(a.getAttribute('href')); })[0],
      book = links.filter(function (a) { return a.getAttribute('href') === '#contact'; })[0];
    if (tel && book) {
      sticky = doc.createElement('div');
      sticky.className = 'lp-sticky';
      var t = tel.cloneNode(true), b = book.cloneNode(true);
      t.className = 'lp-btn lp-btn--ghost'; b.className = 'lp-btn lp-btn--fire';
      sticky.appendChild(t); sticky.appendChild(b);
      body.appendChild(sticky);
    }
  }
  function updateSticky() {
    if (!sticky) return;
    var h = innerHeight, show = heroCtas.getBoundingClientRect().bottom < 0;
    if (contact) { var cr = contact.getBoundingClientRect(); if (cr.top < h && cr.bottom > 0) show = false; }
    if (footer && footer.getBoundingClientRect().top < h) show = false;
    sticky.classList.toggle('is-on', show);
    sticky.setAttribute('aria-hidden', show ? 'false' : 'true');
    $$('a', sticky).forEach(function (a) { a.tabIndex = show ? 0 : -1; });
  }
  onScroll();

  /* ---------- capability check + lazy 3D ---------- */
  // Needs real GPU WebGL: software renderers (SwiftShader, llvmpipe) are too slow, so they get the CSS scene
  function hasWebGL() {
    try {
      var c = doc.createElement('canvas'), gl = window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl'));
      if (!gl) return false;
      if (/[?&]3d=1/.test(location.search)) return true;
      var ext = gl.getExtension('WEBGL_debug_renderer_info'), r = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : '';
      var lose = gl.getExtension('WEBGL_lose_context'); if (lose) lose.loseContext();
      return !/swiftshader|llvmpipe|software|basic render/i.test(r);
    } catch (e) { return false; }
  }
  var conn = navigator.connection || {};
  var lowPower = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4 && navigator.deviceMemory && navigator.deviceMemory <= 2) || conn.saveData;
  var can3D = !reduce && !lowPower && hasWebGL();
  var stage = doc.querySelector('[data-stage]'), chart = doc.querySelector('[data-chart]');
  var theme = body.getAttribute('data-scene') || 'trades';

  function chartFallback() {
    if (!chart || chart.classList.contains('is-fallback')) return;
    chart.classList.add('is-fallback');
    var fb = chart.querySelector('.lp-chart-fallback'), labels = (chart.getAttribute('data-labels') || '').split('|');
    var cols = [['#ffb347', '#E84425'], ['#38e1ff', '#4E6AAF'], ['#ff7a3d', '#ff4f8b'], ['#8b7bff', '#4E6AAF'], ['#ff4f8b', '#c2341b'], ['#5effc9', '#2a9cd6']];
    labels.forEach(function (l, i) {
      var d = doc.createElement('div');
      d.className = 'lp-fb-bar';
      d.style.cssText = '--h:' + (55 + 30 * Math.abs(Math.sin(i * 1.3 + 0.6))).toFixed(0) + '%;--c1:' + cols[i % 6][0] + ';--c2:' + cols[i % 6][1] + ';transition-delay:' + i * 90 + 'ms';
      var s = doc.createElement('span'); s.textContent = l; d.appendChild(s);
      fb.appendChild(d);
    });
  }

  var mod = null;
  function loadMod() {
    if (!mod) mod = import('/assets/landing/hero3d.js');
    return mod;
  }
  function whenNear(el, cb, margin) {
    if (!el) return;
    if (!('IntersectionObserver' in window)) return cb();
    var o = new IntersectionObserver(function (es) {
      if (es.some(function (e) { return e.isIntersecting; })) { o.disconnect(); cb(); }
    }, { rootMargin: margin || '200px 0px' });
    o.observe(el);
  }
  function hotCard(i) {
    $$('[data-card]').forEach(function (c) { c.classList.toggle('is-hot', String(i) === c.getAttribute('data-card')); });
  }

  if (!can3D) {
    if (stage) stage.classList.add('is-static');
    if (chart) chartFallback();
    return;
  }
  function start() {
    whenNear(stage, function () {
      loadMod().then(function (m) { m.mountHero(stage, theme, { mobile: isMobile }); })
        .catch(function () { if (stage) { stage.classList.remove('is-live'); stage.classList.add('is-static'); } });
    }, '100px 0px');
    whenNear(chart, function () {
      loadMod().then(function (m) { m.mountChart(chart, theme, { mobile: isMobile, onHot: hotCard }); })
        .catch(chartFallback);
    }, '300px 0px');
  }
  // Defer Three.js until the page has painted and gone idle
  function idle() { (window.requestIdleCallback || function (f) { return setTimeout(f, 300); })(start, { timeout: 2500 }); }
  if (doc.readyState === 'complete') setTimeout(idle, 400);
  else addEventListener('load', function () { setTimeout(idle, 400); });
})();
