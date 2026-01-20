"""
Excel file reading and writing module
"""

import pandas as pd
from typing import List, Dict
import logging
from config import EXCEL_COLUMNS

logger = logging.getLogger(__name__)


class ExcelHandler:
    """Handler class for Excel file operations"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
    
    def get_sheet_names(self) -> List[str]:
        """
        Returns all sheet names in the Excel file
        
        Returns:
            List of sheet names
        """
        try:
            excel_file = pd.ExcelFile(self.file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Failed to get sheet names: {e}")
            return []
    
    def read_excel(self, sheet_name=None) -> pd.DataFrame:
        """
        Reads Excel file (single or multi-sheet)
        
        Args:
            sheet_name: Sheet name or index. None reads first sheet.
        
        Returns:
            pandas DataFrame
        """
        try:
            if sheet_name is None:
                # Read first sheet
                self.df = pd.read_excel(self.file_path)
                logger.info(f"Excel file read: {self.file_path} ({len(self.df)} rows)")
            else:
                # Read specified sheet
                self.df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                logger.info(f"Excel sheet '{sheet_name}' read: {len(self.df)} rows")
            
            # Normalize column names (different sheets may have different names)
            self._normalize_column_names()
            
            return self.df
        except Exception as e:
            logger.error(f"Excel reading error: {e}")
            raise
    
    def _normalize_column_names(self):
        """
        Converts different column names to standard names
        E.g.: 'Websitesi' -> 'Website', 'E-Posta' -> 'Email'
        """
        if self.df is None:
            return
        
        # Column mapping table
        column_mapping = {
            # Website variations
            'Websitesi': 'Website',
            'Websites': 'Website',
            'Web Sitesi': 'Website',
            'websitesi': 'Website',
            'website': 'Website',
            
            # Email variations
            'E-Posta': 'Email',
            'E-posta': 'Email',
            'e-posta': 'Email',
            'EPosta': 'Email',
            'eposta': 'Email',
            'E-Mail': 'Email',
            'email': 'Email',
            
            # Phone variations
            'Telefon ': 'Phone',
            'Telefon': 'Phone',
            'telefon': 'Phone',
            
            # Company name variations
            'Firma Adı': 'Company Name',
            'Firma Adi': 'Company Name',
            'Şirket Adı': 'Company Name',
            
            # Address variations
            'Adres': 'Address',
            
            # Sector variations
            'Sektör': 'Sector',
            'Sektor': 'Sector',
            
            # Maps variations
            'Google Maps Linki': 'Google Maps URL',
            'Google Maps Link': 'Google Maps URL',
            'googleMapsURL': 'Google Maps URL',
            'Maps Link': 'Google Maps URL'
        }
        
        # Rename operation
        renamed_cols = {}
        for old_name, new_name in column_mapping.items():
            if old_name in self.df.columns:
                renamed_cols[old_name] = new_name
        
        if renamed_cols:
            self.df.rename(columns=renamed_cols, inplace=True)
            logger.debug(f"Column names normalized: {renamed_cols}")
    
    def write_excel(self, df: pd.DataFrame, output_path: str, sheet_name='Sheet1'):
        """
        Writes DataFrame to Excel file
        
        Args:
            df: DataFrame to write
            output_path: Output file path
            sheet_name: Sheet name
        """
        try:
            df.to_excel(output_path, index=False, sheet_name=sheet_name, engine='openpyxl')
            logger.info(f"Results saved: {output_path}")
        except Exception as e:
            logger.error(f"Excel writing error: {e}")
            raise
    
    def write_excel_multisheet(self, sheets_dict: dict, output_path: str):
        """
        Writes multiple sheets to Excel file
        
        Args:
            sheets_dict: {sheet_name: DataFrame} dictionary
            output_path: Output file path
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in sheets_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f"Multi-sheet Excel saved: {output_path} ({len(sheets_dict)} sheets)")
        except Exception as e:
            logger.error(f"Multi-sheet Excel writing error: {e}")
            raise
    
    def get_websites(self) -> List[Dict]:
        """
        Extracts website information from Excel
        
        Returns:
            List of dicts containing website information
        """
        if self.df is None:
            raise ValueError("Call read_excel() method first")
        
        results = []
        website_col = EXCEL_COLUMNS['website']
        email_col = EXCEL_COLUMNS['email']
        
        for idx, row in self.df.iterrows():
            # If website exists and email is empty/missing
            website = str(row.get(website_col, '')).strip()
            email = str(row.get(email_col, '')).strip()
            
            # If email is empty or NaN
            if website and website != 'nan' and (not email or email == 'nan'):
                results.append({
                    'index': idx,
                    'company': row.get(EXCEL_COLUMNS['company'], ''),
                    'website': website,
                    'current_email': email
                })
        
        logger.info(f"Found {len(results)} websites with missing emails")
        return results
    
    def update_email(self, index: int, email: str):
        """
        Updates the email in specified row
        
        Args:
            index: Row index
            email: New email address
        """
        if self.df is None:
            raise ValueError("Call read_excel() method first")
        
        email_col = EXCEL_COLUMNS['email']
        self.df.at[index, email_col] = email
        logger.debug(f"Row {index} email updated: {email}")
