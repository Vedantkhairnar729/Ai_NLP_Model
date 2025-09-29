"""Core NLP processing functionality for the Ocean Hazard Monitoring system"""
import logging
import re
import string
from typing import List, Dict, Any, Optional, Union

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import spacy
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Configure logging
logger = logging.getLogger(__name__)

class NLPProcessor:
    """Core NLP processor for text cleaning, tokenization, and analysis"""
    
    def __init__(self):
        # Initialize NLP components
        try:
            # Download required NLTK resources if not already present
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            
            # Initialize processing components
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
            # Initialize spaCy model
            try:
                self.nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
            except OSError:
                logger.warning("en_core_web_sm model not found. Downloading...")
                from spacy.cli import download
                download('en_core_web_sm')
                self.nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
            
            # Initialize transformer model for sentiment analysis
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
            
            logger.info("NLPProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NLPProcessor: {str(e)}")
            # Set minimal components even if some initialization fails
            self.stop_words = set()
            self.lemmatizer = None
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Clean raw text by removing unwanted characters and formatting"""
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Remove URLs
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            
            # Remove mentions and hashtags (keeping the text after hashtag)
            text = re.sub(r'@\w+', '', text)
            text = re.sub(r'#([^\s]+)', r'\1', text)
            
            # Remove punctuation
            text = text.translate(str.maketrans('', '', string.punctuation))
            
            # Remove numbers
            text = re.sub(r'\d+', '', text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into individual words"""
        if not text or not isinstance(text, str):
            return []
        
        try:
            tokens = word_tokenize(text)
            return tokens
        except Exception as e:
            logger.error(f"Error tokenizing text: {str(e)}")
            return []
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords from token list"""
        if not tokens or not isinstance(tokens, list):
            return []
        
        try:
            filtered_tokens = [token for token in tokens if token not in self.stop_words]
            return filtered_tokens
        except Exception as e:
            logger.error(f"Error removing stopwords: {str(e)}")
            return tokens
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens to their base form"""
        if not tokens or not isinstance(tokens, list) or not self.lemmatizer:
            return tokens
        
        try:
            lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            return lemmatized_tokens
        except Exception as e:
            logger.error(f"Error lemmatizing tokens: {str(e)}")
            return tokens
    
    def preprocess_text(self, text: str) -> Dict[str, Any]:
        """Complete text preprocessing pipeline"""
        result = {
            "original_text": text,
            "cleaned_text": "",
            "tokens": [],
            "tokens_no_stopwords": [],
            "lemmatized_tokens": []
        }
        
        try:
            # Clean text
            cleaned_text = self.clean_text(text)
            result["cleaned_text"] = cleaned_text
            
            # Tokenize
            tokens = self.tokenize_text(cleaned_text)
            result["tokens"] = tokens
            
            # Remove stopwords
            tokens_no_stopwords = self.remove_stopwords(tokens)
            result["tokens_no_stopwords"] = tokens_no_stopwords
            
            # Lemmatize
            lemmatized_tokens = self.lemmatize_tokens(tokens_no_stopwords)
            result["lemmatized_tokens"] = lemmatized_tokens
            
            # Join processed tokens back into text
            result["processed_text"] = " ".join(lemmatized_tokens)
            
        except Exception as e:
            logger.error(f"Error in text preprocessing pipeline: {str(e)}")
        
        return result
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Extract keywords from text using simple frequency-based approach"""
        if not text or not isinstance(text, str):
            return []
        
        try:
            # Preprocess text
            preprocessed = self.preprocess_text(text)
            
            # Calculate word frequencies
            word_freq = {}
            for token in preprocessed["lemmatized_tokens"]:
                if len(token) > 2:  # Ignore very short words
                    word_freq[token] = word_freq.get(token, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Return top N keywords
            return [
                {"keyword": word, "frequency": freq}
                for word, freq in sorted_words[:top_n]
            ]
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using transformer model"""
        if not text or not isinstance(text, str):
            return {"positive": 0.0, "negative": 1.0, "label": "negative"}
        
        try:
            # Tokenize input text
            inputs = self.sentiment_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Get model output
            outputs = self.sentiment_model(**inputs)
            
            # Calculate probabilities
            import torch
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1).tolist()[0]
            
            # Determine label
            label = "positive" if probabilities[1] > probabilities[0] else "negative"
            
            return {
                "negative": probabilities[0],
                "positive": probabilities[1],
                "label": label
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"positive": 0.0, "negative": 1.0, "label": "negative"}
    
    def process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of texts efficiently"""
        if not texts or not isinstance(texts, list):
            return []
        
        try:
            results = []
            for text in texts:
                # Get preprocessing results
                preprocessed = self.preprocess_text(text)
                
                # Add keywords and sentiment analysis
                preprocessed["keywords"] = self.extract_keywords(text)
                preprocessed["sentiment"] = self.analyze_sentiment(text)
                
                results.append(preprocessed)
            
            return results
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            return []

# Example usage
if __name__ == "__main__":
    processor = NLPProcessor()
    
    # Example text from a citizen report
    example_text = "There's major flooding near the pier in Coastal City! Waves are over 10 feet high and several buildings are affected."
    
    # Process the text
    processed = processor.preprocess_text(example_text)
    keywords = processor.extract_keywords(example_text)
    sentiment = processor.analyze_sentiment(example_text)
    
    print("Original text:", example_text)
    print("Cleaned text:", processed["cleaned_text"])
    print("Keywords:", keywords)
    print("Sentiment:", sentiment)