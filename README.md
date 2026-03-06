# 🌍 Global AI Knowledge Engine

> A mini open-source knowledge engine that continuously scrapes the web, extracts entities, and builds a live, structured knowledge graph about the world.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B.svg)](https://streamlit.io)
[![spaCy](https://img.shields.io/badge/spaCy-3.7-09A3D5.svg)](https://spacy.io)

---

## 🧠 What is this?

The **Global AI Knowledge Engine** is an automated pipeline that:

1. **🕷️ Scrapes** — Continuously collects data from news feeds, Wikipedia, RSS, and web sources
2. **🧬 Extracts** — Uses NLP (spaCy + transformers) to identify named entities and relationships
3. **🕸️ Builds** — Constructs a structured knowledge graph connecting entities (people, orgs, places, events)
4. **🔄 Updates** — Automatically refreshes knowledge on a configurable schedule
5. **📊 Serves** — REST API + Streamlit dashboard for exploration and querying

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Global AI Knowledge Engine                      │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │  🕷️ Scraper   │──▶│ 🧬 Extractor │──▶│  🕸️ Knowledge Graph  │ │
│  │              │   │              │   │                      │ │
│  │ • RSS Feeds  │   │ • spaCy NER  │   │ • NetworkX Graph     │ │
│  │ • Wikipedia  │   │ • Relations  │   │ • JSON Storage       │ │
│  │ • News sites │   │ • Concepts   │   │ • Neo4j (optional)   │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
│                                                  │               │
│  ┌───────────────────────────────────────────────▼─────────────┐ │
│  │                   ⏰ Scheduler                               │ │
│  │         Continuously updates every N seconds                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────┐   ┌────────────────────────────────┐   │
│  │  🚀 FastAPI REST API  │   │  📊 Streamlit Dashboard         │   │
│  │  /entities/search    │   │  • Graph visualization          │   │
│  │  /graph/export       │   │  • Entity explorer              │   │
│  │  /stats              │   │  • Live feed                    │   │
│  └──────────────────────┘   └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
global-ai-knowledge-engine/
├── main.py                      # Main entry point & CLI
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Full stack deployment
├── .env.example                 # Configuration template
│
├── scraper/                     # 🕷️ Web Scraping
│   ├── web_scraper.py           #   Async multi-source scraper
│   └── source_registry.py      #   RSS/API source registry
│
├── extractor/                   # 🧬 Entity Extraction
│   └── entity_extractor.py     #   spaCy NER + relation extraction
│
├── graph/                       # 🕸️ Knowledge Graph
│   └── knowledge_graph.py      #   NetworkX-based graph engine
│
├── scheduler/                   # ⏰ Continuous Updates
│   └── update_scheduler.py     #   APScheduler-based pipeline
│
├── api/                         # 🚀 REST API
│   └── app.py                  #   FastAPI endpoints
│
├── dashboard/                   # 📊 Visualization
│   └── app.py                  #   Streamlit interactive dashboard
│
└── data/                        # 💾 Data Storage
    └── knowledge_graph.json    #   Persisted graph (auto-created)
```

---

## 🚀 Quick Start

### Option 1: Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/PranayMahendrakar/global-ai-knowledge-engine.git
cd global-ai-knowledge-engine

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Configure (optional)
cp .env.example .env
# Edit .env with your settings

# 5. Run the knowledge engine
python main.py --topics "artificial intelligence" "climate change" "technology"
```

### Option 2: Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/PranayMahendrakar/global-ai-knowledge-engine.git
cd global-ai-knowledge-engine

# Copy and configure
cp .env.example .env

# Start all services
docker-compose up -d
```

Services will be available at:
- 📊 **Dashboard**: http://localhost:8501
- 🚀 **API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs

---

## 🔧 CLI Usage

```bash
# Run the full pipeline with custom topics
python main.py --topics "AI" "climate" "geopolitics" --interval 1800

# Start only the REST API server
python main.py --api --port 8000

# Start only the Streamlit dashboard
python main.py --dashboard
```

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check & stats |
| GET | `/stats` | Full graph statistics |
| GET | `/entities/search?q=OpenAI` | Search entities |
| GET | `/entities/{name}` | Get entity details |
| GET | `/entities/{name}/subgraph` | Get entity neighborhood |
| GET | `/entities/top/connected` | Top connected entities |
| POST | `/scrape` | Trigger manual scrape |
| GET | `/graph/export` | Export for visualization |
| GET | `/graph/export/json` | Download full graph JSON |

---

## 📊 Dashboard Features

The Streamlit dashboard (`http://localhost:8501`) provides:

- **Graph Stats** — Node/edge counts, entity type distributions, top entities
- **Entity Explorer** — Search and explore entities with full details
- **Graph Visualization** — Interactive vis.js network visualization
- **Live Feed** — Real-time update status and source tracking

---

## 🧬 Entity Types Extracted

| Type | Examples |
|------|---------|
| `person` | Elon Musk, Geoffrey Hinton |
| `organization` | OpenAI, Google DeepMind, NASA |
| `location` | United States, Silicon Valley |
| `event` | COP28, World Economic Forum |
| `product` | GPT-4, Tesla Model 3 |
| `group` | OPEC, G7, EU |

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

```env
# Topics to track
TOPICS=artificial intelligence,machine learning,climate change

# Update every hour
UPDATE_INTERVAL=3600

# Max articles per topic per cycle
MAX_ARTICLES_PER_TOPIC=20

# Storage
GRAPH_STORAGE_PATH=data/knowledge_graph.json

# NLP Model
SPACY_MODEL=en_core_web_sm
```

---

## 🔬 How It Works

**1. Scraping Pipeline**
The `WebScraper` fetches articles asynchronously from RSS feeds and Wikipedia using `aiohttp`. It maintains a deduplication cache to avoid reprocessing the same URLs.

**2. Entity Extraction**
The `EntityExtractor` uses spaCy's NLP pipeline to identify named entities (PERSON, ORG, GPE, EVENT, etc.) and extracts relationships via dependency parsing. Each entity is normalized and stored with metadata.

**3. Knowledge Graph Building**
The `KnowledgeGraph` uses NetworkX's `MultiDiGraph` to store entities as nodes and relationships as directed edges. Nodes track mention counts, first/last seen dates, and source URLs for provenance.

**4. Continuous Updates**
The `UpdateScheduler` uses APScheduler to run the full scrape → extract → update cycle at configurable intervals. The graph auto-saves every 5 minutes.

---

## 🛣️ Roadmap

- [ ] Advanced transformer-based NER (BERT/RoBERTa)
- [ ] Entity disambiguation & coreference resolution
- [ ] Fact verification pipeline
- [ ] Neo4j production backend
- [ ] GraphQL API
- [ ] Multi-language support
- [ ] Knowledge graph embedding (Node2Vec, GraphSAGE)
- [ ] Semantic search with FAISS
- [ ] Event timeline extraction
- [ ] Confidence scoring system

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ by [Pranay M Mahendrakar](https://github.com/PranayMahendrakar) | SONYTECH*
