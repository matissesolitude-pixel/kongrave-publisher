#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""empty_legs.py — Cockpit des alertes empty legs (vols de repositionnement).

Source de vérité : `destinations.json` (12 destinations, codes aéroports, saisons,
fourchettes de prix) et `plateformes.json` (où poser les alertes et comment).

Le script ne réserve rien et n'interroge aucune API : il produit ce qui manque
réellement quand on met en place une veille — la fiche de configuration à recopier
dans chaque formulaire d'alerte, le tableau des routes, la checklist du jour, et un
tableau de bord HTML consultable sur mobile.

Commandes :
  routes                  tableau des routes (densité, saison, prix, décote cible)
  alertes [--plateforme]  fiches de configuration plateforme par plateforme
  veille  [--telegram]    checklist du jour : destinations en saison + fenêtre J-2/J-1
  dashboard [--out]       génère le tableau de bord HTML

Exemples :
  python empty_legs/empty_legs.py routes
  python empty_legs/empty_legs.py alertes --plateforme xo
  python empty_legs/empty_legs.py veille --telegram
  python empty_legs/empty_legs.py dashboard --out output/empty_legs.html
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parent

DESTINATIONS_JSON = BASE_DIR / "destinations.json"
PLATEFORMES_JSON = BASE_DIR / "plateformes.json"

MOIS_COURTS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
MOIS_NOMS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

# Fenêtre où tombent les vraies décotes : l'opérateur cherche à amortir son carburant.
FENETRE_VEILLE_JOURS = (1, 2)


def charger():
    """Retourne (meta, destinations, plateformes)."""
    dest = json.load(open(DESTINATIONS_JSON, encoding="utf-8"))
    plat = json.load(open(PLATEFORMES_JSON, encoding="utf-8"))
    return dest["_meta"], dest["destinations"], plat["plateformes"]


def eur(montant):
    """12500 -> '12 500 €' (espace insécable fine, lisible en terminal comme en HTML)."""
    return f"{montant:,}".replace(",", " ") + " €"


def duree(heures):
    """1.25 -> '1 h 15' ; 6.5 -> '6 h 30' ; 11 -> '11 h'."""
    h, m = int(heures), round((heures - int(heures)) * 60)
    return f"{h} h" if m == 0 else f"{h} h {m:02d}"


def tronque(texte, largeur):
    return texte if len(texte) <= largeur else texte[: largeur - 1] + "…"


def fourchette(bornes):
    return "—" if not bornes else f"{eur(bornes[0])} – {eur(bornes[1])}"


def decote(dest):
    """Décote cible en % entre le milieu de la fourchette charter et celui de l'empty leg."""
    charter, el = dest.get("prix_charter_eur"), dest.get("prix_empty_leg_eur")
    if not charter or not el:
        return None
    mid_c = (charter[0] + charter[1]) / 2
    mid_e = (el[0] + el[1]) / 2
    return round((1 - mid_e / mid_c) * 100)


def codes(dest, separateur=" / "):
    return separateur.join(
        a["iata"] if a["iata"] != "—" else a["oaci"] for a in dest["aeroports"]
    )


def en_saison(dest, mois):
    return mois in dest["mois_forts"]


# --------------------------------------------------------------------------- routes


