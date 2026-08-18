# create-graph-action-video

Outil de génération de vidéos TikTok (format vertical 1080×1920) représentant l'évolution d'un investissement en actions sur le long terme. Tout est piloté par un fichier `scenario.json`.

---

## Concept

Le graphique affiche jusqu'à trois courbes sur la même période :

| # | Courbe | Toujours affichée | Description |
|---|--------|:-----------------:|-------------|
| 1 | **Montant investi** | Oui | Somme cumulée réellement versée (apports réguliers ou unique) |
| 2 | **Valeur sans dividendes** | Oui | Valeur du portefeuille basée sur la seule appréciation du cours (Adjusted Close hors dividendes) |
| 3 | **Valeur avec dividendes réinvestis** | Si l'action verse des dividendes | Valeur du portefeuille en supposant que chaque dividende perçu est immédiatement réinvesti en parts supplémentaires |

La courbe 3 n'apparaît que si l'action a effectivement versé des dividendes sur la période. L'écart entre les courbes 2 et 3 montre l'impact concret des dividendes réinvestis sur le long terme.

### Axes

| Axe | Contenu | Style |
|-----|---------|-------|
| Vertical (gauche) | Prix / Valeur en devise | **Gras, noir** |
| Horizontal | Années | **Gras, noir** |

Le fond de la vidéo est **blanc**.

---

### Légende des courbes

| Courbe | Couleur suggérée |
|--------|-----------------|
| Montant investi | Gris `#888888` |
| Valeur sans dividendes | Bleu `#2979FF` |
| Valeur avec dividendes réinvestis | Vert `#00C853` |

---

## Mise en page de la vidéo

```
┌─────────────────────────────────┐
│                                 │
│   Si tu avais investi 10€       │
│   par semaine dans McDo         │
│   au lieu d'acheter des McDo    │  ← Texte accroche (haut)
│   chaque semaine...             │
│                                 │
│                                 │
│                                 │
│         [espace libre]          │
│                                 │
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │      GRAPHIQUE            │  │  ← Graphique (centre-bas)
│  │   (deux courbes)          │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

- **Haut de l'écran** : texte d'accroche, défini dans `scenario.json`, centré, en gras
- **Centre-bas** : graphique animé avec les deux courbes
- **Fond** : blanc `#FFFFFF` sur toute la vidéo

---

## scenario.json

Fichier de configuration unique qui pilote l'intégralité de la vidéo.

```json
{
  "text": {
    "headline": "Si tu avais investi 10€ par semaine dans McDo\nau lieu d'acheter des McDo chaque semaine",
    "font_size": 52,
    "color": "#111111"
  },
  "data": {
    "ticker": "MCD",
    "start_date": "2015-01-01",
    "end_date": "2025-01-01",
    "weekly_investment": 10,
    "currency": "EUR",
    "reinvest_dividends": true
  },
  "video": {
    "output": "video_MCD.mp4",
    "duration_seconds": 10,
    "fps": 30
  }
}
```

### Détail des champs

#### `text`
| Champ | Description |
|-------|-------------|
| `headline` | Texte affiché en haut de l'écran. Utiliser `\n` pour les sauts de ligne. |
| `font_size` | Taille de la police (défaut : 52) |
| `color` | Couleur du texte en hex (défaut : `#111111`) |

#### `data`
| Champ | Description |
|-------|-------------|
| `ticker` | Symbole boursier (ex : `MCD`, `AAPL`, `MC.PA`) |
| `start_date` | Date de début de l'investissement (`YYYY-MM-DD`) |
| `end_date` | Date de fin (`YYYY-MM-DD`), défaut : aujourd'hui |
| `weekly_investment` | Apport hebdomadaire en devise (ou `monthly_investment` pour mensuel) |
| `currency` | Devise d'affichage |
| `reinvest_dividends` | `true` : affiche la 3ème courbe avec dividendes réinvestis. `false` : uniquement les 2 premières courbes. Défaut : `true` |

#### `video`
| Champ | Description |
|-------|-------------|
| `output` | Nom du fichier MP4 généré |
| `duration_seconds` | Durée totale de la vidéo |
| `fps` | Images par seconde (défaut : 30) |

---

## Stack technique

### Pipeline de rendu 

```
yfinance → scenario.json → index.html (D3.js) → Playwright → FFmpeg → MP4
```

