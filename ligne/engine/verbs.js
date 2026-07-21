/* ============================================================================
   LA LIGNE — verbs.js — GRAMMAIRE DU MOUVEMENT
   Chaque verbe = une physique PROUVÉE UNE FOIS, réutilisée partout.
   Une brique/scène ne code JAMAIS de mouvement : elle appelle des verbes.

   API : Verbs.<nom>(ctx, args) -> endTime (temps de fin, pour le chaînage)
     ctx = {
       tl,               // la timeline GSAP (paused, scrubbée par HyperFrames)
       ball,             // l'élément balle-pivot (un <circle>)
       PVT,              // { cx, cy } position logique courante de la balle
       ballX(), ballY(), // raccourcis lecture position balle
       setBall(x,y),     // met à jour PVT (à appeler après avoir bougé la balle)
     }
     args = objet déjà RÉSOLU par l'interpréteur (el|els, from, to, targets, t, dur, ...)

   Sources physiques (constantes identiques au code validé) :
     tomber/rebondir/rouler/faucher/grossir  <- balle L2 (index.html cascade/replay)
     naitre/deployer/absorber                <- test pivot (index_pivot.html, svgOrigin)
   Verbes neufs (définis une fois) : entrer, se_diviser, fusionner, se_retourner,
     se_derober, barrer, ecrire, pulser, arreter, poser, tracer, immobiliser.
   ============================================================================ */
