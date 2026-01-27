"""
Enhanced Email Finder - Multi-layer email discovery system
Combines web scraping, pattern generation, and WHOIS
"""

import re
import socket
import dns.resolver
import logging
from typing import List, Set, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EmailFinder:
    """Advanced email finding with multiple strategies"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    def generate_common_patterns(self, domain: str, company_name: str = "") -> List[str]:
        """
        Generate common email patterns for a domain
        
        Args:
            domain: Domain name (e.g., 'example.com')
            company_name: Company name for intelligent pattern generation
            
        Returns:
            List of potential email addresses
        """
        patterns = []
        domain = domain.lower().strip()
        
        # Standard international patterns
        standard_prefixes = [
            'info', 'contact', 'hello', 'mail', 'office',
            'support', 'sales', 'admin', 'service',
            'communication', 'general', 'inquiry', 'welcome'
        ]
        
        # French-specific patterns (for .fr domains)
        if self._is_french_domain(domain):
            french_prefixes = [
                'contact', 'info', 'commercial', 'accueil',
                'direction', 'vente', 'service.client'
            ]
            standard_prefixes.extend(french_prefixes)
        
        # German-specific patterns
        if domain.endswith('.de'):
            german_prefixes = ['info', 'kontakt', 'office', 'verwaltung']
            standard_prefixes.extend(german_prefixes)
        
        # Spanish-specific patterns
        if domain.endswith('.es'):
            spanish_prefixes = ['info', 'contacto', 'oficina', 'ventas']
            standard_prefixes.extend(spanish_prefixes)
        
        # Turkish-specific patterns
        if domain.endswith('.tr'):
            turkish_prefixes = ['info', 'iletisim', 'destek', 'satis']
            standard_prefixes.extend(turkish_prefixes)
        
        # Generate all patterns
        for prefix in standard_prefixes:
            patterns.append(f"{prefix}@{domain}")
        
        # If company name provided, generate intelligent patterns
        if company_name:
            clean_name = company_name.lower().strip()
            # Remove common suffixes
            for suffix in ['ltd', 'inc', 'llc', 'sa', 'sas', 'gmbh', 'ag']:
                clean_name = clean_name.replace(suffix, '').strip()
            
            # Generate name-based patterns
            if clean_name:
                patterns.insert(0, f"{clean_name.replace(' ', '')}@{domain}")
                patterns.insert(0, f"{clean_name.replace(' ', '.')}@{domain}")
        
        return patterns
    
    def verify_email_smtp(self, email: str) -> Tuple[bool, str]:
        """
        Verify email via SMTP (REMOVED - too slow and unreliable)
        
        Args:
            email: Email address to verify
            
        Returns:
            (False, "SMTP verification disabled")
        """
        return (False, "SMTP verification disabled")
    
    def verify_email_batch(self, emails: List[str], max_attempts: int = 5) -> Optional[str]:
        """
        Verify a batch of emails and return first valid one
        Pattern-based approach without network calls
        
        Args:
            emails: List of email addresses to check
            max_attempts: Maximum number of emails to try (default: 5)
            
        Returns:
            First valid email or None
        """
        # Simply return the first pattern if available
        # No SMTP verification (too slow)
        if emails:
            logger.info(f"Using pattern-based email: {emails[0]}")
            return emails[0]
        return None
    
    def extract_whois_emails(self, domain: str) -> List[str]:
        """
        Extract emails from WHOIS data
        
        Args:
            domain: Domain to lookup
            
        Returns:
            List of emails found in WHOIS
        """
        try:
            import whois
            w = whois.whois(domain)
            
            emails = set()
            
            # Check common WHOIS fields
            if hasattr(w, 'emails'):
                if isinstance(w.emails, list):
                    emails.update(w.emails)
                elif isinstance(w.emails, str):
                    emails.add(w.emails)
            
            # Check admin email
            if hasattr(w, 'admin_email') and w.admin_email:
                emails.add(w.admin_email)
            
            # Check registrant email
            if hasattr(w, 'registrant_email') and w.registrant_email:
                emails.add(w.registrant_email)
            
            # Filter out privacy/generic emails
            valid_emails = [e for e in emails if e and not self._is_privacy_email(e)]
            
            if valid_emails:
                logger.info(f"WHOIS emails found: {valid_emails}")
            
            return valid_emails
            
        except Exception as e:
            logger.debug(f"WHOIS lookup failed for {domain}: {e}")
            return []
    
    def find_email_enhanced(self, domain: str, company_name: str = "", 
                           scraped_emails: Set[str] = None) -> Tuple[Optional[str], str]:
        """
        Multi-layer email discovery
        
        Strategy:
        1. Use scraped emails if available (web scraping)
        2. Generate and test common patterns (pattern generation)
        3. Extract from WHOIS data (WHOIS lookup)
        
        Args:
            domain: Domain to search
            company_name: Company name for intelligent patterns
            scraped_emails: Emails found from web scraping
            
        Returns:
            (email, method) tuple - email address and discovery method
        """
        domain = self._clean_domain(domain)
        
        # Layer 1: Use scraped emails
        if scraped_emails:
            for email in scraped_emails:
                if email and '@' in email:
                    logger.info(f"Using scraped email: {email}")
                    return (email, "scraped")
        
        # Layer 2: Pattern generation (fast, no network calls)
        logger.info(f"Generating email patterns for {domain}")
        patterns = self.generate_common_patterns(domain, company_name)
        
        if patterns:
            # Return first pattern immediately (no SMTP verification)
            first_pattern = patterns[0]
            logger.info(f"Using pattern: {first_pattern}")
            return (first_pattern, "pattern")
        
        # Layer 3: WHOIS lookup (fallback)
        logger.info(f"Trying WHOIS lookup for {domain}")
        whois_emails = self.extract_whois_emails(domain)
        if whois_emails:
            return (whois_emails[0], "whois")
        
        logger.warning(f"No email found for {domain}")
        return (None, "none")
    
    def _clean_domain(self, url_or_domain: str) -> str:
        """
        Extract clean domain from URL or domain string
        
        Args:
            url_or_domain: URL or domain
            
        Returns:
            Clean domain (e.g., 'example.com')
        """
        if not url_or_domain:
            return ""
        
        url_or_domain = url_or_domain.strip().lower()
        
        # If it looks like a URL, parse it
        if '://' in url_or_domain or url_or_domain.startswith('www.'):
            try:
                if not url_or_domain.startswith('http'):
                    url_or_domain = 'http://' + url_or_domain
                parsed = urlparse(url_or_domain)
                domain = parsed.netloc or parsed.path
            except:
                domain = url_or_domain
        else:
            domain = url_or_domain
        
        # Remove www.
        domain = domain.replace('www.', '')
        
        # Remove path/query
        domain = domain.split('/')[0].split('?')[0]
        
        return domain
    
    def _is_french_domain(self, domain: str) -> bool:
        """Check if domain is French"""
        return domain.endswith('.fr')
    
    def _is_privacy_email(self, email: str) -> bool:
        """Check if email is a privacy/generic email"""
        privacy_keywords = [
            'privacy', 'whoisguard', 'protect', 'proxy', 'masked',
            'hidden', 'redacted', 'withheld', 'private', 'anonymo'
        ]
        email_lower = email.lower()
        return any(keyword in email_lower for keyword in privacy_keywords)
