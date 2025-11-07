#!/usr/bin/env python3
"""
Main script for ID Card OCR processing
Extracts information from ID card images using Tencent Cloud API
and outputs results to CSV file
"""

import os
import sys
import csv
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tencentcloud_idcard_ocr import idcard_ocr

# Setup logging
# Ensure .archive/logs directory exists
log_dir = Path(__file__).parent / ".archive" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "ocr_processing.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter to ensure we don't exceed API rate limits"""
    
    def __init__(self, max_requests_per_second=20):
        self.max_requests = max_requests_per_second
        self.requests = []
        
    def wait_if_needed(self):
        """Wait if necessary to stay within rate limits"""
        now = time.time()
        
        # Remove requests older than 1 second
        self.requests = [req_time for req_time in self.requests if now - req_time < 1.0]
        
        # If we've hit the limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = 1.0 - (now - self.requests[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                # Clear old requests after waiting
                now = time.time()
                self.requests = [req_time for req_time in self.requests if now - req_time < 1.0]
        
        # Record this request
        self.requests.append(time.time())


def extract_person_name_from_filename(filename):
    """Extract person name from filename (remove _front/_back and .png)"""
    name = filename.replace('_front.png', '').replace('_back.png', '')
    name = name.replace('.png', '')
    return name


