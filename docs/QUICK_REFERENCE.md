# Quick Reference Guide

## Setup (One-Time)

```bash
# 1. Create .env file
echo "TENCENTCLOUD_SECRET_ID=your_secret_id" > .env
echo "TENCENTCLOUD_SECRET_KEY=your_secret_key" >> .env

# 2. Install dependencies
uv sync
```

## Running the Script

```bash
# Process all images in outputs/ directory
python main.py
```

## Output Files

| File | Description | Encoding |
|------|-------------|----------|
| `id_card_results.csv` | Detailed results for all persons | UTF-8 BOM |
| `processing_summary.txt` | Summary with statistics and failed items | UTF-8 |
| `ocr_processing.log` | Detailed processing log | UTF-8 |

## Status Codes

### Overall Status
- ✓ 成功 (SUCCESS) - Both sides OK
- ⚠ 仅正面成功 (Front Only) - Only front succeeded
- ⚠ 仅背面成功 (Back Only) - Only back succeeded
- ✗ 失败 (FAILED) - Both sides failed

### Individual Status
- SUCCESS - API call successful
- ERROR - API error (see error column)
- EXCEPTION - Python exception
- MISSING - File not found

## Key Features

✅ **Automatic Image Compression**
- Triggers if base64 size > 10MB
- Reduces quality progressively
- Resizes if needed
- Ensures API compatibility

✅ **Rate Limiting**
- 20 requests/second max
- Automatic throttling
- Prevents API errors

✅ **Chinese Character Support**
- CSV: UTF-8 with BOM (Excel compatible)
- Summary: UTF-8 (all text editors)
- All names display correctly

✅ **Error Recovery**
- Continues if individual items fail
- All errors logged
- Failed items marked in summary

## Expected Performance

For 220 persons (440 images):
- **Minimum time**: ~22 seconds
- **With compression**: +2-5 seconds per large image
- **API success rate**: Typically 99%+

## Common Issues

### "Credentials not found"
→ Check `.env` file exists and has correct format

### "InvalidParameter: Config type"
→ Fixed in current version (Config now JSON string)

### Image too large
→ Automatically compressed (no action needed)

### Poor OCR accuracy
→ Check original image quality in `outputs/` folder

## File Locations

```
IDCardOCR/
├── .env                      # API credentials (create this)
├── main.py                   # Main processing script
├── outputs/                  # Input images (PNG files)
├── id_card_results.csv       # Output: detailed results
├── processing_summary.txt    # Output: summary report
└── ocr_processing.log        # Output: processing log
```

## Compression Messages

```
警告: 图片Base64编码后大小为 12.45MB，超过10MB限制
正在压缩图片...
  尝试 1: 质量=95, 大小=11.23MB
  尝试 2: 质量=85, 大小=9.87MB
✓ 压缩成功: 12.45MB -> 9.87MB
```

This is normal and automatic!

## Quick Checks

Before running:
- [ ] `.env` file exists with credentials
- [ ] `outputs/` folder has PNG images
- [ ] Images named with `_front.png` and `_back.png`

After running:
- [ ] Check `processing_summary.txt` for overview
- [ ] Open `id_card_results.csv` in Excel
- [ ] Review failed items (if any)

## Troubleshooting Commands

```bash
# Verify Python version
python --version  # Should be 3.12+

# Test imports
uv run python -c "from dotenv import load_dotenv; from PIL import Image; print('OK')"

# Check .env file
cat .env  # (Linux/Mac)
type .env  # (Windows)

# Count images
ls outputs/*.png | wc -l  # (Linux/Mac)
dir /b outputs\*.png | find /c /v ""  # (Windows)
```

## Support Files

- `README.md` - Full documentation
- `USAGE_GUIDE.md` - Detailed usage guide
- `IMAGE_COMPRESSION_FEATURE.md` - Compression details
- `BUGFIX_CONFIG_PARAMETER.md` - Config parameter fix
- `processing_summary_example.txt` - Example summary output

---

**Last Updated**: November 7, 2025

