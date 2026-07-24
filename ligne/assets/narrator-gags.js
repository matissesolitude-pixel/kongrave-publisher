/* ═══════════════════════════════════════════════════════════════════════════
   MR DOLLAR — BIBLIOTHÈQUE DE GAGS (primitives réutilisables)
   Codé UNE fois, branché sur chaque épisode. Aucun sur-mesure par Reel.

   Doctrine (Bible, PARTIE II bis) :
   · Le gag ouvre S1, dure ~1 à 1,5 s, puis IL PASSE LA MAIN.
   · Mr Dollar est PETIT, en ENCRE #20242A, jamais en teal. Il souffre
     COMIQUEMENT (cartoon, sans conséquence) ; la boule teal souffre
     MÉCANIQUEMENT dans la démonstration. Il n'apparaît PAS en S4.
   · Frame 0 = tension max : le gag est DÉJÀ en cours à t=0, jamais construit
     depuis un écran vide.
   · L'AGENT est un objet DÉJÀ codé dans l'épisode (rideau, gouffre, jauge…).
     La primitive ne dessine pas l'agent : elle se positionne par rapport à lui.
   · GARDE-FOU IMAGERIE : aucun accessoire guru (cigare, liasses, luxe) sauf
     ironie explicite — la retenue fait la crédibilité de la marque.

   USAGE dans un moteur :
     const MrD = MrDollar.init({svg:SVG, poses:NPOSE});
     // en S1 :
     MrD.gag(u, {primitive:'bumpInto', agent:{x:cut, y:1400},
                 reaction:'sonné', raccord:'point',
                 rest:{x:170, y:1430, h:232}});
     // ailleurs (il accompagne, petit) :
     MrD.show('point_soft', 152, 1440, 246, op, false);
     // en S4 : MrD.hide();
   ═══════════════════════════════════════════════════════════════════════════ */
