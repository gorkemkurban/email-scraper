"""
Email Scraper - Graphical User Interface
Modern, user-friendly GUI for email extraction
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

from excel_handler import ExcelHandler
from web_scraper import WebScraper
from email_extractor import EmailExtractor


class TextHandler(logging.Handler):
    """Directs log messages to text widget"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.config(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.config(state='disabled')
        self.text_widget.after(0, append)


class EmailScraperGUI:
    """Email Scraper Graphical Interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Email Scraper - Business Lead Finder")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Variables
        self.input_file = None
        self.output_file = None
        self.is_running = False
        self.stats = {"found": 0, "not_found": 0, "total": 0}
        
        # Theme
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.setup_logging()
    
    def setup_ui(self):
        """Create UI components"""
        
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="Email Scraper - Business Lead Finder",
            font=("Arial", 18, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Automatically extract email addresses from websites",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # File selection section
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding="15")
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Input file
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Excel File:", width=15).pack(side=tk.LEFT)
        
        self.input_label = ttk.Label(
            input_frame, 
            text="No file selected...",
            foreground="gray"
        )
        self.input_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        select_btn = ttk.Button(
            input_frame,
            text="Select File",
            command=self.select_input_file
        )
        select_btn.pack(side=tk.RIGHT)
        
        # Output file
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output File:", width=15).pack(side=tk.LEFT)
        
        self.output_label = ttk.Label(
            output_frame,
            text="Will be generated automatically...",
            foreground="gray"
        )
        self.output_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Action buttons
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(
            action_frame,
            text="Start Analysis",
            command=self.start_analysis,
            state=tk.DISABLED
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            action_frame,
            text="Stop",
            command=self.stop_analysis,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Help buttons - right side
        ttk.Button(
            action_frame,
            text="Download Template",
            command=self.download_template
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Help",
            command=self.show_help
        ).pack(side=tk.RIGHT, padx=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding="15")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress = ttk.Progressbar(
            progress_frame,
            length=400,
            mode='determinate'
        )
        self.progress.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(
            progress_frame,
            text="Ready...",
            font=("Arial", 9)
        )
        self.progress_label.pack(anchor=tk.W)
        
        # Statistics section
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding="15")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_label = ttk.Label(
            stats_frame,
            text="Found: 0  |  Not Found: 0  |  Total: 0",
            font=("Arial", 11, "bold")
        )
        self.stats_label.pack()
        
        # Log section
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            yscrollcommand=log_scroll.set,
            height=15,
            state='disabled',
            font=("Consolas", 9)
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
    
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        
        # Add GUI handler
        text_handler = TextHandler(self.log_text)
        text_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(text_handler)
    
    def select_input_file(self):
        """File selection dialog"""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if filename:
            self.input_file = filename
            self.input_label.config(text=os.path.basename(filename), foreground="black")
            
            # Generate output filename
            base_name = Path(filename).stem
            output_dir = Path(filename).parent
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = str(output_dir / f"{base_name}_result_{timestamp}.xlsx")
            self.output_label.config(text=os.path.basename(self.output_file), foreground="black")
            
            # Enable start button
            self.start_btn.config(state=tk.NORMAL)
            
            self.log_message(f"File selected: {os.path.basename(filename)}")
    
    def log_message(self, message):
        """Add log message"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def update_progress(self, current, total, message=""):
        """Update progress bar"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = percentage
            self.progress_label.config(text=f"{message} ({current}/{total})")
    
    def update_stats(self):
        """Update statistics"""
        self.stats_label.config(
            text=f"Found: {self.stats['found']}  |  "
                 f"Not Found: {self.stats['not_found']}  |  "
                 f"Total: {self.stats['total']}"
        )
    
    def start_analysis(self):
        """Start analysis"""
        if not self.input_file:
            messagebox.showerror("Error", "Please select an Excel file first!")
            return
        
        # Configure buttons
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_running = True
        
        # Reset statistics
        self.stats = {"found": 0, "not_found": 0, "total": 0}
        self.update_stats()
        
        # Clear log
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # Run in thread
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
    
    def stop_analysis(self):
        """Stop analysis"""
        self.is_running = False
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("\nAnalysis stopped!")
    
    def run_analysis(self):
        """Run analysis (in thread)"""
        try:
            logger = logging.getLogger(__name__)
            logger.info("=" * 60)
            logger.info("EMAIL SCRAPER STARTED")
            logger.info("=" * 60)
            
            # Read Excel and check sheets
            excel_handler = ExcelHandler(self.input_file)
            sheet_names = excel_handler.get_sheet_names()
            
            logger.info(f"\nExcel file: {os.path.basename(self.input_file)}")
            logger.info(f"Total sheets: {len(sheet_names)}")
            
            if len(sheet_names) > 1:
                logger.info(f"Sheets: {', '.join(sheet_names)}")
            
            # Process all sheets
            all_sheets_data = {}
            total_found = 0
            total_not_found = 0
            total_processed = 0
            
            # Calculate total rows once (skip this - too slow for large files)
            # Just process each sheet as we go
            
            for sheet_idx, sheet_name in enumerate(sheet_names, 1):
                if not self.is_running:
                    break
                
                logger.info(f"\n{'='*60}")
                logger.info(f"SHEET {sheet_idx}/{len(sheet_names)}: {sheet_name}")
                logger.info(f"{'='*60}")
                
                try:
                    # Read sheet with structure preservation
                    sheet_handler = ExcelHandler(self.input_file)
                    df = sheet_handler.read_excel(sheet_name=sheet_name, preserve_structure=True)
                    
                    # Get websites
                    websites = sheet_handler.get_websites(detect_header=True)
                    
                    if not websites:
                        logger.info(f"All emails present in '{sheet_name}', skipping...")
                        all_sheets_data[sheet_name] = sheet_handler.df
                        continue
                    
                    logger.info(f"\nSearching emails for {len(websites)} companies...\n")
                    
                    # Create web scraper
                    scraper = WebScraper()
                
                    sheet_found = 0
                    sheet_not_found = 0
                
                    # Search email for each website
                    for i, site_info in enumerate(websites, 1):
                        if not self.is_running:
                            break
                        
                        company = site_info['company']
                        website = site_info['website']
                        index = site_info['index']
                        email_col_idx = site_info.get('email_col_idx')
                        
                        # Limit company name display
                        display_company = company[:50] if company and company != 'nan' else 'Unknown Company'
                    
                        logger.info(f"[{i}/{len(websites)}] {display_company}")
                        logger.info(f"    {website}")
                        
                        # Update progress
                        total_processed += 1
                        self.update_progress(
                            i, 
                            len(websites),
                            f"[Sheet {sheet_idx}/{len(sheet_names)}] {display_company[:30]}..."
                        )
                        
                        try:
                            # Find email
                            email = scraper.scrape_website(website)
                            
                            if email:
                                logger.info(f"    Found: {email}\n")
                                sheet_handler.update_email(index, email, email_col_idx=email_col_idx)
                                sheet_found += 1
                                total_found += 1
                            else:
                                logger.info(f"    Not found\n")
                                sheet_not_found += 1
                                total_not_found += 1
                            
                            self.stats['found'] = total_found
                            self.stats['not_found'] = total_not_found
                            self.stats['total'] = total_found + total_not_found
                            self.update_stats()
                            
                        except Exception as e:
                            logger.error(f"    Error: {e}\n")
                            sheet_not_found += 1
                            total_not_found += 1
                            self.stats['not_found'] = total_not_found
                            self.stats['total'] = total_found + total_not_found
                            self.update_stats()
                    
                    # Sheet summary
                    logger.info(f"\n'{sheet_name}' Summary:")
                    logger.info(f"   Found: {sheet_found}")
                    logger.info(f"   Not found: {sheet_not_found}")
                    
                    # Save sheet data
                    all_sheets_data[sheet_name] = sheet_handler.df
                    
                except Exception as sheet_error:
                    logger.error(f"Error processing sheet '{sheet_name}': {sheet_error}")
                    import traceback
                    traceback.print_exc()
                    # Continue with next sheet instead of stopping
                    continue
            
            if self.is_running:
                # Save results
                logger.info("\nSaving results...")
                
                if len(all_sheets_data) == 1:
                    # Single sheet
                    excel_handler.write_excel(
                        list(all_sheets_data.values())[0], 
                        self.output_file,
                        sheet_name=list(all_sheets_data.keys())[0]
                    )
                else:
                    # Multi-sheet
                    excel_handler.write_excel_multisheet(all_sheets_data, self.output_file)
                
                logger.info("\n" + "=" * 60)
                logger.info("SUMMARY")
                logger.info("=" * 60)
                logger.info(f"Sheets processed: {len(sheet_names)}")
                logger.info(f"Emails found: {total_found}")
                logger.info(f"Not found: {total_not_found}")
                logger.info(f"Output file: {os.path.basename(self.output_file)}")
                logger.info("=" * 60)
                
                # Success message
                messagebox.showinfo(
                    "Complete!",
                    f"Process complete!\n\n"
                    f"Sheets processed: {len(sheet_names)}\n"
                    f"Emails found: {total_found}\n"
                    f"Not found: {total_not_found}\n\n"
                    f"Results saved:\n{os.path.basename(self.output_file)}"
                )
        
        except Exception as e:
            logger.error(f"\nFatal error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            # Reset buttons
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.is_running = False
    
    def show_help(self):
        """Show help window"""
        help_window = tk.Toplevel(self.root)
        help_window.title("How to Use")
        help_window.geometry("700x600")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(help_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        help_text = tk.Text(
            help_window,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            padx=20,
            pady=20
        )
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=help_text.yview)
        
        # Help content
        help_content = """