1. `render.py` fetche les données historiques via **yfinance**
2. Injecte les données calculées dans `scenario.json`
3. Sert `index.html` via un serveur HTTP local
4. **Playwright** enregistre l'animation du navigateur en temps réel
5. **FFmpeg** encode la capture WebM → MP4 H.264

---

### Pourquoi JS/HTML plutôt que Matplotlib ?

| Critère | JS/HTML + Playwright | Matplotlib + Pillow |
|---------|:--------------------:|:-------------------:|
| Qualité du rendu | SVG antialiasé, crisp à 1080×1920 | Rendu bitmap, moins fin |
| Animation courbe | `requestAnimationFrame` — fluide nativement | Frame par frame manuel |
| Typographie | CSS + polices web, wrapping automatique | API limitée, gestion manuelle |
| Courbes | Bézier smooth | Segments droits entre points |
| Cohérence projet | Même pipeline que `create-sms-story-video` | Stack séparée |

---

### Briques techniques

| Brique | Rôle |
|--------|------|
| **Python** | Orchestration, fetch des données, injection dans `scenario.json` |
| **yfinance** | Historique des cours ajustés + dividendes — gratuit, sans clé API |
| **pandas** | Manipulation des séries temporelles retournées par yfinance |
| **D3.js** | Rendu SVG du graphique, animation "courbe qui se trace" de gauche à droite, axes personnalisés |
| **Playwright** | Capture de l'animation HTML en temps réel (headless Chromium) |
| **FFmpeg** | Encodage WebM → MP4 H.264 final |

### Pourquoi D3.js et pas Chart.js ?

D3.js offre un contrôle total sur l'animation progressive (la courbe se dessine point par point de gauche à droite via `stroke-dashoffset`), les axes en gras/noir, et le positionnement pixel-perfect des éléments. Chart.js anime tout d'un coup et offre moins de liberté sur le dessin séquentiel des courbes.

---

Outil à **usage unique** : chaque exécution appelle l'API, récupère l'historique complet, génère la vidéo. Pas de cache, pas de base de données.

---

## Sources de données

### yfinance (source principale)
- Wrapper Python non officiel sur Yahoo Finance
- Gratuit, sans clé API
- Fournit l'`Adjusted Close` nativement via `Ticker.history()`
- Fournit l'historique des dividendes via `Ticker.dividends`
- Limite : instable sur de très longues périodes ou pour certains marchés non-US

### Financial Modeling Prep — FMP (source secondaire)
- API REST officielle, clé requise (plan gratuit limité)
- Données historiques fiables avec cours ajustés
- Endpoint dédié pour l'historique des dividendes (`/historical/stock_dividend/{ticker}`)
- Utilisé en fallback si yfinance échoue ou retourne des données incomplètes

### Calcul du réinvestissement des dividendes

À chaque date de versement de dividende :
1. Récupérer le montant brut du dividende par action
2. Calculer le dividende total reçu = `nb_parts_détenues × dividende_par_action`
3. Acheter de nouvelles parts au cours du jour = `dividende_total / cours_ajusté_du_jour`
4. Ajouter ces nouvelles parts au portefeuille pour les calculs suivants

Ce calcul produit la courbe **"Valeur avec dividendes réinvestis"**.

---

## Points d'attention critiques

### Cours ajusté (`Adjusted Close`)

Toujours utiliser le **cours ajusté des splits et dividendes**, jamais le cours brut.

> Exemple : si une action fait un split 1:10, son cours brut chute de 90% du jour au lendemain. Sans ajustement, la courbe "montant actuel" s'effondrerait artificiellement — le graphique serait faux et trompeur.

Les deux sources (yfinance et FMP) fournissent ce champ ; il faut s'assurer de l'utiliser explicitement.

---

## Format de sortie

- **Résolution** : 1080 × 1920 px (portrait TikTok)
- **FPS** : 30 (configurable)
- **Format** : MP4 (H.264)
- **Fond** : blanc `#FFFFFF`
- **Animation** : la courbe se dessine de gauche à droite au fil de la vidéo

---

## Structure du projet (cible)

```
create-graph-action-video/
├── README.md
├── render.py          # Point d'entrée — lit scenario.json et orchestre tout
├── fetcher.py         # Récupération des données historiques (yfinance / FMP)
├── graph.py           # Rendu frame par frame du graphique (Matplotlib)
├── encoder.py         # Assemblage des frames PNG → MP4 via FFmpeg
└── scenario.json      # Configuration complète de la vidéo à générer
```

## Utilisation

```bash
python3 render.py --scenario scenario.json
```
