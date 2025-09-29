"""Hazard detection and classification for the Ocean Hazard Monitoring system"""
import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from .nlp_processor import NLPProcessor

# Configure logging
logger = logging.getLogger(__name__)

class HazardDetector:
    """Detects and classifies ocean hazards from text data"""
    
    def __init__(self):
        # Initialize NLP processor
        self.nlp_processor = NLPProcessor()
        
        # Define hazard keywords and patterns
        self.hazard_patterns = {
            "flood": [
                r'flood(ing)?',
                r'water level(s)? rise',
                r'submerged',
                r'inundat(e|ion)'
            ],
            "storm_surge": [
                r'storm\s*surge',
                r'surge\s*warning',
                r'coastal\s*surge',
                r'sea\s*level\s*rise'
            ],
            "tsunami": [
                r'tsunami',
                r'tidal\s*wave',
                r'seismic\s*sea\s*wave'
            ],
            "high_waves": [
                r'high\s*waves?',
                r'large\s*waves?',
                r'dangerous\s*waves?',
                r'rough\s*seas?',
                r'wave\s*height'
            ],
            "erosion": [
                r'erosion',
                r'coastal\s*erosion',
                r'beach\s*loss',
                r'shoreline\s*retreat'
            ],
            "marine_pollution": [
                r'oil\s*spill',
                r'pollut(e|ion)',
                r'contaminat(e|ion)',
                r'marine\s*debris',
                r'plastic\s*waste'
            ],
            "harmful_algal_bloom": [
                r'harmful\s*algal\s*bloom',
                r'red\s*tide',
                r'blue\s*tide',
                r'algal\s*bloom'
            ],
            "coastal_storm": [
                r'coastal\s*storm',
                r'tropical\s*storm',
                r'hurricane',
                r'typhoon',
                r'cyclone'
            ]
        }
        
        # Define severity indicators
        self.severity_indicators = {
            "high": [
                r'major',
                r'severe',
                r'catastrophic',
                r'dangerous',
                r'urgent',
                r'emergency',
                r'critical',
                r'extreme',
                r'life-threatening',
                r'evacuation',
                r'damage',
                r'destroy',
                r'collapse',
                r'injured',
                r'casualty',
                r'fatal'
            ],
            "medium": [
                r'moderate',
                r'significant',
                r'noticeable',
                r'concerning',
                r'warning',
                r'alert',
                r'precautionary',
                r'potential',
                r'possible',
                r'expected'
            ],
            "low": [
                r'minor',
                r'slight',
                r'mild',
                r'small',
                r'observation',
                r'monitoring',
                r'update',
                r'information'
            ]
        }
        
        # Define location patterns
        self.location_patterns = [
            r'\bin\s+([^,]+)',  # "in City Name"
            r'\sat\s+([^,]+)',  # "at Location"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:coast|beach|pier|harbor|port|town|city|village)',  #