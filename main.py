#!/usr/bin/env python3
"""
Main script for ID Card OCR processing
Extracts information from ID card images using Tencent Cloud API
and outputs results to CSV file
"""

import argparse
import csv
import logging
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config
from src.constants import FileConstants, OutputConstants, StatusMessages
from src.tencentcloud_idcard_ocr import idcard_ocr


class RateLimiter:
    """Rate limiter using deque for O(1) performance"""

    def __init__(self, max_requests_per_second: int = 20):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_second: Maximum allowed requests per second
        """
        self.max_requests = max_requests_per_second
        self.requests: deque = deque()
        self.lock = None  # For thread safety

    def wait_if_needed(self) -> None:
        """Wait if necessary to stay within rate limits"""
        now = time.time()

        # Remove requests older than 1 second (O(1) per removal)
        while self.requests and now - self.requests[0] >= 1.0:
            self.requests.popleft()

        # If we've hit the limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = 1.0 - (now - self.requests[0])
            if sleep_time > 0:
                logging.debug(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                # Clear old requests after waiting
                now = time.time()
                while self.requests and now - self.requests[0] >= 1.0:
                    self.requests.popleft()

        # Record this request
        self.requests.append(now)


def setup_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / OutputConstants.OCR_LOG_FILENAME

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def extract_person_name_from_filename(filename: str) -> str:
    """
    Extract person name from filename by removing suffixes.

    Args:
        filename: Image filename

    Returns:
        Person name without _front/_back suffixes
    """
    name = filename.replace(FileConstants.FRONT_SUFFIX, '')
    name = name.replace(FileConstants.BACK_SUFFIX, '')
    name = name.replace(FileConstants.PNG_EXTENSION, '')
    return name


def group_images_by_person(image_files: List[Path]) -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Group image files by person (front/back pairs).

    Args:
        image_files: List of image file paths

    Returns:
        Dictionary mapping person names to their front/back image paths
    """
    person_images: Dict[str, Dict[str, Optional[Path]]] = {}

    for img in image_files:
        person_name = extract_person_name_from_filename(img.name)

        if person_name not in person_images:
            person_images[person_name] = {'front': None, 'back': None}

        if FileConstants.FRONT_SUFFIX in img.name:
            person_images[person_name]['front'] = img
        elif FileConstants.BACK_SUFFIX in img.name:
            person_images[person_name]['back'] = img

    return person_images


def process_card_side(
    image_path: Path,
    card_side: str,
    limiter: RateLimiter,
    person_name: str,
    config: Config
) -> Dict[str, str]:
    """
    Process one side of an ID card.

    Args:
        image_path: Path to image file
        card_side: 'FRONT' or 'BACK'
        limiter: Rate limiter instance
        person_name: Person name for logging
        config: Configuration instance

    Returns:
        Dictionary with status, data, and error information
    """
    result = {
        'status': StatusMessages.STATUS_MISSING,
        'error': '',
        'data': {}
    }

    if not image_path:
        return result

    try:
        limiter.wait_if_needed()
        logging.info(f"  Processing {card_side.lower()} image: {image_path.name}")

        # Validate path
        validated_path = config.validate_input_path(image_path)

        response = idcard_ocr(
            str(validated_path),
            card_side=card_side,
            secret_id=config.secret_id,
            secret_key=config.secret_key
        )

        if 'Response' in response:
            resp_data = response['Response']

            if 'Error' in resp_data:
                error_code = resp_data['Error'].get('Code', 'Unknown')
                error_msg = resp_data['Error'].get('Message', 'Unknown error')
                logging.error(f"  API Error ({card_side}): {error_code} - {error_msg}")

                result['status'] = StatusMessages.STATUS_ERROR
                result['error'] = f"{error_code}: {error_msg}"
            else:
                # Extract data based on card side
                if card_side == StatusMessages.CARD_SIDE_FRONT:
                    result['data'] = {
                        'name': resp_data.get('Name', ''),
                        'gender': resp_data.get('Sex', ''),
                        'nation': resp_data.get('Nation', ''),
                        'birth': resp_data.get('Birth', ''),
                        'address': resp_data.get('Address', ''),
                        'id_num': f"'{resp_data.get('IdNum', '')}" if resp_data.get('IdNum') else ''
                    }
                else:  # BACK
                    result['data'] = {
                        'authority': resp_data.get('Authority', ''),
                        'valid_date': resp_data.get('ValidDate', '')
                    }

                result['status'] = StatusMessages.STATUS_SUCCESS
                logging.info(f"  ✓ {card_side} side processed successfully")

    except Exception as e:
        logging.error(f"  Exception processing {card_side} image: {str(e)}")
        result['status'] = StatusMessages.STATUS_EXCEPTION
        result['error'] = str(e)

    return result


