"""
Web scraping module - Advanced email extraction
"""

import requests
from bs4 import BeautifulSoup, Comment
from typing import Optional, Set
import logging
import time
import re
import urllib.parse
from config import REQUEST_TIMEOUT, MAX_RETRIES, USER_AGENT
from email_extractor import EmailExtractor
from page_detector import PageDetector

logger = logging.getLogger(__name__)


class WebScraper:
    """Website crawling and email address extraction"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8,fr;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def scrape_website(self, url: str) -> str:
        """
        Website'i ziyaret edip email adresini bulur
        
        Args:
            url: Ziyaret edilecek URL
            
        Returns:
            Bulunan email adresi veya boş string
        """
        logger.info(f"Website taranıyor: {url}")
        
        # URL formatını düzelt
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        all_emails: Set[str] = set()
        
        # 1. Ana sayfayı tara
        homepage_emails = self._scrape_page(url)
        all_emails.update(homepage_emails)
        
        # Eğer email bulunduysa, devam etme
        valid_email = EmailExtractor.get_best_email(all_emails)
        if valid_email:
            logger.info(f"Ana sayfada email bulundu: {valid_email}")
            return valid_email
        
        # 2. Ana sayfadan soup al (iletişim/hakkımızda linklerini bulmak için)
        soup = self._get_page_soup(url)
        if not soup:
            return ""
        
        # 3. İletişim sayfalarını bul ve tara
        contact_pages = PageDetector.find_contact_pages(soup, url)
        for contact_url in contact_pages[:2]:  # Maksimum 2 iletişim sayfası
            time.sleep(1)  # Rate limiting
            contact_emails = self._scrape_page(contact_url)
            all_emails.update(contact_emails)
            
            valid_email = EmailExtractor.get_best_email(all_emails)
            if valid_email:
                logger.info(f"İletişim sayfasında email bulundu: {valid_email}")
                return valid_email
        
        # 4. Hakkımızda sayfalarını bul ve tara
        about_pages = PageDetector.find_about_pages(soup, url)
        for about_url in about_pages[:1]:  # Maksimum 1 hakkımızda sayfası
            time.sleep(1)  # Rate limiting
            about_emails = self._scrape_page(about_url)
            all_emails.update(about_emails)
            
            valid_email = EmailExtractor.get_best_email(all_emails)
            if valid_email:
                logger.info(f"Hakkımızda sayfasında email bulundu: {valid_email}")
                return valid_email
        
        # Hiç email bulunamadı
        logger.warning(f"Email bulunamadı: {url}")
        return ""
    
    def _scrape_page(self, url: str) -> Set[str]:
        """
        Belirtilen sayfayı tarayıp email'leri çıkarır - ULTRA AGRESİF MOD
        HER KÖŞE-BUCAK TARANIR
        
        Args:
            url: Taranacak URL
            
        Returns:
            Bulunan email'ler
        """
        soup = self._get_page_soup(url)
        if not soup:
            return set()
        
        emails = set()
        html_str = str(soup)
        
        # 1. Görünür metin içinde email ara
        text = soup.get_text(separator=' ', strip=True)
        emails.update(EmailExtractor.extract_emails(text))
        
        # 2. HAM HTML içinde email ara (gizli/obfuscated için)
        emails.update(EmailExtractor.extract_emails(html_str))
        
        # 3. mailto: linklerini bul (TÜM varyasyonlar)
        mailto_emails = self._extract_mailto_links(soup)
        emails.update(mailto_emails)
        
        # 4. CloudFlare protected email'leri decode et
        cloudflare_emails = EmailExtractor.extract_cloudflare_emails(html_str)
        emails.update(cloudflare_emails)
        
        # 5. Form field'larında email ara
        form_emails = self._extract_from_forms(soup)
        emails.update(form_emails)
        
        # 6. JavaScript içinde gömülü email'leri ara
        js_emails = self._extract_from_javascript(soup)
        emails.update(js_emails)
        
        # 7. TÜM HTML attribute'larında @ içeren değerleri tara
        attr_emails = self._extract_from_all_attributes(soup)
        emails.update(attr_emails)
        
        # 8. HTML yorumlarında gizli email'leri ara
        comment_emails = self._extract_from_comments(soup)
        emails.update(comment_emails)
        
        if emails:
            logger.debug(f"{url} - {len(emails)} email bulundu")
        
        return emails
    
    def _extract_mailto_links(self, soup: BeautifulSoup) -> Set[str]:
        """
        mailto: linklerinden email'leri çıkarır - GENİŞLETİLMİŞ
        """
        emails = set()
        
        for link in soup.find_all('a'):
            # href attribute
            href = str(link.get('href', '')).strip()
            
            # mailto: kontrolü (case insensitive)
            if 'mailto:' in href.lower():
                # mailto:info@example.com?subject=... formatından email'i al
                email_part = href.lower().replace('mailto:', '').split('?')[0].split('&')[0].strip()
                if '@' in email_part:
                    # Birden fazla email varsa (mailto:a@x.com,b@y.com)
                    for email in email_part.split(','):
                        email = email.strip()
                        if '@' in email:
                            emails.add(email)
                            logger.debug(f"mailto: linki bulundu: {email}")
            
            # Tüm data-* attribute'larında email ara
            for attr_name, attr_value in link.attrs.items():
                if isinstance(attr_value, str) and '@' in attr_value:
                    found = EmailExtractor.extract_emails(attr_value)
                    if found:
                        emails.update(found)
                        logger.debug(f"Link attribute '{attr_name}' içinde: {found}")
            
            # Link metninin içinde email olabilir
            link_text = link.get_text()
            if '@' in link_text:
                found = EmailExtractor.extract_emails(link_text)
                if found:
                    emails.update(found)
                    logger.debug(f"Link metninde: {found}")
        
        return emails
    
    def _extract_from_forms(self, soup: BeautifulSoup) -> Set[str]:
        """
        Form field'larından email'leri çıkarır
        """
        emails = set()
        
        for input_field in soup.find_all(['input', 'textarea', 'select']):
            # Placeholder
            placeholder = input_field.get('placeholder', '')
            if placeholder and '@' in placeholder:
                emails.update(EmailExtractor.extract_emails(placeholder))
            
            # Value
            value = input_field.get('value', '')
            if value and '@' in value:
                emails.update(EmailExtractor.extract_emails(value))
            
            # Title
            title = input_field.get('title', '')
            if title and '@' in title:
                emails.update(EmailExtractor.extract_emails(title))
            
            # Data attribute'lar
            for attr, val in input_field.attrs.items():
                if isinstance(val, str) and '@' in val:
                    emails.update(EmailExtractor.extract_emails(val))
        
        if emails:
            logger.debug(f"Form field'larında {len(emails)} email bulundu")
        
        return emails
    
    def _extract_from_javascript(self, soup: BeautifulSoup) -> Set[str]:
        """
        JavaScript kodlarından email'leri çıkarır - ULTRA AGRESİF
        """
        emails = set()
        
        for script in soup.find_all('script'):
            script_text = script.string if script.string else str(script)
            
            if not script_text or len(script_text) < 5:
                continue
            
            # 1. Normal email pattern
            emails.update(EmailExtractor.extract_emails(script_text))
            
            # 2. String concatenation: "info" + "@" + "domain.com"
            concat_pattern = r'["\']([a-z0-9._%+-]+)["\']\s*\+\s*["\']@["\']\s*\+\s*["\']([a-z0-9.-]+\.[a-z]{2,})["\']'
            for match in re.findall(concat_pattern, script_text, re.IGNORECASE):
                email = f"{match[0]}@{match[1]}".lower()
                emails.add(email)
                logger.debug(f"JS concat email: {email}")
            
            # 3. Hex encoded: \x69\x6e\x66\x6f\x40...
            hex_pattern = r'((?:\\x[0-9a-fA-F]{2})+)'
            for hex_str in re.findall(hex_pattern, script_text):
                try:
                    decoded = bytes.fromhex(hex_str.replace('\\x', '')).decode('utf-8', errors='ignore')
                    if '@' in decoded:
                        emails.update(EmailExtractor.extract_emails(decoded))
                except:
                    pass
            
            # 4. URL encoded: info%40domain.com
            if '%40' in script_text or '%2E' in script_text:
                try:
                    decoded_url = urllib.parse.unquote(script_text)
                    emails.update(EmailExtractor.extract_emails(decoded_url))
                except:
                    pass
        
        if emails:
            logger.debug(f"JavaScript'te {len(emails)} email bulundu")
        
        return emails
    
    def _extract_from_all_attributes(self, soup: BeautifulSoup) -> Set[str]:
        """
        TÜM HTML element'lerinin TÜM attribute'larında @ içeren değerleri tara
        """
        emails = set()
        
        for element in soup.find_all(True):  # True = tüm tag'ler
            for attr_name, attr_value in element.attrs.items():
                if not attr_value:
                    continue
                
                # String veya list olabilir
                if isinstance(attr_value, list):
                    attr_value = ' '.join(str(v) for v in attr_value)
                else:
                    attr_value = str(attr_value)
                
                # @ içeriyorsa email ara
                if '@' in attr_value:
                    found = EmailExtractor.extract_emails(attr_value)
                    if found:
                        emails.update(found)
                        logger.debug(f"Attribute '{attr_name}': {found}")
        
        if emails:
            logger.debug(f"HTML attribute'larında {len(emails)} email bulundu")
        
        return emails
    
    def _extract_from_comments(self, soup: BeautifulSoup) -> Set[str]:
        """
        HTML yorumlarında gizli email'leri ara
        """
        emails = set()
        
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        
        for comment in comments:
            comment_text = str(comment)
            if '@' in comment_text:
                found = EmailExtractor.extract_emails(comment_text)
                if found:
                    emails.update(found)
                    logger.debug(f"HTML yorumunda: {found}")
        
        if emails:
            logger.debug(f"HTML yorumlarında {len(emails)} email bulundu")
        
        return emails
    
    def _get_page_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        URL'den BeautifulSoup nesnesi oluşturur
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                    verify=True
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                
                soup = BeautifulSoup(response.text, 'lxml')
                return soup
                
            except requests.exceptions.SSLError:
                try:
                    response = self.session.get(
                        url, 
                        timeout=REQUEST_TIMEOUT,
                        allow_redirects=True,
                        verify=False
                    )
                    response.encoding = response.apparent_encoding
                    soup = BeautifulSoup(response.text, 'lxml')
                    return soup
                except Exception as e:
                    logger.warning(f"SSL bypass denemesi başarısız: {e}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout ({attempt + 1}/{MAX_RETRIES}): {url}")
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"İstek hatası ({attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Beklenmeyen hata: {e}")
                break
        
        return None