def cmd_routes(args):
    meta, destinations, _ = charger()
    mois = args.mois or date.today().month

    print(f"\nROUTES EMPTY LEGS — {len(destinations)} destinations")
    print(f"Base de départ : {meta['bases_depart']['principale'][0]['nom']} "
          f"(+ rayon élargi GVA / NCE / BRU / LUX)")
    print(f"Repère de saison : {MOIS_NOMS[mois - 1]}\n")

    ligne = "{:<24} {:<31} {:<9} {:<21} {:<21} {:>7}"
    print(ligne.format("DESTINATION", "AÉROPORTS", "DENSITÉ", "CHARTER PLEIN", "CIBLE EMPTY LEG", "DÉCOTE"))
    print("-" * 119)
    for d in sorted(destinations, key=lambda x: -x["densite_empty_legs"]):
        pts = "●" * d["densite_empty_legs"] + "·" * (5 - d["densite_empty_legs"])
        marque = " ◂ en saison" if en_saison(d, mois) else ""
        dec = decote(d)
        print(ligne.format(
            tronque(d["nom"] + marque, 24),
            tronque(codes(d), 31),
            pts,
            fourchette(d.get("prix_charter_eur")),
            fourchette(d.get("prix_empty_leg_eur")),
            f"-{dec} %" if dec else "—",
        ))
    print("\nDensité = épaisseur réelle de l'offre d'empty legs (5 = flux quotidien, 0 = marché fermé).")
    print("Prix indicatifs : le prix affiché par l'opérateur fait toujours foi.\n")

    for d in destinations:
        if d["densite_empty_legs"] == 0:
            print(f"! {d['nom']} — marché fermé aux opérateurs occidentaux : aucune alerte à poser.")
        elif d["densite_empty_legs"] == 1:
            print(f"! {d['nom']} — densité quasi nulle : poser l'alerte, ne rien attendre.")
    print()


# -------------------------------------------------------------------------- alertes


def cmd_alertes(args):
    _, destinations, plateformes = charger()
    if args.plateforme:
        plateformes = [p for p in plateformes if p["id"] == args.plateforme]
        if not plateformes:
            sys.exit(f"Plateforme inconnue. Choix : {', '.join(p['id'] for p in charger()[2])}")

    for p in plateformes:
        couvertes = [d for d in destinations if p["id"] in d["plateformes_prioritaires"]]
        print("\n" + "=" * 78)
        print(f"{p['nom'].upper()}  —  priorité {p['priorite']}  —  {p['type']}")
        print("=" * 78)
        print(f"Coût     : {p['cout']}")
        print(f"Alerte   : {p['canal_alerte']} ({p['granularite']})")
        print(f"Zone     : {p['zone_forte']}")
        print("\nMise en place :")
        for i, etape in enumerate(p["configuration"], 1):
            print(f"  {i}. {etape}")
        print(f"\nRoutes à saisir sur cette plateforme ({len(couvertes)}) :")
        for d in couvertes:
            print(f"  □ Paris LBG (rayon 300 km)  ->  {d['nom']:<22} {codes(d)}")
            print(f"      dates ouvertes · plafond {fourchette(d.get('prix_empty_leg_eur'))}")
        print(f"\nForce  : {p['forces']}")
        print(f"Limite : {p['limites']}")
    print()


# --------------------------------------------------------------------------- veille


def texte_veille(mois=None):
    """Checklist du jour : ce qui est réellement en saison, et le geste à faire."""
    _, destinations, _ = charger()
    mois = mois or date.today().month
    actives = [d for d in destinations if en_saison(d, mois) and d["densite_empty_legs"] >= 2]
    actives.sort(key=lambda d: -d["densite_empty_legs"])

    lignes = [f"VEILLE EMPTY LEGS — {MOIS_NOMS[mois - 1]}", ""]
    lignes.append(f"{len(actives)} destinations alimentées ce mois-ci :")
    for d in actives:
        dec = decote(d)
        lignes.append(
            f"  • {d['nom']} ({codes(d, ' ')}) — viser {fourchette(d.get('prix_empty_leg_eur'))}"
            + (f", soit -{dec} %" if dec else "")
        )
    lignes += [
        "",
        f"Fenêtre chaude : J-{FENETRE_VEILLE_JOURS[1]} à J-{FENETRE_VEILLE_JOURS[0]} avant décollage.",
        "C'est là que tombent les vraies décotes, quand l'opérateur cherche à amortir son carburant.",
        "",
        "Geste du jour :",
        "  1. Ouvrir la carte Welojets et l'app PrivateFly (vue des jets positionnés autour de Paris).",
        "  2. Vérifier que les notifications push XO sont toujours actives (elles sautent aux mises à jour).",
        "  3. Sur toute offre retenue : confirmer le plan B commercial AVANT de payer.",
    ]
    hors_saison = [d["nom"] for d in destinations if not en_saison(d, mois) and d["densite_empty_legs"] >= 1]
    if hors_saison:
        lignes += ["", "Hors saison ce mois-ci (alerte posée, rendement quasi nul) : " + ", ".join(hors_saison) + "."]
    return "\n".join(lignes)


