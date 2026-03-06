"""
⏰ Update Scheduler Module
Continuously updates the knowledge graph by:
- Scheduling periodic web scrapes
- Running incremental entity extraction
- Merging new knowledge into the graph
- Auto-saving graph state
"""

import asyncio
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from scraper.web_scraper import WebScraper
from extractor.entity_extractor import EntityExtractor
from graph.knowledge_graph import KnowledgeGraph


class UpdateScheduler:
    """
    Orchestrates continuous knowledge updates on a schedule.
    Supports multiple update frequencies per topic.
    """

    def __init__(
        self,
        scraper: WebScraper,
        extractor: EntityExtractor,
        graph: KnowledgeGraph,
        topics: List[str],
        interval: int = 3600,
        save_interval: int = 300,
    ):
        self.scraper = scraper
        self.extractor = extractor
        self.graph = graph
        self.topics = topics
        self.interval = interval
        self.save_interval = save_interval

        self.scheduler = AsyncIOScheduler()
        self._cycle_count = 0
        self._last_run = None
        self._running = False

    async def start(self):
        """Start the continuous update pipeline."""
        logger.info(f"🚀 Starting scheduler: {len(self.topics)} topics, {self.interval}s interval")

        # Schedule knowledge update
        self.scheduler.add_job(
            self._update_cycle,
            trigger=IntervalTrigger(seconds=self.interval),
            id="knowledge_update",
            name="Knowledge Graph Update",
            replace_existing=True,
        )

        # Schedule auto-save (more frequent)
        self.scheduler.add_job(
            self._auto_save,
            trigger=IntervalTrigger(seconds=self.save_interval),
            id="auto_save",
            name="Auto Save Graph",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        logger.info("✅ Scheduler started. Press Ctrl+C to stop.")

        try:
            # Keep running
            while self._running:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Scheduler stopping...")
            await self.stop()

    async def stop(self):
        """Gracefully stop the scheduler."""
        self._running = False
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.graph.save()
        logger.info("✅ Scheduler stopped. Final graph saved.")

    async def _update_cycle(self):
        """Run one complete update cycle across all topics."""
        self._cycle_count += 1
        cycle_start = datetime.now()
        logger.info(f"🔄 Update cycle #{self._cycle_count} starting at {cycle_start.strftime('%H:%M:%S')}")

        total_new = 0
        for topic in self.topics:
            try:
                new_entities = await self._update_topic(topic)
                total_new += new_entities
            except Exception as e:
                logger.error(f"Error updating topic '{topic}': {e}")

        duration = (datetime.now() - cycle_start).total_seconds()
        self._last_run = datetime.now().isoformat()
        logger.info(
            f"✅ Cycle #{self._cycle_count} complete: "
            f"+{total_new} entities in {duration:.1f}s. "
            f"Graph: {self.graph.node_count()} nodes, {self.graph.edge_count()} edges"
        )

    async def _update_topic(self, topic: str) -> int:
        """Update knowledge for a single topic. Returns number of new entities."""
        logger.debug(f"  📡 Updating topic: {topic}")

        # Scrape new articles
        articles = await self.scraper.scrape_topic(topic, max_articles=10)
        if not articles:
            logger.debug(f"  ⚠️ No articles found for '{topic}'")
            return 0

        # Extract entities from each article
        total_entities = 0
        for article in articles:
            try:
                enriched = self.extractor.extract(article)
                self.graph.add_entities(enriched, source=article.get("url", ""))
                total_entities += enriched.get("entity_count", 0)
            except Exception as e:
                logger.warning(f"  ⚠️ Entity extraction error: {e}")

        logger.debug(f"  ✅ Topic '{topic}': {len(articles)} articles, ~{total_entities} entities")
        return total_entities

    async def _auto_save(self):
        """Auto-save the graph periodically."""
        try:
            self.graph.save()
            logger.debug(f"💾 Auto-saved: {self.graph.node_count()} nodes, {self.graph.edge_count()} edges")
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")

    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            "running": self._running,
            "cycle_count": self._cycle_count,
            "last_run": self._last_run,
            "topics": self.topics,
            "interval_seconds": self.interval,
            "graph_nodes": self.graph.node_count(),
            "graph_edges": self.graph.edge_count(),
            "next_run": str(self.scheduler.get_job("knowledge_update").next_run_time)
                if self.scheduler.running and self.scheduler.get_job("knowledge_update") else None,
        }

    def add_topic(self, topic: str):
        """Dynamically add a new topic to track."""
        if topic not in self.topics:
            self.topics.append(topic)
            logger.info(f"➕ Added topic: {topic}")

    def remove_topic(self, topic: str):
        """Remove a topic from tracking."""
        if topic in self.topics:
            self.topics.remove(topic)
            logger.info(f"➖ Removed topic: {topic}")
