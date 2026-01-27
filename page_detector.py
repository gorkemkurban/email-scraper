"""
Contact and about page detection module (multi-language)
"""

from typing import List, Set
from urllib.parse import urljoin, urlparse
import logging
from bs4 import BeautifulSoup
from config import CONTACT_PAGE_KEYWORDS, ABOUT_PAGE_KEYWORDS

logger = logging.getLogger(__name__)


class PageDetector:
    """Find contact and about pages on websites"""
    
    @staticmethod
    def find_contact_pages(soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find contact page links
        
        Args:
            soup: BeautifulSoup nesnesi
            base_url: Ana URL
            
        Returns:
            Contact page URL'leri
        """
        return PageDetector._find_pages_by_keywords(
            soup, base_url, CONTACT_PAGE_KEYWORDS, 'contact'
        )
    
    @staticmethod
    def find_about_pages(soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        About page linklerini bulur
        
        Args:
            soup: BeautifulSoup nesnesi
            base_url: Ana URL
            
        Returns:
            About page URL'leri
        """
        return PageDetector._find_pages_by_keywords(
            soup, base_url, ABOUT_PAGE_KEYWORDS, 'about'
        )
    
    @staticmethod
    def _find_pages_by_keywords(soup: BeautifulSoup, base_url: str, 
                                keywords_dict: dict, page_type: str) -> List[str]:
        """
        Find page links based on keywords
        
        Args:
            soup: BeautifulSoup object
            base_url: Main URL
            keywords_dict: Language-based keywords
            page_type: Page type (for logging)
            
        Returns:
            Found URLs
        """
        found_urls: Set[str] = set()
        
        # Merge keywords from all languages
        all_keywords = []
        for lang_keywords in keywords_dict.values():
            all_keywords.extend(lang_keywords)
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()
            
            # Keyword check (href or link text)
            for keyword in all_keywords:
                keyword_lower = keyword.lower()
                
                # Keyword in URL or link text?
                if keyword_lower in href or keyword_lower in text:
                    # Build full URL
                    full_url = urljoin(base_url, link['href'])
                    
                    # Check if same domain
                    if PageDetector._is_same_domain(base_url, full_url):
                        found_urls.add(full_url)
                        logger.debug(f"{page_type} page found: {full_url}")
                        break
        
        result = list(found_urls)[:3]  # Maximum 3 pages
        logger.info(f"{len(result)} {page_type} pages found")
        return result
    
    @staticmethod
    def _is_same_domain(url1: str, url2: str) -> bool:
        """
        Check if two URLs are on the same domain
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if same domain
        """
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False