def cmd_veille(args):
    message = texte_veille(args.mois)
    print("\n" + message + "\n")
    if args.telegram:
        sys.path.insert(0, str(ROOT))
        import notify  # réutilise le canal Telegram déjà configuré pour le pipeline

        print("[veille] envoi Telegram :", "OK" if notify.send(message) else "échec (voir stderr)")


# ------------------------------------------------------------------------ dashboard

CSS = """
:root{
  --ground:#ECEFEE; --surface:#FFFFFF; --surface-2:#F4F7F6; --line:#D2DAD8;
  --ink:#111A1C; --ink-2:#4C5B5C; --ink-3:#758586;
  --accent:#1C5F63; --accent-soft:#DBE9E8;
  --go:#2C6E4E; --tiede:#8C6712; --stop:#93392B;
  --shadow:0 1px 2px rgba(17,26,28,.06), 0 8px 24px -18px rgba(17,26,28,.35);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0D1315; --surface:#151E20; --surface-2:#1A2528; --line:#293639;
    --ink:#E7EEEC; --ink-2:#A2B2B2; --ink-3:#7D8E8E;
    --accent:#63C0BF; --accent-soft:#123033;
    --go:#63B189; --tiede:#D0A63E; --stop:#D4715E;
    --shadow:0 1px 2px rgba(0,0,0,.5), 0 10px 28px -20px rgba(0,0,0,.9);
  }
}
:root[data-theme="dark"]{
  --ground:#0D1315; --surface:#151E20; --surface-2:#1A2528; --line:#293639;
  --ink:#E7EEEC; --ink-2:#A2B2B2; --ink-3:#7D8E8E;
  --accent:#63C0BF; --accent-soft:#123033;
  --go:#63B189; --tiede:#D0A63E; --stop:#D4715E;
  --shadow:0 1px 2px rgba(0,0,0,.5), 0 10px 28px -20px rgba(0,0,0,.9);
}
*{box-sizing:border-box}
body{
  background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  font-size:15px; line-height:1.55; margin:0;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:900px; margin:0 auto; padding:28px 18px 72px; display:flex; flex-direction:column; gap:26px}
.wrap > *, section > *, .strip > *, .data > *{min-width:0}
.scroll{min-width:0; max-width:100%}
h1,h2,h3{font-family:Archivo,"IBM Plex Sans",system-ui,sans-serif; text-wrap:balance; margin:0}
h1{font-size:clamp(28px,6vw,44px); font-weight:700; letter-spacing:-.022em; line-height:1.04}
h2{font-size:19px; font-weight:700; letter-spacing:-.01em}
h3{font-size:17px; font-weight:600; letter-spacing:-.005em}
p{margin:0}
.eyebrow{
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px; font-weight:500;
  letter-spacing:.16em; text-transform:uppercase; color:var(--accent);
}
.sub{color:var(--ink-2); max-width:62ch}
header.page{display:flex; flex-direction:column; gap:12px; padding-bottom:4px; border-bottom:2px solid var(--ink); }
.regles{display:grid; gap:10px; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); margin-top:6px}
.regle{background:var(--surface); border:1px solid var(--line); border-radius:3px; padding:12px 14px; box-shadow:var(--shadow)}
.regle b{display:block; font-family:Archivo,sans-serif; font-size:14px; margin-bottom:3px}
.regle span{color:var(--ink-2); font-size:13.5px}
section{display:flex; flex-direction:column; gap:14px}
.section-head{display:flex; align-items:baseline; justify-content:space-between; gap:12px; flex-wrap:wrap;
  border-bottom:1px solid var(--line); padding-bottom:8px}
.strip{
  background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--ink-3);
  border-radius:3px; padding:16px 16px 14px; box-shadow:var(--shadow);
  display:flex; flex-direction:column; gap:12px;
}
.strip[data-actif="1"]{border-left-color:var(--accent)}
.strip[data-densite="0"]{border-left-color:var(--stop)}
.strip-head{display:flex; align-items:flex-start; justify-content:space-between; gap:12px; flex-wrap:wrap}
.strip-head .zone{color:var(--ink-3); font-size:12.5px; font-family:"IBM Plex Mono",monospace; letter-spacing:.04em}
.pills{display:flex; gap:6px; flex-wrap:wrap; align-items:center}
.pill{
  font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.06em; text-transform:uppercase;
  border:1px solid var(--line); border-radius:2px; padding:3px 7px; color:var(--ink-2); background:var(--surface-2);
  white-space:nowrap;
}
.pill.saison{border-color:var(--accent); color:var(--accent); background:var(--accent-soft)}
.pill.stop{border-color:var(--stop); color:var(--stop); background:transparent}
.codes{display:flex; gap:6px; flex-wrap:wrap}
.code{
  font-family:"IBM Plex Mono",monospace; font-size:12.5px; font-weight:500;
  background:var(--surface-2); border:1px solid var(--line); border-radius:2px; padding:4px 8px;
  display:flex; gap:7px; align-items:baseline;
}
.code b{color:var(--ink); letter-spacing:.05em}
.code i{font-style:normal; color:var(--ink-3); font-size:11.5px}
.data{display:grid; gap:14px; grid-template-columns:1fr; align-items:end}
@media(min-width:620px){ .data{grid-template-columns:minmax(0,1fr) minmax(0,1.15fr)} }
.meter-label{
  font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--ink-3); margin-bottom:6px; display:block;
}
.seg{display:flex; gap:4px}
.seg i{height:7px; flex:1; background:var(--line); border-radius:1px}
.seg i.on{background:var(--accent)}
.strip[data-densite="0"] .seg i.on{background:var(--stop)}
.prix{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; font-variant-numeric:tabular-nums}
.prix .cible{font-family:Archivo,sans-serif; font-size:19px; font-weight:700; letter-spacing:-.01em}
.prix .barre{color:var(--ink-3); font-size:12.5px}
.prix .dec{
  font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:500; color:var(--go);
  border:1px solid currentColor; border-radius:2px; padding:2px 6px;
}
.mois{display:flex; gap:3px}
.mois-bloc{margin-top:12px}
.mois span{
  flex:1; text-align:center; font-family:"IBM Plex Mono",monospace; font-size:10px; padding:3px 0;
  color:var(--ink-3); background:var(--surface-2); border-radius:1px; border:1px solid transparent;
}
.mois span.on{background:var(--accent-soft); color:var(--accent); font-weight:600}
.mois span.now{border-color:var(--ink); color:var(--ink)}
.mois span.on.now{border-color:var(--accent)}
dl.faits{display:grid; grid-template-columns:1fr; gap:2px 14px; margin:0; font-size:13.5px; overflow-wrap:anywhere}
@media(min-width:560px){ dl.faits{grid-template-columns:minmax(88px,auto) minmax(0,1fr); gap:5px 14px} }
dl.faits dd{min-width:0}
dl.faits dt{
  font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.12em; text-transform:uppercase;
  color:var(--ink-3); padding-top:3px;
}
dl.faits dd{margin:0; color:var(--ink-2)}
dl.faits dd b{color:var(--ink); font-weight:600}
.note{
  font-size:13.5px; color:var(--ink-2); background:var(--surface-2); border-left:2px solid var(--accent);
  padding:9px 12px; border-radius:0 2px 2px 0;
}
.strip[data-densite="0"] .note{border-left-color:var(--stop)}
table{width:100%; border-collapse:collapse; font-size:13.5px}
.scroll{overflow-x:auto; border:1px solid var(--line); border-radius:3px; background:var(--surface)}
th,td{text-align:left; padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top}
th{
  font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.12em; text-transform:uppercase;
  color:var(--ink-3); font-weight:500; white-space:nowrap;
}
tr:last-child td{border-bottom:none}
td.num{font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; white-space:nowrap}
.plat{background:var(--surface); border:1px solid var(--line); border-radius:3px; padding:15px 16px;
  box-shadow:var(--shadow); display:flex; flex-direction:column; gap:10px}
.plat ol{margin:0; padding-left:18px; color:var(--ink-2); font-size:13.5px; display:flex; flex-direction:column; gap:4px}
.fine{font-size:12.5px; color:var(--ink-3); max-width:70ch}
footer{border-top:1px solid var(--line); padding-top:16px; display:flex; flex-direction:column; gap:8px}
"""

