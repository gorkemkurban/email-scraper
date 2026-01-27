"""
Configuration settings and constants
"""

# Web Scraping Settings
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Email Validation
# Filter out personal and system email services
BLACKLISTED_DOMAINS = [
    'gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com',
    'yandex.com', 'mail.ru', 'protonmail.com', 'icloud.com',
    'liand.com', 'msn.com', 'aol.com', 'inbox.com',
    'gmx.com', 'zoho.com', 'mail.com', 'tutanota.com',
    # Technical/spam domains
    'sentry.wixpress.com', 'sentry-next.wixpress.com', 'wixpress.com', 'wix.com',
    'example.com', 'test.com', 'localhost', 'domain.com',
    'email.com', 'yourdomain.com', 'yoursite.com',
    # Image/asset domains
    '4x.png', '2x.png', '3x.png', '.png', '.jpg', '.gif',
    'sentry.io', 'sentry-cdn.com'
]

# Example email addresses to filter out
EXAMPLE_EMAILS = [
    'utilisateur@domaine.com', 'example@example.com', 'info@example.com',
    'contact@example.com', 'test@test.com', 'email@email.com',
    'your@email.com', 'youremail@domain.com', 'name@domain.com'
]

# Page Detection - Multi-Language Keywords
CONTACT_PAGE_KEYWORDS = {
    'tr': ['withtisim', 'withtişim', 'bize-ulasin', 'bize-ulaşın', 'contact', 'contactez', 'kontakt'],
    'en': ['contact', 'contact-us', 'reach-us', 'get-in-touch'],
    'fr': ['contact', 'contactez', 'contactez-nous', 'nous-contacter'],
    'de': ['kontakt', 'kontaktieren', 'kontaktiere-uns'],
    'es': ['contacto', 'contactar', 'contactenos'],
    'it': ['contatto', 'contattaci', 'contatti'],
    'ar': ['اتصل', 'تواصل', 'contact'],
    'pt': ['contato', 'contacto', 'fale-conosco'],
    'nl': ['contact', 'contacteer', 'neem-contact-op'],
    'pl': ['kontakt', 'skontaktuj'],
    'ru': ['контакт', 'связаться', 'contact']
}

ABOUT_PAGE_KEYWORDS = {
    'tr': ['hakkimizda', 'hakkımızda', 'hakkinda', 'kurumsal', 'about'],
    'en': ['about', 'about-us', 'who-we-are', 'our-story', 'company'],
    'fr': ['a-propos', 'qui-sommes-nous', 'notre-histoire', 'about'],
    'de': ['uber-uns', 'über-uns', 'about', 'unternehmen'],
    'es': ['sobre-nosotros', 'quienes-somos', 'acerca', 'about'],
    'it': ['chi-siamo', 'about', 'la-nostra-storia'],
    'ar': ['من نحن', 'عن الشركة', 'about'],
    'pt': ['sobre', 'sobre-nos', 'quem-somos', 'about'],
    'nl': ['oandr-ons', 'about', 'wie-zijn-we'],
    'pl': ['o-nas', 'about'],
    'ru': ['о-нас', 'о-компании', 'about']
}

# Excel Column Names
EXCEL_COLUMNS = {
    'company': 'Company Name',
    'address': 'Address',
    'phone': 'Phone',
    'website': 'Website',
    'sector': 'Sector',
    'email': 'Email',
    'maps': 'Google Maps URL'
}

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(leandlname)s - %(message)s'
