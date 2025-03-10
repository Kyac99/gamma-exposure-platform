# GammaTracker - Plateforme d'analyse de Gamma Exposure

GammaTracker est une plateforme complète de scraping et d'analyse des actifs américains avec un focus particulier sur le Gamma Exposure. Cette plateforme permet de visualiser les données de marché, les niveaux de gamma, et de générer des plans de trading automatisés.

## Fonctionnalités

- **Scraping de données** : Collecte automatique des données de marché et d'options pour les indices et actions américains
- **Calcul du Gamma Exposure** : Analyse précise des niveaux de gamma et identification des points de support/résistance
- **Visualisation interactive** : Tableaux de bord et graphiques pour explorer les données
- **Plans de trading automatisés** : Génération de stratégies basées sur l'analyse du gamma
- **Mise à jour automatique** : Rafraîchissement périodique des données et notifications

## Architecture

- **Backend** : Python/Flask pour l'API REST et les calculs de gamma
- **Frontend** : React.js pour l'interface utilisateur
- **Base de données** : MongoDB pour le stockage des données
- **Déploiement** : Configuration Docker pour faciliter le déploiement

## Actifs suivis

- **Indices** : S&P 500 (^GSPC), Nasdaq 100 (^NDX), Dow Jones (^DJI)
- **Actions** : AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA

## Installation et déploiement

### Prérequis
- Docker et Docker Compose
- Git

### Installation

1. Clonez le dépôt Git :
```bash
git clone https://github.com/Kyac99/gamma-exposure-platform.git
cd gamma-exposure-platform
```

2. Lancez l'application avec Docker Compose :
```bash
docker-compose up -d
```

3. Accédez à l'application :
```
http://localhost
```

### Configuration

Les principaux paramètres de configuration se trouvent dans les fichiers suivants :
- `.env` pour les variables d'environnement
- `backend/app.py` pour les paramètres du backend
- `frontend/src/config.js` pour les paramètres du frontend

## Développement

### Structure du projet

```
gamma-exposure-platform/
├── backend/
│   ├── app.py          # Application Flask principale
│   ├── Dockerfile      # Configuration Docker pour le backend
│   └── requirements.txt # Dépendances Python
├── frontend/
│   ├── public/         # Fichiers statiques
│   ├── src/            # Code source React
│   ├── Dockerfile      # Configuration Docker pour le frontend
│   └── package.json    # Dépendances JavaScript
└── docker-compose.yml  # Configuration Docker Compose
```

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.