"""
Announcement Processor - NLP Engine
Processes and analyzes BSE announcements using NLP
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from ..utils.logger import get_logger


class AnnouncementProcessor:
    """Processes announcements using NLP to identify trading opportunities."""
    
    def __init__(self, config: Dict):
        """
        Initialize announcement processor.
        
        Args:
            config: NLP configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        self.primary_keywords = config.get('keywords', {}).get('primary', [
            'Award of Order', 'Receives Order', 'Secures Contract', 'Order received'
        ])
        self.secondary_keywords = config.get('keywords', {}).get('secondary', [
            'Contract', 'Agreement', 'Supply', 'Purchase Order'
        ])
        
        self.min_order_value = config.get('min_order_value', 10000000)  # 1 crore
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
        
        # Initialize NLP model
        self.nlp = None
        self.matcher = None
        self._initialize_nlp()
        
        self.logger.info("Announcement Processor initialized")
    
    def _initialize_nlp(self):
        """Initialize NLP model and patterns."""
        if not SPACY_AVAILABLE:
            self.logger.warning("spaCy not available. Using basic pattern matching.")
            return
        
        try:
            model_name = self.config.get('model', 'en_core_web_sm')
            self.nlp = spacy.load(model_name)
            self.matcher = Matcher(self.nlp.vocab)
            
            # Define patterns for order announcements
            patterns = [
                [{"LOWER": "award"}, {"LOWER": "of"}, {"LOWER": "order"}],
                [{"LOWER": "receives"}, {"LOWER": "order"}],
                [{"LOWER": "secures"}, {"LOWER": "contract"}],
                [{"LOWER": "order"}, {"LOWER": "received"}],
                [{"LOWER": "purchase"}, {"LOWER": "order"}],
            ]
            
            self.matcher.add("ORDER_AWARD", patterns)
            self.logger.info(f"NLP model loaded: {model_name}")
            
        except OSError:
            self.logger.error(f"Failed to load spaCy model. Run: python -m spacy download {model_name}")
            self.nlp = None
        except Exception as e:
            self.logger.error(f"Error initializing NLP: {e}")
            self.nlp = None
    
    async def process_announcement(self, announcement: Dict) -> Dict:
        """
        Process a single announcement.
        
        Args:
            announcement: Announcement dictionary from scraper
            
        Returns:
            Processed announcement with analysis results
        """
        try:
            title = announcement.get('title', '')
            company_name = announcement.get('company_name', '')
            
            # Basic validation
            if not title or not company_name:
                return self._create_result(announcement, False, "Missing title or company name")
            
            # Check if it's a tradeable announcement
            is_tradeable, reason, extracted_data = self._analyze_announcement(title, company_name)
            
            # Create result
            result = self._create_result(
                announcement, 
                is_tradeable, 
                reason, 
                extracted_data
            )
            
            self.logger.debug(f"Processed announcement: {company_name} - {is_tradeable}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing announcement: {e}")
            return self._create_result(announcement, False, f"Processing error: {e}")
    
    def _analyze_announcement(self, title: str, company_name: str) -> tuple:
        """
        Analyze announcement to determine if it's tradeable.
        
        Args:
            title: Announcement title
            company_name: Company name
            
        Returns:
            Tuple of (is_tradeable, reason, extracted_data)
        """
        title_lower = title.lower()
        extracted_data = {}
        
        # Step 1: Check for primary keywords
        primary_match = any(keyword.lower() in title_lower for keyword in self.primary_keywords)
        
        if not primary_match:
            # Check for secondary keywords as fallback
            secondary_match = any(keyword.lower() in title_lower for keyword in self.secondary_keywords)
            if not secondary_match:
                return False, "No relevant keywords found", extracted_data
        
        # Step 2: Extract order value
        order_value = self._extract_order_value(title)
        extracted_data['order_value'] = order_value
        extracted_data['order_value_text'] = self._extract_order_value_text(title)
        
        # Step 3: Check minimum order value threshold
        if order_value and order_value < self.min_order_value:
            return False, f"Order value {order_value} below threshold {self.min_order_value}", extracted_data
        
        # Step 4: Extract company symbol (basic implementation)
        symbol = self._extract_company_symbol(company_name, title)
        extracted_data['symbol'] = symbol
        extracted_data['company_name'] = company_name
        
        # Step 5: Confidence scoring
        confidence = self._calculate_confidence(title, primary_match, order_value)
        extracted_data['confidence'] = confidence
        
        if confidence < self.confidence_threshold:
            return False, f"Confidence {confidence} below threshold {self.confidence_threshold}", extracted_data
        
        # Step 6: Advanced NLP analysis (if available)
        if self.nlp:
            nlp_result = self._advanced_nlp_analysis(title)
            extracted_data.update(nlp_result)
        
        return True, "Valid order announcement", extracted_data
    
    def _extract_order_value(self, text: str) -> Optional[float]:
        """
        Extract order value from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Order value in rupees or None
        """
        # Patterns for Indian currency amounts
        patterns = [
            r'(?:rs\.?|inr|rupees?)\s*([0-9,]+(?:\.[0-9]+)?)\s*(crore|cr|lakh|lakhs?)',
            r'([0-9,]+(?:\.[0-9]+)?)\s*(crore|cr|lakh|lakhs?)',
            r'(?:rs\.?|inr|rupees?)\s*([0-9,]+(?:\.[0-9]+)?)',
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    
                    # Convert to rupees
                    if len(match.groups()) > 1:
                        unit = match.group(2).lower()
                        if 'crore' in unit or 'cr' == unit:
                            amount *= 10000000  # 1 crore = 10 million
                        elif 'lakh' in unit:
                            amount *= 100000  # 1 lakh = 100 thousand
                    
                    return amount
                    
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_order_value_text(self, text: str) -> str:
        """Extract the original order value text."""
        patterns = [
            r'(?:rs\.?|inr|rupees?)\s*[0-9,]+(?:\.[0-9]+)?\s*(?:crore|cr|lakh|lakhs?)',
            r'[0-9,]+(?:\.[0-9]+)?\s*(?:crore|cr|lakh|lakhs?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_company_symbol(self, company_name: str, title: str) -> str:
        """
        Extract company symbol from name or title.
        This is a basic implementation - in production, use a symbol lookup database.
        
        Args:
            company_name: Company name
            title: Announcement title
            
        Returns:
            Company symbol (basic guess)
        """
        # Basic symbol extraction - remove common words and take first few characters
        clean_name = re.sub(r'\b(limited|ltd|pvt|private|company|corp|corporation)\b', '', 
                           company_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'[^a-zA-Z\s]', '', clean_name).strip()
        
        if clean_name:
            # Take first word or first 4-6 characters
            words = clean_name.split()
            if words:
                return words[0][:6].upper()
        
        return company_name[:6].upper()
    
    def _calculate_confidence(self, title: str, primary_match: bool, order_value: Optional[float]) -> float:
        """
        Calculate confidence score for the announcement.
        
        Args:
            title: Announcement title
            primary_match: Whether primary keywords matched
            order_value: Extracted order value
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0
        
        # Base confidence for keyword match
        if primary_match:
            confidence += 0.5
        else:
            confidence += 0.3
        
        # Boost for order value
        if order_value:
            confidence += 0.2
            # Higher confidence for larger orders
            if order_value > 100000000:  # > 10 crores
                confidence += 0.1
        
        # Check for specific patterns
        title_lower = title.lower()
        
        # Positive indicators
        if any(word in title_lower for word in ['agreement', 'contract', 'supply']):
            confidence += 0.1
        
        if 'year' in title_lower or 'years' in title_lower:
            confidence += 0.05
        
        # Negative indicators
        if any(word in title_lower for word in ['board meeting', 'consider', 'proposed', 'potential']):
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _advanced_nlp_analysis(self, text: str) -> Dict:
        """
        Perform advanced NLP analysis using spaCy.
        
        Args:
            text: Text to analyze
            
        Returns:
            Analysis results dictionary
        """
        if not self.nlp:
            return {}
        
        try:
            doc = self.nlp(text)
            
            # Find pattern matches
            matches = self.matcher(doc)
            pattern_matches = len(matches) > 0
            
            # Extract entities
            entities = []
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
            
            return {
                'pattern_matches': pattern_matches,
                'entities': entities,
                'sentence_count': len(list(doc.sents)),
                'token_count': len(doc)
            }
            
        except Exception as e:
            self.logger.error(f"Error in advanced NLP analysis: {e}")
            return {}
    
    def _create_result(self, announcement: Dict, is_tradeable: bool, reason: str, 
                      extracted_data: Optional[Dict] = None) -> Dict:
        """
        Create standardized result dictionary.
        
        Args:
            announcement: Original announcement
            is_tradeable: Whether announcement is tradeable
            reason: Reason for decision
            extracted_data: Extracted data dictionary
            
        Returns:
            Result dictionary
        """
        return {
            'announcement_hash': announcement.get('hash'),
            'is_tradeable': is_tradeable,
            'reason': reason,
            'extracted_data': extracted_data or {},
            'processed_at': datetime.now(),
            'confidence': extracted_data.get('confidence', 0.0) if extracted_data else 0.0,
            'symbol': extracted_data.get('symbol', '') if extracted_data else '',
            'order_value': extracted_data.get('order_value') if extracted_data else None,
            'original_announcement': announcement
        } 