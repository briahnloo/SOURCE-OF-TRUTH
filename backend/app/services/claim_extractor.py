"""Claim extraction service

Extracts declarative claims from article text using NLP.
Distinguishes factual assertions from quotes, attributions, and speculation.
"""

from dataclasses import dataclass
from typing import List, Optional
import spacy
from loguru import logger


@dataclass
class Claim:
    """Structured claim extracted from article text"""
    text: str                      # The claim statement
    context: str                   # Surrounding sentences for context
    attribution: Optional[str]     # Who is making the claim (if attributed)
    is_quoted: bool                # Is this in quotes?
    hedge_words: List[str]         # "allegedly", "may", "reportedly"
    sentence_type: str             # "assertion", "attribution", "speculation"
    location: str                  # "headline", "lead", "body"


class ClaimExtractor:
    """Extracts factual claims from article text using NLP"""
    
    def __init__(self):
        """Initialize claim extractor with spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            raise
        
        # Roundup/compilation article indicators
        self.roundup_indicators = {
            'this week', 'weekly roundup', 'top stories', 'headlines',
            'in brief', 'quick hits', 'news roundup', 'the week',
            'politics', 'business', 'world news', 'today in',
            'daily briefing', 'morning brief', 'evening brief',
            'digest', 'wrap-up', 'recap', 'summary'
        }
        
        # Hedge words that indicate uncertainty
        self.hedge_words = {
            'allegedly', 'reportedly', 'purportedly', 'supposedly',
            'may', 'might', 'could', 'would', 'possibly', 'perhaps',
            'appears', 'seems', 'suggests', 'indicates', 'likely'
        }
        
        # Attribution verbs
        self.attribution_verbs = {
            'says', 'said', 'claims', 'claimed', 'alleges', 'alleged',
            'states', 'stated', 'asserts', 'asserted', 'according',
            'believes', 'believes', 'argues', 'argued', 'contends',
            'maintains', 'insists', 'suggests', 'reports', 'told'
        }
        
        # Debunking indicators
        self.debunking_words = {
            'false', 'misleading', 'debunked', 'fact-check', 'untrue',
            'incorrect', 'wrong', 'misinformation', 'disinformation',
            'hoax', 'fabricated', 'unverified', 'disputed'
        }
    
    def extract_claims(self, text: str, title: str = "") -> List[Claim]:
        """
        Extract declarative claims from article text.
        
        Args:
            text: Full article text
            title: Article headline (for location tracking)
            
        Returns:
            List of extracted claims
        """
        if not text or len(text) < 50:
            return []
        
        # Clean text: remove boilerplate
        text = self._clean_boilerplate(text)
        
        if not text or len(text) < 100:
            return []
        
        claims = []
        
        # Process title as potential claim
        if title:
            title_claim = self._process_sentence(title, "", "headline")
            if title_claim and len(title_claim.text) > 15:
                claims.append(title_claim)
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 30]
        
        # Process first 3 substantive paragraphs as "lead"
        lead_text = ' '.join(paragraphs[:3]) if len(paragraphs) >= 3 else text[:500]
        lead_claims = self._extract_from_text(lead_text, "lead")
        claims.extend(lead_claims)
        
        # Process remaining text as "body" (limit to avoid performance issues)
        if len(paragraphs) > 3:
            body_text = ' '.join(paragraphs[3:10])  # First 10 paragraphs total
            body_claims = self._extract_from_text(body_text, "body")
            claims.extend(body_claims)
        
        return claims
    
    def _clean_boilerplate(self, text: str) -> str:
        """
        Remove common boilerplate content from articles.
        
        Args:
            text: Raw article text
            
        Returns:
            Cleaned text with boilerplate removed
        """
        # Boilerplate patterns to remove
        boilerplate_patterns = [
            # Support/subscription messages
            r'Your support helps us.*?(?=\n\n|\Z)',
            r'Your donation.*?(?=\n\n|\Z)',
            r'We need reporters on the ground.*?(?=\n\n|\Z)',
            r'Read more Support Now.*?(?=\n\n|\Z)',
            r'Support The Independent.*?(?=\n\n|\Z)',
            r'The Independent is trusted.*?(?=\n\n|\Z)',
            r'We choose not to lock.*?(?=\n\n|\Z)',
            r'.*?makes all the difference.*?(?=\n\n|\Z)',
            r'Subscribe to Independent Premium.*?(?=\n\n|\Z)',
            
            # Navigation/UI elements
            r'Read more:.*?(?=\n)',
            r'Sign up.*?newsletter.*?(?=\n\n|\Z)',
            r'Follow us on.*?(?=\n)',
            r'Share this article.*?(?=\n)',
            
            # Cookie/privacy notices
            r'We use cookies.*?(?=\n\n|\Z)',
            r'By continuing to use.*?(?=\n\n|\Z)',
        ]
        
        import re
        cleaned = text
        for pattern in boilerplate_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove multiple newlines
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def _extract_from_text(self, text: str, location: str) -> List[Claim]:
        """Extract claims from a text segment"""
        if not text:
            return []
        
        # Parse with spaCy
        doc = self.nlp(text)
        claims = []
        
        # Process each sentence
        sentences = list(doc.sents)
        for i, sent in enumerate(sentences):
            # Get context (prev + current + next sentence)
            context_parts = []
            if i > 0:
                context_parts.append(sentences[i-1].text)
            context_parts.append(sent.text)
            if i < len(sentences) - 1:
                context_parts.append(sentences[i+1].text)
            context = ' '.join(context_parts)
            
            # Process sentence
            claim = self._process_sentence(sent.text, context, location)
            if claim:
                claims.append(claim)
        
        return claims
    
    def _process_sentence(self, sentence: str, context: str, location: str) -> Optional[Claim]:
        """Process a single sentence to extract claim"""
        if not sentence or len(sentence) < 10:
            return None
        
        # Parse sentence
        doc = self.nlp(sentence)
        
        # Skip questions
        if sentence.strip().endswith('?'):
            return None
        
        # Detect quotes
        is_quoted = '"' in sentence or "'" in sentence or '"' in sentence or '"' in sentence
        
        # Extract hedge words present
        sentence_lower = sentence.lower()
        found_hedges = [w for w in self.hedge_words if w in sentence_lower]
        
        # Detect attribution
        attribution = self._detect_attribution(doc)
        
        # Detect debunking
        is_debunking = any(w in sentence_lower for w in self.debunking_words)
        
        # Classify sentence type
        if attribution:
            sentence_type = "attribution"
        elif is_debunking:
            sentence_type = "debunking"
        elif found_hedges:
            sentence_type = "speculation"
        else:
            sentence_type = "assertion"
        
        # Only return if it's a declarative statement with substance
        if len(doc) < 5:  # Too short
            return None
        
        return Claim(
            text=sentence.strip(),
            context=context,
            attribution=attribution,
            is_quoted=is_quoted,
            hedge_words=found_hedges,
            sentence_type=sentence_type,
            location=location
        )
    
    def _detect_attribution(self, doc) -> Optional[str]:
        """
        Detect if sentence is attributed to someone.
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            Attribution source or None
        """
        # Look for attribution patterns
        for token in doc:
            # Check if token is an attribution verb
            if token.lemma_.lower() in self.attribution_verbs:
                # Try to find the subject (who is saying this)
                for child in token.children:
                    if child.dep_ in ['nsubj', 'nsubjpass']:
                        # Get the full noun phrase
                        subject = child.text
                        # Expand to include modifiers
                        if child.head:
                            subject_span = doc[child.left_edge.i:child.right_edge.i+1]
                            subject = subject_span.text
                        return subject
        
        # Check for "according to" pattern
        text_lower = doc.text.lower()
        if 'according to' in text_lower:
            # Extract what comes after "according to"
            idx = text_lower.index('according to')
            after = doc.text[idx+12:].split(',')[0].split('.')[0].strip()
            if after:
                return after[:100]  # Limit length
        
        return None
    
    def is_roundup_article(self, title: str, text: str = "") -> bool:
        """
        Detect if article is a news roundup/compilation.
        
        These articles aggregate multiple unrelated stories and should not be fact-checked
        as they create keyword soup that triggers false positives.
        
        Args:
            title: Article title
            text: Article text (optional)
            
        Returns:
            True if article appears to be a roundup/compilation
        """
        title_lower = title.lower()
        
        # Check title for roundup indicators
        if any(indicator in title_lower for indicator in self.roundup_indicators):
            logger.info(f"Detected roundup article from title: '{title}'")
            return True
        
        # Check if title is very short and generic (likely a section page)
        title_words = title.split()
        if len(title_words) <= 2 and title_words[0].lower() in ['politics', 'business', 'world', 'sports', 'tech']:
            logger.info(f"Detected generic section title: '{title}'")
            return True
        
        return False

