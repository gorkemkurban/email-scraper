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
    
    def read_excel(self, sheet_name=None, preserve_structure=False) -> pd.DataFrame:
        """
        Reads Excel file (single or multi-sheet)
        
        Args:
            sheet_name: Sheet name or index. None reads first sheet.
            preserve_structure: If True, reads without interpreting headers (preserves all rows)
        
        Returns:
            pandas DataFrame
        """
        try:
            read_kwargs = {}
            if preserve_structure:
                # Read without interpreting first row as header
                read_kwargs['header'] = None
            
            if sheet_name is None:
                # Read first sheet
                self.df = pd.read_excel(self.file_path, **read_kwargs)
                logger.info(f"Excel file read: {self.file_path} ({len(self.df)} rows)")
            else:
                # Read specified sheet
                self.df = pd.read_excel(self.file_path, sheet_name=sheet_name, **read_kwargs)
                logger.info(f"Excel sheet '{sheet_name}' read: {len(self.df)} rows)")
            
            # Normalize column names only if not preserving structure
            if not preserve_structure:
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
    
    def get_websites(self, detect_header=True) -> List[Dict]:
        """
        Extracts website information from Excel
        
        Args:
            detect_header: If True, tries to detect header row and column positions
        
        Returns:
            List of dicts containing website information
        """
        if self.df is None:
            raise ValueError("Call read_excel() method first")
        
        results = []
        
        # If columns are numeric (header=None mode), detect structure
        if detect_header and all(isinstance(col, int) for col in self.df.columns):
            website_col_idx, email_col_idx, company_col_idx = self._detect_columns()
            
            if website_col_idx is None or email_col_idx is None:
                logger.warning("Could not detect Website/Email columns, using standard mode")
                return self._get_websites_standard()
            
            logger.info(f"Detected columns - Website: {website_col_idx}, Email: {email_col_idx}, Company: {company_col_idx}")
            
            # Process rows
            for idx, row in self.df.iterrows():
                # Skip header row (typically first row)
                if idx == 0:
                    continue
                
                website = str(row.iloc[website_col_idx] if website_col_idx < len(row) else '').strip()
                email = str(row.iloc[email_col_idx] if email_col_idx < len(row) else '').strip()
                company = str(row.iloc[company_col_idx] if company_col_idx is not None and company_col_idx < len(row) else '').strip()
                
                # Skip if this looks like a header or separator row
                if self._is_header_or_separator_row(row):
                    continue
                
                # If website exists and email is empty/missing
                if website and website not in ['nan', '', 'Website', 'Websites']:
                    if not email or email in ['nan', '', 'Email', 'E-Posta']:
                        results.append({
                            'index': idx,
                            'company': company,
                            'website': website,
                            'current_email': email,
                            'email_col_idx': email_col_idx
                        })
        else:
            return self._get_websites_standard()
        
        logger.info(f"Found {len(results)} websites with missing emails")
        return results
    
    def _detect_columns(self):
        """Detects Website, Email, and Company columns in numeric-indexed DataFrame"""
        website_col = None
        email_col = None
        company_col = None
        
        # Check first row for headers
        if len(self.df) > 0:
            first_row = self.df.iloc[0]
            for col_idx, val in enumerate(first_row):
                val_str = str(val).strip().lower()
                
                # Website detection
                if 'website' in val_str or 'web' in val_str:
                    website_col = col_idx
                # Email detection  
                elif 'email' in val_str or 'e-posta' in val_str or 'mail' in val_str:
                    email_col = col_idx
                # Company detection
                elif 'firma' in val_str or 'company' in val_str or 'şirket' in val_str:
                    company_col = col_idx
        
        return website_col, email_col, company_col
    
    def _is_header_or_separator_row(self, row) -> bool:
        """Checks if row is a header or separator (city name, etc.)"""
        # Count how many cells are empty
        non_empty = sum(1 for val in row if str(val).strip() not in ['', 'nan', 'None'])
        
        # If only 1-2 cells have data, likely a separator row
        if non_empty <= 2:
            return True
        
        # Check if row contains header-like text
        for val in row:
            val_str = str(val).strip().lower()
            if val_str in ['firma adı', 'company name', 'website', 'email', 'e-posta', 'telefon', 'phone']:
                return True
        
        return False
    
    def _get_websites_standard(self) -> List[Dict]:
        """Standard website extraction (for named columns)"""
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
        
        return results
    
    def update_email(self, index: int, email: str, email_col_idx=None):
        """
        Updates the email in specified row
        
        Args:
            index: Row index
            email: New email address
            email_col_idx: Column index (for numeric columns), None uses named column
        """
        if self.df is None:
            raise ValueError("Call read_excel() method first")
        
        if email_col_idx is not None:
            # Numeric column mode
            self.df.iat[index, email_col_idx] = email
        else:
            # Named column mode
            email_col = EXCEL_COLUMNS['email']
            self.df.at[index, email_col] = email
        
        logger.debug(f"Row {index} email updated: {email}")