def process_single_person(
    person_name: str,
    images: Dict[str, Optional[Path]],
    limiter: RateLimiter,
    config: Config
) -> Dict[str, str]:
    """
    Process both sides of one person's ID card.

    Args:
        person_name: Person's name
        images: Dictionary with 'front' and 'back' image paths
        limiter: Rate limiter instance
        config: Configuration instance

    Returns:
        Dictionary with all extracted data and status
    """
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
        'overall_status': ''
    }

    # Process front image
    front_result = process_card_side(
        images['front'],
        StatusMessages.CARD_SIDE_FRONT,
        limiter,
        person_name,
        config
    )
    result['front_status'] = front_result['status']
    result['front_error'] = front_result['error']
    result.update(front_result['data'])

    # Process back image
    back_result = process_card_side(
        images['back'],
        StatusMessages.CARD_SIDE_BACK,
        limiter,
        person_name,
        config
    )
    result['back_status'] = back_result['status']
    result['back_error'] = back_result['error']
    result.update(back_result['data'])

    # Determine overall status
    front_ok = result['front_status'] == StatusMessages.STATUS_SUCCESS
    back_ok = result['back_status'] == StatusMessages.STATUS_SUCCESS

    if front_ok and back_ok:
        result['overall_status'] = StatusMessages.SUCCESS_BOTH
    elif front_ok:
        result['overall_status'] = StatusMessages.SUCCESS_FRONT_ONLY
    elif back_ok:
        result['overall_status'] = StatusMessages.SUCCESS_BACK_ONLY
    else:
        result['overall_status'] = StatusMessages.FAILED

    return result


def process_with_concurrency(
    person_images: Dict[str, Dict[str, Optional[Path]]],
    limiter: RateLimiter,
    config: Config,
    max_workers: int = 5
) -> List[Dict[str, str]]:
    """
    Process multiple persons concurrently while respecting rate limits.

    Args:
        person_images: Dictionary mapping person names to their images
        limiter: Rate limiter instance
        config: Configuration instance
        max_workers: Maximum concurrent workers

    Returns:
        List of result dictionaries
    """
    results = []

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_person = {
            executor.submit(
                process_single_person,
                person_name,
                images,
                limiter,
                config
            ): person_name
            for person_name, images in person_images.items()
        }

        # Collect results as they complete
        for idx, future in enumerate(as_completed(future_to_person), 1):
            person_name = future_to_person[future]
            try:
                result = future.result()
                results.append(result)
                logging.info(
                    f"[{idx}/{len(person_images)}] Completed: {person_name} - "
                    f"{result['overall_status']}"
                )
            except Exception as e:
                logging.error(f"Error processing {person_name}: {str(e)}")
                # Create error result
                results.append({
                    'person_name': person_name,
                    'overall_status': StatusMessages.FAILED,
                    'front_status': StatusMessages.STATUS_EXCEPTION,
                    'back_status': StatusMessages.STATUS_EXCEPTION,
                    'front_error': str(e),
                    'back_error': str(e),
                })

    return results


def calculate_statistics(results: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Calculate processing statistics from results.

    Args:
        results: List of result dictionaries

    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_persons': len(results),
        'both_sides_success': 0,
        'front_only_success': 0,
        'back_only_success': 0,
        'both_sides_failed': 0,
        'front_missing': 0,
        'back_missing': 0,
        'total_api_calls': 0,
        'successful_calls': 0,
        'failed_calls': 0,
    }

    for result in results:
        overall = result['overall_status']
        if overall == StatusMessages.SUCCESS_BOTH:
            stats['both_sides_success'] += 1
        elif overall == StatusMessages.SUCCESS_FRONT_ONLY:
            stats['front_only_success'] += 1
        elif overall == StatusMessages.SUCCESS_BACK_ONLY:
            stats['back_only_success'] += 1
        else:
            stats['both_sides_failed'] += 1

        # Count API calls
        if result['front_status'] == StatusMessages.STATUS_MISSING:
            stats['front_missing'] += 1
        else:
            stats['total_api_calls'] += 1
            if result['front_status'] == StatusMessages.STATUS_SUCCESS:
                stats['successful_calls'] += 1
            else:
                stats['failed_calls'] += 1

        if result['back_status'] == StatusMessages.STATUS_MISSING:
            stats['back_missing'] += 1
        else:
            stats['total_api_calls'] += 1
            if result['back_status'] == StatusMessages.STATUS_SUCCESS:
                stats['successful_calls'] += 1
            else:
                stats['failed_calls'] += 1

    return stats


