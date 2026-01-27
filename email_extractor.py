"""
Email address extraction and validation module
"""

import re
from typing import List, Set
import logging
from config import BLACKLISTED_DOMAINS, EXAMPLE_EMAILS

logger = logging.getLogger(__name__)


class EmailExtractor:
    """Extract email addresses from HTML content"""
    
    # Email regex pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # CloudFlare protected email pattern
    CLOUDFLARE_PATTERN = r'data-cfemail="([a-f0-9]+)"'
    
    # Text-based email patterns (info [at] domain [dot] com)
    TEXT_EMAIL_PATTERN = r'\b([a-z0-9._%+-]+)\s*(?:\[at\]|@|\(at\)|\[a\])\s*([a-z0-9.-]+)\s*(?:\[dot\]|\.|\.|\(dot\))\s*([a-z]{2,})\b'
    
    @staticmethod
    def extract_emails(text: str) -> Set[str]:
        """
        Extract all email addresses from given text - ULTRA AGGRESSIVE
        
        Args:
            text: Aranacak metin
            
        Returns:
            Found email adresleri seti
        """
        if not text:
            return set()
        
        emails = set()
        
        # 1. Normal email pattern
        normal_emails = set(re.findall(EmailExtractor.EMAIL_PATTERN, text, re.IGNORECASE))
        emails.update(normal_emails)
        
        # 2. Text-based email pattern (info [at] domain [dot] com)
        text_emails = re.findall(EmailExtractor.TEXT_EMAIL_PATTERN, text, re.IGNORECASE)
        for match in text_emails:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            emails.add(email)
            logger.debug(f"Text-based email bulundu: {email}")
        
        # 3. Space'li email pattern: info @ domain . com
        spaced_pattern = r'\b([a-z0-9._%+-]+)\s*@\s*([a-z0-9.-]+)\s*\.\s*([a-z]{2,})\b'
        spaced_emails = re.findall(spaced_pattern, text, re.IGNORECASE)
        for match in spaced_emails:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            emails.add(email)
            logger.debug(f"Space'li email bulundu: {email}")
        
        # 4. HTML entity encoded: &#64; = @, &#46; = .
        entity_decoded = text.replace('&#64;', '@').replace('&#46;', '.').replace('&#x40;', '@')
        if entity_decoded != text:
            entity_emails = re.findall(EmailExtractor.EMAIL_PATTERN, entity_decoded, re.IGNORECASE)
            emails.update(entity_emails)
            if entity_emails:
                logger.debug(f"HTML entity encoded email: {entity_emails}")
        
        # 5. Written AT and DOT: info AT domain DOT com
        at_dot_pattern = r'\b([a-z0-9._%+-]+)\s+(?:AT|at)\s+([a-z0-9.-]+)\s+(?:DOT|dot)\s+([a-z]{2,})\b'
        at_dot_emails = re.findall(at_dot_pattern, text, re.IGNORECASE)
        for match in at_dot_emails:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            emails.add(email)
            logger.debug(f"AT/DOT email bulundu: {email}")
        
        # Clean and convert to lowercase
        emails = {email.lower().strip() for email in emails if email and len(email) > 5}
        
        return emails
    
    @staticmethod
    def decode_cloudflare_email(encoded: str) -> str:
        """
        Decodes CloudFlare protected email
        
        Args:
            encoded: Hex encoded email
            
        Returns:
            Decoded email
        """
        try:
            r = int(encoded[:2], 16)
            email = ''.join([chr(int(encoded[i:i+2], 16) ^ r) for i in range(2, len(encoded), 2)])
            return email
        except:
            return ""
    
    @staticmethod
    def extract_cloudflare_emails(html: str) -> Set[str]:
        """
        Extracts CloudFlare protected emails
        
        Args:
            html: HTML content
            
        Returns:
            Set of decoded emails
        """
        emails = set()
        matches = re.findall(EmailExtractor.CLOUDFLARE_PATTERN, html)
        
        for encoded in matches:
            decoded = EmailExtractor.decode_cloudflare_email(encoded)
            if decoded and '@' in decoded:
                emails.add(decoded)
                logger.debug(f"CloudFlare email decode edildi: {decoded}")
        
        return emails
    
    @staticmethod
    def is_valid_business_email(email: str) -> bool:
        """
        Check if email is a business email
        Filter generic email services and example emails
        
        Args:
            email: Kontrol edwithcek email
            
        Returns:
            True if valid business email
        """
        email = email.lower().strip()
        
        # Skip very short or very long emails
        if len(email) < 6 or len(email) > 100:
            return False
        
        # Example email'leri kontrol et
        if email in EXAMPLE_EMAILS:
            logger.debug(f"Example email skipped: {email}")
            return False
        
        # Extract domain
        try:
            local_part, domain = email.split('@')
        except (IndexError, ValueError):
            return False
        
        # Genel email servislerini filtrele
        if domain in BLACKLISTED_DOMAINS:
            logger.debug(f"Blacklist domain skipped: {email}")
            return False
        
        # Aggressively filter Sentry, Wix and other system domains
        system_keywords = ['sentry', 'wixpress', 'wix.com', 'sentry.io']
        if any(keyword in domain.lower() for keyword in system_keywords):
            logger.debug(f"System domain skipped: {email}")
            return False
        
        # File extensions (.png, .jpg, etc.)
        fwith_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js', '.html', '.php']
        if any(email.endswith(ext) or domain.endswith(ext) for ext in fwith_extensions):
            logger.debug(f"File extension skipped: {email}")
            return False
        
        # Hex/random string or UUID (24+ karakter)
        # Systems like Sentry/Wix use 32-char hashes
        if len(local_part) >= 24 and all(c in '0123456789abcdef' for c in local_part):
            logger.debug(f"Hex/UUID string skipped: {email}")
            return False
        
        # Domain must have dot
        if '.' not in domain:
            logger.debug(f"Invalid domain skipped: {email}")
            return False
        
        # Very long domains are usually system domains
        if len(domain) > 40:
            logger.debug(f"Very long domain skipped: {email}")
            return False
        
        return True
    
    @staticmethod
    def filter_valid_emails(emails: Set[str]) -> List[str]:
        """
        Filters email list and returns valid ones
        
        Args:
            emails: Set of emails
            
        Returns:
            Filtered email list (sorted by priority)
        """
        valid_emails = [email for email in emails if EmailExtractor.is_valid_business_email(email)]
        
        if not valid_emails:
            return []
        
        # Priority order: info, contact, others
        priority_prefixes = ['info@', 'contact@', 'sales@', 'commercial@']
        
        prioritized = []
        others = []
        
        for email in valid_emails:
            if any(email.startswith(prefix) for prefix in priority_prefixes):
                prioritized.append(email)
            else:
                others.append(email)
        
        # Move priority emails to front
        result = prioritized + others
        
        logger.debug(f"Filtrelenen email'ler: {result}")
        return result
    
    @staticmethod
    def get_best_email(emails: Set[str]) -> str:
        """
        Selects the most suitable email from list
        
        Args:
            emails: Set of emails
            
        Returns:
            Best email or empty string
        """
        valid_emails = EmailExtractor.filter_valid_emails(emails)
        
        if valid_emails:
            logger.info(f"Best email selected: {valid_emails[0]}")
            return valid_emails[0]
        
        return ""