EMAIL SCRAPER - USER GUIDE

Quick Start:
1. Click "Select File"
2. Choose your Excel file
3. Click "Start Analysis"
4. Results are automatically saved when complete

Excel File Structure:

Required columns:
- Website (required): Company website URL
- Email (required): Email column (program fills this)

Optional columns:
- Company Name
- Address
- Phone
- Sector
- Google Maps URL

Important: 
- "Website" column must have data
- "Email" column empty rows will be searched
- Rows with existing emails are skipped

Example Excel Row:

Company Name: ACME Corp
Website: https://www.acme.com
Email: [EMPTY] → Program will fill this

Features:

- 8-layer Email Detection
  * Homepage scanning
  * Contact page detection
  * About page scanning
  * mailto: links
  * Form fields
  * JavaScript encoding
  * HTML attributes
  * HTML comments

- 11-language Contact Page Detection
  (EN, FR, DE, ES, IT, PT, NL, PL, RU, AR, TR)

- Smart Filtering
  * Filters personal emails (Gmail, Hotmail)
  * Filters system emails (Sentry, Wix)
  * Removes junk patterns

- Multi-sheet Excel Support
  * Process files with multiple sheets
  * Preserves sheet structure in output

Success Rate:

50-60% success rate is normal. Reasons for not finding:
- Website doesn't publicly display email
- Bot protection blocking
- Email genuinely not on website

