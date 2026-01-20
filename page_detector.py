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
            İletişim sayfası URL'leri
        """
        return PageDetector._find_pages_by_keywords(
            soup, base_url, CONTACT_PAGE_KEYWORDS, 'iletişim'
        )
    
    @staticmethod
    def find_about_pages(soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Hakkımızda sayfası linklerini bulur
        
        Args:
            soup: BeautifulSoup nesnesi
            base_url: Ana URL
            
        Returns:
            Hakkımızda sayfası URL'leri
        """
        return PageDetector._find_pages_by_keywords(
            soup, base_url, ABOUT_PAGE_KEYWORDS, 'hakkımızda'
        )
    
    @staticmethod
    def _find_pages_by_keywords(soup: BeautifulSoup, base_url: str, 
                                keywords_dict: dict, page_type: str) -> List[str]:
        """
        Anahtar kelimelere göre sayfa linklerini bulur
        
        Args:
            soup: BeautifulSoup nesnesi
            base_url: Ana URL
            keywords_dict: Dil bazlı anahtar kelimeler
            page_type: Sayfa tipi (loglama için)
            
        Returns:
            Bulunan URL'ler
        """
        found_urls: Set[str] = set()
        
        # Tüm dillerdeki anahtar kelimeleri birleştir
        all_keywords = []
        for lang_keywords in keywords_dict.values():
            all_keywords.extend(lang_keywords)
        
        # Tüm linkleri bul
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()
            
            # Anahtar kelime kontrolü (href veya link metni)
            for keyword in all_keywords:
                keyword_lower = keyword.lower()
                
                # URL'de veya link metninde anahtar kelime var mı?
                if keyword_lower in href or keyword_lower in text:
                    # Tam URL oluştur
                    full_url = urljoin(base_url, link['href'])
                    
                    # Aynı domain'de mi kontrol et
                    if PageDetector._is_same_domain(base_url, full_url):
                        found_urls.add(full_url)
                        logger.debug(f"{page_type} sayfası bulundu: {full_url}")
                        break
        
        result = list(found_urls)[:3]  # Maksimum 3 sayfa
        logger.info(f"{len(result)} adet {page_type} sayfası bulundu")
        return result
    
    @staticmethod
    def _is_same_domain(url1: str, url2: str) -> bool:
        """
        İki URL'nin aynı domain'de olup olmadığını kontrol eder
        
        Args:
            url1: İlk URL
            url2: İkinci URL
            
        Returns:
            Aynı domain ise True
        """
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False
