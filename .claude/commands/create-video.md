# Skill — Créer une vidéo de graph boursier

> **Langue** : tous les scénarios sont en anglais — headline, labels (`Invested`, `Total gain`, `Total loss`), nom de société.

Générateur de vidéos verticales (1080×1920, TikTok/Reels/Shorts) animant l'évolution d'un investissement boursier dans le temps.

## Pipeline

```
scenario.json → fetcher.py (yfinance) → _computed.json → index.html (D3.js) → Playwright → FFmpeg → .mp4
```

## Commande

```bash
python3 render.py --scenario scenario.json
```

Avec un fichier différent :

```bash
python3 render.py --scenario scenario_AAPL.json
```

## Format du `scenario.json`

```json
{
  "text": {
    "headline": "Si tu avais investi 10€/semaine\ndans McDonald's depuis 10 ans",
    "text_prefix": "POV:",
    "company_name": "McDonald's",
    "company_color": "#FFC300",
    "invested_label": "Investi",
    "gain_label": "Gain total",
    "loss_label": "Perte totale",
    "font_size": 58,
    "color": "#111111"
  },
  "data": {
    "ticker": "MCD",
    "start_date": "2016-08-18",
    "start_investment": 0,
    "weekly_investment": 10,
    "currency": "USD",
    "reinvest_dividends": true
  },
  "video": {
    "output": "video_MCD.mp4",
    "duration_seconds": 61,
    "fps": 30
  }
}
```

## Champs `text`

| Champ | Type | Description |
|-------|------|-------------|
| `headline` | string | Texte affiché en haut de la vidéo. `\n` = saut de ligne. |
| `text_prefix` | string | Préfixe avant le headline (ex. `"POV:"`) |
| `company_name` | string | Nom de l'entreprise affiché dans les labels |
| `company_color` | string | Couleur hex de la marque |
| `invested_label` | string | Label de la courbe "montant investi" |
| `gain_label` | string | Label affiché quand le portefeuille est en gain |
| `loss_label` | string | Label affiché quand le portefeuille est en perte |
| `font_size` | number | Taille du texte headline (défaut : 52) |
| `color` | string | Couleur du texte (défaut : `#111111`) |
| `tag_colors` | object | Couleurs pour les balises HTML dans le headline — ex. `{ "a": "#86868B" }` |

## Champs `data`

| Champ | Type | Description |
|-------|------|-------------|
| `ticker` | string | Symbole boursier : `MCD`, `AAPL`, `MC.PA`… |
| `start_date` | string | Date de début de l'investissement `YYYY-MM-DD` |
| `end_date` | string | Date de fin (défaut : aujourd'hui) |
| `start_investment` | number | Montant investi en une seule fois au départ |
| `weekly_investment` | number | Montant investi chaque semaine |
| `monthly_investment` | number | Montant investi chaque mois (exclusif avec `weekly_investment`) |
| `currency` | string | Devise affichée (`"USD"`, `"EUR"`…) |
| `reinvest_dividends` | boolean | `true` = affiche la 3e courbe avec dividendes réinvestis |

> Au moins un de `start_investment`, `weekly_investment` ou `monthly_investment` doit être non nul.

## Champs `video`

| Champ | Type | Description |
|-------|------|-------------|
| `output` | string | Nom du fichier MP4 généré |
| `duration_seconds` | number | Durée totale de la vidéo en secondes |
| `fps` | number | Images par seconde (défaut : 30) |

## Exemples de scénarios

**Investissement hebdomadaire — MCD sur 10 ans**
```json
{
  "text": {
    "headline": "Si tu avais investi 10€/semaine\ndans McDonald's depuis 10 ans",
    "text_prefix": "POV:",
    "company_name": "McDonald's",
    "company_color": "#FFC300",
    "invested_label": "Investi",
    "gain_label": "Gain total",
    "loss_label": "Perte totale",
    "font_size": 58,
    "color": "#111111"
  },
  "data": {
    "ticker": "MCD",
    "start_date": "2016-08-18",
    "weekly_investment": 10,
    "currency": "USD",
    "reinvest_dividends": true
  },
  "video": {
    "output": "video_MCD.mp4",
    "duration_seconds": 61,
    "fps": 30
  }
}
```

**Investissement one-shot historique — AAPL depuis le premier iMac**
```json
{
  "text": {
    "headline": "You invested $1,299 in <a>Apple</a>\ninstead of buying the first iMac",
    "text_prefix": "POV:",
    "tag_colors": { "a": "#86868B" },
    "company_name": "Apple",
    "company_color": "#86868B",
    "invested_label": "Invested",
    "gain_label": "Total gain",
    "loss_label": "Total loss",
    "font_size": 58,
    "color": "#111111"
  },
  "data": {
    "ticker": "AAPL",
    "start_date": "1998-08-15",
    "start_investment": 1299,
    "weekly_investment": 0,
    "currency": "USD",
    "reinvest_dividends": true
  },
  "video": {
    "output": "video_AAPL.mp4",
    "duration_seconds": 61,
    "fps": 30
  }
}
```

## Prérequis système

```bash
pip install yfinance pandas playwright
python3 -m playwright install chromium
# ffmpeg doit être installé sur le système
```

## GitHub Actions

Le workflow `.github/workflows/render-video.yml` permet de lancer un rendu sans machine locale.
Depuis l'onglet **Actions** → **Render Video** → **Run workflow**, renseigner :

| Input | Description |
|-------|-------------|
| `ticker` | Symbole boursier |
| `start_date` | Date de début `YYYY-MM-DD` |
| `weekly_investment` | Montant hebdomadaire |
| `headline` | Texte du headline (`\n` pour les sauts de ligne) |
| `duration_seconds` | Durée de la vidéo en secondes |

Le MP4 est téléchargeable en artifact à la fin du job.

## Résolution des problèmes fréquents

| Erreur | Solution |
|--------|---------|
| `Playwright not installed` | `pip install playwright && python3 -m playwright install chromium` |
| `yfinance not installed` | `pip install yfinance pandas` |
| `No price data found for ticker` | Vérifier le symbole (Paris : `MC.PA`, pas `MC`) |
| Vidéo trop courte / coupée | Augmenter `duration_seconds` dans la section `video` |
| Port HTTP déjà utilisé | Modifier la variable `port = 9754` dans `render.py` |