def process_id_cards(input_dir, output_csv, summary_file, rate_limit=20):
    """
    Process all ID card images in the input directory
    
    Args:
        input_dir: Directory containing the front and back images
        output_csv: Path to output CSV file
        summary_file: Path to summary report file
        rate_limit: Maximum API requests per second (default: 20)
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    # Get all image files
    all_images = list(input_path.glob("*.png"))
    
    if not all_images:
        logger.warning(f"No PNG images found in {input_dir}")
        return
    
    # Group images by person (front and back pairs)
    person_images = {}
    for img in all_images:
        person_name = extract_person_name_from_filename(img.name)
        
        if person_name not in person_images:
            person_images[person_name] = {'front': None, 'back': None}
        
        if '_front.png' in img.name:
            person_images[person_name]['front'] = img
        elif '_back.png' in img.name:
            person_images[person_name]['back'] = img
    
    logger.info(f"Found {len(person_images)} persons with ID card images")
    logger.info(f"Starting OCR processing with rate limit: {rate_limit} requests/second")
    
    # Initialize rate limiter
    limiter = RateLimiter(max_requests_per_second=rate_limit)
    
    # Prepare results
    results = []
    success_count = 0
    error_count = 0
    
    # Track detailed statistics
    stats = {
        'total_persons': 0,
        'both_sides_success': 0,
        'front_only_success': 0,
        'back_only_success': 0,
        'both_sides_failed': 0,
        'front_missing': 0,
        'back_missing': 0,
        'api_errors': [],
        'exceptions': []
    }
    
    # Process each person
    for idx, (person_name, images) in enumerate(person_images.items(), 1):
        logger.info(f"\n[{idx}/{len(person_images)}] Processing: {person_name}")
        
        result = {
            'person_name': person_name,
            'front_image': images['front'].name if images['front'] else 'N/A',
            'back_image': images['back'].name if images['back'] else 'N/A',
            # Front side fields
            'name': '',
            'gender': '',
            'nation': '',
            'birth': '',
            'address': '',
            'id_num': '',
            # Back side fields
            'authority': '',
            'valid_date': '',
            # Status fields
            'front_status': '',
            'back_status': '',
            'front_error': '',
            'back_error': '',
            'overall_status': ''  # New field for overall status
        }
        
        stats['total_persons'] += 1
        
        # Process front image
        if images['front']:
            try:
                limiter.wait_if_needed()
                logger.info(f"  Processing front image: {images['front'].name}")
                
                response = idcard_ocr(str(images['front']), card_side='FRONT')
                
                if 'Response' in response:
                    resp_data = response['Response']
                    
                    if 'Error' in resp_data:
                        error_code = resp_data['Error'].get('Code', 'Unknown')
                        error_msg = resp_data['Error'].get('Message', 'Unknown error')
                        logger.error(f"  API Error (Front): {error_code} - {error_msg}")
                        result['front_status'] = 'ERROR'
                        result['front_error'] = f"{error_code}: {error_msg}"
                        error_count += 1
                        stats['api_errors'].append({
                            'person': person_name,
                            'side': 'FRONT',
                            'error': f"{error_code}: {error_msg}"
                        })
                    else:
                        # Extract information from front side
                        result['name'] = resp_data.get('Name', '')
                        result['gender'] = resp_data.get('Sex', '')
                        result['nation'] = resp_data.get('Nation', '')
                        result['birth'] = resp_data.get('Birth', '')
                        result['address'] = resp_data.get('Address', '')
                        # Add apostrophe prefix to prevent Excel from treating as number
                        id_num = resp_data.get('IdNum', '')
                        result['id_num'] = f"'{id_num}" if id_num else ''
                        result['front_status'] = 'SUCCESS'
                        
                        logger.info(f"  ✓ Front side processed - Name: {result['name']}, ID: {result['id_num']}")
                        success_count += 1
                        
            except Exception as e:
                logger.error(f"  Exception processing front image: {str(e)}")
                result['front_status'] = 'EXCEPTION'
                result['front_error'] = str(e)
                error_count += 1
                stats['exceptions'].append({
                    'person': person_name,
                    'side': 'FRONT',
                    'error': str(e)
                })
        else:
            logger.warning(f"  No front image found for {person_name}")
            result['front_status'] = 'MISSING'
            stats['front_missing'] += 1
        
        # Process back image
        if images['back']:
            try:
                limiter.wait_if_needed()
                logger.info(f"  Processing back image: {images['back'].name}")
                
                response = idcard_ocr(str(images['back']), card_side='BACK')
                
                if 'Response' in response:
                    resp_data = response['Response']
                    
                    if 'Error' in resp_data:
                        error_code = resp_data['Error'].get('Code', 'Unknown')
                        error_msg = resp_data['Error'].get('Message', 'Unknown error')
                        logger.error(f"  API Error (Back): {error_code} - {error_msg}")
                        result['back_status'] = 'ERROR'
                        result['back_error'] = f"{error_code}: {error_msg}"
                        error_count += 1
                        stats['api_errors'].append({
                            'person': person_name,
                            'side': 'BACK',
                            'error': f"{error_code}: {error_msg}"
                        })
                    else:
                        # Extract information from back side
                        result['authority'] = resp_data.get('Authority', '')
                        result['valid_date'] = resp_data.get('ValidDate', '')
                        result['back_status'] = 'SUCCESS'
                        
                        logger.info(f"  ✓ Back side processed - Authority: {result['authority']}, Valid Date: {result['valid_date']}")
                        success_count += 1
                        
            except Exception as e:
                logger.error(f"  Exception processing back image: {str(e)}")
                result['back_status'] = 'EXCEPTION'
                result['back_error'] = str(e)
                error_count += 1
                stats['exceptions'].append({
                    'person': person_name,
                    'side': 'BACK',
                    'error': str(e)
                })
        else:
            logger.warning(f"  No back image found for {person_name}")
            result['back_status'] = 'MISSING'
            stats['back_missing'] += 1
        
        # Determine overall status
        front_ok = result['front_status'] == 'SUCCESS'
        back_ok = result['back_status'] == 'SUCCESS'
        
        if front_ok and back_ok:
            result['overall_status'] = '✓ 成功 (SUCCESS)'
            stats['both_sides_success'] += 1
        elif front_ok:
            result['overall_status'] = '⚠ 仅正面成功 (Front Only)'
            stats['front_only_success'] += 1
        elif back_ok:
            result['overall_status'] = '⚠ 仅背面成功 (Back Only)'
            stats['back_only_success'] += 1
        else:
            result['overall_status'] = '✗ 失败 (FAILED)'
            stats['both_sides_failed'] += 1
        
        results.append(result)
    
    # Write results to CSV
    logger.info(f"\nWriting results to CSV: {output_csv}")
    
    csv_columns = [
        'overall_status', 'person_name', 'front_image', 'back_image',
        'name', 'gender', 'nation', 'birth', 'address', 'id_num',
        'authority', 'valid_date',
        'front_status', 'back_status', 'front_error', 'back_error'
    ]
    
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"✓ CSV file created successfully: {output_csv}")
        
    except Exception as e:
        logger.error(f"Error writing CSV file: {str(e)}")
    
    # Generate summary report
    logger.info(f"\nGenerating summary report: {summary_file}")
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ID CARD OCR PROCESSING SUMMARY\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Overall Statistics
            f.write("【总体统计 / OVERALL STATISTICS】\n")
            f.write("-" * 80 + "\n")
            f.write(f"总处理人数 (Total Persons):              {stats['total_persons']}\n")
            f.write(f"API调用总数 (Total API Calls):           {success_count + error_count}\n")
            f.write(f"成功调用数 (Successful Calls):           {success_count}\n")
            f.write(f"失败调用数 (Failed Calls):               {error_count}\n")
            f.write(f"成功率 (Success Rate):                   {(success_count/(success_count+error_count)*100) if (success_count+error_count) > 0 else 0:.1f}%\n")
            f.write("\n")
            
            # Detailed Results
            f.write("【详细结果 / DETAILED RESULTS】\n")
            f.write("-" * 80 + "\n")
            f.write(f"✓ 正反面均成功 (Both Sides Success):      {stats['both_sides_success']} ({stats['both_sides_success']/stats['total_persons']*100:.1f}%)\n")
            f.write(f"⚠ 仅正面成功 (Front Only):                {stats['front_only_success']} ({stats['front_only_success']/stats['total_persons']*100:.1f}%)\n")
            f.write(f"⚠ 仅背面成功 (Back Only):                 {stats['back_only_success']} ({stats['back_only_success']/stats['total_persons']*100:.1f}%)\n")
            f.write(f"✗ 正反面均失败 (Both Sides Failed):       {stats['both_sides_failed']} ({stats['both_sides_failed']/stats['total_persons']*100:.1f}%)\n")
            f.write("\n")
            
            # Missing Images
            f.write("【缺失图像 / MISSING IMAGES】\n")
            f.write("-" * 80 + "\n")
            f.write(f"缺失正面 (Missing Front):                 {stats['front_missing']}\n")
            f.write(f"缺失背面 (Missing Back):                  {stats['back_missing']}\n")
            f.write("\n")
            
            # Failed Items - List all failures
            failed_items = [r for r in results if r['overall_status'] == '✗ 失败 (FAILED)']
            if failed_items:
                f.write("【失败项目列表 / FAILED ITEMS】\n")
                f.write("-" * 80 + "\n")
                f.write(f"共 {len(failed_items)} 个失败项目:\n\n")
                
                for idx, item in enumerate(failed_items, 1):
                    f.write(f"{idx}. {item['person_name']}\n")
                    f.write(f"   正面状态 (Front): {item['front_status']}")
                    if item['front_error']:
                        f.write(f" - {item['front_error']}")
                    f.write("\n")
                    f.write(f"   背面状态 (Back):  {item['back_status']}")
                    if item['back_error']:
                        f.write(f" - {item['back_error']}")
                    f.write("\n\n")
            else:
                f.write("【失败项目列表 / FAILED ITEMS】\n")
                f.write("-" * 80 + "\n")
                f.write("无失败项目 (No failed items)\n\n")
            
            # Partial Success Items
            partial_items = [r for r in results if '仅' in r['overall_status']]
            if partial_items:
                f.write("【部分成功项目 / PARTIAL SUCCESS ITEMS】\n")
                f.write("-" * 80 + "\n")
                f.write(f"共 {len(partial_items)} 个部分成功项目:\n\n")
                
                for idx, item in enumerate(partial_items, 1):
                    f.write(f"{idx}. {item['person_name']} - {item['overall_status']}\n")
                    f.write(f"   正面: {item['front_status']}")
                    if item['front_error']:
                        f.write(f" ({item['front_error']})")
                    f.write("\n")
                    f.write(f"   背面: {item['back_status']}")
                    if item['back_error']:
                        f.write(f" ({item['back_error']})")
                    f.write("\n\n")
            
            # API Errors
            if stats['api_errors']:
                f.write("【API错误详情 / API ERRORS】\n")
                f.write("-" * 80 + "\n")
                for idx, err in enumerate(stats['api_errors'], 1):
                    f.write(f"{idx}. {err['person']} [{err['side']}]: {err['error']}\n")
                f.write("\n")
            
            # Exceptions
            if stats['exceptions']:
                f.write("【程序异常 / EXCEPTIONS】\n")
                f.write("-" * 80 + "\n")
                for idx, exc in enumerate(stats['exceptions'], 1):
                    f.write(f"{idx}. {exc['person']} [{exc['side']}]: {exc['error']}\n")
                f.write("\n")
            
            # Output Files
            f.write("【输出文件 / OUTPUT FILES】\n")
            f.write("-" * 80 + "\n")
            f.write(f"详细结果 (Detailed Results): {output_csv}\n")
            f.write(f"处理日志 (Processing Log):   ocr_processing.log\n")
            f.write(f"本摘要 (This Summary):        {summary_file}\n")
            f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("处理完成 (Processing Completed)\n")
            f.write("="*80 + "\n")
        
        logger.info(f"✓ Summary report created: {summary_file}")
        
    except Exception as e:
        logger.error(f"Error writing summary file: {str(e)}")
    
    # Print summary to console
    logger.info("\n" + "="*60)
    logger.info("处理摘要 / PROCESSING SUMMARY")
    logger.info("="*60)
    logger.info(f"总处理人数:        {stats['total_persons']}")
    logger.info(f"正反面均成功:      {stats['both_sides_success']}")
    logger.info(f"仅正面成功:        {stats['front_only_success']}")
    logger.info(f"仅背面成功:        {stats['back_only_success']}")
    logger.info(f"完全失败:          {stats['both_sides_failed']}")
    logger.info(f"API调用成功:       {success_count}")
    logger.info(f"API调用失败:       {error_count}")
    logger.info("-"*60)
    logger.info(f"结果已保存至:      {output_csv}")
    logger.info(f"摘要已保存至:      {summary_file}")
    logger.info("="*60)


def main():
    """Main entry point"""
    # Load environment variables from .env file
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")
    else:
        logger.warning(f".env file not found at {env_file}")
    
    # Check for required environment variables
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")
    
    if not secret_id or not secret_key:
        logger.error("ERROR: Tencent Cloud credentials not found!")
        logger.error("Please set TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY in .env file")
        logger.error("Example .env file:")
        logger.error("  TENCENTCLOUD_SECRET_ID=your_secret_id_here")
        logger.error("  TENCENTCLOUD_SECRET_KEY=your_secret_key_here")
        sys.exit(1)
    
    logger.info("✓ Tencent Cloud credentials found")
    
    # Configuration
    INPUT_DIR = Path(__file__).parent / "outputs"
    ARCHIVE_DIR = Path(__file__).parent / ".archive"
    OUTPUT_CSV = ARCHIVE_DIR / "results" / "id_card_results.csv"
    SUMMARY_FILE = ARCHIVE_DIR / "results" / "processing_summary.txt"
    RATE_LIMIT = 20  # requests per second
    
    # Ensure archive directories exist
    (ARCHIVE_DIR / "results").mkdir(parents=True, exist_ok=True)
    (ARCHIVE_DIR / "logs").mkdir(parents=True, exist_ok=True)
    (ARCHIVE_DIR / "temp_files").mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "="*60)
    logger.info("ID CARD OCR PROCESSING")
    logger.info("="*60)
    logger.info(f"Input directory: {INPUT_DIR}")
    logger.info(f"Output CSV: {OUTPUT_CSV}")
    logger.info(f"Summary file: {SUMMARY_FILE}")
    logger.info(f"Rate limit: {RATE_LIMIT} requests/second")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # Process ID cards
    process_id_cards(INPUT_DIR, OUTPUT_CSV, SUMMARY_FILE, rate_limit=RATE_LIMIT)
    
    logger.info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Processing completed!")


if __name__ == "__main__":
    main()
