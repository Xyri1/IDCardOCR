# ID Card OCR - Usage Guide

## Quick Start

### 1. Setup Environment

Create a `.env` file in the project root with your Tencent Cloud credentials:

```env
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
```

**Get your credentials:**
1. Visit [Tencent Cloud Console](https://console.cloud.tencent.com/cam/capi)
2. Create or copy your Secret ID and Secret Key
3. Paste them into the `.env` file

### 2. Install Dependencies

```bash
uv sync
# or if using pip:
pip install python-dotenv
```

### 3. Run the Script

```bash
uv run python main.py
# or:
python main.py
```

## What the Script Does

1. **Loads Environment Variables**: Reads your API credentials from `.env`
2. **Scans Output Directory**: Finds all ID card images in `outputs/` directory
3. **Groups Images**: Pairs front and back images for each person
4. **Processes with OCR**: Calls Tencent Cloud API with rate limiting (20 req/sec)
5. **Extracts Information**:
   - **Front**: Name, Gender, Nation, Birth Date, Address, ID Number
   - **Back**: Issuing Authority, Validity Period
6. **Generates Three Output Files**:
   - `id_card_results.csv` - Detailed results (UTF-8 with BOM for Excel)
   - `processing_summary.txt` - Summary with failed items list (UTF-8)
   - `ocr_processing.log` - Detailed processing log
7. **Tracks Status**: Marks each item as successful, partially successful, or failed

## Expected Processing Time

With 220 persons (440 images total):
- API calls needed: 440
- Rate limit: 20 requests/second
- **Minimum time: ~22 seconds**
- Actual time may be slightly longer due to network latency

## Output Files

### 1. id_card_results.csv

Detailed CSV file with all extracted information (UTF-8 with BOM encoding for Excel compatibility):

**Columns:**
```
overall_status,person_name,front_image,back_image,name,gender,nation,birth,address,id_num,authority,valid_date,front_status,back_status,front_error,back_error
```

**Example rows:**
```csv
✓ 成功 (SUCCESS),张三身份证,张三身份证_front.png,张三身份证_back.png,张三,男,汉,1990/01/01,北京市朝阳区...,110101199001011234,朝阳分局,2020.01.01-2030.01.01,SUCCESS,SUCCESS,,
⚠ 仅正面成功 (Front Only),李四身份证,李四身份证_front.png,李四身份证_back.png,李四,女,汉,1985/05/15,上海市浦东...,310115198505151234,,ERROR,SUCCESS,InvalidParameter: Low quality,
✗ 失败 (FAILED),王五身份证,王五身份证_front.png,王五身份证_back.png,,,,,,,,ERROR,ERROR,InvalidParameter: ...,RequestLimitExceeded: ...
```

**Overall Status Values:**
- ✓ 成功 (SUCCESS) - Both front and back processed successfully
- ⚠ 仅正面成功 (Front Only) - Only front side succeeded
- ⚠ 仅背面成功 (Back Only) - Only back side succeeded  
- ✗ 失败 (FAILED) - Both sides failed

### 2. processing_summary.txt

Comprehensive summary report in Chinese and English (UTF-8 encoding):

**Contains:**
- **总体统计 (Overall Statistics)**: Total persons, API calls, success rate
- **详细结果 (Detailed Results)**: Breakdown by success type with percentages
- **缺失图像 (Missing Images)**: Count of missing front/back images
- **失败项目列表 (Failed Items)**: Complete list with error details
- **部分成功项目 (Partial Success)**: Items with only one side processed
- **API错误详情 (API Errors)**: All API errors encountered
- **程序异常 (Exceptions)**: Any program exceptions
- **输出文件 (Output Files)**: List of generated files

**Example format:**
```
================================================================================
ID CARD OCR PROCESSING SUMMARY
Generated: 2025-11-07 14:30:25
================================================================================

【总体统计 / OVERALL STATISTICS】
--------------------------------------------------------------------------------
总处理人数 (Total Persons):              220
API调用总数 (Total API Calls):           440
成功调用数 (Successful Calls):           435
失败调用数 (Failed Calls):               5
成功率 (Success Rate):                   98.9%

【失败项目列表 / FAILED ITEMS】
--------------------------------------------------------------------------------
共 2 个失败项目:

1. 张三身份证
   正面状态 (Front): ERROR - InvalidParameter: Low quality
   背面状态 (Back):  ERROR - InvalidParameter: Low quality
...
```

### 3. ocr_processing.log

Detailed processing log with timestamps:
- Which files are being processed
- Extracted information from each API call
- Real-time error messages
- Progress indicators
- Final summary statistics

## Status Codes

### Overall Status (overall_status column)

| Status | Meaning | Description |
|--------|---------|-------------|
| ✓ 成功 (SUCCESS) | Complete success | Both front and back processed successfully |
| ⚠ 仅正面成功 (Front Only) | Partial success | Only front side succeeded |
| ⚠ 仅背面成功 (Back Only) | Partial success | Only back side succeeded |
| ✗ 失败 (FAILED) | Complete failure | Both sides failed or missing |

### Individual Side Status (front_status/back_status columns)

| Status | Meaning |
|--------|---------|
| SUCCESS | OCR completed successfully |
| ERROR | API returned an error (see error column) |
| EXCEPTION | Python exception occurred |
| MISSING | Image file not found |

## Common Issues

### "Tencent Cloud credentials not found"

**Solution**: Make sure `.env` file exists in project root with valid credentials.

```bash
# Check if .env exists
ls -la .env

# If not, create it:
echo "TENCENTCLOUD_SECRET_ID=your_id" > .env
echo "TENCENTCLOUD_SECRET_KEY=your_key" >> .env
```

### "No PNG images found"

**Solution**: Run the extraction script first to convert PDFs to images:

```bash
python src/extract_id_cards.py
```

### Rate Limit Errors

The script includes automatic rate limiting, but if you encounter errors:

1. Check your API quota in Tencent Cloud Console
2. Adjust rate limit in `main.py`:
   ```python
   RATE_LIMIT = 10  # Reduce from 20 to 10 requests/second
   ```

### Poor OCR Quality

If extracted text is inaccurate:

1. Check image quality in `outputs/` directory
2. Ensure images are clear and properly oriented
3. Adjust DPI settings in `extract_id_cards.py` (default: 300 DPI)

### ID Numbers Show Scientific Notation in Excel

**Issue**: When opening CSV in Excel, ID numbers appear as `4.41625E+17`

**Solution**: ✅ **Already Fixed Automatically**
- The script now adds an apostrophe prefix to ID numbers
- Apostrophe is hidden in Excel cells (visible only in formula bar)
- Numbers display correctly when opened in Excel
- All 18 digits are preserved
- See `EXCEL_ID_NUMBER_FIX.md` for details

## Advanced Configuration

You can modify `main.py` to customize:

### Change Input/Output Directories

```python
# Around line 277
INPUT_DIR = Path(__file__).parent / "my_custom_outputs"
OUTPUT_CSV = Path(__file__).parent / "my_results.csv"
```

### Adjust Rate Limit

```python
# Around line 279
RATE_LIMIT = 15  # requests per second
```

### Change Log Level

```python
# Around line 23
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more verbose logs
    # ...
)
```

## Workflow Example

Complete workflow from PDFs to CSV:

```bash
# Step 1: Place PDFs in inputs/ directory
cp /path/to/pdfs/*.pdf inputs/

# Step 2: Extract images from PDFs
python src/extract_id_cards.py
# Output: Creates PNG files in outputs/

# Step 3: Run OCR processing
python main.py
# Output: Creates id_card_results.csv

# Step 4: Review results
# Open id_card_results.csv in Excel (Chinese characters will display correctly)
# Read processing_summary.txt for overview and failed items list
# Check ocr_processing.log for detailed processing information
```

## Cost Estimation

Tencent Cloud OCR pricing (as of 2024):
- Free tier: 1,000 calls/month
- After free tier: ¥0.15 per call

For 440 images:
- If within free tier: ¥0
- If exceeding free tier: 440 × ¥0.15 = ¥66

**Note**: Check current pricing at [Tencent Cloud OCR Pricing](https://cloud.tencent.com/product/ocr/pricing)

## Troubleshooting Checklist

- [ ] `.env` file exists with valid credentials
- [ ] `outputs/` directory contains PNG images
- [ ] Images are named with `_front.png` and `_back.png` suffixes
- [ ] Python 3.12+ is installed
- [ ] Dependencies are installed (`uv sync`)
- [ ] Network connection is stable
- [ ] Tencent Cloud account has sufficient quota

## Support

For issues or questions:
1. Check `ocr_processing.log` for detailed error messages
2. Verify your API credentials
3. Test with a single pair of images first
4. Check Tencent Cloud console for API status

## API Reference

Tencent Cloud ID Card OCR API documentation:
- [API Documentation](https://cloud.tencent.com/document/product/866/33524)
- [Error Codes](https://cloud.tencent.com/document/product/866/33528)

