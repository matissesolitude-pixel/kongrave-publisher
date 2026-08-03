#!/usr/bin/env python3
"""
ig_status.py — dit ce que le compte a VRAIMENT en ligne.

  python3 ig_status.py [n]

Un media_id retourné par media_publish prouve que Meta a accepté la publication, pas
qu'elle soit visible sur le profil. Ce script lit la liste réelle des médias du compte
et affiche leur type, leur date et leur permalien. C'est la seule vérification possible
depuis l'extérieur — le token ne vit que dans les Secrets GitHub, donc ça tourne en CI.
"""
import sys

import ig_api


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    media = ig_api.list_recent_media(limit=n)
    print(f"[status] compte {ig_api._ig_user_id()} — {len(media)} médias remontés\n")
    print(f"  {'#':<3}{'type':<16}{'date':<22}id / permalien")
    carrousels = 0
    for i, m in enumerate(media):
        t = m.get("media_type", "?")
        if t == "CAROUSEL_ALBUM":
            carrousels += 1
        print(f"  {i:<3}{t:<16}{(m.get('timestamp') or '')[:19]:<22}{m.get('id')}")
        if m.get("permalink"):
            print(f"     {m['permalink']}")
    print(f"\n[status] {carrousels} carrousel(s) dans les {len(media)} derniers médias")
    since = next((i for i, m in enumerate(media) if m.get("media_type") == "CAROUSEL_ALBUM"), None)
    if since is None:
        print("[status] AUCUN carrousel dans cette fenêtre")
    else:
        print(f"[status] {since} post(s) depuis le carrousel le plus récent "
              f"(cycle {since + 1} — { 'aligné' if (since + 1) % 3 == 0 else 'DÉCALÉ'})")


if __name__ == "__main__":
    main()
