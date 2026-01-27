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
            'Connection': 'keep-aliand',
        })
    
    def scrape_website(self, url: str) -> str:
        """
        Visit website and find email address
        
        Args:
            url: URL to visit
            
        Returns:
            Found email address or empty string
        """
        logger.info(f"Scanning website: {url}")
        
        # Fix URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        all_emails: Set[str] = set()
        
        # 1. Scan homepage
        homepage_emails = self._scrape_page(url)
        all_emails.update(homepage_emails)
        
        # If email found, don't continue
        valid_email = EmailExtractor.get_best_email(all_emails)
        if valid_email:
            logger.info(f"Email found on homepage: {valid_email}")
            return valid_email
        
        # 2. Get soup from homepage (to find contact/about links)
        soup = self._get_page_soup(url)
        if not soup:
            return ""
        
        # 3. Find and scan contact pages
        contact_pages = PageDetector.find_contact_pages(soup, url)
        for contact_url in contact_pages[:2]:  # Maximum 2 contact pages
            time.sleep(1)  # Rate limiting
            contact_emails = self._scrape_page(contact_url)
            all_emails.update(contact_emails)
            
            valid_email = EmailExtractor.get_best_email(all_emails)
            if valid_email:
                logger.info(f"Email found on contact page: {valid_email}")
                return valid_email
        
        # 4. Find and scan about pages
        about_pages = PageDetector.find_about_pages(soup, url)
        for about_url in about_pages[:1]:  # Maximum 1 about page
            time.sleep(1)  # Rate limiting
            about_emails = self._scrape_page(about_url)
            all_emails.update(about_emails)
            
            valid_email = EmailExtractor.get_best_email(all_emails)
            if valid_email:
                logger.info(f"Email found on about page: {valid_email}")
                return valid_email
        
        # No email found at all
        logger.warning(f"Email not found: {url}")
        return ""
    
    def _scrape_page(self, url: str) -> Set[str]:
        """
        Scan specified page and extract emails - ULTRA AGGRESSIVE MODE
        EVERY CORNER IS SCANNED
        
        Args:
            url: URL to scan
            
        Returns:
            Found emails
        """
        soup = self._get_page_soup(url)
        if not soup:
            return set()
        
        emails = set()
        html_str = str(soup)
        
        # 1. Search for emails in visible text
        text = soup.get_text(separator=' ', strip=True)
        emails.update(EmailExtractor.extract_emails(text))
        
        # 2. Search for emails in raw HTML (hidden/obfuscated)
        emails.update(EmailExtractor.extract_emails(html_str))
        
        # 3. Find mailto: links (all variations)
        mailto_emails = self._extract_mailto_links(soup)
        emails.update(mailto_emails)
        
        # 4. Decode CloudFlare protected emails
        cloudflare_emails = EmailExtractor.extract_cloudflare_emails(html_str)
        emails.update(cloudflare_emails)
        
        # 5. Search for emails in form fields
        form_emails = self._extract_from_forms(soup)
        emails.update(form_emails)
        
        # 6. Search for embedded emails in JavaScript
        js_emails = self._extract_from_javascript(soup)
        emails.update(js_emails)
        
        # 7. Scan all HTML attributes for values containing @
        attr_emails = self._extract_from_all_attributes(soup)
        emails.update(attr_emails)
        
        # 8. Search for hidden emails in HTML comments
        comment_emails = self._extract_from_comments(soup)
        emails.update(comment_emails)
        
        if emails:
            logger.debug(f"{url} - {len(emails)} emails found")
        
        return emails
    
    def _extract_mailto_links(self, soup: BeautifulSoup) -> Set[str]:
        """
        Extract emails from mailto: links - EXTENDED
        """
        emails = set()
        
        for link in soup.find_all('a'):
            # href attribute
            href = str(link.get('href', '')).strip()
            
            # mailto: check (case insensitive)
            if 'mailto:' in href.lower():
                # mailto:info@example.com?subject=... format - extract email
                email_part = href.lower().replace('mailto:', '').split('?')[0].split('&')[0].strip()
                if '@' in email_part:
                    # If multiple emails (mailto:a@x.com,b@y.com)
                    for email in email_part.split(','):
                        email = email.strip()
                        if '@' in email:
                            emails.add(email)
                            logger.debug(f"mailto: link found: {email}")
            
            # Search for emails in all data-* attributes
            for attr_name, attr_value in link.attrs.items():
                if isinstance(attr_value, str) and '@' in attr_value:
                    found = EmailExtractor.extract_emails(attr_value)
                    if found:
                        emails.update(found)
                        logger.debug(f"Link attribute '{attr_name}': {found}")
            
            # Link text may contain email
            link_text = link.get_text()
            if '@' in link_text:
                found = EmailExtractor.extract_emails(link_text)
                if found:
                    emails.update(found)
                    logger.debug(f"In link text: {found}")
        
        return emails
    
    def _extract_from_forms(self, soup: BeautifulSoup) -> Set[str]:
        """
        Extract emails from form fields
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
            
            # Data attributes
            for attr, val in input_field.attrs.items():
                if isinstance(val, str) and '@' in val:
                    emails.update(EmailExtractor.extract_emails(val))
        
        if emails:
            logger.debug(f"Found {len(emails)} emails in form fields")
        
        return emails
    
    def _extract_from_javascript(self, soup: BeautifulSoup) -> Set[str]:
        """
        Extract emails from JavaScript code - ULTRA AGGRESSIVE
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
            logger.debug(f"Found {len(emails)} emails in JavaScript")
        
        return emails
    
    def _extract_from_all_attributes(self, soup: BeautifulSoup) -> Set[str]:
        """
        Scan all HTML elements' attributes for values containing @
        """
        emails = set()
        
        for element in soup.find_all(True):  # True = all tags
            for attr_name, attr_value in element.attrs.items():
                if not attr_value:
                    continue
                
                # Can be string or list
                if isinstance(attr_value, list):
                    attr_value = ' '.join(str(v) for v in attr_value)
                else:
                    attr_value = str(attr_value)
                
                # If contains @, search for emails
                if '@' in attr_value:
                    found = EmailExtractor.extract_emails(attr_value)
                    if found:
                        emails.update(found)
                        logger.debug(f"Attribute '{attr_name}': {found}")
        
        if emails:
            logger.debug(f"Found {len(emails)} emails in HTML attributes")
        
        return emails
    
    def _extract_from_comments(self, soup: BeautifulSoup) -> Set[str]:
        """
        Search for hidden emails in HTML comments
        """
        emails = set()
        
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        
        for comment in comments:
            comment_text = str(comment)
            if '@' in comment_text:
                found = EmailExtractor.extract_emails(comment_text)
                if found:
                    emails.update(found)
                    logger.debug(f"In HTML comment: {found}")
        
        if emails:
            logger.debug(f"Found {len(emails)} emails in HTML comments")
        
        return emails
    
    def _get_page_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Create BeautifulSoup object from URL
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                    andrify=True
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
                        andrify=False
                    )
                    response.encoding = response.apparent_encoding
                    soup = BeautifulSoup(response.text, 'lxml')
                    return soup
                except Exception as e:
                    logger.warning(f"SSL bypass attempt failed: {e}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout ({attempt + 1}/{MAX_RETRIES}): {url}")
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error ({attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        return None
