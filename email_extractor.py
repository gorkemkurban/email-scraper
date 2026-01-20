"""
Email adresi çıkarma ve validasyon modülü
"""

import re
from typing import List, Set
import logging
from config import BLACKLISTED_DOMAINS, EXAMPLE_EMAILS

logger = logging.getLogger(__name__)


class EmailExtractor:
    """HTML içeriğinden email adresi çıkarma"""
    
    # Email regex pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # CloudFlare protected email pattern
    CLOUDFLARE_PATTERN = r'data-cfemail="([a-f0-9]+)"'
    
    # Text-based email patterns (info [at] domain [dot] com)
    TEXT_EMAIL_PATTERN = r'\b([a-z0-9._%+-]+)\s*(?:\[at\]|@|\(at\)|\[a\])\s*([a-z0-9.-]+)\s*(?:\[dot\]|\.|\.|\(dot\))\s*([a-z]{2,})\b'
    
    @staticmethod
    def extract_emails(text: str) -> Set[str]:
        """
        Verilen metinden tüm email adreslerini çıkarır - ULTRA AGRESİF
        
        Args:
            text: Aranacak metin
            
        Returns:
            Bulunan email adresleri seti
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
        
        # 5. AT ve DOT yazılı: info AT domain DOT com
        at_dot_pattern = r'\b([a-z0-9._%+-]+)\s+(?:AT|at)\s+([a-z0-9.-]+)\s+(?:DOT|dot)\s+([a-z]{2,})\b'
        at_dot_emails = re.findall(at_dot_pattern, text, re.IGNORECASE)
        for match in at_dot_emails:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            emails.add(email)
            logger.debug(f"AT/DOT email bulundu: {email}")
        
        # Temizle ve küçük harfe çevir
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
        Email'in kurumsal email olup olmadığını kontrol eder
        Genel email servisleri ve örnek email'leri filtreler
        
        Args:
            email: Kontrol edilecek email
            
        Returns:
            Geçerli kurumsal email ise True
        """
        email = email.lower().strip()
        
        # Çok kısa veya çok uzun email'leri atla
        if len(email) < 6 or len(email) > 100:
            return False
        
        # Örnek email'leri kontrol et
        if email in EXAMPLE_EMAILS:
            logger.debug(f"Örnek email atlandı: {email}")
            return False
        
        # Domain'i çıkar
        try:
            local_part, domain = email.split('@')
        except (IndexError, ValueError):
            return False
        
        # Genel email servislerini filtrele
        if domain in BLACKLISTED_DOMAINS:
            logger.debug(f"Blacklist domain atlandı: {email}")
            return False
        
        # Sentry, Wix ve diğer sistem domain'lerini agresif filtrele
        system_keywords = ['sentry', 'wixpress', 'wix.com', 'sentry.io']
        if any(keyword in domain.lower() for keyword in system_keywords):
            logger.debug(f"Sistem domain atlandı: {email}")
            return False
        
        # Dosya uzantıları (.png, .jpg, vb.)
        file_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js', '.html', '.php']
        if any(email.endswith(ext) or domain.endswith(ext) for ext in file_extensions):
            logger.debug(f"Dosya uzantısı atlandı: {email}")
            return False
        
        # Hex/random string veya UUID (24+ karakter)
        # Sentry/Wix gibi sistemler 32 karakterli hash kullanır
        if len(local_part) >= 24 and all(c in '0123456789abcdef' for c in local_part):
            logger.debug(f"Hex/UUID string atlandı: {email}")
            return False
        
        # Domain'de nokta olmalı
        if '.' not in domain:
            logger.debug(f"Geçersiz domain atlandı: {email}")
            return False
        
        # Çok uzun domain'ler genelde sistem domain'leridir
        if len(domain) > 40:
            logger.debug(f"Çok uzun domain atlandı: {email}")
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
        
        # Öncelik sıralaması: info, contact, diğerleri
        priority_prefixes = ['info@', 'contact@', 'sales@', 'commercial@']
        
        prioritized = []
        others = []
        
        for email in valid_emails:
            if any(email.startswith(prefix) for prefix in priority_prefixes):
                prioritized.append(email)
            else:
                others.append(email)
        
        # Öncelikli email'leri başa al
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
            logger.info(f"En iyi email seçildi: {valid_emails[0]}")
            return valid_emails[0]
        
        return ""
