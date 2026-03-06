"""
🚀 REST API Module
FastAPI-based REST API for the Knowledge Engine.
Provides endpoints to:
- Query entities
- Search the knowledge graph
- Get graph statistics
- Trigger manual updates
- Export graph data
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import threading
from loguru import logger

from graph.knowledge_graph import KnowledgeGraph
from scraper.web_scraper import WebScraper
from extractor.entity_extractor import EntityExtractor

# Global state
_graph: Optional[KnowledgeGraph] = None
_scraper: Optional[WebScraper] = None
_extractor: Optional[EntityExtractor] = None

app = FastAPI(
    title="🌍 Global AI Knowledge Engine API",
    description="Query and explore the world knowledge graph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    topic: str
    max_articles: int = 10


class AddTopicRequest(BaseModel):
    topic: str


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Global AI Knowledge Engine",
        "graph": _graph.get_stats() if _graph else None
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "graph_loaded": _graph is not None,
        "node_count": _graph.node_count() if _graph else 0,
        "edge_count": _graph.edge_count() if _graph else 0,
    }


@app.get("/stats", tags=["Graph"])
async def get_stats():
    """Get knowledge graph statistics."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
    return _graph.get_stats()


@app.get("/entities/search", tags=["Entities"])
async def search_entities(
    q: str = Query(..., description="Search query"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(20, ge=1, le=100, description="Max results")
):
    """Search for entities in the knowledge graph."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")

    results = _graph.search_entities(q, entity_type=entity_type, limit=limit)
    return {"query": q, "results": results, "count": len(results)}


@app.get("/entities/{entity_text}", tags=["Entities"])
async def get_entity(entity_text: str):
    """Get detailed information about a specific entity."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")

    entity = _graph.query_entity(entity_text)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_text}' not found")
    return entity


@app.get("/entities/{entity_text}/subgraph", tags=["Entities"])
async def get_entity_subgraph(
    entity_text: str,
    hops: int = Query(2, ge=1, le=4, description="Number of hops from entity")
):
    """Get a subgraph centered on an entity."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")

    subgraph = _graph.get_subgraph(entity_text, hops=hops)
    return subgraph


@app.get("/entities/top/connected", tags=["Entities"])
async def get_top_entities(
    n: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = None
):
    """Get the most connected entities in the graph."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")

    return _graph.get_most_connected(n=n, entity_type=entity_type)


@app.post("/scrape", tags=["Data Ingestion"])
async def scrape_topic(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Trigger a manual scrape for a topic."""
    if not _scraper or not _extractor or not _graph:
        raise HTTPException(status_code=503, detail="Engine not fully initialized")

    background_tasks.add_task(
        _run_scrape,
        request.topic,
        request.max_articles
    )

    return {"status": "started", "topic": request.topic, "max_articles": request.max_articles}


async def _run_scrape(topic: str, max_articles: int):
    """Background task to scrape and update graph."""
    try:
        articles = await _scraper.scrape_topic(topic, max_articles=max_articles)
        for article in articles:
            enriched = _extractor.extract(article)
            _graph.add_entities(enriched, source=article.get("url", ""))
        _graph.save()
        logger.info(f"Manual scrape complete: {topic}, {len(articles)} articles")
    except Exception as e:
        logger.error(f"Manual scrape failed: {e}")


@app.get("/graph/export", tags=["Graph"])
async def export_graph():
    """Export the full graph for visualization."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")

    return _graph.export_for_visualization()


@app.get("/graph/export/json", tags=["Graph"])
async def export_graph_json():
    """Export full graph data as JSON."""
    if not _graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")

    import json
    from fastapi.responses import StreamingResponse
    import io

    data = _graph.export_for_visualization()
    json_str = json.dumps(data, indent=2)
    return StreamingResponse(
        io.StringIO(json_str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=knowledge_graph.json"}
    )


def initialize_engine(graph_path: str = "data/knowledge_graph.json"):
    """Initialize the global engine components."""
    global _graph, _scraper, _extractor

    _graph = KnowledgeGraph(storage_path=graph_path)
    _scraper = WebScraper()
    _extractor = EntityExtractor()

    logger.info(f"✅ Engine initialized: {_graph.node_count()} nodes, {_graph.edge_count()} edges")


def start_api(port: int = 8000, graph_path: str = "data/knowledge_graph.json"):
    """Start the FastAPI server."""
    initialize_engine(graph_path)
    logger.info(f"🚀 Starting API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
