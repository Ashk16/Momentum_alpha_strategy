"""
BSE Scraper Module
Handles ethical web scraping of BSE corporate announcements
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup

from ..utils.logger import get_logger


class BSEScraper:
    """Scraper for BSE corporate announcements."""
    
    def __init__(self, config: Dict):
        """
        Initialize BSE scraper.
        
        Args:
            config: Scraper configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        self.base_url = config.get('base_url', 'https://www.bseindia.com/corporates/ann.html')
        self.poll_interval = config.get('poll_interval', 15)
        self.timeout = config.get('timeout', 30)
        self.user_agent = config.get('user_agent', 'MomentumAlpha/1.0')
        self.max_retries = config.get('max_retries', 3)
        self.backoff_factor = config.get('backoff_factor', 1.0)
        
        # Track seen announcements to detect new ones
        self.seen_announcements: Set[str] = set()
        self.last_scrape_time: Optional[datetime] = None
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.logger.info(f"BSE Scraper initialized - URL: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the scraper session."""
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        self.logger.info("BSE Scraper session initialized")
    
    async def cleanup(self):
        """Clean up the scraper session."""
        if self.session:
            await self.session.close()
            self.logger.info("BSE Scraper session closed")
    
    async def get_new_announcements(self) -> List[Dict]:
        """
        Get new announcements since last check.
        
        Returns:
            List of new announcement dictionaries
        """
        try:
            if not self.session:
                await self.initialize()
            
            # Fetch current announcements
            announcements = await self._fetch_announcements()
            
            # Filter for new announcements
            new_announcements = self._filter_new_announcements(announcements)
            
            self.last_scrape_time = datetime.now()
            
            if new_announcements:
                self.logger.info(f"Found {len(new_announcements)} new announcements")
            
            return new_announcements
        
        except Exception as e:
            self.logger.error(f"Error fetching announcements: {e}")
            return []
    
    async def _fetch_announcements(self) -> List[Dict]:
        """
        Fetch announcements from BSE website.
        
        Returns:
            List of announcement dictionaries
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Fetching announcements (attempt {attempt + 1})")
                
                async with self.session.get(self.base_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return self._parse_announcements(html_content)
                    else:
                        self.logger.warning(f"HTTP {response.status} received")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout on attempt {attempt + 1}")
            except Exception as e:
                self.logger.error(f"Error on attempt {attempt + 1}: {e}")
            
            if attempt < self.max_retries - 1:
                wait_time = self.backoff_factor * (2 ** attempt)
                self.logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        self.logger.error(f"Failed to fetch announcements after {self.max_retries} attempts")
        return []
    
    def _parse_announcements(self, html_content: str) -> List[Dict]:
        """
        Parse announcements from HTML content.
        
        Args:
            html_content: HTML content of the BSE announcements page
            
        Returns:
            List of parsed announcement dictionaries
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            announcements = []
            
            # Find the announcements table (adjust selector based on actual BSE structure)
            # This is a generic implementation - may need adjustment for actual BSE HTML
            table = soup.find('table', {'id': 'tbldatanew'}) or soup.find('table', class_='data')
            
            if not table:
                self.logger.warning("Could not find announcements table")
                return announcements
            
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # Ensure minimum required columns
                    announcement = self._extract_announcement_data(cells)
                    if announcement:
                        announcements.append(announcement)
            
            self.logger.debug(f"Parsed {len(announcements)} announcements")
            return announcements
        
        except Exception as e:
            self.logger.error(f"Error parsing announcements: {e}")
            return []
    
    def _extract_announcement_data(self, cells: List) -> Optional[Dict]:
        """
        Extract announcement data from table cells.
        
        Args:
            cells: List of table cell elements
            
        Returns:
            Announcement dictionary or None
        """
        try:
            # Adjust indices based on actual BSE table structure
            announcement = {
                'timestamp': datetime.now(),
                'scrape_time': datetime.now(),
                'date': self._extract_text(cells[0]),
                'time': self._extract_text(cells[1]) if len(cells) > 1 else '',
                'company_name': self._extract_text(cells[2]) if len(cells) > 2 else '',
                'title': self._extract_text(cells[3]) if len(cells) > 3 else '',
                'category': self._extract_text(cells[4]) if len(cells) > 4 else '',
            }
            
            # Extract PDF link if available
            pdf_link = self._extract_pdf_link(cells)
            if pdf_link:
                announcement['pdf_url'] = pdf_link
            
            # Create unique hash for deduplication
            announcement['hash'] = self._create_announcement_hash(announcement)
            
            # Basic validation
            if not announcement['title'] or not announcement['company_name']:
                return None
            
            return announcement
        
        except Exception as e:
            self.logger.error(f"Error extracting announcement data: {e}")
            return None
    
    def _extract_text(self, cell) -> str:
        """Extract clean text from a table cell."""
        if cell:
            text = cell.get_text(strip=True)
            return text.replace('\n', ' ').replace('\r', '').strip()
        return ''
    
    def _extract_pdf_link(self, cells: List) -> Optional[str]:
        """
        Extract PDF link from table cells.
        
        Args:
            cells: List of table cell elements
            
        Returns:
            PDF URL or None
        """
        for cell in cells:
            links = cell.find_all('a')
            for link in links:
                href = link.get('href', '')
                if href and ('.pdf' in href.lower() or 'pdf' in href.lower()):
                    # Convert relative URL to absolute
                    if href.startswith('http'):
                        return href
                    else:
                        return urljoin(self.base_url, href)
        return None
    
    def _create_announcement_hash(self, announcement: Dict) -> str:
        """
        Create a unique hash for an announcement.
        
        Args:
            announcement: Announcement dictionary
            
        Returns:
            MD5 hash string
        """
        # Create hash from key fields
        hash_string = f"{announcement.get('date', '')}{announcement.get('time', '')}" \
                     f"{announcement.get('company_name', '')}{announcement.get('title', '')}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _filter_new_announcements(self, announcements: List[Dict]) -> List[Dict]:
        """
        Filter announcements to return only new ones.
        
        Args:
            announcements: List of all announcements
            
        Returns:
            List of new announcements
        """
        new_announcements = []
        
        for announcement in announcements:
            announcement_hash = announcement.get('hash')
            if announcement_hash and announcement_hash not in self.seen_announcements:
                self.seen_announcements.add(announcement_hash)
                new_announcements.append(announcement)
        
        return new_announcements
    
    def check_robots_txt(self) -> bool:
        """
        Check robots.txt compliance.
        
        Returns:
            True if scraping is allowed, False otherwise
        """
        try:
            parsed_url = urlparse(self.base_url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                # Simple check - in production, use robotparser
                robots_content = response.text.lower()
                if 'disallow: /' in robots_content or 'disallow: /corporates' in robots_content:
                    self.logger.warning("Robots.txt disallows scraping")
                    return False
            
            return True
        
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt: {e}")
            return True  # Assume allowed if can't check
    
    def get_stats(self) -> Dict:
        """
        Get scraper statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'seen_announcements_count': len(self.seen_announcements),
            'last_scrape_time': self.last_scrape_time,
            'base_url': self.base_url,
            'poll_interval': self.poll_interval,
            'session_active': self.session is not None and not self.session.closed
        } 