JS = """
(function(){
  var m = new Date().getMonth() + 1;
  document.querySelectorAll('[data-mois]').forEach(function(el){
    var mois = JSON.parse(el.getAttribute('data-mois'));
    var actif = mois.indexOf(m) !== -1;
    el.setAttribute('data-actif', actif ? '1' : '0');
    var pill = el.querySelector('.pill.saison');
    if (pill && !actif) { pill.hidden = true; }
    var cell = el.querySelector('.mois span:nth-child(' + m + ')');
    if (cell) { cell.classList.add('now'); }
  });
  var noms = ['janvier','février','mars','avril','mai','juin','juillet','août',
              'septembre','octobre','novembre','décembre'];
  var cible = document.getElementById('mois-courant');
  if (cible) { cible.textContent = noms[m - 1]; }
})();
"""


def html_destination(d):
    dec = decote(d)
    pts = "".join(
        f'<i class="{"on" if i < d["densite_empty_legs"] else ""}"></i>' for i in range(5)
    )
    mois = "".join(
        f'<span class="{"on" if (i + 1) in d["mois_forts"] else ""}">{MOIS_COURTS[i]}</span>'
        for i in range(12)
    )
    aeroports = "".join(
        f'<span class="code" title="{a["note"]}"><b>{a["iata"] if a["iata"] != "—" else a["oaci"]}</b>'
        f'<i>{a["oaci"] if a["iata"] != "—" else "OACI"}</i><i>{a["nom"]}</i></span>'
        for a in d["aeroports"]
    )
    plateformes = "".join(
        f'<span class="pill">{p}</span>' for p in d["plateformes_prioritaires"]
    ) or '<span class="pill stop">aucune plateforme ne vend cette route</span>'

    if d.get("prix_empty_leg_eur"):
        bloc_prix = (
            f'<span class="cible">{fourchette(d["prix_empty_leg_eur"])}</span>'
            f'<span class="barre">au lieu de {fourchette(d["prix_charter_eur"])}</span>'
            + (f'<span class="dec">-{dec} %</span>' if dec else "")
        )
    else:
        bloc_prix = '<span class="cible">Hors marché</span>'

    jours = ", ".join(d["jours_forts"]) if d["jours_forts"] else "—"
    return f"""
    <article class="strip" data-mois='{json.dumps(d["mois_forts"])}' data-densite="{d['densite_empty_legs']}">
      <div class="strip-head">
        <div>
          <h3>{d['nom']}</h3>
          <span class="zone">{d['zone']}</span>
        </div>
        <div class="pills">
          <span class="pill saison">en saison</span>
          <span class="pill">{duree(d['duree_vol_h'])} de vol</span>
        </div>
      </div>
      <div class="codes">{aeroports}</div>
      <div class="data">
        <div>
          <span class="meter-label">Densité de l'offre — {d['densite_empty_legs']}/5</span>
          <div class="seg">{pts}</div>
          <div class="mois-bloc">
            <span class="meter-label">Mois où l'offre est alimentée</span>
            <div class="mois">{mois}</div>
          </div>
        </div>
        <div>
          <span class="meter-label">Cible empty leg (appareil entier)</span>
          <div class="prix">{bloc_prix}</div>
        </div>
      </div>
      <dl class="faits">
        <dt>Saison</dt><dd>{d['saison_haute']}</dd>
        <dt>Jours forts</dt><dd>{jours}</dd>
        <dt>Appareil</dt><dd>{d['categorie_avion']}</dd>
        <dt>Plan B</dt><dd>{d['plan_b']}</dd>
        <dt>Alertes</dt><dd><div class="pills">{plateformes}</div></dd>
      </dl>
      <p class="note">{d['notes']}</p>
    </article>"""


