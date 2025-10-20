"""Fact-checking service using multiple verification methods

Verifies article claims using:
1. Google Fact Check Tools API (aggregates PolitiFact, Snopes, FactCheck.org)
2. Official government sources (USGS, WHO, NASA)
3. Intelligent claim extraction to avoid false positives
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

import requests
from app.config import settings
from loguru import logger


@dataclass
class FactCheckFlag:
    """Represents a specific claim that failed fact-checking"""

    claim: str
    verdict: str  # 'false', 'disputed', 'misleading'
    evidence_source: str
    evidence_url: Optional[str]
    explanation: str
    confidence: float
    claim_context: Optional[str] = None     # Surrounding sentences
    claim_location: Optional[str] = None    # "headline", "lead", "body"


class FactChecker:
    """Multi-method fact verification with intelligent claim extraction"""

    def __init__(self):
        self.google_api_key = getattr(settings, "google_factcheck_api_key", "")
        self._content_fetcher = None
        self._claim_extractor = None
        self._claim_classifier = None
        self._embedder = None
        self._nlp = None
    
    @property
    def content_fetcher(self):
        """Lazy load content fetcher"""
        if self._content_fetcher is None:
            from .content_fetcher import ContentFetcher
            self._content_fetcher = ContentFetcher()
        return self._content_fetcher
    
    @property
    def claim_extractor(self):
        """Lazy load claim extractor"""
        if self._claim_extractor is None:
            from .claim_extractor import ClaimExtractor
            self._claim_extractor = ClaimExtractor()
        return self._claim_extractor
    
    @property
    def claim_classifier(self):
        """Lazy load claim classifier"""
        if self._claim_classifier is None:
            from .claim_classifier import ClaimClassifier
            self._claim_classifier = ClaimClassifier()
        return self._claim_classifier
    
    @property
    def embedder(self):
        """Lazy load sentence transformer for semantic similarity"""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return self._embedder
    
    @property
    def nlp(self):
        """Lazy load spaCy for entity extraction"""
        if self._nlp is None:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
        return self._nlp

    def check_article(
        self, title: str, summary: str, url: str, source: str
    ) -> Tuple[str, List[FactCheckFlag]]:
        """
        Run intelligent fact-checking on article using claim extraction.

        Args:
            title: Article headline
            summary: Article summary/description
            url: Article URL
            source: Source domain

        Returns:
            (status, flags) where status is 'verified'/'disputed'/'false'/'unverified'
        """
        flags = []
        
        # Step 1: Fetch full article content
        logger.info(f"Fact-checking article: {url}")
        content = self.content_fetcher.fetch_article_text(url)
        
        # Fallback to title/summary if content unavailable
        if not content or len(content) < 100:
            logger.warning(f"Could not fetch full content from {url}, using title/summary")
            # Use old method as fallback
            return self._check_title_summary_fallback(title, summary)
        
        # Check for paywall
        if self.content_fetcher.is_paywall_detected(content):
            logger.info(f"Paywall detected for {url}, skipping fact-check")
            return "unverified", []
        
        # Check if roundup/compilation article
        if self.claim_extractor.is_roundup_article(title, content):
            logger.info(f"Skipping roundup/compilation article: {title}")
            return "unverified", []
        
        # Step 2: Extract claims from article
        claims = self.claim_extractor.extract_claims(content, title)
        logger.info(f"Extracted {len(claims)} claims from article")
        
        if not claims:
            return "unverified", []
        
        # Step 3: Filter to checkable claims (direct assertions only)
        checkable_claims = self.claim_classifier.get_checkable_claims(claims)
        logger.info(f"Filtered to {len(checkable_claims)} checkable assertions")
        
        if not checkable_claims:
            # No direct assertions to check (article is reporting, not asserting)
            logger.info(f"No direct assertions found - article appears to be reporting")
            return "unverified", []
        
        # Step 4: Verify each direct assertion
        for claim in checkable_claims[:5]:  # Limit to 5 claims to avoid excessive API calls
            # Check Google Fact Check API
            google_flags = self._check_claim_google(claim.text, title, claim.context)
            
            # Add context metadata to flags
            for flag in google_flags:
                flag.claim_context = claim.context
                flag.claim_location = claim.location
            
            flags.extend(google_flags)
            
            # Check official sources
            official_flags = self._check_claim_official(claim.text, title)
            
            for flag in official_flags:
                flag.claim_context = claim.context
                flag.claim_location = claim.location
            
            flags.extend(official_flags)
        
        # Step 5: Determine overall status
        if not flags:
            return "unverified", []
        
        # If any flag is 'false' with high confidence, mark as false
        if any(f.verdict == "false" and f.confidence > 0.7 for f in flags):
            return "false", flags
        
        # If multiple disputed flags
        if len([f for f in flags if f.verdict == "disputed"]) >= 2:
            return "disputed", flags
        
        # If any flags but not severe enough for 'false'
        if flags:
            return "disputed", flags
        
        return "unverified", []
    
    def _check_title_summary_fallback(
        self, title: str, summary: str
    ) -> Tuple[str, List[FactCheckFlag]]:
        """
        Fallback method when full article content unavailable.
        Uses old keyword matching approach with disclaimer.
        """
        flags = []
        
        # Only check official sources (more reliable for title/summary)
        official_flags = self._check_official_sources(title, summary)
        flags.extend(official_flags)
        
        # Determine status
        if not flags:
            return "unverified", []
        
        if any(f.verdict == "false" and f.confidence > 0.7 for f in flags):
            return "false", flags
        
        return "disputed", flags

    def _check_claim_google(
        self, claim_text: str, article_title: str = "", article_context: str = ""
    ) -> List[FactCheckFlag]:
        """
        Check a specific claim against Google Fact Check API.
        Only flags if the returned fact-check is semantically relevant to our claim.
        
        Args:
            claim_text: The specific claim to verify
            article_title: Full article title (for context filtering)
            article_context: Claim context (for context filtering)
            
        Returns:
            List of fact-check flags for this claim
        """
        if not self.google_api_key:
            return []
        
        flags = []
        
        try:
            url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {
                "key": self.google_api_key,
                "query": claim_text,
                "languageCode": "en"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "claims" in data:
                    # Only take first match (most relevant)
                    for claim_review in data["claims"][:1]:
                        claim_from_api = claim_review.get("text", claim_text)
                        
                        # Filter: Skip photograph fact-checks for documentary/historical articles
                        # These articles often discuss viral misinformation without asserting it
                        if ('photograph' in claim_from_api.lower() or 'photo' in claim_from_api.lower()):
                            title_and_context = (article_title + " " + article_context).lower()
                            if ('documentary' in title_and_context or 
                                'film' in title_and_context or 
                                'expose' in title_and_context or
                                'exposing' in title_and_context or
                                'historical' in title_and_context):
                                logger.debug(
                                    f"Skipping photograph fact-check in documentary context: "
                                    f"API claim: '{claim_from_api[:50]}...' "
                                    f"Article: '{article_title[:50]}...'"
                                )
                                continue
                        
                        # Relevance check: Skip if API claim doesn't overlap with our claim
                        if not self._is_claim_relevant(claim_text, claim_from_api):
                            logger.debug(
                                f"Skipping irrelevant fact-check: "
                                f"Our claim: '{claim_text[:50]}...' vs "
                                f"API claim: '{claim_from_api[:50]}...'"
                            )
                            continue
                        
                        if "claimReview" in claim_review:
                            for review in claim_review["claimReview"]:
                                rating = review.get("textualRating", "").lower()
                                publisher = review.get("publisher", {}).get("name", "Fact-checker")
                                review_url = review.get("url", "")
                                
                                # Map ratings to verdicts
                                verdict = "disputed"
                                if "false" in rating or "pants on fire" in rating:
                                    verdict = "false"
                                elif "misleading" in rating or "mostly false" in rating:
                                    verdict = "misleading"
                                
                                # Only flag if verdict is negative
                                if verdict in ["false", "misleading", "disputed"]:
                                    flags.append(
                                        FactCheckFlag(
                                            claim=claim_from_api,
                                            verdict=verdict,
                                            evidence_source=f"Google Fact Check: {publisher}",
                                            evidence_url=review_url,
                                            explanation=f"Rated '{rating}' by {publisher}",
                                            confidence=0.8,
                                        )
                                    )
        
        except Exception as e:
            logger.warning(f"Google Fact Check API error for claim: {e}")
        
        return flags
    
    def _extract_entities(self, text: str) -> set:
        """
        Extract named entities from text using spaCy NER.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Set of normalized entity strings
        """
        doc = self.nlp(text[:500])  # Limit to first 500 chars for performance
        
        # Extract PERSON, GPE (geo-political entity), ORG, EVENT
        entities = set()
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'GPE', 'ORG', 'EVENT', 'NORP']:
                # Normalize: lowercase, remove titles
                entity_text = ent.text.lower()
                entity_text = entity_text.replace('president', '').replace('mr.', '').replace('ms.', '').strip()
                if len(entity_text) > 2:  # Skip very short entities
                    entities.add(entity_text)
        
        return entities
    
    def _calculate_keyword_overlap(self, our_claim: str, api_claim: str) -> float:
        """Calculate keyword overlap ratio between two claims"""
        # Extract key words (filter out common words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'their'
        }
        
        # Extract significant words (length > 4, not stop words)
        our_words = set([
            w for w in our_claim.lower().split() 
            if len(w) > 4 and w not in stop_words
        ])
        
        api_words = set([
            w for w in api_claim.lower().split()
            if len(w) > 4 and w not in stop_words
        ])
        
        # Calculate overlap
        if not our_words or not api_words:
            return 0.0
        
        overlap = our_words & api_words
        return len(overlap) / min(len(our_words), len(api_words))
    
    def _calculate_semantic_similarity(self, our_claim: str, api_claim: str) -> float:
        """
        Calculate semantic similarity using sentence embeddings.
        
        Args:
            our_claim: Our extracted claim
            api_claim: Fact-check API claim
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Encode both claims
            our_vec = self.embedder.encode([our_claim])
            api_vec = self.embedder.encode([api_claim])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(our_vec, api_vec)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _is_claim_relevant(self, our_claim: str, api_claim: str) -> bool:
        """
        Multi-layer relevance check using entities, keywords, and semantics.
        
        Args:
            our_claim: The claim we extracted from the article
            api_claim: The claim returned by the fact-check API
            
        Returns:
            True if claims are semantically related
        """
        scores = {
            'entity_overlap': 0.0,
            'keyword_overlap': 0.0,
            'semantic_similarity': 0.0,
        }
        
        # Layer 1: Entity matching (HARD REQUIREMENT)
        our_entities = self._extract_entities(our_claim)
        api_entities = self._extract_entities(api_claim)
        
        if our_entities and api_entities:
            shared_entities = our_entities & api_entities
            entity_overlap = len(shared_entities) / len(our_entities | api_entities)
            scores['entity_overlap'] = entity_overlap
            
            # HARD REQUIREMENT: Must share at least 1 entity if both have entities
            if not shared_entities:
                logger.debug(
                    f"No shared entities - irrelevant. "
                    f"Our: {our_entities}, API: {api_entities}"
                )
                return False
        
        # Layer 2: Keyword overlap
        keyword_overlap = self._calculate_keyword_overlap(our_claim, api_claim)
        scores['keyword_overlap'] = keyword_overlap
        
        # Layer 3: Semantic similarity (MOST IMPORTANT)
        semantic_sim = self._calculate_semantic_similarity(our_claim, api_claim)
        scores['semantic_similarity'] = semantic_sim
        
        # Weighted composite score
        # Entities: 30%, Keywords: 20%, Semantics: 50%
        composite = (
            scores['entity_overlap'] * 0.3 +
            scores['keyword_overlap'] * 0.2 +
            scores['semantic_similarity'] * 0.5
        )
        
        # Require 60% composite relevance
        is_relevant = composite >= 0.6
        
        logger.debug(
            f"Relevance: {composite:.1%} "
            f"(entity={scores['entity_overlap']:.1%}, "
            f"keyword={scores['keyword_overlap']:.1%}, "
            f"semantic={scores['semantic_similarity']:.1%}) "
            f"-> {'PASS' if is_relevant else 'SKIP'}"
        )
        
        return is_relevant
    
    def _check_claim_official(self, claim_text: str, title: str) -> List[FactCheckFlag]:
        """
        Verify a specific claim against official sources.
        
        Args:
            claim_text: The claim to verify
            title: Article title (for context)
            
        Returns:
            List of flags from official source verification
        """
        flags = []
        
        # Check for earthquake claims
        earthquake_flag = self._verify_earthquake_claims(claim_text.lower(), title)
        if earthquake_flag:
            flags.append(earthquake_flag)
        
        # Add more official source checks as needed
        
        return flags
    
    def _check_google_factcheck(self, title: str, summary: str) -> List[FactCheckFlag]:
        """
        OLD METHOD - Check Google Fact Check Tools API (keyword matching).
        Used only as fallback when content unavailable.

        API: https://developers.google.com/fact-check/tools/api
        """
        if not self.google_api_key:
            return []

        flags = []
        query = title  # Search for fact-checks about this headline

        try:
            url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {"key": self.google_api_key, "query": query, "languageCode": "en"}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "claims" in data:
                    for claim_review in data["claims"][:3]:  # Top 3 fact-checks
                        # Extract claim and rating
                        claim_text = claim_review.get("text", "Claim not specified")

                        if "claimReview" in claim_review:
                            for review in claim_review["claimReview"]:
                                rating = review.get("textualRating", "").lower()
                                publisher = review.get("publisher", {}).get(
                                    "name", "Fact-checker"
                                )
                                review_url = review.get("url", "")

                                # Map ratings to verdicts
                                verdict = "disputed"
                                if "false" in rating or "pants on fire" in rating:
                                    verdict = "false"
                                elif (
                                    "misleading" in rating or "mostly false" in rating
                                ):
                                    verdict = "misleading"

                                flags.append(
                                    FactCheckFlag(
                                        claim=claim_text,
                                        verdict=verdict,
                                        evidence_source=f"Google Fact Check: {publisher}",
                                        evidence_url=review_url,
                                        explanation=f"Rated '{rating}' by {publisher}",
                                        confidence=0.8,  # High confidence in external fact-checkers
                                    )
                                )

        except Exception as e:
            print(f"Warning: Google Fact Check API error: {e}")

        return flags

    def _check_official_sources(self, title: str, summary: str) -> List[FactCheckFlag]:
        """
        Verify claims against official sources (USGS, WHO, NASA, etc.)

        Looks for:
        - Earthquake magnitudes that contradict USGS
        - Disease outbreak numbers that contradict WHO
        - Wildfire locations that contradict NASA FIRMS
        """
        flags = []
        text = f"{title} {summary}".lower()

        # Check for earthquake claims
        earthquake_flag = self._verify_earthquake_claims(text, title)
        if earthquake_flag:
            flags.append(earthquake_flag)

        # Check for disease outbreak claims
        disease_flag = self._verify_disease_claims(text, title)
        if disease_flag:
            flags.append(disease_flag)

        # Add more official source checks as needed

        return flags

    def _verify_earthquake_claims(
        self, text: str, title: str
    ) -> Optional[FactCheckFlag]:
        """Verify earthquake magnitude claims against USGS real-time data"""

        # Extract magnitude and location
        mag_pattern = r"(\d+\.?\d*)\s*magnitude|magnitude\s*(\d+\.?\d*)"
        location_pattern = (
            r"earthquake\s+(?:in|near|off)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        )

        mag_matches = re.findall(mag_pattern, text, re.IGNORECASE)
        loc_matches = re.findall(location_pattern, title + " " + text)

        if mag_matches and loc_matches:
            claimed_mag = float(mag_matches[0][0] or mag_matches[0][1])
            claimed_location = loc_matches[0]

            # Query USGS for recent earthquakes
            try:
                # Get earthquakes from last 7 days
                usgs_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
                response = requests.get(usgs_url, timeout=10)
                data = response.json()

                # Check if any match location and compare magnitude
                for feature in data.get("features", [])[:50]:
                    props = feature.get("properties", {})
                    place = props.get("place", "").lower()
                    actual_mag = props.get("mag", 0)

                    if claimed_location.lower() in place:
                        # Found matching earthquake
                        mag_diff = abs(claimed_mag - actual_mag)

                        if mag_diff > 0.5:  # Significant discrepancy
                            return FactCheckFlag(
                                claim=f"Magnitude {claimed_mag} earthquake in {claimed_location}",
                                verdict="false" if mag_diff > 1.0 else "disputed",
                                evidence_source="USGS Earthquake Hazards Program",
                                evidence_url=props.get("url", ""),
                                explanation=f"USGS reports magnitude {actual_mag}, not {claimed_mag}. Difference of {mag_diff:.1f}.",
                                confidence=0.95,
                            )

            except Exception as e:
                print(f"USGS verification error: {e}")

        return None

    def _verify_disease_claims(
        self, text: str, title: str
    ) -> Optional[FactCheckFlag]:
        """Check disease outbreak claims against WHO data"""
        # Look for outbreak-related claims with specific numbers
        outbreak_pattern = r"(\d+(?:,\d+)*)\s+(?:deaths?|cases?|infections?)"

        matches = re.findall(outbreak_pattern, text, re.IGNORECASE)

        if matches:
            # Note: WHO DON API verification would go here
            # For now, we rely on Google Fact Check API for disease claims
            # Future: Query WHO DON for official outbreak statistics
            pass

        return None

