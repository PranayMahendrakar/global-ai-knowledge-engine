#!/usr/bin/env python3
"""
🌍 Global AI Knowledge Engine
Main entry point - orchestrates the full pipeline:
1. Scrape web data
2. Extract entities
3. Build knowledge graph
4. Continuously update
"""

import asyncio
import argparse
from loguru import logger
from dotenv import load_dotenv

from scraper.web_scraper import WebScraper
from extractor.entity_extractor import EntityExtractor
from graph.knowledge_graph import KnowledgeGraph
from scheduler.update_scheduler import UpdateScheduler
from api.app import start_api
from dashboard.app import start_dashboard

load_dotenv()


async def run_pipeline(topics: list[str], update_interval: int = 3600):
    """Run the full knowledge engine pipeline."""
    logger.info("🌍 Starting Global AI Knowledge Engine...")

    # Initialize components
    scraper = WebScraper()
    extractor = EntityExtractor()
    kg = KnowledgeGraph()
    scheduler = UpdateScheduler(
        scraper=scraper,
        extractor=extractor,
        graph=kg,
        topics=topics,
        interval=update_interval
    )

    # Initial data ingestion
    logger.info(f"📥 Starting initial scrape for topics: {topics}")
    for topic in topics:
        articles = await scraper.scrape_topic(topic, max_articles=20)
        for article in articles:
            entities = extractor.extract(article)
            kg.add_entities(entities, source=article['url'])

    kg.save()
    logger.info(f"✅ Initial graph built: {kg.node_count()} nodes, {kg.edge_count()} edges")

    # Start continuous update scheduler
    logger.info(f"⏰ Scheduling updates every {update_interval}s...")
    await scheduler.start()


def main():
    parser = argparse.ArgumentParser(description="🌍 Global AI Knowledge Engine")
    parser.add_argument("--topics", nargs="+", default=[
        "artificial intelligence", "machine learning", "climate change",
        "technology", "science", "geopolitics"
    ], help="Topics to track")
    parser.add_argument("--interval", type=int, default=3600,
                        help="Update interval in seconds (default: 3600)")
    parser.add_argument("--api", action="store_true", help="Start REST API server")
    parser.add_argument("--dashboard", action="store_true", help="Start Streamlit dashboard")
    parser.add_argument("--port", type=int, default=8000, help="API port")

    args = parser.parse_args()

    if args.api:
        start_api(port=args.port)
    elif args.dashboard:
        start_dashboard()
    else:
        asyncio.run(run_pipeline(args.topics, args.interval))


if __name__ == "__main__":
    main()