const Verbs = (() => {
  const YOU = '#1E5F6E', THEM = '#8A5323', INK = '#20242A';
  const isBall = (ctx, el) => el === ctx.ball;

  const V = {

    /* ---- NAÎTRE : un élément se détache d'un point et grandit (svgOrigin) ---- */
    naitre(ctx, { el, from, t, dur = 0.45, ease = 'back.out(1.4)' }) {
      const [fx, fy] = from || [ctx.ballX(), ctx.ballY()];
      ctx.tl.set(el, { autoAlpha: 1, svgOrigin: `${fx} ${fy}`, scale: 0.001 }, t);
      ctx.tl.to(el, { scale: 1, duration: dur, ease }, t);
      return t + dur;
    },

    /* ---- DÉPLOYER : plusieurs éléments naissent de la balle, décalés ---- */
    deployer(ctx, { els, t, dur = 0.45, stagger = 0.12, from }) {
      const src = from || [ctx.ballX(), ctx.ballY()];
      els.forEach((el, k) => V.naitre(ctx, { el, from: src, t: t + stagger * k, dur }));
      return t + stagger * Math.max(0, els.length - 1) + dur;
    },

    /* ---- ABSORBER : les éléments se rétractent dans la balle (collapse) ---- */
    absorber(ctx, { els, t, dur = 0.4, stagger = 0.03, into }) {
      const [tx, ty] = into || [ctx.ballX(), ctx.ballY()];
      els.forEach((el, k) => {
        const tt = t + stagger * k;
        ctx.tl.to(el, { scale: 0.001, svgOrigin: `${tx} ${ty}`, duration: dur, ease: 'power2.in' }, tt);
        ctx.tl.set(el, { autoAlpha: 0 }, tt + dur + 0.001);
      });
      return t + stagger * Math.max(0, els.length - 1) + dur;
    },

    /* ---- ENTRER : arrive d'un bord du cadre, décélère ---- */
    entrer(ctx, { el, edge = 'left', dist = 320, t, dur = 0.6, ease = 'power2.out' }) {
      const dx = edge === 'left' ? -dist : edge === 'right' ? dist : 0;
      const dy = edge === 'top' ? -dist : edge === 'bottom' ? dist : 0;
      ctx.tl.set(el, { autoAlpha: 1, x: dx, y: dy }, t);
      ctx.tl.to(el, { x: 0, y: 0, duration: dur, ease }, t);
      return t + dur;
    },

    /* ---- TOMBER : chute avec gravité réelle (power4.in) ---- */
    tomber(ctx, { el, toY, by, t, dur = 0.32, ease = 'power4.in' }) {
      const e = el || ctx.ball;
      if (isBall(ctx, e)) {                       // balle = circle, attr cy (physique L2 exacte)
        ctx.tl.to(e, { attr: { cy: toY }, duration: dur, ease }, t);
        ctx.setBall(ctx.ballX(), toY);
      } else {                                    // élément générique = translation y
        ctx.tl.to(e, { y: `+=${by != null ? by : 420}`, duration: dur, ease }, t);
      }
      return t + dur;
    },

    /* ---- REBONDIR : n rebonds pleine hauteur décroissants (balle) ---- */
    rebondir(ctx, { topY, botY, t, n = 1, until, period = 0.55, upDur = 0.30, downDur = 0.25 }) {
      const ball = ctx.ball;
      const top = topY != null ? topY : ctx.ballY() - 120;
      const bot = botY != null ? botY : ctx.ballY();
      let bt = t, count = 0;
      const stop = until != null ? until : t + n * period;
      while (bt < stop - period + 0.001) {
        ctx.tl.to(ball, { attr: { cy: top }, duration: upDur, ease: 'power2.out' }, bt)
              .to(ball, { attr: { cy: bot }, duration: downDur, ease: 'power2.in' }, bt + upDur);
        bt += period; count++;
      }
      ctx.setBall(ctx.ballX(), bot);
      return bt;
    },

    /* ---- ROULER : suit une trajectoire, vitesse constante (ease none) ---- */
    rouler(ctx, { el, toX, toY, t, dur = 0.8, ease = 'none' }) {
      const e = el || ctx.ball;
      const attrs = { cx: toX };
      if (toY != null) attrs.cy = toY;
      ctx.tl.to(e, { attr: attrs, duration: dur, ease }, t);
      if (isBall(ctx, e)) ctx.setBall(toX, toY != null ? toY : ctx.ballY());
      return t + dur;
    },

    /* ---- FAUCHER : la balle plonge puis balaie ; chaque cible tombe AU CONTACT ---- */
    faucher(ctx, { targets, fromX, toX, rowY, t, diveDur = 0.42, dur = 1.0, fallColor = THEM }) {
      const ball = ctx.ball, N = targets.length;
      ctx.tl.to(ball, { attr: { cx: fromX, cy: rowY }, duration: diveDur, ease: 'power3.in' }, t); // plongée en rampe
      const rollStart = t + diveDur;
      ctx.tl.to(ball, { attr: { cx: toX, cy: rowY }, duration: dur, ease: 'none' }, rollStart);    // roule vitesse constante
      ctx.setBall(toX, rowY);
      targets.forEach((m, k) => {                                    // contact réel : tk = roll + k/N·dur
        const tk = rollStart + (k / N) * dur;
        ctx.tl.to(m, { fill: fallColor, y: '+=340', autoAlpha: 0, duration: 0.26, ease: 'power4.in' }, tk);
      });
      return rollStart + dur;
    },

    /* ---- GROSSIR : croissance continue sur toute la fenêtre ---- */
    grossir(ctx, { el, toBox, fromBox, ratio, t, dur = 1.4, ease = 'power1.inOut' }) {
      if (toBox) {                                                   // rect : croît vers une boîte (scale archetype)
        if (fromBox) ctx.tl.fromTo(el, { attr: fromBox }, { attr: toBox, duration: dur, ease }, t);
        else ctx.tl.to(el, { attr: toBox, duration: dur, ease }, t);
      } else {                                                       // scale par ratio
        ctx.tl.set(el, { transformOrigin: '50% 50%', autoAlpha: 1 }, t);
        ctx.tl.to(el, { scale: ratio || 2, duration: dur, ease }, t);
      }
      return t + dur;
    },

    /* ---- SE_DIVISER : un élément devient n (les copies naissent de son centre) ---- */
    se_diviser(ctx, { el, into, from, t, dur = 0.5 }) {
      const src = from || [ctx.ballX(), ctx.ballY()];
      if (el) ctx.tl.to(el, { autoAlpha: 0, duration: 0.2, ease: 'power2.in' }, t); // l'original s'efface
      into.forEach((c, k) => V.naitre(ctx, { el: c, from: src, t: t + 0.08 + 0.06 * k, dur }));
      return t + 0.08 + 0.06 * Math.max(0, into.length - 1) + dur;
    },

    /* ---- FUSIONNER : n éléments convergent vers un point et deviennent un ---- */
    fusionner(ctx, { els, to, result, t, dur = 0.45 }) {
      const [tx, ty] = to || [ctx.ballX(), ctx.ballY()];
      els.forEach((e) => {
        ctx.tl.to(e, { scale: 0.001, svgOrigin: `${tx} ${ty}`, duration: dur, ease: 'power2.in' }, t);
        ctx.tl.set(e, { autoAlpha: 0 }, t + dur + 0.001);
      });
      if (result) V.naitre(ctx, { el: result, from: [tx, ty], t: t + dur * 0.7, dur: 0.4 });
      return t + dur + 0.3;
    },

    /* ---- SE_RETOURNER : flip, révèle l'autre face ---- */
    se_retourner(ctx, { el, back, t, dur = 0.5 }) {
      ctx.tl.set(el, { transformOrigin: '50% 50%' }, t);
      ctx.tl.to(el, { scaleX: 0, duration: dur / 2, ease: 'power2.in' }, t);
      ctx.tl.set(el, { autoAlpha: 0 }, t + dur / 2);
      if (back) {
        ctx.tl.set(back, { autoAlpha: 1, transformOrigin: '50% 50%', scaleX: 0 }, t + dur / 2);
        ctx.tl.to(back, { scaleX: 1, duration: dur / 2, ease: 'power2.out' }, t + dur / 2);
      }
      return t + dur;
    },

    /* ---- SE_DÉROBER : le support disparaît sous l'élément, qui tombe ---- */
    se_derober(ctx, { support, el, toY, t, dur = 0.5 }) {
      ctx.tl.to(support, { autoAlpha: 0, duration: 0.2, ease: 'power2.in' }, t);
      V.tomber(ctx, { el, toY, by: toY == null ? 460 : undefined, t: t + 0.08, dur, ease: 'power4.in' });
      return t + 0.08 + dur;
    },

    /* ---- BARRER : annulé — marqué d'une croix puis chute hors cadre ---- */
    barrer(ctx, { el, cross, t, dur = 0.5, color = THEM }) {
      ctx.tl.to(el, { fill: color, stroke: color, duration: 0.15 }, t);
      if (cross) V.naitre(ctx, { el: cross, from: null, t, dur: 0.2 });
      ctx.tl.to(el, { y: '+=440', autoAlpha: 0, duration: dur, ease: 'power4.in' }, t + 0.18);
      if (cross) ctx.tl.to(cross, { y: '+=440', autoAlpha: 0, duration: dur, ease: 'power4.in' }, t + 0.18);
      return t + 0.18 + dur;
    },

    /* ---- ÉCRIRE : du texte apparaît (mot à mot sur la voix, ou d'un coup) ---- */
    // args.words = [{el, t}] déjà résolus (un el par mot, avec son temps de sync) OU {el, t}
    ecrire(ctx, { words, el, t, wordDur = 0.16 }) {
      if (words && words.length) {
        let end = t;
        words.forEach((w) => {
          ctx.tl.fromTo(w.el, { autoAlpha: 0, scale: 0.8, transformOrigin: '50% 50%' },
            { autoAlpha: 1, scale: 1, duration: wordDur, ease: 'back.out(2)' }, w.t);
          end = Math.max(end, w.t + wordDur);
        });
        return end;
      }
      ctx.tl.fromTo(el, { autoAlpha: 0, scale: 0.85, transformOrigin: '50% 50%' },
        { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'back.out(1.8)' }, t);
      return t + 0.3;
    },

    /* ---- PULSER : une pulsation UNIQUE d'emphase (pas d'oscillation décorative) ---- */
    pulser(ctx, { el, t, amp = 1.09, dur = 0.42 }) {
      ctx.tl.set(el, { transformOrigin: '50% 50%' }, t);
      ctx.tl.to(el, { scale: amp, duration: dur * 0.4, ease: 'sine.out' }, t)
            .to(el, { scale: 1, duration: dur * 0.6, ease: 'sine.inOut' }, t + dur * 0.4);
      return t + dur;
    },

    /* ---- ARRÊTER : l'élément décélère et s'immobilise sur une cible ---- */
    arreter(ctx, { el, toY, toX, t, dur = 0.5, ease = 'power3.out' }) {
      const e = el || ctx.ball;
      const attrs = {};
      if (isBall(ctx, e)) {
        if (toX != null) attrs.cx = toX;
        if (toY != null) attrs.cy = toY;
        ctx.tl.to(e, { attr: attrs, duration: dur, ease }, t);
        ctx.setBall(toX != null ? toX : ctx.ballX(), toY != null ? toY : ctx.ballY());
      } else {
        const to = {};
        if (toX != null) to.x = toX; if (toY != null) to.y = toY;
        ctx.tl.to(e, to.x != null || to.y != null ? { ...to, duration: dur, ease } : { attr: { cy: toY }, duration: dur, ease }, t);
      }
      return t + dur;
    },

    /* ---- POSER : la balle se pose délicatement sur un support (petit rebond d'atterrissage) ---- */
    poser(ctx, { toX, toY, t, dur = 0.5 }) {
      const ball = ctx.ball;
      const x = toX != null ? toX : ctx.ballX();
      ctx.tl.to(ball, { attr: { cx: x, cy: toY }, duration: dur, ease: 'power2.in' }, t);       // descend
      ctx.tl.to(ball, { attr: { cy: toY - 26 }, duration: 0.12, ease: 'power2.out' }, t + dur)  // micro-rebond
            .to(ball, { attr: { cy: toY }, duration: 0.14, ease: 'power2.in' });
      ctx.setBall(x, toY);
      return t + dur + 0.26;
    },

    /* ---- TRACER : une main tire un trait vers une cible (draw-on du trait) ---- */
    // args.stroke = un <path> armé (arm()) reliant main -> cible ; hand suit la fin du trait
    tracer(ctx, { stroke, hand, t, dur = 0.7, ease = 'power1.inOut' }) {
      if (stroke) {
        ctx.tl.set(stroke, { autoAlpha: 1 }, t);
        ctx.tl.fromTo(stroke, { strokeDashoffset: stroke.__L || 0 },
          { strokeDashoffset: 0, duration: dur, ease }, t);
      }
      return t + dur;
    },

    /* ---- IMMOBILISER : l'élément se fige définitivement (beat de clôture) ---- */
    immobiliser(ctx, { el, t, dur = 0.4 }) {
      const e = el || ctx.ball;
      ctx.tl.set(e, { transformOrigin: '50% 50%' }, t);
      ctx.tl.to(e, { scale: 1.12, duration: dur * 0.45, ease: 'power2.out' }, t)
            .to(e, { scale: 1, duration: dur * 0.55, ease: 'power2.inOut' }, t + dur * 0.45);
      return t + dur;
    },

  };
  return V;
})();
if (typeof window !== 'undefined') window.Verbs = Verbs;
