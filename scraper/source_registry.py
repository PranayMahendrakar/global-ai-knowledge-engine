"""
📚 Source Registry
Manages all knowledge sources (RSS feeds, APIs, websites)
organized by topic categories.
"""

from typing import List, Dict


class SourceRegistry:
    """Registry of all knowledge sources organized by topic."""

    SOURCES = {
        "default": [
            {"type": "rss", "url": "https://feeds.bbci.co.uk/news/rss.xml", "name": "BBC News"},
            {"type": "rss", "url": "https://rss.cnn.com/rss/edition.rss", "name": "CNN"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "artificial intelligence": [
            {"type": "rss", "url": "https://feeds.feedburner.com/bdtechtalks", "name": "Tech Talks"},
            {"type": "rss", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "name": "Wired AI"},
            {"type": "rss", "url": "https://techcrunch.com/tag/artificial-intelligence/feed/", "name": "TechCrunch AI"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "machine learning": [
            {"type": "rss", "url": "https://machinelearningmastery.com/blog/feed/", "name": "ML Mastery"},
            {"type": "rss", "url": "https://towardsdatascience.com/feed", "name": "Towards Data Science"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "climate change": [
            {"type": "rss", "url": "https://www.theguardian.com/environment/climate-crisis/rss", "name": "Guardian Climate"},
            {"type": "rss", "url": "https://insideclimatenews.org/feed/", "name": "Inside Climate News"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "technology": [
            {"type": "rss", "url": "https://feeds.arstechnica.com/arstechnica/index", "name": "Ars Technica"},
            {"type": "rss", "url": "https://www.theverge.com/rss/index.xml", "name": "The Verge"},
            {"type": "rss", "url": "https://techcrunch.com/feed/", "name": "TechCrunch"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "science": [
            {"type": "rss", "url": "https://www.sciencedaily.com/rss/all.xml", "name": "Science Daily"},
            {"type": "rss", "url": "https://www.nature.com/news.rss", "name": "Nature News"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "geopolitics": [
            {"type": "rss", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "name": "BBC World"},
            {"type": "rss", "url": "https://foreignpolicy.com/feed/", "name": "Foreign Policy"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "health": [
            {"type": "rss", "url": "https://rss.medicalnewstoday.com/featurednews.xml", "name": "Medical News Today"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
        "economics": [
            {"type": "rss", "url": "https://feeds.feedburner.com/feedburner/HmQz", "name": "Bloomberg"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org", "name": "Wikipedia"},
        ],
    }

    def get_sources_for_topic(self, topic: str) -> List[Dict]:
        """Get all sources for a given topic."""
        topic_lower = topic.lower()
        # Exact match
        if topic_lower in self.SOURCES:
            return self.SOURCES[topic_lower]
        # Partial match
        for key, sources in self.SOURCES.items():
            if key in topic_lower or topic_lower in key:
                return sources
        # Default fallback
        return self.SOURCES["default"]

    def add_source(self, topic: str, source: Dict):
        """Add a new source for a topic."""
        if topic not in self.SOURCES:
            self.SOURCES[topic] = []
        self.SOURCES[topic].append(source)

    def list_topics(self) -> List[str]:
        """List all tracked topics."""
        return list(self.SOURCES.keys())

    def list_sources(self) -> List[Dict]:
        """List all sources across all topics."""
        all_sources = []
        for topic, sources in self.SOURCES.items():
            for source in sources:
                all_sources.append({**source, "topic": topic})
        return all_sources
