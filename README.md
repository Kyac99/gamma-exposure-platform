# GammaTracker - Plateforme Gamma Exposure

## Présentation
GammaTracker est une plateforme complète pour le scraping et l'analyse des actifs américains avec un focus particulier sur le Gamma Exposure. Cette solution permet de visualiser les données de marché, les niveaux de gamma, et de générer des plans de trading automatisés.

## Fonctionnalités

- **Scraping de données** : Collecte automatique des données de marché et d'options
- **Calcul du Gamma Exposure** : Analyse des niveaux de gamma et identification des supports/résistances
- **Visualisation interactive** : Tableaux de bord et graphiques pour explorer les données
- **Plans de trading automatisés** : Génération de stratégies basées sur l'analyse du gamma
- **Mise à jour automatique** : Rafraîchissement périodique des données

## Architecture

- **Backend** : Python/Flask avec intégration yfinance pour les données
- **Frontend** : React.js pour l'interface utilisateur interactive
- **Base de données** : MongoDB pour le stockage des données
- **Déploiement** : Configuration Docker pour faciliter le déploiement

## Installation et démarrage

### Prérequis
- Docker et Docker Compose
- Git

### Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/Kyac99/gamma-exposure-platform.git
cd gamma-exposure-platform
```

2. Démarrez l'application avec Docker Compose :
```bash
docker-compose up -d
```

3. Accédez à l'application dans votre navigateur :
```
http://localhost
```

## Actifs suivis

### Indices
- S&P 500 (^GSPC)
- Nasdaq 100 (^NDX)
- Dow Jones (^DJI)

### Actions
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- META (Meta Platforms)
- NVDA (NVIDIA)

## Utilisation

### Dashboard
Le tableau de bord présente une vue d'ensemble des indices et actions avec les valeurs de Gamma Exposure associées. Les graphiques permettent de visualiser rapidement les tendances et les anomalies.

### Liste des actifs
Cette vue permet d'explorer en détail tous les actifs suivis, avec des options de filtrage et de recherche.

### Détail d'un actif
Pour chaque actif, des visualisations détaillées du Gamma Exposure par niveau de prix sont disponibles, permettant d'identifier les zones de support et de résistance.

### Plan de trading
Un plan de trading automatisé est généré pour chaque actif, basé sur l'analyse du Gamma Exposure. Ce plan inclut des recommandations sur les entrées, sorties, et la gestion des risques.

## Développement

### Structure du projet
```
gamma-exposure-platform/
├── backend/                # API et logique métier en Python/Flask
│   ├── app.py              # Application principale
│   ├── Dockerfile          # Configuration Docker
│   └── requirements.txt    # Dépendances Python
├── frontend/               # Interface utilisateur en React
│   ├── public/             # Fichiers statiques
│   ├── src/                # Code source React
│   │   ├── components/     # Composants React
│   │   └── styles/         # Fichiers CSS
│   ├── Dockerfile          # Configuration Docker
│   └── package.json        # Dépendances JavaScript
└── docker-compose.yml      # Configuration Docker Compose
```

## Ressources sur le Gamma Exposure

Le Gamma Exposure (GEX) est une mesure qui quantifie l'ampleur du gamma des options détenues sur un marché et son impact potentiel sur les prix des actifs sous-jacents. Dans notre plateforme :

- Un **Gamma Net positif** indique généralement un biais haussier et des niveaux de support potentiels
- Un **Gamma Net négatif** indique généralement un biais baissier et des niveaux de résistance potentiels
- Les **niveaux significatifs de gamma** peuvent agir comme des aimants ou des barrières pour les prix

### Comment interpréter les niveaux de Gamma

1. **Gamma Positif (Support)** : 
   - Lorsque le prix descend vers un niveau avec un gamma net positif important, il tend à rebondir.
   - Les market makers achètent quand le prix baisse, créant une force haussière.

2. **Gamma Négatif (Résistance)** :
   - Lorsque le prix monte vers un niveau avec un gamma net négatif important, il tend à être repoussé.
   - Les market makers vendent quand le prix monte, créant une force baissière.

3. **Clustering de Gamma** :
   - Les niveaux où le gamma est fortement concentré sont particulièrement significatifs.
   - Plus la concentration est importante, plus l'effet magnétique ou répulsif est puissant.

## API Backend

Le backend expose plusieurs endpoints REST :

- `GET /api/market-data` - Récupère les données de marché pour tous les actifs
- `GET /api/market-data/<ticker>` - Récupère les données de marché pour un actif spécifique
- `GET /api/gamma-data` - Récupère les données de gamma pour tous les actifs
- `GET /api/gamma-data/<ticker>` - Récupère les données de gamma pour un actif spécifique
- `GET /api/trading-strategy/<ticker>` - Génère une stratégie de trading pour un actif
- `POST /api/refresh-data` - Force le rafraîchissement des données

## Évolutions futures

- Ajout de plus d'actifs (ETFs, autres indices)
- Intégration de l'analyse technique traditionnelle
- Module d'apprentissage automatique pour affiner les stratégies
- Alertes en temps réel pour les opportunités de trading
- Backtesting des stratégies basées sur le gamma

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Contributeurs

- [Kyac]

## Contact

Pour toute question ou suggestion, veuillez nous contacter à [...].
