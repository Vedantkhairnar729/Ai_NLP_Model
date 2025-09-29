"""Core data collection functionality for the Ocean Hazard Monitoring system"""
import abc
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
import tweepy
from dotenv import load_dotenv
import os

# Configure logging
logger = logging.getLogger(__name__)

class DataSource(abc.ABC):
    """Abstract base class for data sources"""
    
    @abc.abstractmethod
    def collect_data(self, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Collect data from the source"""
        pass

class CitizenReportSource(DataSource):
    """Data source for citizen reports"""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or "https://api.oceanhazard.example/reports"
        
    def collect_data(self, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Collect citizen reports from the API"""
        try:
            params = params or {}
            # In a real implementation, this would make an API call
            # For now, we'll return mock data
            logger.info(f"Collecting citizen reports with params: {params}")
            
            # Mock data for demonstration
            return [
                {
                    "id": "report_1",
                    "type": "flood",
                    "location": "Coastal City A",
                    "latitude": 34.0522,
                    "longitude": -118.2437,
                    "severity": "high",
                    "description": "Major flooding near the pier",
                    "timestamp": datetime.now().isoformat(),
                    "source": "citizen_report"
                },
                {
                    "id": "report_2",
                    "type": "storm_surge",
                    "location": "Beach Town B",
                    "latitude": 36.7783,
                    "longitude": -119.4179,
                    "severity": "medium",
                    "description": "Waves reaching the boardwalk",
                    "timestamp": (datetime.now() - pd.Timedelta(hours=1)).isoformat(),
                    "source": "citizen_report"
                }
            ]
        except Exception as e:
            logger.error(f"Error collecting citizen reports: {str(e)}")
            return []

class SocialMediaSource(DataSource):
    """Data source for social media posts"""
    
    def __init__(self):
        load_dotenv()
        # In a real implementation, we would authenticate with the Twitter API
        # For now, we'll just store the keys
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
    def collect_data(self, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Collect social media posts related to ocean hazards"""
        try:
            params = params or {}
            keywords = params.get("keywords", ["ocean hazard", "coastal flooding", "storm surge"])
            logger.info(f"Collecting social media posts with keywords: {keywords}")
            
            # In a real implementation, this would use the Twitter API
            # For now, we'll return mock data
            return [
                {
                    "id": "tweet_1",
                    "text": "The waves are getting dangerously high at Coastal City beach! #oceanhazard #flooding",
                    "location": "Coastal City",
                    "latitude": 34.0522,
                    "longitude": -118.2437,
                    "timestamp": (datetime.now() - pd.Timedelta(minutes=30)).isoformat(),
                    "source": "twitter",
                    "user": "@concerned_citizen"
                },
                {
                    "id": "tweet_2",
                    "text": "Just heard a weather alert about potential storm surge in the area. Stay safe everyone!",
                    "location": "Beach Town",
                    "latitude": 36.7783,
                    "longitude": -119.4179,
                    "timestamp": (datetime.now() - pd.Timedelta(hours=2)).isoformat(),
                    "source": "twitter",
                    "user": "@local_weather"
                }
            ]
        except Exception as e:
            logger.error(f"Error collecting social media posts: {str(e)}")
            return []

class NewsFeedSource(DataSource):
    """Data source for news feeds"""
    
    def __init__(self):
        self.news_sources = ["https://example-news.com/ocean-hazards", "https://weather-service.example/alerts"]
        
    def collect_data(self, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Collect news articles related to ocean hazards"""
        try:
            params = params or {}
            logger.info("Collecting news articles about ocean hazards")
            
            # In a real implementation, this would scrape news websites or use news APIs
            # For now, we'll return mock data
            return [
                {
                    "id": "news_1",
                    "title": "Coastal Communities Prepare for Upcoming Storm",
                    "content": "Local authorities are issuing warnings and preparing emergency response teams as a tropical system approaches the coast.",
                    "source": "Coastal News Network",
                    "url": "https://example-news.com/storm-warning",
                    "timestamp": (datetime.now() - pd.Timedelta(hours=4)).isoformat(),
                    "location": "Regional Coast"
                }
            ]
        except Exception as e:
            logger.error(f"Error collecting news articles: {str(e)}")
            return []

class DataCollector:
    """Core data collector that aggregates data from multiple sources"""
    
    def __init__(self):
        self.sources = {
            "citizen_reports": CitizenReportSource(),
            "social_media": SocialMediaSource(),
            "news_feeds": NewsFeedSource()
        }
        self.collected_data = []
        
    def register_source(self, name: str, source: DataSource):
        """Register a new data source"""
        self.sources[name] = source
        logger.info(f"Registered new data source: {name}")
        
    def collect_all_data(self, params: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Collect data from all registered sources"""
        all_data = []
        params = params or {}
        
        for source_name, source in self.sources.items():
            source_params = params.get(source_name, {})
            logger.info(f"Collecting data from {source_name}")
            
            try:
                source_data = source.collect_data(source_params)
                all_data.extend(source_data)
                logger.info(f"Successfully collected {len(source_data)} items from {source_name}")
            except Exception as e:
                logger.error(f"Error collecting data from {source_name}: {str(e)}")
        
        self.collected_data = all_data
        return all_data
    
    def collect_from_source(self, source_name: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Collect data from a specific source"""
        if source_name not in self.sources:
            logger.error(f"Source not found: {source_name}")
            return []
        
        logger.info(f"Collecting data from {source_name}")
        return self.sources[source_name].collect_data(params)
    
    def save_data(self, file_path: str, format: str = "csv"):
        """Save collected data to a file"""
        if not self.collected_data:
            logger.warning("No data to save")
            return
        
        try:
            df = pd.DataFrame(self.collected_data)
            if format.lower() == "csv":
                df.to_csv(file_path, index=False)
            elif format.lower() == "json":
                df.to_json(file_path, orient="records")
            else:
                logger.error(f"Unsupported format: {format}")
                return
            
            logger.info(f"Successfully saved {len(self.collected_data)} items to {file_path}")
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {str(e)}")

# Example usage
if __name__ == "__main__":
    collector = DataCollector()
    data = collector.collect_all_data()
    print(f"Collected {len(data)} items")
    for item in data:
        print(f"- {item['source']}: {item.get('description', item.get('text', item.get('title', 'No description')))}")