def html_plateforme(p, destinations):
    couvertes = [d["nom"] for d in destinations if p["id"] in d["plateformes_prioritaires"]]
    etapes = "".join(f"<li>{e}</li>" for e in p["configuration"])
    return f"""
    <div class="plat">
      <div class="strip-head">
        <div><h3>{p['nom']}</h3><span class="zone">{p['type']}</span></div>
        <div class="pills"><span class="pill">priorité {p['priorite']}</span></div>
      </div>
      <dl class="faits">
        <dt>Coût</dt><dd><b>{p['cout']}</b></dd>
        <dt>Alerte</dt><dd>{p['canal_alerte']} — {p['granularite']}</dd>
      </dl>
      <ol>{etapes}</ol>
      <dl class="faits">
        <dt>Routes</dt><dd>{', '.join(couvertes) if couvertes else 'aucune route de la liste'}</dd>
        <dt>Force</dt><dd>{p['forces']}</dd>
        <dt>Limite</dt><dd>{p['limites']}</dd>
      </dl>
    </div>"""


def construire_html():
    meta, destinations, plateformes = charger()
    ordonnees = sorted(destinations, key=lambda d: -d["densite_empty_legs"])

    strips = "".join(html_destination(d) for d in ordonnees)
    plats = "".join(html_plateforme(p, destinations) for p in plateformes)

    lignes_bases = "".join(
        f'<tr><td class="num">{b["iata"]} · {b["oaci"]}</td><td>{b["nom"]}</td><td>{b["note"]}</td></tr>'
        for cle in ("principale", "secondaires", "elargies")
        for b in meta["bases_depart"][cle]
    )

    lignes_routes = "".join(
        f'<tr><td>{d["nom"]}</td><td class="num">{codes(d, " ")}</td>'
        f'<td class="num">{d["densite_empty_legs"]}/5</td>'
        f'<td class="num">{fourchette(d.get("prix_empty_leg_eur"))}</td>'
        f'<td class="num">{"-" + str(decote(d)) + " %" if decote(d) else "—"}</td></tr>'
        for d in ordonnees
    )

    return f"""<title>Cockpit Empty Legs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
  <header class="page">
    <span class="eyebrow">Veille vols de repositionnement · 12 destinations</span>
    <h1>Cockpit Empty Legs</h1>
    <p class="sub">Où poser les alertes, quoi saisir dans chaque formulaire, et à quel prix une offre
    mérite qu'on décroche. Base de départ&nbsp;: Paris-Le Bourget, rayon élargi à Genève, Nice,
    Bruxelles et Luxembourg. Nous sommes en <b id="mois-courant">saison</b>.</p>
    <div class="regles">
      <div class="regle"><b>Ultra-flexibilité</b><span>L'itinéraire, la date et l'heure sont fixés
        par le client principal. Vous ne négociez rien&nbsp;: vous acceptez ou vous passez.</span></div>
      <div class="regle"><b>Aller simple, appareil entier</b><span>Le prix affiché couvre tout l'avion,
        que vous soyez seul ou huit. À moins de quatre passagers, comparez toujours à la business.</span></div>
      <div class="regle"><b>Risque d'annulation</b><span>Si le client plein tarif décale son vol, votre
        empty leg saute. Le plan B commercial se réserve <em>avant</em> de payer.</span></div>
      <div class="regle"><b>Fenêtre J-2 / J-1</b><span>Les vraies décotes (-70&nbsp;%) tombent 24 à 48 h
        avant décollage, quand l'opérateur cherche à amortir son carburant.</span></div>
    </div>
  </header>

  <section>
    <div class="section-head"><h2>Les 12 routes</h2>
      <span class="fine">Classées par densité réelle de l'offre</span></div>
    <div class="scroll"><table>
      <thead><tr><th>Destination</th><th>Aéroports</th><th>Densité</th><th>Cible empty leg</th><th>Décote</th></tr></thead>
      <tbody>{lignes_routes}</tbody>
    </table></div>
    {strips}
  </section>

  <section>
    <div class="section-head"><h2>Configuration des alertes</h2>
      <span class="fine">La même alerte, posée en parallèle sur 4 à 6 plateformes</span></div>
    <p class="fine">Aucune plateforme ne voit plus d'un tiers de l'offre&nbsp;: la couverture vient du
    nombre d'alertes simultanées, pas du choix de la «&nbsp;meilleure&nbsp;» plateforme. Commencer par les
    gratuites, ne payer un abonnement qu'une fois le rythme de voyage établi.</p>
    {plats}
  </section>

  <section>
    <div class="section-head"><h2>Aéroports de départ à cocher</h2>
      <span class="fine">Rayon 300 km&nbsp;: un départ de Genève reste rentable</span></div>
    <div class="scroll"><table>
      <thead><tr><th>Code</th><th>Aéroport</th><th>Pourquoi</th></tr></thead>
      <tbody>{lignes_bases}</tbody>
    </table></div>
  </section>

  <footer>
    <p class="fine">{meta['avertissement']}</p>
    <p class="fine">Fourchettes de prix indicatives (marché 2025-2026) servant de seuil de décision,
    pas de devis. Les conditions d'accès, les visas et les régimes de sanctions évoluent&nbsp;: vérifier
    avant chaque réservation.</p>
  </footer>
</div>
<script>{JS}</script>
"""


