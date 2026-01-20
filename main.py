"""
Email Scraper - Ana Program
Excel'deki business lead'lerin websitelerinden email adreslerini bulur
"""

import sys
import logging
import time
from pathlib import Path
from config import LOG_LEVEL, LOG_FORMAT
from excel_handler import ExcelHandler
from web_scraper import WebScraper

# Loglama yapılandırması
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('email_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Program başlangıç banner'ı"""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║         EMAIL SCRAPER - Business Lead Finder          ║
    ║           Website'lerden Email Adresi Bulma           ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def main(input_file: str, output_file: str = None):
    """
    Ana program fonksiyonu
    
    Args:
        input_file: Giriş Excel dosyası
        output_file: Çıkış Excel dosyası (opsiyonel)
    """
    print_banner()
    
    # Çıkış dosyası belirtilmemişse, input dosyasının adına _output ekle
    if not output_file:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_output{input_path.suffix}")
    
    logger.info(f"Giriş dosyası: {input_file}")
    logger.info(f"Çıkış dosyası: {output_file}")
    
    try:
        # Excel handler'ı oluştur
        excel_handler = ExcelHandler(input_file)
        df = excel_handler.read_excel()
        
        # Email eksik olan website'leri al
        websites = excel_handler.get_websites()
        
        if not websites:
            logger.info("Tüm firmaların email adresleri mevcut!")
            print("\n✅ Tüm firmaların email adresleri zaten mevcut.")
            return
        
        print(f"\n📋 {len(websites)} firma için email adresi aranacak...\n")
        
        # Web scraper'ı oluştur
        scraper = WebScraper()
        
        # İstatistikler
        found_count = 0
        not_found_count = 0
        
        # Her website için email ara
        for i, site_info in enumerate(websites, 1):
            company = site_info['company']
            website = site_info['website']
            index = site_info['index']
            
            print(f"[{i}/{len(websites)}] {company}")
            print(f"    🌐 {website}")
            
            try:
                # Email'i bul
                email = scraper.scrape_website(website)
                
                if email:
                    print(f"    ✅ Email bulundu: {email}")
                    excel_handler.update_email(index, email)
                    found_count += 1
                else:
                    print(f"    ❌ Email bulunamadı")
                    not_found_count += 1
                
                print()
                
                # Rate limiting (site'lere aşırı yükleme yapmamak için)
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Hata oluştu ({company}): {e}")
                print(f"    ⚠️  Hata: {e}\n")
                not_found_count += 1
                continue
        
        # Sonuçları kaydet
        print("💾 Sonuçlar kaydediliyor...")
        excel_handler.write_excel(excel_handler.df, output_file)
        
        # Özet
        print("\n" + "="*60)
        print("📊 ÖZET")
        print("="*60)
        print(f"✅ Email bulundu:      {found_count}")
        print(f"❌ Email bulunamadı:   {not_found_count}")
        print(f"📁 Çıkış dosyası:      {output_file}")
        print("="*60)
        
        logger.info("İşlem tamamlandı!")
        
    except FileNotFoundError:
        logger.error(f"Dosya bulunamadı: {input_file}")
        print(f"\n❌ Hata: '{input_file}' dosyası bulunamadı!")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}", exc_info=True)
        print(f"\n❌ Hata oluştu: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python main.py <input.xlsx> [output.xlsx]")
        print("\nÖrnek:")
        print("  python main.py leads.xlsx")
        print("  python main.py leads.xlsx sonuclar.xlsx")
        sys.exit(1)
    
    input_excel = sys.argv[1]
    output_excel = sys.argv[2] if len(sys.argv) > 2 else None
    
    main(input_excel, output_excel)
