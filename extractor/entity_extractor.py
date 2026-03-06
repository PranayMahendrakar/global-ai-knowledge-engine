"""
🧠 Entity Extractor Module
Extracts named entities, relationships, and concepts from text using:
- spaCy NLP pipeline
- Transformer-based NER
- Relationship extraction
- Concept linking
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import spacy
from loguru import logger


@dataclass
class Entity:
    """Represents a named entity."""
    text: str
    label: str          # PERSON, ORG, GPE, EVENT, etc.
    start: int
    end: int
    confidence: float = 1.0
    aliases: List[str] = field(default_factory=list)
    properties: Dict = field(default_factory=dict)
    source_url: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Relation:
    """Represents a relationship between two entities."""
    subject: str        # Entity text
    predicate: str      # Relationship type
    object: str         # Entity text
    confidence: float = 1.0
    source_url: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EntityExtractor:
    """
    Multi-model entity extraction pipeline.
    Combines spaCy and rule-based extraction for high accuracy.
    """

    ENTITY_TYPES = {
        "PERSON": "person",
        "ORG": "organization",
        "GPE": "location",
        "LOC": "location",
        "PRODUCT": "product",
        "EVENT": "event",
        "WORK_OF_ART": "creative_work",
        "LAW": "law",
        "LANGUAGE": "language",
        "DATE": "date",
        "TIME": "time",
        "MONEY": "money",
        "QUANTITY": "quantity",
        "NORP": "group",
        "FAC": "facility",
    }

    RELATION_PATTERNS = [
        # Subject VERB Object patterns
        ("founded", "founder_of"),
        ("established", "established"),
        ("acquired", "acquired"),
        ("partnered with", "partner_of"),
        ("works for", "employee_of"),
        ("is CEO of", "ceo_of"),
        ("is located in", "located_in"),
        ("is part of", "part_of"),
        ("develops", "develops"),
        ("invented", "invented_by"),
        ("discovered", "discovered_by"),
        ("published", "published_by"),
        ("created", "created_by"),
        ("collaborated with", "collaborates_with"),
    ]

    def __init__(self, model: str = "en_core_web_sm"):
        logger.info(f"Loading spaCy model: {model}")
        try:
            self.nlp = spacy.load(model)
        except OSError:
            logger.warning(f"Model {model} not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model], check=True)
            self.nlp = spacy.load(model)

        self._entity_cache: Dict[str, Entity] = {}

    def extract(self, article: Dict) -> Dict:
        """
        Extract all entities and relations from an article.
        Returns enriched article with entities and relations.
        """
        text = article.get("text", "") or article.get("summary", "")
        title = article.get("title", "")
        full_text = f"{title}. {text}" if title else text

        if not full_text.strip():
            return {**article, "entities": [], "relations": [], "concepts": []}

        # Process with spaCy
        doc = self.nlp(full_text[:10000])  # Limit to 10k chars

        # Extract entities
        entities = self._extract_entities(doc, article.get("url", ""))

        # Extract relations
        relations = self._extract_relations(doc, entities, article.get("url", ""))

        # Extract key concepts (noun chunks)
        concepts = self._extract_concepts(doc)

        logger.debug(f"Extracted {len(entities)} entities, {len(relations)} relations from '{title[:50]}'")

        return {
            **article,
            "entities": [e.__dict__ for e in entities],
            "relations": [r.__dict__ for r in relations],
            "concepts": concepts,
            "entity_count": len(entities),
        }

    def _extract_entities(self, doc, source_url: str) -> List[Entity]:
        """Extract named entities from a spaCy doc."""
        entities = []
        seen = set()

        for ent in doc.ents:
            label = self.ENTITY_TYPES.get(ent.label_, ent.label_.lower())

            # Normalize entity text
            normalized = ent.text.strip()
            if not normalized or len(normalized) < 2:
                continue

            # Deduplicate
            key = (normalized.lower(), label)
            if key in seen:
                continue
            seen.add(key)

            entity = Entity(
                text=normalized,
                label=label,
                start=ent.start_char,
                end=ent.end_char,
                source_url=source_url,
                properties={"spacy_label": ent.label_}
            )
            entities.append(entity)

            # Cache for cross-document linking
            self._entity_cache[normalized.lower()] = entity

        return entities

    def _extract_relations(self, doc, entities: List[Entity], source_url: str) -> List[Relation]:
        """Extract relationships between entities using dependency parsing."""
        relations = []
        entity_texts = {e.text.lower() for e in entities}

        for sent in doc.sents:
            for token in sent:
                # Look for verbs connecting two entities
                if token.pos_ == "VERB":
                    subj = None
                    obj = None

                    for child in token.children:
                        if child.dep_ in ("nsubj", "nsubjpass") and child.text.lower() in entity_texts:
                            subj = child.text
                        if child.dep_ in ("dobj", "pobj", "attr") and child.text.lower() in entity_texts:
                            obj = child.text

                    if subj and obj:
                        relations.append(Relation(
                            subject=subj,
                            predicate=token.lemma_,
                            object=obj,
                            source_url=source_url
                        ))

        # Also apply pattern-based extraction
        text_lower = doc.text.lower()
        for pattern, predicate in self.RELATION_PATTERNS:
            if pattern in text_lower:
                idx = text_lower.find(pattern)
                # Find nearest entities around this pattern
                nearby_entities = [
                    e for e in entities
                    if abs(e.start - idx) < 200 or abs(e.end - idx) < 200
                ]
                if len(nearby_entities) >= 2:
                    relations.append(Relation(
                        subject=nearby_entities[0].text,
                        predicate=predicate,
                        object=nearby_entities[1].text,
                        confidence=0.7,
                        source_url=source_url
                    ))

        return relations[:50]  # Cap at 50 relations per article

    def _extract_concepts(self, doc) -> List[str]:
        """Extract key concepts as noun phrases."""
        concepts = []
        seen = set()

        for chunk in doc.noun_chunks:
            concept = chunk.text.strip().lower()
            # Filter short/common phrases
            if len(concept) > 3 and concept not in seen:
                # Remove leading determiners
                concept = concept.lstrip("the ").lstrip("a ").lstrip("an ")
                if concept and len(concept) > 3:
                    concepts.append(concept)
                    seen.add(concept)

        return concepts[:30]  # Return top 30 concepts

    def batch_extract(self, articles: List[Dict]) -> List[Dict]:
        """Extract entities from a batch of articles."""
        return [self.extract(article) for article in articles]

    def get_entity_stats(self) -> Dict:
        """Get statistics about extracted entities."""
        from collections import Counter
        label_counts = Counter(e.label for e in self._entity_cache.values())
        return {
            "total_entities": len(self._entity_cache),
            "by_type": dict(label_counts),
            "top_entities": sorted(
                self._entity_cache.keys(),
                key=lambda k: len(self._entity_cache[k].text)
            )[:20]
        }
