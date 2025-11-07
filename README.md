# ID Card OCR

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

A Python project for extracting information from Chinese ID card PDFs using Tencent Cloud OCR API.

> **Note**: This project processes sensitive personal information. Ensure you have proper authorization and comply with data protection regulations (GDPR, CCPA, etc.) when using this tool.

## Features

- Extract front and back images from ID card PDFs (supports 1-page and 2-page formats)
- Automatic detection of ID card front/back sides
- OCR processing using Tencent Cloud API
- **Automatic image compression** if base64 encoded size > 10MB
- Rate limiting (20 requests/second) to respect API limits
- Export results to CSV file
- Comprehensive logging

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Format](#output-format)
- [Project Structure](#project-structure)
- [Git Workflow](#git-workflow)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- Python 3.12 or higher
- Tencent Cloud account with OCR API access
- API credentials (Secret ID and Secret Key)

> **Security Note**: Never commit your `.env` file or share your API credentials publicly.

## Installation

1. Clone the repository:
```bash
cd IDCardOCR
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install python-dotenv pillow
```

## Configuration

1. Create a `.env` file in the project root:
```bash
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
```

2. Get your credentials from [Tencent Cloud Console](https://console.cloud.tencent.com/cam/capi)

## Usage

### Step 1: Extract Images from PDFs

Place your ID card PDF files in the `inputs/` directory, then run:

```bash
python src/extract_id_cards.py
```

This will extract front and back images to the `outputs/` directory.

### Step 2: Run OCR Processing

Process all extracted images and generate CSV results:

```bash
python main.py
```

The script will:
- Load credentials from `.env` file
- Process all images in `outputs/` directory
- Respect the 20 requests/second rate limit
- Generate `id_card_results.csv` with all extracted information (Chinese characters fully supported)
- Create `processing_summary.txt` with operation summary and failed items list
- Create `ocr_processing.log` with detailed processing logs

## Output Format

### CSV File (id_card_results.csv)

The CSV file contains the following columns (UTF-8 with BOM for Excel compatibility):

| Column | Description |
|--------|-------------|
| overall_status | Overall status: ✓ 成功/⚠ 仅正面成功/⚠ 仅背面成功/✗ 失败 |
| person_name | Name extracted from filename |
| front_image | Front image filename |
| back_image | Back image filename |
| name | Name (from ID card) |
| gender | Gender |
| nation | Nation/Ethnicity |
| birth | Birth date |
| address | Address |
| id_num | ID card number |
| authority | Issuing authority |
| valid_date | Validity period |
| front_status | Processing status for front side |
| back_status | Processing status for back side |
| front_error | Error message (if any) for front side |
| back_error | Error message (if any) for back side |

### Summary Report (processing_summary.txt)

A comprehensive text report containing:
- **总体统计**: Total persons, API calls, success rate
- **详细结果**: Success breakdown (both sides, front only, back only, failed)
- **缺失图像**: Missing front/back images count
- **失败项目列表**: Complete list of all failed items with error details
- **部分成功项目**: Items with only one side processed successfully
- **API错误详情**: All API errors encountered
- **程序异常**: All exceptions that occurred

This file is fully compatible with Chinese characters and can be viewed in any text editor.

## Project Structure

```
IDCardOCR/
├── .archive/            # Generated files, logs, results (excluded from git)
├── docs/                # Documentation files
├── example/             # Example PDF files
├── inputs/              # Place PDF files here
├── outputs/             # Extracted images (PNG)
├── manual_review/       # Files for manual review
├── src/
│   ├── extract_id_cards.py        # PDF to image extraction
│   ├── tencentcloud_idcard_ocr.py # Tencent Cloud API client
│   └── utils/           # Utility scripts
├── main.py              # Main OCR processing script
├── README.md            # This file
├── PROJECT_STRUCTURE.md # Detailed project structure
└── .env                 # API credentials (create this)
```

See `PROJECT_STRUCTURE.md` for complete directory structure and file descriptions.

## Rate Limiting

The script automatically handles rate limiting to stay within the Tencent Cloud API limit of 20 requests per second. For 220 persons (440 images), the processing will take approximately:
- 440 requests ÷ 20 requests/second = 22 seconds minimum

## Error Handling

- API errors are logged and included in the CSV output
- Network exceptions are caught and logged
- Missing images are marked as 'MISSING' in status columns
- Processing continues even if individual images fail

## Output Files

Three files are created in `.archive/` after processing:
1. **`.archive/results/id_card_results.csv`** - Detailed results for all persons (UTF-8 with BOM)
2. **`.archive/results/processing_summary.txt`** - Summary report with statistics and failed items (UTF-8)
3. **`.archive/logs/ocr_processing.log`** - Detailed processing log with timestamps

Additionally, from the extraction step:
- **`.archive/logs/id_extraction.log`** - PDF to image extraction logs

## Additional Resources

- **`PROJECT_STRUCTURE.md`** - Complete project structure and file descriptions
- **`docs/QUICK_REFERENCE.md`** - Quick reference guide
- **`docs/USAGE_GUIDE.md`** - Detailed usage instructions
- **`docs/EXCEL_ID_NUMBER_FIX.md`** - Excel formatting details
- **`docs/IMAGE_COMPRESSION_FEATURE.md`** - Image compression documentation

## Troubleshooting

### "Tencent Cloud credentials not found"
Make sure your `.env` file exists and contains valid credentials.

### Rate limit errors
The script includes automatic rate limiting, but if you still encounter rate limit errors, you can adjust the `RATE_LIMIT` variable in `main.py`.

### Image quality issues
If OCR results are poor, check the quality of extracted images in the `outputs/` directory. You may need to adjust the DPI settings in `extract_id_cards.py`.

### Large image files (> 10MB base64 encoded)
The script automatically compresses images that exceed 10MB when base64 encoded. You'll see compression messages in the log. This ensures all images can be processed by the API.

### ID numbers showing scientific notation in Excel
The script automatically adds an apostrophe prefix before ID numbers to prevent Excel from converting them to scientific notation. The apostrophe is hidden in Excel cells but visible in the formula bar. Numbers display correctly with all 18 digits preserved. See `EXCEL_ID_NUMBER_FIX.md` for details.

## Git Workflow

### What's Tracked
- ✅ Source code and scripts
- ✅ Documentation
- ✅ Configuration files
- ✅ Directory structure (via `.gitkeep` files)

### What's Excluded
- ❌ Input PDF files (`inputs/*`)
- ❌ Extracted images (`outputs/*`)
- ❌ Generated results (`.archive/*`)
- ❌ API credentials (`.env`)
- ❌ Manual review files (`manual_review/*`)

This ensures sensitive ID card data is never committed to git while preserving the project structure.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is provided for legitimate use cases only. Users are responsible for:
- Obtaining proper authorization before processing any personal data
- Complying with applicable data protection laws (GDPR, CCPA, etc.)
- Ensuring secure handling and storage of sensitive information
- Respecting privacy rights of individuals

The authors and contributors are not responsible for misuse of this software.

## Acknowledgments

- [Tencent Cloud OCR API](https://cloud.tencent.com/product/ocr) for OCR capabilities
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- [Pillow](https://python-pillow.org/) for image processing
- All contributors who help improve this project

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/IDCardOCR/issues)
- 💬 [Discussions](https://github.com/yourusername/IDCardOCR/discussions)

## Star History

If you find this project useful, please consider giving it a ⭐!