def cmd_dashboard(args):
    sortie = Path(args.out) if args.out else ROOT / "output" / "empty_legs.html"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(construire_html(), encoding="utf-8")
    print(f"[dashboard] écrit : {sortie} ({sortie.stat().st_size // 1024} Ko)")


# ----------------------------------------------------------------------------- cli


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sous = parser.add_subparsers(dest="commande", required=True)

    p_routes = sous.add_parser("routes", help="tableau des routes")
    p_routes.add_argument("--mois", type=int, choices=range(1, 13), help="mois de référence (défaut : mois courant)")
    p_routes.set_defaults(func=cmd_routes)

    p_alertes = sous.add_parser("alertes", help="fiches de configuration par plateforme")
    p_alertes.add_argument("--plateforme", help="limiter à une plateforme (xo, victor, ...)")
    p_alertes.set_defaults(func=cmd_alertes)

    p_veille = sous.add_parser("veille", help="checklist du jour")
    p_veille.add_argument("--mois", type=int, choices=range(1, 13))
    p_veille.add_argument("--telegram", action="store_true", help="envoyer la checklist via notify.py")
    p_veille.set_defaults(func=cmd_veille)

    p_dash = sous.add_parser("dashboard", help="génère le tableau de bord HTML")
    p_dash.add_argument("--out", help="chemin de sortie (défaut : output/empty_legs.html)")
    p_dash.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
