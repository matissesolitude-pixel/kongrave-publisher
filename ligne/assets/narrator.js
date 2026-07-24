/* ═══════════════════════════════════════════════════════════════════════════
   MR DOLLAR — NARRATEUR (simple)
   Codé UNE fois, branché sur chaque épisode. Aucun sur-mesure par Reel.

   DOCTRINE (arrêtée le 24/07/2026) :
   · PAS DE GAG. Il n'y a plus de primitives, d'agent, de réaction ni de
     raccord. Mr Dollar APPARAÎT POUR PARLER, quand le moteur le décide,
     puis il s'efface. C'est tout. Le trop-plein d'options rendait chaque
     épisode illisible ; on garde ce qui marche.
   · Ce qui reste, et qui est NON NÉGOCIABLE :
       1. ZÉRO CHEVAUCHEMENT — il cherche une zone libre, rétrécit, ou
          disparaît. Le schéma prime toujours sur lui (placeClear).
       2. DÉPLACEMENT MARCHÉ — il glisse à vitesse de marche et on le VOIT
          marcher, jamais de téléportation ni de saccade.
       3. LIP-SYNC — sa bouche suit l'amplitude de la voix, avec hystérésis
          (sinon les yeux convulsent). Muet = bouche au repos.
       4. POSES QUI VEULENT DIRE QUELQUE CHOSE — routines d'intentions, pas
          de pointage en boucle.
       5. IL REGARDE ET POINTE DU BON CÔTÉ — `pointAt` calcule le sens.
   · Il est PETIT, en ENCRE #20242A, jamais en teal. Il n'apparaît PAS en S4.
   · GARDE-FOU IMAGERIE : aucun accessoire guru (cigare, liasses, luxe) sauf
     ironie explicite — la retenue fait la crédibilité de la marque.

   USAGE dans un moteur :
     // il entre et il parle (u = temps local de l'apparition)
     MrD.enter(u, {t:t, rest:{x:180, y:1430, h:220}, routine:'explique'});
     // il désigne quelque chose de précis
     MrD.enter(u, {t:t, rest:{x:180, y:1430, h:220}, routine:'designe', lookAt:820});
     // ailleurs : MrD.hide();
   ═══════════════════════════════════════════════════════════════════════════ */
(function (root) {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };

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

  /* ── SYNCHRO LABIALE ─────────────────────────────────────────────────────
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

  /* ── LES YEUX : CLIGNEMENT ───────────────────────────────────────────────
     YEUX OUVERTS = ON NE TOUCHE À RIEN. Le dessin d'origine est le bon ; le
     recouvrir donnait un regard inquiétant. On n'intervient QUE le temps du
     clignement, où l'on pose une paupière par-dessus. */
  MrDollar.prototype.setEyes = function (map) { this.eyeMap = map || {}; };
  MrDollar.prototype._blink = function (t) {
    // deux périodes premières entre elles -> jamais métronomique, mais déterministe
    var a = (t / 3.7) % 1, b = (t / 5.3) % 1;
    var d = 0.038;                                  // ~0.14 s de fermeture
    return (a < d || b < d) ? 1 : 0;
  };
  MrDollar.prototype._drawEyes = function (pose, t) {
    var E = this.eyeMap && this.eyeMap[pose];
    if (!this.eyeG) { this.eyeG = document.createElementNS(NS, 'g'); this.g.appendChild(this.eyeG); }
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
  MrDollar.prototype._obstacles = function () {
    var svg = this.g.ownerSVGElement || this.g.parentNode, out = [];
    if (!svg || !svg.querySelectorAll) return out;
    var els = svg.querySelectorAll('rect,circle,ellipse,line,polyline,polygon,path,text,image');
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
  MrDollar.prototype._bestSpot = function (pose, x, y, h, op, flip, rot) {
    var obs = this._obstacles();
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
  MrDollar.prototype.placeClear = function (pose, x, y, h, op, flip, rot) {
    var t = this._t || 0;
    var dt = (this._lastT == null) ? 0.033 : Math.min(0.2, Math.max(0.001, t - this._lastT));
    this._lastT = t;
    var tgt = this._bestSpot(pose, x, y, h, op, flip, rot);
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
     Chaque pose est une INTENTION, pas une variation décorative. Le pointage est
     RARE : il ne sert qu'au moment où il désigne vraiment. */
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

  MrDollar.prototype.show = function (pose, x, y, h, op, flip) { this.draw(pose, x, y, h, op, flip, 0, 1, 1); };
  MrDollar.prototype.hide = function () { this.g.setAttribute('opacity', '0'); };

  /* ── API PRINCIPALE : IL APPARAÎT POUR PARLER ────────────────────────────
     C'est la SEULE façon de le faire entrer en scène. Il arrive en fondu, se
     place dans une zone libre (en marchant si besoin), enchaîne les poses de sa
     routine et sa bouche suit la voix.
       u    = temps local de l'apparition (0 = il arrive)
       spec = { t, rest:{x,y,h}, routine, lookAt, op, flip }
              lookAt = abscisse de ce qu'il désigne (il se tourne vers elle)  */
  MrDollar.prototype.enter = function (u, spec) {
    spec = spec || {};
    this._t = spec.t;
    var rest = spec.rest || { x: 180, y: 1430, h: 220 };
    var op = (spec.op == null ? 1 : spec.op) * clamp(u / 0.45, 0, 1);   // fondu d'arrivée
    if (op <= 0.02) { this.hide(); return; }
    // respiration : il est vivant même immobile (deux harmoniques, jamais figé)
    var br = 4 * Math.sin(u * 1.15) + 2 * Math.sin(u * 2.27);
    var base = this.seq(u, spec.routine || 'explique', true);
    if (spec.lookAt != null)
      this.pointAt(base, spec.t, rest.x + br, rest.y, rest.h, op, spec.lookAt);
    else
      this.say(base, spec.t, rest.x + br, rest.y, rest.h, op, !!spec.flip);
  };
  /* Compatibilité : les moteurs écrits du temps des gags appellent encore .gag().
     Les champs de gag (primitive / agent / reaction / raccord) sont IGNORÉS —
     il arrive simplement et il parle. */
  MrDollar.prototype.gag = function (u, spec) { this.enter(u, spec); };

  root.MrDollar = { init: function (cfg) { return new MrDollar(cfg); } };
})(typeof window !== 'undefined' ? window : this);
