# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - 2026-01-27

### Added - Pattern-Based Email Discovery
- Smart Email Patterns: Automatically generates common email patterns (info@, contact@, sales@)
- Instant Results: No SMTP verification delays, returns immediately
- Language-Specific: French (bonjour@, accueil@), German (kontakt@), Spanish (contacto@)
- WHOIS Backup: Falls back to WHOIS data if patterns don't work
- Enhanced Statistics: Shows breakdown (Scraped/Patterns/WHOIS)
- Much Faster: No network delays from SMTP verification

### Performance Improvement
- Previous approach: SMTP verification was too slow and often timed out
- New approach: Direct pattern generation - most companies use standard patterns
- Test results: 10/10 emails found (6 scraped + 4 patterns) in quick test
- Expected: Significant reduction in 'Not Found' results

### Technical Changes
- Removed slow SMTP verification (was causing timeouts)
- Enhanced email_finder.py with pattern-first strategy  
- Improved error handling for connection issues
- Better privacy email filtering (Wix, abuse addresses)

## [2.1.1] - 2026-01-26

### Fixed - CAPTCHA Detection Improvements
- Smarter CAPTCHA Detection: Reduced false positives with intelligent multi-signal detection
- Better Cloudflare Handling: Sites using Cloudflare no longer automatically marked as CAPTCHA
- Multi-Signal Analysis: Requires at least 2 strong indicators before marking as CAPTCHA
- Specific Pattern Matching: Checks for actual captcha widgets (g-recaptcha, h-captcha, challenge forms)
- HTTP 403 Intelligence: HTTP 403 errors now checked for real captcha presence before marking
- Challenge Page Detection: Identifies real challenge pages by title, content, and structure

### Technical Details
- Added _is_real_captcha() method with multi-signal scoring system
- Looks for specific captcha indicators: g-recaptcha, h-captcha, cf-challenge-form, data-sitekey
- Checks challenge-specific text
- Analyzes page title for challenge keywords
- Requires 2+ signals to confirm CAPTCHA (prevents false positives)

## [2.1.0] - 2026-01-26

### Added - Anti-Hang Protection and Manual Control
- Manual Skip Button: New 'Skip Current Site' button in GUI to manually skip stuck websites
- Automatic Timeout Protection: Each website now has a hard 15-second timeout limit
- Thread-Based Scraping: Background scraping with periodic skip checks every 0.5 seconds
- SKIPPED Marker: Manually skipped sites are marked as 'SKIPPED' in Excel output
- Enhanced Help Documentation: Updated help window with skip button instructions

### Changed
- Increased REQUEST_TIMEOUT from 2.5s to 3s for more reliable connections
- Increased MAX_WEBSITE_TIMEOUT from 10s to 15s per site
- Skip button automatically activates/deactivates with analysis state

### Fixed
- Program hanging on bot-protected sites
- No way to skip problematic websites without stopping entire analysis
- Infinite loops when websites take too long to respond
- Missing user feedback when sites are taking too long

## [2.0.0] - 2026-01-23

### Added - System Safety and Performance
- Memory Protection: 500MB RAM limit with automatic cleanup
- CPU Throttling: Auto-pause when CPU usage exceeds 80 percent
- Network Safety: Connection pooling and timeout controls
- Disk Protection: Pre-validates minimum free space before operations
- Auto-Save System: Progress automatically saved every 10 companies
- Crash Recovery: Safe shutdown on Ctrl+C with data preservation
- System Monitoring: Real-time RAM and CPU usage display
- Performance Optimizations: Lightweight HTML parser, reduced page scanning

### Changed
- Reduced timeout from 10s to 8s for faster processing
- Reduced max retries from 3 to 2 attempts
- Changed HTML parser from lxml to html.parser for lower memory usage
- Rate limiting reduced from 2s to 1.5s between sites
- Maximum pages per site limited to 3 for better performance

### Fixed
- Memory leak from unclosed HTTP sessions
- Program freezing on slow websites
- Resource exhaustion on large Excel files

## [1.0.0] - Initial Release

### Features
- Multi-sheet Excel file support
- 8-layer email extraction system
- Multi-language contact page detection
- Smart email validation and filtering
- Real-time progress tracking
- GUI with live statistics
