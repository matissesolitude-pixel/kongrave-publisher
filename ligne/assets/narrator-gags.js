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
     MrD.show('point', 152, 1440, 246, op, false);
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

  /* RYTHME DU GAG — un gag trop rapide n'est pas lu comme un gag.
     Il faut le temps de voir la CAUSE, d'encaisser le CHOC, puis de lire la RÉACTION.
     (Corrigé le 24/07 : 0,75+0,50 était trop court, personne n'avait le temps de comprendre.) */
  var HIT = 1.30;   // le choc TIENT : on voit ce qui lui arrive
  var RAC = 0.95;   // le temps de la réaction — c'est là que le comique se lit
  var HAND = 1.15;  // il passe la main

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
    this._drawEyes(pose, this._t);
  };
  /* ── SYNCHRO LABIALE (Bible) ────────────────────────────────────────────
     Mr Dollar EST la voix du Reel. À l'écran sa bouche bouge sur l'AMPLITUDE de
     l'audio (jamais de bouche figée pendant qu'on l'entend parler) ; hors champ
     la voix continue. Pas de lip-sync phonétique : les deux variantes de bouche
     (_wide ouverte / _soft fermée) sont les positions du cycle. */
  MrDollar.prototype.setAmp = function (arr, fps) { this.amp = arr || null; this.fps = fps || 30; };
  /* Bouche : hystérésis + maintien minimum. Sans ça la bouche bat au rythme de
     l'amplitude (jusqu'à 30 Hz) et, les deux variantes étant deux DESSINS distincts,
     les yeux se mettent à convulser. On ne change d'état que si le son le justifie
     durablement, et jamais plus vite que MOUTH_HOLD. */
  var MOUTH_HOLD = 0.13;
  MrDollar.prototype.mouth = function (t) {
    if (!this.amp || !this.amp.length) return 'soft';
    t = t || 0;
    var a = this.amp[Math.floor(t * this.fps)] || 0;
    if (this._mState == null) { this._mState = 'soft'; this._mT = t; }
    if (t - this._mT >= MOUTH_HOLD) {
      var want = this._mState === 'wide' ? (a > 0.20 ? 'wide' : 'soft')   // hystérésis
                                         : (a > 0.38 ? 'wide' : 'soft');
      if (want !== this._mState) { this._mState = want; this._mT = t; }
    }
    return this._mState;
  };
  /* Une paire n'est utilisable pour le lip-sync que si les deux dessins sont
     ALIGNÉS (yeux au même endroit). Sinon on garde une seule pose : mieux vaut
     pas d'animation de bouche qu'un visage qui tremble. */
  MrDollar.prototype._pairOK = function (base) {
    if (!this._pair) this._pair = {};
    if (this._pair[base] != null) return this._pair[base];
    var A = this.eyeMap && this.eyeMap[base + '_soft'], B = this.eyeMap && this.eyeMap[base + '_wide'];
    var ok = false;
    if (A && B && A.eyes && B.eyes && this.poses[base + '_soft'] && this.poses[base + '_wide']) {
      var d = 0;
      for (var i = 0; i < 2; i++)
        d = Math.max(d, Math.abs(A.eyes[i].x - B.eyes[i].x) + Math.abs(A.eyes[i].y - B.eyes[i].y));
      ok = (d < 14);
    }
    this._pair[base] = ok;
    return ok;
  };
  MrDollar.prototype.resolve = function (pose, t) {
    if (/_(soft|wide)$/.test(pose)) return pose;
    // PENDANT UN GAG IL NE PARLE PAS : bouche au repos, aucune synchro labiale.
    if (this._inGag) {
      if (this.poses[pose + '_soft']) return pose + '_soft';
      if (this.poses[pose + '_wide']) return pose + '_wide';
      return this.poses[pose] ? pose : pose + '_soft';
    }
    if (this._pairOK(pose)) {                       // paire alignée : la bouche peut jouer
      var a = pose + '_' + this.mouth(t);
      if (this.poses[a]) return a;
    }
    if (this.poses[pose + '_soft']) return pose + '_soft';
    if (this.poses[pose + '_wide']) return pose + '_wide';
    return this.poses[pose] ? pose : pose + '_soft';
  };
  /* Poses capables de parler (paire alignée) — le séquenceur les privilégie
     quand il y a de la voix et qu'on voit son visage. */
  MrDollar.prototype.canTalk = function (base) { return this._pairOK(base); };
  MrDollar.prototype.say = function (base, t, x, y, h, op, flip, rot, sx, sy) {
    this._t = t;
    this.placeClear(this.resolve(base, t), x, y, h, op, flip, rot);
  };
  /* IL DÉSIGNE QUELQUE CHOSE — le sens est calculé, jamais deviné.
     Les poses visent à DROITE par défaut : si la cible est à sa gauche, on miroite.
     Règle : il regarde et pointe TOUJOURS vers ce qu'il désigne. */
  MrDollar.prototype.pointAt = function (base, t, x, y, h, op, targetX, rot, sx, sy) {
    this._t = t;
    this.placeClear(this.resolve(base, t), x, y, h, op, (targetX < x), rot);
  };
  /* ── LES YEUX : CLIGNEMENT + REGARD (il s'adresse à nous) ────────────────
     Les pupilles sont peintes dans le dessin vectorisé : on les RECOUVRE et on
     les redessine, ce qui donne d'un coup le clignement et le contrôle du regard.
     Par DÉFAUT il regarde la CAMÉRA — il narre, il s'adresse au spectateur.
     Quand il désigne quelque chose, son regard part vers la cible. */
  MrDollar.prototype.setEyes = function (map) { this.eyeMap = map || {}; };
  MrDollar.prototype.gaze = function (gx, gy) { this._gx = gx; this._gy = (gy == null ? 0.10 : gy); };
  MrDollar.prototype._blink = function (t) {
    // deux périodes premières entre elles -> jamais métronomique, mais déterministe
    var a = (t / 3.7) % 1, b = (t / 5.3) % 1;
    var d = 0.038;                                  // ~0.14 s de fermeture
    return (a < d || b < d) ? 1 : 0;
  };
  MrDollar.prototype._drawEyes = function (pose, t) {
    var E = this.eyeMap && this.eyeMap[pose];
    if (!this.eyeG) { this.eyeG = document.createElementNS(NS, 'g'); this.g.appendChild(this.eyeG); }
    // YEUX OUVERTS = ON NE TOUCHE À RIEN. Le dessin d'origine est le bon ; le recouvrir
    // donnait un regard inquiétant. On n'intervient QUE le temps du clignement.
    if (!E || !E.eyes || !this._blink(t || 0)) { this.eyeG.innerHTML = ''; return; }
    var h = '';
    for (var i = 0; i < E.eyes.length; i++) {
      var e = E.eyes[i];
      h += '<circle cx="' + e.x + '" cy="' + e.y + '" r="' + (e.r * 1.5).toFixed(1) + '" fill="#F2EFE7"/>' +
           '<path d="M' + (e.x - e.r * 1.1).toFixed(1) + ' ' + e.y + ' q' + (e.r * 1.1).toFixed(1) + ' ' +
           (e.r * 0.5).toFixed(1) + ' ' + (e.r * 2.2).toFixed(1) + ' 0" fill="none" stroke="#20242A" stroke-width="6" stroke-linecap="round"/>';
    }
    this.eyeG.innerHTML = h;
  };
  /* ── LOI : ZÉRO CHEVAUCHEMENT ────────────────────────────────────────────
     Un plan illisible fait décrocher ; la lisibilité fait le watch time, donc la
     portée. Le narrateur ne se place donc JAMAIS à l'aveugle : il mesure ce qui
     occupe déjà l'écran, cherche une zone libre, rétrécit si besoin — et
     DISPARAÎT si rien n'est libre. Le schéma prime toujours sur le narrateur. */
  MrDollar.prototype._obstacles = function (textOnly) {
    var svg = this.g.ownerSVGElement || this.g.parentNode, out = [];
    if (!svg || !svg.querySelectorAll) return out;
    var els = svg.querySelectorAll(textOnly ? 'text' : 'rect,circle,ellipse,line,polyline,polygon,path,text,image');
    for (var i = 0; i < els.length; i++) {
      var e = els[i];
      if (this.g.contains(e)) continue;                       // lui-même
      if (e.closest && e.closest('defs')) continue;           // non dessiné
      var op = parseFloat(e.getAttribute('opacity'));
      if (!isNaN(op) && op < 0.06) continue;                  // invisible
      var r; try { r = e.getBoundingClientRect(); } catch (x) { continue; }
      if (r.width < 3 || r.height < 3) continue;
      out.push(r);
    }
    return out;
  };
  MrDollar.prototype._overlapArea = function (r, obs) {
    var a = 0;
    for (var i = 0; i < obs.length; i++) {
      var o = obs[i];
      var w = Math.min(r.right, o.right) - Math.max(r.left, o.left);
      var h = Math.min(r.bottom, o.bottom) - Math.max(r.top, o.top);
      if (w > 0 && h > 0) a += w * h;
    }
    return a;
  };
  /* Cherche la meilleure zone libre SANS l'appliquer (mesure seulement). */
  MrDollar.prototype._bestSpot = function (pose, x, y, h, op, flip, rot, opts) {
    var obs = this._obstacles(opts && opts.avoid === 'text');
    var dx = [0, -130, 130, -260, 260, -390, 390], sc = [1, 0.82, 0.66], best = null;
    for (var si = 0; si < sc.length; si++) {
      for (var di = 0; di < dx.length; di++) {
        var c = { x: x + dx[di], y: y, h: h * sc[si] };
        this.draw(pose, c.x, c.y, c.h, op, flip, rot, 1, 1);
        var r; try { r = this.g.getBoundingClientRect(); } catch (e) { return best; }
        // il doit rester ENTIER dans la zone sûre : s'écarter hors champ n'est pas une solution
        if (r.left < 40 || r.right > 1040 || r.bottom > 1500) continue;
        var ov = this._overlapArea(r, obs) / Math.max(1, r.width * r.height);
        if (best === null || ov < best.ov) best = { x: c.x, y: c.y, h: c.h, ov: ov };
        if (ov < 0.02) return best;
      }
    }
    return (best && best.ov < 0.10) ? best : null;
  };

  /* Place SANS chevauchement ET SANS saccade : il GLISSE vers sa cible à vitesse de
     marche, et tant qu'il se déplace on le voit MARCHER, face au sens de la marche.
     Un recalcul de zone libre ne doit jamais produire une téléportation. */
  MrDollar.prototype.placeClear = function (pose, x, y, h, op, flip, rot, opts) {
    opts = opts || {};
    var t = this._t || 0;
    var dt = (this._lastT == null) ? 0.033 : Math.min(0.2, Math.max(0.001, t - this._lastT));
    this._lastT = t;
    var tgt = this._bestSpot(pose, x, y, h, op, flip, rot, opts);
    // fondu : apparaître/disparaître en douceur plutôt que d'un coup
    var f = (this._fade == null) ? 0 : this._fade;
    f = tgt ? Math.min(1, f + dt * 5) : Math.max(0, f - dt * 5);
    this._fade = f;
    if (!tgt) {
      if (f <= 0.02 || !this._cur) { this.hide(); return false; }
      tgt = this._cur;                                   // il s'efface sur place
    }
    // premier placement, ou retour après une absence : on se pose, on ne traverse pas l'écran
    if (!this._cur || f < 0.06) this._cur = { x: tgt.x, y: tgt.y, h: tgt.h };
    var d = tgt.x - this._cur.x, SPD = 700, step = SPD * dt;
    var moving = Math.abs(d) > 8;
    this._cur.x += (Math.abs(d) <= step) ? d : (d > 0 ? step : -step);
    this._cur.y += (tgt.y - this._cur.y) * Math.min(1, dt * 6);
    this._cur.h += (tgt.h - this._cur.h) * Math.min(1, dt * 6);
    var pf = moving ? this.resolve('walk', t) : pose;     // ON LE VOIT MARCHER
    var fl = moving ? (d < 0) : flip;                     // il regarde là où il va
    this.draw(pf, this._cur.x, this._cur.y, this._cur.h, op * f, fl, moving ? 0 : rot, 1, 1);
    return true;
  };
  /* ── SÉQUENCEUR DE POSES ────────────────────────────────────────────────
     Il ne tient JAMAIS la même attitude pendant toute une apparition : il enchaîne.
     `seq` = liste de poses (noms de base), jouées dans l'ordre avec des durées
     légèrement inégales (rythme naturel, pas métronomique) et déterministes. */
  /* Chaque pose est une INTENTION, pas une variation décorative.
     Le pointage est RARE : il ne sert qu'au moment où il désigne vraiment.
     'talk' = poses au visage visible, capables d'animer la bouche. */
  var ROUTINES = {
    // il désigne une chose précise, puis il laisse regarder (il ne pointe pas en continu)
    designe:  [['point', 1.1], ['present', 1.6], ['idle', 1.8], ['hips', 1.5]],
    // il développe une idée : présentation ouverte, puis attente
    explique: [['present', 1.7], ['idle', 1.6], ['hips', 1.5], ['present', 1.4]],
    // il est là, il écoute, il ne commente pas
    attend:   [['idle', 1.9], ['armscross', 1.7], ['hips', 1.6], ['idle', 1.5]],
    // il encaisse ce que la démonstration vient de montrer
    reagit:   [['startle', 0.9], ['mouthcover', 1.3], ['armscross', 1.7], ['sad', 1.5]],
    doute:    [['puzzled', 1.5], ['facepalm', 1.2], ['armscross', 1.8]],
    constate: [['flat', 1.8], ['sad', 1.6], ['armscross', 1.7]]
  };
  /* Retourne la pose courante d'une routine. u = temps local de l'apparition. */
  MrDollar.prototype.seq = function (u, routine, wantTalk) {
    var L = (typeof routine === 'string') ? (ROUTINES[routine] || ROUTINES.attend) : routine;
    if (!L || !L.length) return 'idle';
    var acc = 0, pick = L[L.length - 1][0];
    for (var i = 0; i < 60; i++) {
      var e = L[i % L.length];
      if (u < acc + e[1]) { pick = e[0]; break; }
      acc += e[1];
    }
    // s'il y a de la voix et qu'on voit son visage, préférer une pose qui peut parler
    if (wantTalk && !this.canTalk(pick)) {
      for (var j = 0; j < L.length; j++) if (this.canTalk(L[j][0])) return L[j][0];
    }
    return pick;
  };
  /* ── LA CAUSE DOIT ÊTRE À L'IMAGE ────────────────────────────────────────
     Un gag dont on ne voit pas la cause n'est pas drôle, il est illisible.
     L'AGENT (objet de l'épisode) doit être VISIBLE et EN CONTACT au moment du choc.
     La bibliothèque ne peut pas dessiner l'agent — il appartient à la scène — mais
     elle marque le POINT D'IMPACT : quelques traits rayonnants, langage cartoon
     universel, qui relient visuellement l'agent au personnage. */
  MrDollar.prototype._impact = function (ax, ay, k, dir) {
    if (!this.hitG) {
      this.hitG = document.createElementNS(NS, 'g');
      (this.g.parentNode || this.g).insertBefore(this.hitG, this.g);
    }
    if (k <= 0.02) { this.hitG.innerHTML = ''; return; }
    var h = '', n = 6, base = (dir < 0 ? Math.PI : 0);
    for (var i = 0; i < n; i++) {
      var a = base - 0.75 + (1.5 * i / (n - 1));
      var r0 = 26 + 10 * (1 - k), r1 = r0 + 34 * k;
      h += '<line x1="' + (ax + Math.cos(a) * r0).toFixed(1) + '" y1="' + (ay + Math.sin(a) * r0 * 0.8).toFixed(1) +
           '" x2="' + (ax + Math.cos(a) * r1).toFixed(1) + '" y2="' + (ay + Math.sin(a) * r1 * 0.8).toFixed(1) +
           '" stroke="#20242A" stroke-width="' + (7 * k).toFixed(1) + '" stroke-linecap="round" opacity="' + k.toFixed(2) + '"/>';
    }
    this.hitG.innerHTML = h;
  };
  MrDollar.prototype.show = function (pose, x, y, h, op, flip) { this.draw(pose, x, y, h, op, flip, 0, 1, 1); };
  MrDollar.prototype.hide = function () { this.g.setAttribute('opacity', '0'); };

  /* La RÉACTION choisit la pose et une inflexion (Bible VARIABLE C). */
  var REACT = {
    'sonné':               { pose: 'startle',    tilt: 1.0, bob: 1.0 },
    'surpris':             { pose: 'startle',    tilt: 0.5, bob: 0.6 },   // sursaut, bras en l'air
    'résigné':             { pose: 'sad',        tilt: 0.2, bob: 0.2 },   // abattu
    'inquiet':             { pose: 'mouthcover', tilt: 0.4, bob: 0.5 },   // mains sur la bouche
    'impuissant':          { pose: 'despair',    tilt: 0.7, bob: 0.7 },   // tête dans les mains
    'curieux':             { pose: 'peekover',   tilt: 0.2, bob: 0.3 },   // il regarde par-dessus
    'vexé':                { pose: 'armscross',  tilt: 0.0, bob: 0.15 },  // bras croisés
    'faussement confiant': { pose: 'hips',       tilt: 0.3, bob: 0.4 },   // mains sur les hanches
    'soulagé trop tôt':    { pose: 'hipswave',   tilt: 0.2, bob: 0.3 },
    'fier puis humilié':   { pose: 'present',    tilt: 0.9, bob: 0.9 }
  };
  /* Le RACCORD : comment il passe la main (Bible VARIABLE F). */
  var RACCORD = {
    'point':   'point',     // il se relève et pointe le "?"
    'ecarte':  'back',      // il se détourne et laisse la place (pose de dos)
    'sol':     'floorpoint',// il reste au sol et pointe le "?"
    'sortie':  'walk'       // il sort du cadre
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
      return { pose: k > 0.25 ? 'blown' : null, dx: -110 * k - 40, dy: -70 * k * eOut(1 - k + 0.001), rot: -34 * k * r.tilt,
               sx: 1 + 0.12 * k, sy: 1 - 0.08 * k, bob: 8 * k * wob(u, 14, 4.5) * r.bob };
    },
    // l'agent descend sur lui : il est aplati, il reprend sa forme
    crushedBy: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { pose: k > 0.25 ? 'flattened' : null, dx: -20, dy: 0, rot: 0, sx: 1 + 0.10 * k, sy: 1 - 0.10 * k,
               bob: 4 * k * wob(u, 16, 6) * r.bob };
    },
    // deux agents l'étirent : il est allongé horizontalement, il se rétracte
    stretchedBy: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { pose: k > 0.25 ? 'squeezed' : null, dx: 0, dy: 0, rot: 0, sx: 1 + 0.15 * k, sy: 1 - 0.08 * k,
               bob: 5 * k * wob(u, 13, 5) * r.bob };
    },
    // il est aspiré/effacé par l'agent : il rétrécit vers lui puis revient
    vanishInto: function (u, a, r) {
      var k = clamp(1 - u / HIT, 0, 1);
      return { pose: k > 0.35 ? 'handonly' : null, dx: -40 + 40 * k, dy: 0, rot: 6 * k * r.tilt, sx: 1, sy: 1,
               op: 1 - 0.35 * k, bob: 3 * k * wob(u, 11, 5) * r.bob };
    }
  };

  /* ── FAMILLES 2/3/4 : IL AGIT · IL EST · LE CONTRASTE ────────────────────
     Ici il ne subit pas : le mouvement vient de LUI (ou de son immobilité). */
  var P2 = {
    // il agit : signe, claquement, salto, sifflement
    gesture: function (u, type) {
      var c = clamp(u / 0.55, 0, 1);
      if (type === 'salto') return { pose: 'walk', dx: 0, dy: -120 * Math.sin(Math.PI * c), rot: -360 * eInOut(c), sx: 1, sy: 1 };
      if (type === 'snap')  return { pose: 'point', dx: 0, dy: 0, rot: -6 * Math.sin(u * 18) * (1 - c), sx: 1, sy: 1 };
      if (type === 'whistle') return { pose: 'idle', dx: 0, dy: -5 * Math.abs(Math.sin(u * 5)), rot: 0, sx: 1, sy: 1 };
      return { pose: 'wave', dx: 0, dy: 0, rot: 5 * Math.sin(u * 7) * (1 - 0.6 * c), sx: 1, sy: 1 }; // 'wave'
    },
    // il EST : boucle courte, calme. Seule, elle n'arrête pas le pouce (Bible) :
    // à n'utiliser QU'AVEC contrast().
    idle: function (u, type) {
      var b = 3 * Math.sin(u * 1.15) + 1.4 * Math.sin(u * 2.25);
      if (type === 'arms_crossed' || type === 'vexe') return { pose: 'armscross', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
      if (type === 'bored')  return { pose: 'flat', dx: 0, dy: b, rot: 2 * Math.sin(u * 0.6), sx: 1, sy: 1 };
      if (type === 'waits')  return { pose: 'hips', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
      // ⚠ 'chill' (lunettes + cocktail) = imagerie guru : UNIQUEMENT en IRONIE (famille CONTRASTE),
      //   jamais en ouverture neutre — une frame suffit à envoyer le signal inverse de la marque.
      if (type === 'chill')  return { pose: 'chill', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
      return { pose: 'idle', dx: 0, dy: b, rot: 0, sx: 1, sy: 1 };
    },
    // il AGIT SUR l'agent de l'épisode : il tire / pousse / efface / soulève
    act: function (u, verb) {
      var c = eInOut(clamp(u / 0.9, 0, 1));
      if (verb === 'push')  return { pose: 'present', dx: 46 * c, dy: 0, rot: 8 * c, sx: 1, sy: 1 };
      if (verb === 'erase') return { pose: 'point', dx: 26 * Math.sin(u * 7), dy: 0, rot: 0, sx: 1, sy: 1 };
      if (verb === 'lift')  return { pose: 'present', dx: 0, dy: -30 * c, rot: 0, sx: 1, sy: 1 };
      return { pose: 'pullrope', dx: -52 * c, dy: 0, rot: -4 * c, sx: 1, sy: 1 };   // 'pull'
    }
  };

  /* HOOK 'zoom' — le plus simple et le plus sûr : on OUVRE en hyper gros plan sur
     lui (son visage remplit le cadre, expression déjà jouée = tension frame 0), puis
     on dézoome jusqu'à sa taille normale et la démonstration prend le relais.
     Aucun agent requis : le mouvement d'échelle accroche à lui seul. */
  var ZOOM_IN = 0.55, ZOOM_OUT = 1.35;
  MrDollar.prototype.hookZoom = function (u, spec) {
    var rest = spec.rest || { x: 180, y: 1430, h: 215 };
    var pose = spec.pose || (REACT[spec.reaction] && REACT[spec.reaction].pose) || 'oh';
    var k = eInOut(clamp((u - ZOOM_IN) / ZOOM_OUT, 0, 1));      // il tient d'abord, puis recule
    var h = lerp(1500, rest.h, k);
    var x = lerp(540, rest.x, k);
    var y = lerp(2560, rest.y, k);                              // pieds hors cadre -> le visage remplit
    var br = (1 - k) * (5 * Math.sin(u * 2.1) + 2 * Math.sin(u * 3.7));   // il respire, jamais figé
    this.draw(this.resolve(pose, spec.t), x + br, y, h, (spec.op == null ? 1 : spec.op), spec.flip, 0, 1, 1);
  };

  /* API PRINCIPALE — le gag d'ouverture de S1.
     spec = { primitive, agent:{x,y}, reaction, raccord, rest:{x,y,h}, h, flip,
              idle, verb, type }                                                */
  MrDollar.prototype.gag = function (u, spec) {
    spec = spec || {};
    this._t = spec.t;
    this._inGag = (u < HIT + RAC + HAND);                 // il encaisse : il ne parle pas
    if (spec.primitive === 'zoom') { this.hookZoom(u, spec); return; }
    // Le JSON écrit le raccord en clair ("il se relève et pointe le ?") : on le ramène à sa clé.
    var rk = String(spec.raccord || 'point').toLowerCase();
    spec.raccord = /point/.test(rk) ? 'point' : /écart|ecart/.test(rk) ? 'ecarte'
                 : /sol|reste au sol/.test(rk) ? 'sol' : /sort|cadre/.test(rk) ? 'sortie' : 'point';
    var a = spec.agent || { x: 540, y: 1400 };
    var r = REACT[spec.reaction] || REACT['sonné'];
    var rest = spec.rest || { x: 170, y: a.y, h: 232 };
    var h0 = spec.h || 262;
    var st, pose;

    if (P1[spec.primitive]) {                       // FAMILLE 1 — il subit
      st = P1[spec.primitive](u, a, r);
      var rise = clamp((u - HIT) / RAC, 0, 1);
      pose = (st.pose && rise < 0.5) ? st.pose : (rise < 0.5 ? r.pose : (RACCORD[spec.raccord] || 'point'));
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
      this.draw(this.resolve(pose, spec.t), lerp(x0, -240, hand), y0, h0, 1 - hand, spec.flip, st.rot, st.sx, st.sy);
      return;
    }
    // marque d'impact au point de contact tant que le choc dure : on VOIT ce qui l'a frappé
    if (P1[spec.primitive]) this._impact(a.x, a.y - 90, clamp(1 - u / (HIT * 1.2), 0, 1), (st.dx || 0) < 0 ? -1 : 1);
    var bx = a.x + (st.dx || 0), by = a.y + (st.dy || 0) + (st.bob || 0);
    // le raccord regarde vers la cible (spec.lookAt), sinon on garde spec.flip
    if (spec.lookAt != null) spec.flip = (spec.lookAt < bx);
    var px = lerp(bx, rest.x, hand), py = lerp(by, rest.y, hand), ph = lerp(h0, rest.h, hand);
    if (hand > 0.85) { px += 4 * Math.sin(u * 1.2) + 2 * Math.sin(u * 2.3); }   // vie continue une fois posé
    this._t = spec.t;
    var pf = this.resolve(hand > 0.6 ? (RACCORD[spec.raccord] || 'idle') : pose, spec.t);
    var o = (st.op == null ? 1 : st.op) * (spec.op == null ? 1 : spec.op);
    if (hand > 0.6) this.placeClear(pf, px, py, ph, o, spec.flip, st.rot);   // une fois la main passée : zéro chevauchement
    else this.placeClear(pf, px, py, ph, o, spec.flip, st.rot, { avoid: 'text' });  // pendant le choc : l'agent est la cible
  };

  root.MrDollar = {
    init: function (cfg) { return new MrDollar(cfg); },
    HIT: HIT, RAC: RAC, HAND: HAND,
    primitives: ['bumpInto', 'fall', 'hitBy', 'crushedBy', 'stretchedBy', 'vanishInto',
                 'gesture', 'idle', 'act', 'contrast']
  };
})(typeof window !== 'undefined' ? window : this);
