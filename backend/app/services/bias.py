"""Bias analysis service for source classification

Analyzes coverage bias across four dimensions:
- Geographic: Western vs Eastern vs Global South
- Political: Left vs Center vs Right  
- Tone: Sensational vs Factual
- Detail: Surface vs Deep
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class BiasScore:
    """Bias scores across four dimensions"""
    geographic: Dict[str, float]  # {"western": 0.7, "eastern": 0.2, "global_south": 0.1}
    political: Dict[str, float]   # {"left": 0.3, "center": 0.6, "right": 0.1}
    tone: Dict[str, float]        # {"sensational": 0.2, "factual": 0.8}
    detail: Dict[str, float]      # {"surface": 0.3, "deep": 0.7}


class BiasAnalyzer:
    """Analyzes source bias and calculates event-level bias scores"""
    
    def __init__(self):
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Load source bias metadata from JSON file"""
        metadata_path = Path(__file__).parent.parent / "data" / "source_bias_metadata.json"
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Bias metadata file not found at {metadata_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse bias metadata: {e}")
            return {}
    
    def get_source_bias(self, source_url: str) -> Optional[BiasScore]:
        """Get bias scores for a source
        
        Args:
            source_url: Source URL or domain
            
        Returns:
            BiasScore if source is in metadata, None otherwise
        """
        domain = self._extract_domain(source_url)
        
        if domain not in self.metadata:
            return None
        
        data = self.metadata[domain]
        return BiasScore(
            geographic=data.get("geographic", {}),
            political=data.get("political", {}),
            tone=data.get("tone", {}),
            detail=data.get("detail", {})
        )
    
    def calculate_event_bias(self, article_sources: List[str]) -> BiasScore:
        """Calculate aggregate bias for an event by averaging source biases
        
        Args:
            article_sources: List of source URLs/domains
            
        Returns:
            Averaged BiasScore across all classified sources
        """
        biases = []
        
        for source in article_sources:
            bias = self.get_source_bias(source)
            if bias:
                biases.append(bias)
        
        if not biases:
            # Return neutral defaults if no sources are classified
            return BiasScore(
                geographic={"western": 0.33, "eastern": 0.33, "global_south": 0.34},
                political={"left": 0.33, "center": 0.34, "right": 0.33},
                tone={"sensational": 0.5, "factual": 0.5},
                detail={"surface": 0.5, "deep": 0.5}
            )
        
        # Simple average across all sources
        return self._average_biases(biases)
    
    def _average_biases(self, biases: List[BiasScore]) -> BiasScore:
        """Average multiple bias scores
        
        Args:
            biases: List of BiasScore objects
            
        Returns:
            Averaged BiasScore
        """
        n = len(biases)
        
        avg_geo = {k: sum(b.geographic.get(k, 0) for b in biases) / n 
                   for k in ["western", "eastern", "global_south"]}
        avg_pol = {k: sum(b.political.get(k, 0) for b in biases) / n 
                   for k in ["left", "center", "right"]}
        avg_tone = {k: sum(b.tone.get(k, 0) for b in biases) / n 
                    for k in ["sensational", "factual"]}
        avg_detail = {k: sum(b.detail.get(k, 0) for b in biases) / n 
                      for k in ["surface", "deep"]}
        
        return BiasScore(
            geographic=avg_geo,
            political=avg_pol,
            tone=avg_tone,
            detail=avg_detail
        )
    
    def _extract_domain(self, source: str) -> str:
        """Extract clean domain from source URL or string
        
        Args:
            source: Source URL or domain string
            
        Returns:
            Clean domain name without www prefix and normalized subdomains
        """
        if source.startswith("http"):
            parsed = urlparse(source)
            domain = parsed.netloc
        else:
            domain = source
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Normalize common subdomain patterns to main domain
        # e.g., feeds.npr.org -> npr.org, rss.nytimes.com -> nytimes.com
        domain_mappings = {
            "feeds.npr.org": "npr.org",
            "rss.nytimes.com": "nytimes.com",
            "feeds.bbci.co.uk": "bbc.co.uk",
            "moxie.foxnews.com": "foxnews.com",
            "rss.cnn.com": "cnn.com",
            "rss.dw.com": "dw.com",
        }
        
        if domain in domain_mappings:
            domain = domain_mappings[domain]
        
        return domain