def write_csv_results(results: List[Dict[str, str]], output_path: Path) -> None:
    """
    Write results to CSV file.

    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    csv_columns = [
        'overall_status', 'person_name', 'front_image', 'back_image',
        'name', 'gender', 'nation', 'birth', 'address', 'id_num',
        'authority', 'valid_date',
        'front_status', 'back_status', 'front_error', 'back_error'
    ]

    try:
        with open(output_path, 'w', newline='', encoding=OutputConstants.CSV_ENCODING) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerows(results)

        logging.info(f"✓ CSV file created successfully: {output_path}")

    except Exception as e:
        logging.error(f"Error writing CSV file: {str(e)}")
        raise


def write_summary_report(
    results: List[Dict[str, str]],
    stats: Dict[str, any],
    output_path: Path,
    csv_path: Path
) -> None:
    """
    Write summary report to text file.

    Args:
        results: List of result dictionaries
        stats: Statistics dictionary
        output_path: Path to summary text file
        csv_path: Path to CSV file (for reference in summary)
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ID CARD OCR PROCESSING SUMMARY\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Overall Statistics
            f.write("【总体统计 / OVERALL STATISTICS】\n")
            f.write("-" * 80 + "\n")
            f.write(f"总处理人数 (Total Persons):              {stats['total_persons']}\n")
            f.write(f"API调用总数 (Total API Calls):           {stats['total_api_calls']}\n")
            f.write(f"成功调用数 (Successful Calls):           {stats['successful_calls']}\n")
            f.write(f"失败调用数 (Failed Calls):               {stats['failed_calls']}\n")

            success_rate = (
                (stats['successful_calls'] / stats['total_api_calls'] * 100)
                if stats['total_api_calls'] > 0 else 0
            )
            f.write(f"成功率 (Success Rate):                   {success_rate:.1f}%\n")
            f.write("\n")

            # Detailed Results
            f.write("【详细结果 / DETAILED RESULTS】\n")
            f.write("-" * 80 + "\n")
            f.write(
                f"✓ 正反面均成功 (Both Sides Success):      "
                f"{stats['both_sides_success']} "
                f"({stats['both_sides_success']/stats['total_persons']*100:.1f}%)\n"
            )
            f.write(
                f"⚠ 仅正面成功 (Front Only):                "
                f"{stats['front_only_success']} "
                f"({stats['front_only_success']/stats['total_persons']*100:.1f}%)\n"
            )
            f.write(
                f"⚠ 仅背面成功 (Back Only):                 "
                f"{stats['back_only_success']} "
                f"({stats['back_only_success']/stats['total_persons']*100:.1f}%)\n"
            )
            f.write(
                f"✗ 正反面均失败 (Both Sides Failed):       "
                f"{stats['both_sides_failed']} "
                f"({stats['both_sides_failed']/stats['total_persons']*100:.1f}%)\n"
            )
            f.write("\n")

            # Missing Images
            f.write("【缺失图像 / MISSING IMAGES】\n")
            f.write("-" * 80 + "\n")
            f.write(f"缺失正面 (Missing Front):                 {stats['front_missing']}\n")
            f.write(f"缺失背面 (Missing Back):                  {stats['back_missing']}\n")
            f.write("\n")

            # Failed Items
            failed_items = [r for r in results if r['overall_status'] == StatusMessages.FAILED]
            if failed_items:
                f.write("【失败项目列表 / FAILED ITEMS】\n")
                f.write("-" * 80 + "\n")
                f.write(f"共 {len(failed_items)} 个失败项目:\n\n")

                for idx, item in enumerate(failed_items, 1):
                    f.write(f"{idx}. {item['person_name']}\n")
                    f.write(f"   正面状态 (Front): {item['front_status']}")
                    if item.get('front_error'):
                        f.write(f" - {item['front_error']}")
                    f.write("\n")
                    f.write(f"   背面状态 (Back):  {item['back_status']}")
                    if item.get('back_error'):
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
                    if item.get('front_error'):
                        f.write(f" ({item['front_error']})")
                    f.write("\n")
                    f.write(f"   背面: {item['back_status']}")
                    if item.get('back_error'):
                        f.write(f" ({item['back_error']})")
                    f.write("\n\n")

            # Output Files
            f.write("【输出文件 / OUTPUT FILES】\n")
            f.write("-" * 80 + "\n")
            f.write(f"详细结果 (Detailed Results): {csv_path}\n")
            f.write(f"处理日志 (Processing Log):   {OutputConstants.OCR_LOG_FILENAME}\n")
            f.write(f"本摘要 (This Summary):        {output_path}\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("处理完成 (Processing Completed)\n")
            f.write("=" * 80 + "\n")

        logging.info(f"✓ Summary report created: {output_path}")

    except Exception as e:
        logging.error(f"Error writing summary file: {str(e)}")
        raise


def print_console_summary(stats: Dict[str, any], csv_path: Path, summary_path: Path) -> None:
    """
    Print summary to console.

    Args:
        stats: Statistics dictionary
        csv_path: Path to CSV file
        summary_path: Path to summary file
    """
    logging.info("\n" + "=" * 60)
    logging.info("处理摘要 / PROCESSING SUMMARY")
    logging.info("=" * 60)
    logging.info(f"总处理人数:        {stats['total_persons']}")
    logging.info(f"正反面均成功:      {stats['both_sides_success']}")
    logging.info(f"仅正面成功:        {stats['front_only_success']}")
    logging.info(f"仅背面成功:        {stats['back_only_success']}")
    logging.info(f"完全失败:          {stats['both_sides_failed']}")
    logging.info(f"API调用成功:       {stats['successful_calls']}")
    logging.info(f"API调用失败:       {stats['failed_calls']}")
    logging.info("-" * 60)
    logging.info(f"结果已保存至:      {csv_path}")
    logging.info(f"摘要已保存至:      {summary_path}")
    logging.info("=" * 60)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='ID Card OCR Processing using Tencent Cloud API',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--input-dir',
        type=Path,
        help='Input directory containing ID card images'
    )

    parser.add_argument(
        '--output-csv',
        type=Path,
        help='Output CSV file path'
    )

    parser.add_argument(
        '--summary',
        type=Path,
        help='Summary report file path'
    )

    parser.add_argument(
        '--rate-limit',
        type=int,
        help='API requests per second'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    parser.add_argument(
        '--max-concurrent',
        type=int,
        help='Maximum concurrent processing threads'
    )

    parser.add_argument(
        '--env-file',
        type=Path,
        help='Path to .env file'
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point"""
    args = parse_arguments()

    try:
        # Load configuration
        config = Config.from_env(args.env_file)

        # Override config with CLI arguments if provided
        if args.input_dir:
            config.input_dir = args.input_dir
        if args.rate_limit:
            config.rate_limit = args.rate_limit
        if args.log_level:
            config.log_level = args.log_level
        if args.max_concurrent:
            config.max_concurrent_requests = args.max_concurrent

        # Set output paths
        output_csv = args.output_csv if args.output_csv else config.output_csv_path
        summary_file = args.summary if args.summary else config.summary_file_path

        # Ensure directories exist
        config.ensure_directories()

        # Setup logging
        logger = setup_logging(config.logs_dir, config.log_level)

        logging.info("\n" + "=" * 60)
        logging.info("ID CARD OCR PROCESSING")
        logging.info("=" * 60)
        logging.info(f"Input directory: {config.input_dir}")
        logging.info(f"Output CSV: {output_csv}")
        logging.info(f"Summary file: {summary_file}")
        logging.info(f"Rate limit: {config.rate_limit} requests/second")
        logging.info(f"Max concurrent: {config.max_concurrent_requests} workers")
        logging.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

        # Check if input directory exists
        if not config.input_dir.exists():
            logging.error(f"Input directory does not exist: {config.input_dir}")
            sys.exit(1)

        # Get all image files
        all_images = list(config.input_dir.glob(f"*{FileConstants.PNG_EXTENSION}"))

        if not all_images:
            logging.warning(f"No PNG images found in {config.input_dir}")
            sys.exit(0)

        # Group images by person
        person_images = group_images_by_person(all_images)
        logging.info(f"Found {len(person_images)} persons with ID card images\n")

        # Initialize rate limiter
        limiter = RateLimiter(max_requests_per_second=config.rate_limit)

        # Process ID cards (with concurrency)
        start_time = time.time()
        results = process_with_concurrency(
            person_images,
            limiter,
            config,
            max_workers=config.max_concurrent_requests
        )
        elapsed_time = time.time() - start_time

        # Calculate statistics
        stats = calculate_statistics(results)

        # Write results
        write_csv_results(results, output_csv)
        write_summary_report(results, stats, summary_file, output_csv)

        # Print console summary
        print_console_summary(stats, output_csv, summary_file)

        logging.info(f"\nElapsed time: {elapsed_time:.2f} seconds")
        logging.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("Processing completed!")

        # Exit with appropriate code
        sys.exit(0 if stats['both_sides_failed'] == 0 else 1)

    except ValueError as e:
        print(f"\nConfiguration Error: {e}", file=sys.stderr)
        print("\nPlease ensure:")
        print("  1. .env file exists with TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY")
        print("  2. Credentials are valid")
        print("\nSee README.md for setup instructions.\n")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\nUnexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
