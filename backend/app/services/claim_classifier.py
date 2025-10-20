"""Claim classification service

Classifies claims as direct assertions vs attributed/reported claims.
Prevents false positives from articles reporting on misinformation.
"""

from typing import List
from loguru import logger
from .claim_extractor import Claim


class ClaimClassifier:
    """Classifies claims to determine if they should be fact-checked"""
    
    def __init__(self):
        """Initialize claim classifier"""
        # Patterns that indicate reporting rather than asserting
        self.reporting_patterns = [
            'social media', 'posts claim', 'viral', 'circulating',
            'unverified reports', 'rumors', 'speculation', 'conspiracy'
        ]
    
    def classify_claim(self, claim: Claim) -> str:
        """
        Classify a claim to determine fact-checking eligibility.
        
        Args:
            claim: Extracted claim object
            
        Returns:
            Classification: 'direct_assertion', 'attributed', 'debunking', 'reported'
        """
        # If already classified as non-assertion by extractor
        if claim.sentence_type == "attribution":
            return "attributed"
        
        if claim.sentence_type == "debunking":
            return "debunking"
        
        if claim.sentence_type == "speculation":
            return "reported"
        
        # Check if quoted (likely someone else's words)
        if claim.is_quoted and claim.attribution:
            return "attributed"
        
        # Check for hedge words (uncertainty)
        if claim.hedge_words:
            return "reported"
        
        # Check context for reporting patterns
        context_lower = claim.context.lower()
        if any(pattern in context_lower for pattern in self.reporting_patterns):
            return "reported"
        
        # Check if attribution exists
        if claim.attribution:
            return "attributed"
        
        # If none of the above, it's a direct assertion
        return "direct_assertion"
    
    def should_fact_check(self, claim: Claim) -> bool:
        """
        Determine if a claim should be fact-checked.
        
        Args:
            claim: Extracted claim
            
        Returns:
            True if claim should be verified
        """
        classification = self.classify_claim(claim)
        
        # Only fact-check direct assertions
        if classification != "direct_assertion":
            logger.debug(
                f"Skipping fact-check: '{claim.text[:50]}...' "
                f"(classified as: {classification})"
            )
            return False
        
        # Additional filters
        
        # Skip very short claims
        if len(claim.text) < 15:
            return False
        
        # Skip opinion markers
        opinion_markers = ['i think', 'i believe', 'in my view', 'opinion']
        if any(marker in claim.text.lower() for marker in opinion_markers):
            return False
        
        # Skip government/official statements (likely quotes)
        # Common patterns: "X firmly opposes", "X official statement", etc.
        govt_statement_patterns = ['firmly opposes', 'official statement', 
                                   'ministry said', 'government denies']
        if any(pattern in claim.text.lower() for pattern in govt_statement_patterns):
            logger.debug(
                f"Skipping fact-check: '{claim.text[:50]}...' "
                f"(appears to be government statement/quote)"
            )
            return False
        
        # Skip claims about historical photographs in documentary contexts
        # These are often discussing viral misinformation, not asserting it
        if ('photograph' in claim.text.lower() or 'photo' in claim.text.lower()):
            context_lower = claim.context.lower()
            if ('documentary' in context_lower or 
                'film' in context_lower or 
                'exposing' in context_lower or
                'viral' in context_lower):
                logger.debug(
                    f"Skipping fact-check: '{claim.text[:50]}...' "
                    f"(photograph claim in documentary/viral context)"
                )
                return False
        
        return True
    
    def get_checkable_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Filter claims to only those that should be fact-checked.
        
        Args:
            claims: List of extracted claims
            
        Returns:
            Filtered list of claims eligible for fact-checking
        """
        checkable = [c for c in claims if self.should_fact_check(c)]
        
        logger.info(
            f"Filtered {len(claims)} claims to {len(checkable)} checkable assertions"
        )
        
        return checkable

