# 🌍 Real Time Translator API

API REST de **traduction en temps réel** avec **recherche sémantique**, **détection de plagiat** et **recherche d'images par texte**, construite avec FastAPI, MongoDB, Elasticsearch et un LLM hébergé sur Groq.

> Projet académique — Master MLAIM (Machine Learning Avancé et Intelligence Multimédia), Faculté des Sciences Dhar El Mahraz, Université Sidi Mohamed Ben Abdellah, Fès.

---

## ✨ Fonctionnalités

| Fonctionnalité | Endpoint | Description |
|---|---|---|
| Traduction | `POST /translate` | Traduit un texte avec Llama 3.3 70B (Groq), le stocke dans MongoDB et l'indexe dans Elasticsearch avec son embedding |
| Similarité | `POST /similarity` | Calcule la similarité cosinus entre deux textes (multilingue) |
| Recherche textuelle | `GET /search/text` | Recherche sémantique kNN dans les textes déjà traduits |
| Upload d'image | `POST /upload/image` | Indexe une image avec son embedding CLIP |
| Recherche d'image | `GET /search/image` | Retrouve des images à partir d'une requête en langage naturel |
| Détection de plagiat | `POST /plagiarism/check` | Compare un texte aux textes indexés et signale les correspondances au-dessus d'un seuil |

---

## 🧱 Stack technique

- **API** : FastAPI + Uvicorn
- **LLM de traduction** : Llama 3.3 70B Versatile via l'API Groq (SDK OpenAI)
- **Base de données** : MongoDB (historique des traductions)
- **Moteur de recherche vectoriel** : Elasticsearch 8.x (`dense_vector` + kNN, similarité cosinus)
- **Embeddings texte** : `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions, sentence-transformers)
- **Embeddings image/texte** : CLIP `ViT-B-32` (512 dimensions, open-clip-torch)
- **Configuration** : pydantic-settings + fichier `.env`

---

## 🏗️ Architecture

```
                         ┌──────────────────┐
   POST /translate ────► │     FastAPI      │
                         └───────┬──────────┘
            ┌────────────────────┼─────────────────────┐
            ▼                    ▼                     ▼
      Groq (Llama 3.3)     MongoDB               Elasticsearch
      traduction           historique            index vectoriel
                                                 ├─ documents_text  (384 d)
                                                 └─ documents_image (512 d)
```

### Structure du projet

```
Prj_MongoDB/
├── main.py                  # Routes FastAPI
├── config.py                # Chargement des variables d'environnement
├── db.py                    # Connexion MongoDB
├── models.py                # Schémas Pydantic (requêtes / réponses)
├── requirements.txt
├── .env.example             # Modèle de configuration
└── services/
    ├── translator.py        # Traduction via Groq
    ├── embeddings.py        # Embeddings texte + similarité cosinus
    ├── clip_service.py      # Embeddings image / texte CLIP
    └── es_client.py         # Client Elasticsearch + création des index
```

---

## ✅ Prérequis

- Python 3.10 ou plus (développé avec Python 3.13)
- MongoDB (local ou MongoDB Atlas)
- Elasticsearch 8.x accessible sur `http://localhost:9200`
- Une clé API Groq (gratuite) : <https://console.groq.com>

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/aymane-moubarik/real-time-translator.git
cd real-time-translator
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

> Le premier lancement télécharge les modèles MiniLM et CLIP (quelques centaines de Mo).

### 4. Configurer l'environnement

Copier `.env.example` en `.env` puis renseigner les valeurs :

```env
GROQ_API_KEY=votre_cle_groq
MONGO_URI=mongodb://localhost:27017
MONGO_DB=translator_db
```

### 5. Démarrer MongoDB et Elasticsearch

Avec Docker (Elasticsearch sans authentification, pour le développement local) :

```bash
docker run -d --name elasticsearch -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.4

docker run -d --name mongodb -p 27017:27017 mongo:7
```

### 6. Lancer l'API

```bash
uvicorn main:app --reload
```

- API : <http://127.0.0.1:8000>
- Documentation Swagger interactive : <http://127.0.0.1:8000/docs>

Les index Elasticsearch (`documents_text` et `documents_image`) sont créés automatiquement au démarrage.

---

## 📡 Exemples d'utilisation

### Traduire un texte

```bash
curl -X POST http://127.0.0.1:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour, comment allez-vous ?", "target_lang": "anglais"}'
```

```json
{
  "original_text": "Bonjour, comment allez-vous ?",
  "translated_text": "Hello, how are you?",
  "source_lang": "auto",
  "target_lang": "anglais",
  "timestamp": "2026-10-05T10:00:00"
}
```

### Calculer la similarité entre deux textes

```bash
curl -X POST http://127.0.0.1:8000/similarity \
  -H "Content-Type: application/json" \
  -d '{"text1": "Le chat dort sur le canapé", "text2": "The cat is sleeping on the sofa"}'
```

### Recherche sémantique de texte

```bash
curl "http://127.0.0.1:8000/search/text?query=salutation&top_k=5"
```

### Indexer une image puis la rechercher

```bash
curl -X POST "http://127.0.0.1:8000/upload/image?description=coucher%20de%20soleil" \
  -F "file=@photo.jpg"

curl "http://127.0.0.1:8000/search/image?query=un%20paysage%20au%20coucher%20du%20soleil"
```

Formats acceptés : `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`.

### Détecter un plagiat

```bash
curl -X POST http://127.0.0.1:8000/plagiarism/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour, comment allez-vous ?", "threshold": 0.85}'
```

```json
{
  "text": "Bonjour, comment allez-vous ?",
  "is_plagiarized": true,
  "matches": [{"text": "Bonjour, comment allez-vous ?", "score": 1.0}]
}
```

---

## 📝 Notes

- Le score kNN d'Elasticsearch en similarité cosinus vaut `(1 + cos) / 2`. Un seuil de plagiat de `0.85` correspond donc à une similarité cosinus d'environ `0.70`.
- L'URL d'Elasticsearch est définie dans `services/es_client.py` (`http://localhost:9200`).
- Le champ `source_lang` vaut `auto` par défaut ; la langue cible est passée telle quelle au LLM.

## 🔭 Pistes d'amélioration

- Rendre l'URL d'Elasticsearch configurable via `.env`
- Ajouter des tests automatisés (pytest)
- Ajouter une interface web (Streamlit ou React)
- Dockeriser l'ensemble avec `docker-compose` (API + MongoDB + Elasticsearch + Kibana)
- Ajouter l'authentification sur l'API

## 👤 Auteur

**Aymane EL MOQADEM** — [github.com/aymane-moubarik](https://github.com/aymane-moubarik)

## 📄 Licence

Projet académique à but pédagogique.