FAQ:

Q: Program seems frozen?
A: Normal! Check progress in log section.

Q: Too many "not found" results?
A: 50-60% success rate is normal. Some sites
   don't share emails.

Q: Can I process multiple Excel files?
A: Yes! Process each file separately.

Support:

If you encounter issues:
1. Check the log window for details
2. Review email_scraper.log file
3. Verify Excel file format

"""
        
        help_text.insert(1.0, help_content)
        help_text.config(state='disabled')
    
    def download_template(self):
        """Create and download Excel template"""
        import pandas as pd
        
        # Ask save location
        filename = filedialog.asksaveasfilename(
            title="Save Excel Template",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="email_scraper_template.xlsx"
        )
        
        if not filename:
            return
        
        try:
            # Create sample data
            sample_data = {
                'Company Name': [
                    'Example Company 1',
                    'Example Company 2',
                    'Example Company 3'
                ],
                'Address': [
                    '123 Main St, City',
                    '456 Center Ave, Town',
                    '789 Business Blvd, Metro'
                ],
                'Phone': [
                    '+1 555-123-4567',
                    '+1 555-234-5678',
                    '+1 555-345-6789'
                ],
                'Website': [
                    'https://www.example1.com',
                    'https://www.example2.com',
                    'https://www.example3.com'
                ],
                'Sector': [
                    'Technology',
                    'Manufacturing',
                    'Services'
                ],
                'Email': [
                    '',
                    '',
                    ''
                ],
                'Google Maps URL': [
                    'https://maps.google.com/?cid=123',
                    'https://maps.google.com/?cid=456',
                    'https://maps.google.com/?cid=789'
                ]
            }
            
            df = pd.DataFrame(sample_data)
            df.to_excel(filename, index=False, sheet_name='Companies')
            
            messagebox.showinfo(
                "Success!",
                f"Excel template created:\n{os.path.basename(filename)}\n\n"
                "Replace the example data with your companies\n"
                "and keep the column structure."
            )
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create template:\n{str(e)}")


def main():
    root = tk.Tk()
    app = EmailScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