(function (root) {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  var lerp = function (a, b, f) { return a + (b - a) * clamp(f, 0, 1); };
  var eOut = function (f) { f = clamp(f, 0, 1); return 1 - (1 - f) * (1 - f); };
  var eIn = function (f) { f = clamp(f, 0, 1); return f * f; };
  var eInOut = function (f) { f = clamp(f, 0, 1); return f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2; };
  // oscillation amortie : le rebond cartoon (jamais figé, deux harmoniques)
  var wob = function (u, f, d) { return Math.exp(-(d || 4) * u) * (Math.sin(u * f) + 0.4 * Math.sin(u * f * 2.1)); };

  var HIT = 0.75;   // durée de l'état de choc
  var RAC = 0.50;   // durée du raccord (il se relève / il montre)
  var HAND = 1.10;  // durée du passage de main (il rejoint sa place et reste petit)

  function MrDollar(cfg) {
    this.poses = cfg.poses || {};
    this.g = document.createElementNS(NS, 'g');
    this.g.setAttribute('opacity', '0');
    this.use = document.createElementNS(NS, 'use');
    this.g.appendChild(this.use);
    (cfg.svg || document.querySelector('svg')).appendChild(this.g);
    this.defaultPose = cfg.defaultPose || 'idle_soft';
  }

  /* Rendu bas niveau : ancrage aux PIEDS (x,y), rotation et squash autour des pieds. */
  MrDollar.prototype.draw = function (pose, x, y, h, op, flip, rot, sx, sy) {
    var name = this.poses[pose] ? pose : this.defaultPose;
    var P = this.poses[name];
    if (!P) return;
    pose = name;
    var s = h / P.h, fx = s * (sx == null ? 1 : sx) * (flip ? -1 : 1), fy = s * (sy == null ? 1 : sy);
    this.use.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#np_' + pose);
    this.use.setAttribute('href', '#np_' + pose);
    this.g.setAttribute('transform',
      'translate(' + x.toFixed(1) + ',' + y.toFixed(1) + ') rotate(' + (rot || 0).toFixed(1) + ') ' +
      'scale(' + fx.toFixed(4) + ',' + fy.toFixed(4) + ') translate(' + (-P.w / 2).toFixed(1) + ',' + (-P.h).toFixed(1) + ')');
    this.g.setAttribute('opacity', clamp(op == null ? 1 : op, 0, 1).toFixed(3));
  };
  MrDollar.prototype.show = function (pose, x, y, h, op, flip) { this.draw(pose, x, y, h, op, flip, 0, 1, 1); };
  MrDollar.prototype.hide = function () { this.g.setAttribute('opacity', '0'); };

  /* La RÉACTION choisit la pose et une inflexion (Bible VARIABLE C). */
  var REACT = {
    'sonné':      { pose: 'present_wide', tilt: 1.0,  bob: 1.0 },
    'surpris':    { pose: 'present_wide', tilt: 0.5,  bob: 0.6 },
    'résigné':    { pose: 'idle_soft',    tilt: 0.2,  bob: 0.2 },
    'inquiet':    { pose: 'point_soft',   tilt: 0.4,  bob: 0.5 },
    'impuissant': { pose: 'present_wide', tilt: 0.7,  bob: 0.7 },
    'curieux':    { pose: 'point_soft',   tilt: 0.2,  bob: 0.3 },
    'vexé':       { pose: 'idle_soft',    tilt: 0.0,  bob: 0.15 },
    'fier puis humilié': { pose: 'present_wide', tilt: 0.9, bob: 0.9 }
  };
  /* Le RACCORD : comment il passe la main (Bible VARIABLE F). */
  var RACCORD = {
    'point':   'point_soft',   // il se relève et pointe le "?"
    'ecarte':  'idle_soft',    // il s'écarte et laisse la place
    'sol':     'present_wide', // il reste au sol pendant que le "?" apparaît
    'sortie':  'idle_soft'     // il sort du cadre
  };

  /* ── FAMILLE 1 : IL SUBIT ─────────────────────────────────────────────────
     Chaque primitive rend l'état de CHOC à u=0 (déjà arrivé / en plein geste). */
  var P1 = {
    // il se cogne contre l'agent : nez écrasé, penché vers lui, il rebondit
    bumpInto: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { dx: -78 - 16 * k, dy: 0, rot: -26 * k * r.tilt, sx: 1 + 0.16 * k, sy: 1 - 0.13 * k,
               bob: 9 * k * wob(u, 15, 5) * r.bob };
    },
    // il tombe dans/depuis l'agent : il est déjà bas, il remonte
    fall: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { dx: -30, dy: 96 * k, rot: 18 * k * r.tilt, sx: 1 + 0.10 * k, sy: 1 - 0.10 * k,
               bob: 6 * k * wob(u, 12, 5) * r.bob };
    },
    // l'agent le percute : il est projeté à l'opposé, en l'air
    hitBy: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { dx: -110 * k - 40, dy: -70 * k * eOut(1 - k + 0.001), rot: -34 * k * r.tilt,
               sx: 1 + 0.12 * k, sy: 1 - 0.08 * k, bob: 8 * k * wob(u, 14, 4.5) * r.bob };
    },
    // l'agent descend sur lui : il est aplati, il reprend sa forme
    crushedBy: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { dx: -20, dy: 0, rot: 0, sx: 1 + 0.42 * k, sy: 1 - 0.46 * k,
               bob: 4 * k * wob(u, 16, 6) * r.bob };
    },
    // deux agents l'étirent : il est allongé horizontalement, il se rétracte
    stretchedBy: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { dx: 0, dy: 0, rot: 0, sx: 1 + 0.55 * k, sy: 1 - 0.24 * k,
               bob: 5 * k * wob(u, 13, 5) * r.bob };
    },
    // il est aspiré/effacé par l'agent : il rétrécit vers lui puis revient
    vanishInto: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { dx: -40 + 40 * k, dy: 0, rot: 12 * k * r.tilt, sx: 1 - 0.45 * k, sy: 1 - 0.45 * k,
               op: 1 - 0.35 * k, bob: 3 * k * wob(u, 11, 5) * r.bob };
    }
  };

  /* ── FAMILLES 2/3/4 : IL AGIT · IL EST · LE CONTRASTE ────────────────────
     Ici il ne subit pas : le mouvement vient de LUI (ou de son immobilité). */
  var P2 = {
    // il agit : signe, claquement, salto, sifflement
    gesture: function (u, type) {
      var c = clamp(u / 0.55, 0, 1);
      if (type === 'salto') return { pose: 'walk_wide', dx: 0, dy: -120 * Math.sin(Math.PI * c), rot: -360 * eInOut(c), sx: 1, sy: 1 };
      if (type === 'snap')  return { pose: 'point_soft', dx: 0, dy: 0, rot: -6 * Math.sin(u * 18) * (1 - c), sx: 1, sy: 1 };
      if (type === 'whistle') return { pose: 'idle_soft', dx: 0, dy: -5 * Math.abs(Math.sin(u * 5)), rot: 0, sx: 1, sy: 1 };
      return { pose: 'wave_wide', dx: 0, dy: 0, rot: 5 * Math.sin(u * 7) * (1 - 0.6 * c), sx: 1, sy: 1 }; // 'wave'
    },
    // il EST : boucle courte, calme. Seule, elle n'arrête pas le pouce (Bible) :
    // à n'utiliser QU'AVEC contrast().
    idle: function (u, type) {
      var b = 3 * Math.sin(u * 1.15) + 1.4 * Math.sin(u * 2.25);
      if (type === 'arms_crossed' || type === 'vexe') return { pose: 'wave_hip_soft', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
      if (type === 'bored')  return { pose: 'idle_arms_down_soft', dx: 0, dy: b, rot: 2 * Math.sin(u * 0.6), sx: 1, sy: 1 };
      if (type === 'waits')  return { pose: 'wave_hip_wide', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
      return { pose: 'idle_soft', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
    },
    // il AGIT SUR l'agent de l'épisode : il tire / pousse / efface / soulève
    act: function (u, verb) {
      var c = eInOut(clamp(u / 0.9, 0, 1));
      if (verb === 'push')  return { pose: 'present_wide', dx: 46 * c, dy: 0, rot: 8 * c, sx: 1, sy: 1 };
      if (verb === 'erase') return { pose: 'point_soft', dx: 26 * Math.sin(u * 7), dy: 0, rot: 0, sx: 1, sy: 1 };
      if (verb === 'lift')  return { pose: 'present_wide', dx: 0, dy: -30 * c, rot: 0, sx: 1, sy: 1 };
      return { pose: 'point_soft', dx: -52 * c, dy: 0, rot: -8 * c, sx: 1, sy: 1 };   // 'pull'
    }
  };

  /* API PRINCIPALE — le gag d'ouverture de S1.
     spec = { primitive, agent:{x,y}, reaction, raccord, rest:{x,y,h}, h, flip,
              idle, verb, type }                                                */
  MrDollar.prototype.gag = function (u, spec) {
    spec = spec || {};
    var a = spec.agent || { x: 540, y: 1400 };
    var r = REACT[spec.reaction] || REACT['sonné'];
    var rest = spec.rest || { x: 170, y: a.y, h: 232 };
    var h0 = spec.h || 262;
    var st, pose;

    if (P1[spec.primitive]) {                       // FAMILLE 1 — il subit
      st = P1[spec.primitive](u, a, r);
      var rise = clamp((u - HIT) / RAC, 0, 1);
      pose = rise < 0.5 ? r.pose : (RACCORD[spec.raccord] || 'point_soft');
      st.rot = (st.rot || 0) * (1 - rise);           // il se redresse
      st.sx = lerp(st.sx == null ? 1 : st.sx, 1, rise);
      st.sy = lerp(st.sy == null ? 1 : st.sy, 1, rise);
    } else if (spec.primitive === 'contrast') {      // FAMILLE 4 — le contraste
      st = P2.idle(u, spec.idle || 'arms_crossed');  // lui calme, le chaos DERRIÈRE (l'épisode le dessine)
      pose = st.pose;
    } else if (spec.primitive === 'act') {           // FAMILLE 2 — il agit sur l'agent
      st = P2.act(u, spec.verb || 'pull'); pose = st.pose;
    } else if (spec.primitive === 'idle') {          // FAMILLE 3 — il est
      st = P2.idle(u, spec.type || 'bored'); pose = st.pose;
    } else {                                          // FAMILLE 2 — geste
      st = P2.gesture(u, spec.type || 'wave'); pose = st.pose;
    }

    // PASSAGE DE MAIN : il rejoint sa place et reste PETIT (il ne disparaît pas)
    var hand = eInOut(clamp((u - (HIT + RAC)) / HAND, 0, 1));
    if (hand > 0 && spec.raccord === 'sortie') {
      // variante : il sort réellement du cadre
      var x0 = a.x + (st.dx || 0), y0 = a.y + (st.dy || 0);
      this.draw(pose, lerp(x0, -240, hand), y0, h0, 1 - hand, spec.flip, st.rot, st.sx, st.sy);
      return;
    }
    var bx = a.x + (st.dx || 0), by = a.y + (st.dy || 0) + (st.bob || 0);
    var px = lerp(bx, rest.x, hand), py = lerp(by, rest.y, hand), ph = lerp(h0, rest.h, hand);
    if (hand > 0.85) { px += 4 * Math.sin(u * 1.2) + 2 * Math.sin(u * 2.3); }   // vie continue une fois posé
    this.draw(hand > 0.6 ? (RACCORD[spec.raccord] || 'idle_soft') : pose,
              px, py, ph, (st.op == null ? 1 : st.op) * (spec.op == null ? 1 : spec.op), spec.flip, st.rot, st.sx, st.sy);
  };

  root.MrDollar = {
    init: function (cfg) { return new MrDollar(cfg); },
    HIT: HIT, RAC: RAC, HAND: HAND,
    primitives: ['bumpInto', 'fall', 'hitBy', 'crushedBy', 'stretchedBy', 'vanishInto',
                 'gesture', 'idle', 'act', 'contrast']
  };
})(typeof window !== 'undefined' ? window : this);
