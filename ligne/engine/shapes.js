/* ============================================================================
   LA LIGNE — shapes.js — VOCABULAIRE VISUEL
   Silhouettes SVG paramétrables, style unifié (trait épais, 2D flat, lisible
   en 0,2s), couleur fonctionnelle you/them/neutre. Codée une fois, réutilisée
   partout. Le catalogue GROSSIT, il ne se réinvente jamais.

   API : Shapes.<type>(params) -> <g> SVG (caché, opacity 0), enfants dessinés
         en coordonnées absolues autour de params.at = [cx,cy] (défaut 540,1000).
         params.echelle = multiplicateur numérique de taille (le LAYOUT du moteur
         s'en sert pour réduire ce qui ne rentre pas). params.couleur/taille/label.
         Les verbes animent le <g> retourné (transforms).
   Dépend des globals du moteur : SVG.
   ============================================================================ */
const Shapes = (() => {
  const NSx = 'http://www.w3.org/2000/svg';
  const COL = { you: '#1E5F6E', them: '#8A5323', neutre: '#20242A', ink: '#20242A', paper: '#F2EFE7' };
  const col = c => COL[c] || COL.neutre;
  const E = (tag, a) => { const e = document.createElementNS(NSx, tag); for (const k in (a || {})) e.setAttribute(k, a[k]); return e; };
  const G = () => { const g = document.createElementNS(NSx, 'g'); g.setAttribute('opacity', '0'); SVG.appendChild(g); return g; };
  const stroke = (e, c, w) => { e.setAttribute('fill', 'none'); e.setAttribute('stroke', col(c)); e.setAttribute('stroke-width', w || 10); e.setAttribute('stroke-linecap', 'round'); e.setAttribute('stroke-linejoin', 'round'); return e; };
  const fill = (e, c) => { e.setAttribute('fill', col(c)); e.setAttribute('stroke', 'none'); return e; };
  const label = (g, text, cx, cy, c, fs) => {
    const t = E('text', { x: cx, y: cy, 'text-anchor': 'middle' });
    t.setAttribute('font-family', "'Helvetica Neue',Arial,sans-serif");
    t.setAttribute('font-weight', '800'); t.setAttribute('font-size', String(fs || 38)); t.setAttribute('letter-spacing', '1');
    t.setAttribute('fill', col(c)); t.textContent = String(text).toUpperCase(); g.appendChild(t); return t;
  };
  const TAILLE = { minuscule: 0.32, petite: 0.55, petit: 0.55, moyen: 1, moyenne: 1, grand: 1.5, grande: 1.5, totale: 1.9, enorme: 1.9 };
  const sz = (t, d, e) => (TAILLE[t] != null ? TAILLE[t] : (d != null ? d : 1)) * (e || 1);

  const S = {
    cercle({ at = [540, 1000], couleur = 'neutre', taille = 'moyen', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, r = 90 * sz(taille, 1, echelle), g = G();
      g.appendChild(stroke(E('circle', { cx, cy, r }), couleur, 10));
      if (lbl) label(g, lbl, cx, cy - r - 24, couleur);
      return g;
    },
    point({ at = [540, 1000], couleur = 'you', taille = 'moyen', echelle = 1 } = {}) {
      const [cx, cy] = at, g = G();
      g.appendChild(fill(E('circle', { cx, cy, r: 16 * sz(taille, 1, echelle) }), couleur));
      return g;
    },
    ligne({ at = [540, 1080], couleur = 'neutre', largeur = 720, echelle = 1 } = {}) {
      const [cx, cy] = at, w = largeur * (echelle || 1), g = G();
      g.appendChild(stroke(E('path', { d: `M ${cx - w / 2} ${cy} L ${cx + w / 2} ${cy}` }), couleur, 10));
      return g;
    },
    niveau({ at = [540, 1080], couleur = 'neutre', largeur = 720, echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, w = largeur * (echelle || 1), g = G();
      g.appendChild(stroke(E('path', { d: `M ${cx - w / 2} ${cy} L ${cx + w / 2} ${cy}` }), couleur, 10));
      if (lbl) label(g, lbl, cx, cy - 24, couleur);
      return g;
    },
    barre({ at = [540, 1000], couleur = 'neutre', orientation = 'verticale', taille = 'moyenne', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, g = G(), L = 240 * sz(taille, 1, echelle), th = 40 * (echelle || 1);
      const vert = orientation !== 'horizontale', w = vert ? th : L, h = vert ? L : th;
      g.appendChild(fill(E('rect', { x: cx - w / 2, y: cy - h / 2, width: w, height: h, rx: 6 }), couleur));
      if (lbl) label(g, lbl, cx, cy + h / 2 + 38, couleur);
      return g;
    },
    bloc({ at = [540, 1000], couleur = 'them', taille = 'moyen', orientation, echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, g = G(), s = 108 * sz(taille, 1, echelle);
      let w = s, h = s;
      if (orientation === 'horizontale') { w = s * 1.7; h = s * 0.62; }
      g.appendChild(fill(E('rect', { x: cx - w / 2, y: cy - h / 2, width: w, height: h, rx: 8 }), couleur));
      if (lbl) label(g, lbl, cx, cy + h / 2 + 38, couleur);
      return g;
    },
    colonne({ at = [540, 1200], couleur = 'you', taille = 'moyen', hauteur = 420, echelle = 1, label: lbl } = {}) {
      const [cx, by] = at, w = 140 * (echelle || 1), h = hauteur * sz(taille, 1, echelle), g = G();
      g.appendChild(fill(E('rect', { x: cx - w / 2, y: by - h, width: w, height: h, rx: 6 }), couleur));
      if (lbl) label(g, lbl, cx, by + 40, couleur);
      return g;
    },
    zone({ at = [540, 1000], couleur = 'them', largeur = 200, hauteur = 300, echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, w = largeur * (echelle || 1), h = hauteur * (echelle || 1), g = G();
      const r = fill(E('rect', { x: cx - w / 2, y: cy - h / 2, width: w, height: h, rx: 10 }), couleur);
      r.setAttribute('opacity', '0.26'); g.appendChild(r);
      if (lbl) label(g, lbl, cx, cy, couleur);
      return g;
    },
    courbe({ at = [540, 960], couleur = 'you', amplitude = 'moyenne', largeur = 340, echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, e = echelle || 1;
      const a = (amplitude === 'petite' ? 22 : amplitude === 'enorme' ? 160 : 80) * e, w = largeur * e, x0 = cx - w / 2, g = G();
      const d = `M ${x0} ${cy} L ${x0 + w * 0.2} ${cy - a} L ${x0 + w * 0.4} ${cy + a} L ${x0 + w * 0.6} ${cy - a} L ${x0 + w * 0.8} ${cy + a} L ${x0 + w} ${cy}`;
      g.appendChild(stroke(E('path', { d }), couleur, 7));
      if (lbl) label(g, lbl, cx, cy - a - 34, couleur);
      return g;
    },
    mot({ at = [540, 1000], couleur = 'neutre', texte = 'MOT', taille = 'moyen', echelle = 1 } = {}) {
      const [cx, cy] = at, g = G(), fs = 64 * sz(taille, 1, echelle);
      const t = E('text', { x: cx, y: cy, 'text-anchor': 'middle' });
      t.setAttribute('font-family', "'Helvetica Neue',Arial,sans-serif");
      t.setAttribute('font-weight', '800'); t.setAttribute('font-size', String(fs)); t.setAttribute('letter-spacing', '1');
      t.setAttribute('fill', col(couleur)); t.textContent = String(texte).toUpperCase(); g.appendChild(t);
      return g;
    },
    part({ at = [540, 1000], couleur = 'neutre', fraction = 'petite', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, f = fraction === 'petite' ? 0.3 : fraction === 'moyenne' ? 0.5 : 0.72;
      const s = (84 * f + 30) * (echelle || 1), g = G();
      g.appendChild(fill(E('rect', { x: cx - s / 2, y: cy - s / 2, width: s, height: s, rx: 8 }), couleur));
      if (lbl) label(g, lbl, cx, cy + s / 2 + 36, couleur);
      return g;
    },
    coffre({ at = [540, 1000], couleur = 'neutre', taille = 'moyen', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, s = sz(taille, 1, echelle), w = 170 * s, h = 150 * s, g = G();
      g.appendChild(stroke(E('rect', { x: cx - w / 2, y: cy - h / 2, width: w, height: h, rx: 12 }), couleur, 10));
      g.appendChild(stroke(E('circle', { cx, cy, r: 30 * s }), couleur, 9));
      g.appendChild(stroke(E('path', { d: `M ${cx} ${cy} L ${cx + 20 * s} ${cy - 20 * s}` }), couleur, 9));
      if (lbl) label(g, lbl, cx, cy + h / 2 + 36, couleur);
      return g;
    },
    levier({ at = [540, 1000], couleur = 'neutre', taille = 'moyen', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, s = sz(taille, 1, echelle), g = G();
      g.appendChild(fill(E('path', { d: `M ${cx} ${cy} L ${cx - 40 * s} ${cy + 66 * s} L ${cx + 40 * s} ${cy + 66 * s} Z` }), couleur));
      g.appendChild(stroke(E('path', { d: `M ${cx - 130 * s} ${cy + 38 * s} L ${cx + 130 * s} ${cy - 46 * s}` }), couleur, 12));
      g.appendChild(fill(E('circle', { cx: cx + 130 * s, cy: cy - 46 * s, r: 16 * s }), couleur));
      if (lbl) label(g, lbl, cx, cy + 66 * s + 40, couleur);
      return g;
    },
    main({ at = [540, 1000], couleur = 'you', taille = 'moyen', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, s = sz(taille, 1, echelle), g = G();
      g.appendChild(fill(E('rect', { x: cx - 44 * s, y: cy - 16 * s, width: 88 * s, height: 78 * s, rx: 20 }), couleur));
      for (let k = 0; k < 4; k++) g.appendChild(fill(E('rect', { x: cx - 33 * s + k * 22 * s - 8 * s, y: cy - 70 * s, width: 16 * s, height: 60 * s, rx: 8 }), couleur));
      g.appendChild(fill(E('rect', { x: cx - 62 * s, y: cy - 6 * s, width: 38 * s, height: 16 * s, rx: 8 }), couleur));
      if (lbl) label(g, lbl, cx, cy + 78 * s + 18, couleur);
      return g;
    },
    personnage({ at = [540, 1000], couleur = 'neutre', posture = 'debout', taille = 'moyen', echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, s = sz(taille, 1, echelle), g = G();
      g.appendChild(stroke(E('circle', { cx, cy: cy - 88 * s, r: 28 * s }), couleur, 10));
      let d;
      if (posture === 'tombe') d = `M ${cx - 18 * s} ${cy - 54 * s} L ${cx + 52 * s} ${cy + 4 * s} M ${cx + 8 * s} ${cy - 34 * s} L ${cx - 28 * s} ${cy - 62 * s} M ${cx + 52 * s} ${cy + 4 * s} L ${cx + 88 * s} ${cy - 16 * s} M ${cx + 52 * s} ${cy + 4 * s} L ${cx + 86 * s} ${cy + 32 * s}`;
      else if (posture === 'assis') d = `M ${cx} ${cy - 58 * s} L ${cx} ${cy} L ${cx + 50 * s} ${cy} L ${cx + 50 * s} ${cy + 48 * s} M ${cx} ${cy} L ${cx} ${cy + 48 * s} M ${cx} ${cy - 40 * s} L ${cx + 40 * s} ${cy - 28 * s}`;
      else if (posture === 'tetemains') d = `M ${cx} ${cy - 58 * s} L ${cx} ${cy + 28 * s} M ${cx} ${cy - 42 * s} L ${cx - 28 * s} ${cy - 78 * s} M ${cx} ${cy - 42 * s} L ${cx + 28 * s} ${cy - 78 * s} M ${cx} ${cy + 28 * s} L ${cx - 24 * s} ${cy + 86 * s} M ${cx} ${cy + 28 * s} L ${cx + 24 * s} ${cy + 86 * s}`;
      else d = `M ${cx} ${cy - 58 * s} L ${cx} ${cy + 28 * s} M ${cx} ${cy - 38 * s} L ${cx - 40 * s} ${cy - 12 * s} M ${cx} ${cy - 38 * s} L ${cx + 40 * s} ${cy - 12 * s} M ${cx} ${cy + 28 * s} L ${cx - 26 * s} ${cy + 88 * s} M ${cx} ${cy + 28 * s} L ${cx + 26 * s} ${cy + 88 * s}`;
      g.appendChild(stroke(E('path', { d }), couleur, 10));
      if (lbl) label(g, lbl, cx, cy + 124 * s, couleur);
      return g;
    },
    foule({ at = [540, 880], couleur = 'neutre', n = 12, echelle = 1, label: lbl } = {}) {
      const [cx, cy] = at, e = echelle || 1, g = G(), COLS = Math.min(n, 6);
      for (let k = 0; k < n; k++) {
        const c = k % COLS, r = (k / COLS) | 0, x = cx + (c - (COLS - 1) / 2) * 64 * e, y = cy + r * 84 * e;
        g.appendChild(stroke(E('circle', { cx: x, cy: y - 22 * e, r: 13 * e }), couleur, 7));
        g.appendChild(stroke(E('path', { d: `M ${x} ${y - 9 * e} L ${x} ${y + 28 * e} M ${x} ${y} L ${x - 16 * e} ${y + 13 * e} M ${x} ${y} L ${x + 16 * e} ${y + 13 * e}` }), couleur, 7));
      }
      if (lbl) label(g, lbl, cx, cy - 66 * e, couleur);
      return g;
    },
  };

  S._palette = COL; S._size = sz;
  return S;
})();
if (typeof window !== 'undefined') window.Shapes = Shapes;
