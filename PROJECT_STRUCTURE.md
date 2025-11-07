# Project Structure

```
IDCardOCR/
├── .archive/                    # Generated files (excluded from git)
│   ├── results/                 # Processing results
│   │   ├── id_card_results.csv
│   │   ├── processing_summary.txt
│   │   └── ...
│   ├── logs/                    # Log files
│   │   ├── id_extraction.log
│   │   └── ocr_processing.log
│   └── temp_files/              # Temporary files
│       ├── failed_files.txt
│       └── skipped_files.txt
│
├── docs/                        # Documentation
│   ├── BUGFIX_CONFIG_PARAMETER.md
│   ├── EXCEL_ID_NUMBER_FIX.md
│   ├── IMAGE_COMPRESSION_FEATURE.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── QUICK_REFERENCE.md
│   └── USAGE_GUIDE.md
│
├── example/                     # Example PDF files
│   ├── example1.pdf
│   └── example2.pdf
│
├── inputs/                      # Input PDF files
│   └── *.pdf                    # Place ID card PDFs here
│
├── outputs/                     # Extracted images
│   └── *.png                    # Front and back images
│
├── manual_review/               # Files requiring manual review
│
├── src/                         # Source code
│   ├── extract_id_cards.py      # PDF to image extraction
│   ├── tencentcloud_idcard_ocr.py  # Tencent Cloud API client
│   └── utils/                   # Utility scripts
│       ├── fix_id_numbers.py    # Fix ID numbers in CSV
│       ├── compare_inputs_outputs.py  # Compare inputs/outputs
│       ├── convert_skipped_files.py   # Process skipped files
│       └── parse_log.py         # Parse log files
│
├── main.py                      # Main OCR processing script
├── README.md                    # Main documentation
├── PROJECT_STRUCTURE.md         # This file
├── pyproject.toml               # Python project configuration
├── uv.lock                      # Dependency lock file
├── .env                         # API credentials (create this, excluded from git)
├── .gitignore                   # Git ignore rules
└── .python-version              # Python version specification
```

## Key Files

### Main Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `main.py` | Main OCR processing | `python main.py` |
| `src/extract_id_cards.py` | Extract images from PDFs | `python src/extract_id_cards.py` |

### Core Modules

| File | Purpose |
|------|---------|
| `src/tencentcloud_idcard_ocr.py` | Tencent Cloud API client with auto-compression |

### Utility Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `src/utils/fix_id_numbers.py` | Fix ID number format in CSV | `python src/utils/fix_id_numbers.py` |
| `src/utils/compare_inputs_outputs.py` | Compare input PDFs with output images | `python src/utils/compare_inputs_outputs.py` |
| `src/utils/convert_skipped_files.py` | Process previously skipped files | `python src/utils/convert_skipped_files.py` |
| `src/utils/parse_log.py` | Parse and analyze log files | `python src/utils/parse_log.py` |

## Directories

### Input/Output

- **`inputs/`** - Place your ID card PDF files here
- **`outputs/`** - Extracted front and back images (PNG format)
- **`manual_review/`** - Files that need manual review

### Generated Content

- **`.archive/`** - All generated files, logs, and results
  - Excluded from version control
  - Can be safely deleted (will be regenerated)

### Documentation

- **`docs/`** - All technical documentation
- **`example/`** - Example files for testing

## Workflow

### 1. Setup
```bash
# Install dependencies
uv sync

# Create .env file with credentials
echo "TENCENTCLOUD_SECRET_ID=your_id" > .env
echo "TENCENTCLOUD_SECRET_KEY=your_key" >> .env
```

### 2. Extract Images
```bash
# Extract images from PDFs
python src/extract_id_cards.py
```

### 3. Run OCR
```bash
# Process all images with OCR
python main.py
```

### 4. Review Results
- Check `.archive/results/id_card_results.csv` for detailed data
- Review `.archive/results/processing_summary.txt` for overview
- Check `.archive/logs/` for processing details

## Git Workflow

### Tracked Files
- Source code (`main.py`, `src/`)
- Documentation (`README.md`, `docs/`)
- Configuration (`pyproject.toml`, `.gitignore`)
- Examples (`example/`)
- Empty directory markers (`inputs/.gitkeep`, `outputs/.gitkeep`, `manual_review/.gitkeep`)

### Excluded Files (in `.gitignore`)
- `.archive/` - All generated content
- `.env` - API credentials
- `inputs/*` - Input PDF files (directory structure preserved)
- `outputs/*` - Extracted images (directory structure preserved)
- `manual_review/*` - Manual review files (directory structure preserved)
- `__pycache__/` - Python cache
- `.venv/` - Virtual environment

## Maintenance

### Clean Up Generated Files
```bash
# Remove all generated files
rm -rf .archive/*

# Or on Windows
rmdir /s /q .archive
mkdir .archive
```

### Update Dependencies
```bash
uv sync
```

### Check Project Status
```bash
git status
```

## Notes

- All output files are automatically saved to `.archive/`
- Utility scripts are in `src/utils/` for organization
- Documentation is centralized in `docs/`
- Test scripts have been removed (no longer needed)

## Quick Access

- **Main README**: `README.md`
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Usage Guide**: `docs/USAGE_GUIDE.md`
- **Bug Fixes**: `docs/BUGFIX_*.md`
- **Features**: `docs/*_FEATURE.md`

---

**Last Updated**: November 7, 2025

