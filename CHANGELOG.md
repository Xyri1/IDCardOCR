# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Unit tests
- Integration tests
- CI/CD pipeline
- Docker support
- Web interface
- Support for other OCR providers

## [0.1.0] - 2025-11-07

### Added
- Initial release
- PDF to image extraction for Chinese ID cards
- Support for 1-page and 2-page PDF formats
- Automatic front/back side detection
- Tencent Cloud OCR API integration
- Automatic image compression for files > 10MB
- Rate limiting (20 requests/second)
- CSV export with Chinese character support
- Apostrophe prefix for ID numbers (Excel-friendly)
- Processing summary report
- Comprehensive logging
- Project organization with `.archive/` directory
- Git-friendly file structure
- Complete documentation

### Features

#### Core Functionality
- Extract front and back images from ID card PDFs
- OCR processing using Tencent Cloud API
- Extract: Name, Gender, Nation, Birth Date, Address, ID Number, Authority, Valid Date
- Batch processing of multiple ID cards
- Automatic error recovery and retry logic

#### Image Processing
- Automatic format detection (1-page vs 2-page PDFs)
- Smart front/back detection using OCR
- Automatic image compression (JPEG, quality reduction, resizing)
- Support for RGBA, PNG with palette, and various image formats
- High-quality LANCZOS resampling

#### Data Export
- UTF-8 with BOM CSV export (Excel compatible)
- Bilingual summary reports (Chinese/English)
- Status tracking (success, failed, partial)
- Failed items list with error details
- Detailed processing logs

#### Security & Privacy
- API credentials in `.env` (not tracked by git)
- Input/output files excluded from git
- Sensitive data never committed
- GDPR/CCPA compliance considerations

#### Developer Experience
- Organized project structure
- Comprehensive documentation
- Utility scripts in `src/utils/`
- Clean git workflow
- Example files for testing

### Documentation
- README.md - Main documentation
- PROJECT_STRUCTURE.md - Project organization
- CONTRIBUTING.md - Contribution guidelines
- CODE_OF_CONDUCT.md - Community guidelines
- SECURITY.md - Security policy
- LICENSE - MIT License
- CLEANUP_SUMMARY.md - Organization changes
- GIT_IGNORE_SUMMARY.md - Git workflow details
- docs/ directory with technical documentation

### Technical Details
- Python 3.12+ required
- Dependencies: python-dotenv, Pillow, PyMuPDF
- Rate limiting: 20 requests/second (configurable)
- Image compression: Multi-stage (quality + resize)
- Encoding: UTF-8 with BOM for Excel compatibility

[unreleased]: https://github.com/yourusername/IDCardOCR/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/IDCardOCR/releases/tag/v0.1.0

