"""
Constants used throughout the IDCardOCR application.
Centralizes magic numbers and configuration values.
"""

from pathlib import Path


class ImageConstants:
    """Constants related to image processing"""
    DEFAULT_DPI = 300
    DPI_SCALE_FACTOR = 300 / 72  # Convert 72 DPI to 300 DPI
    MAX_IMAGE_SIZE_MB = 10.0
    COMPRESSION_QUALITY_START = 95
    COMPRESSION_QUALITY_MIN = 5
    COMPRESSION_QUALITY_STEP = 10
    COMPRESSION_QUALITY_RESET = 85
    RESIZE_FACTOR = 0.8
    MARGIN_PERCENTAGE = 0.05
    MIN_TEXT_LENGTH_FOR_DETECTION = 20


class APIConstants:
    """Constants related to Tencent Cloud API"""
    DEFAULT_RATE_LIMIT = 20  # requests per second
    SERVICE = "ocr"
    HOST = "ocr.tencentcloudapi.com"
    ENDPOINT = "https://ocr.tencentcloudapi.com"
    VERSION = "2018-11-19"
    ACTION = "IDCardOCR"
    ALGORITHM = "TC3-HMAC-SHA256"
    REGION = ""
    REQUEST_TIMEOUT_SECONDS = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # seconds


class CardDetectionConstants:
    """Constants for ID card side detection"""
    FRONT_KEYWORDS = ['姓名', '性别', '民族', '出生', '住址', '公民身份号码', '身份证']
    BACK_KEYWORDS = ['签发机关', '有效期限', '发证机关', '签发', '有效']
    VALIDITY_DATE_PATTERN = r'\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}[-日\s]+\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}'
    OCR_HIGH_RESOLUTION_SCALE = 2


class FileConstants:
    """Constants for file operations"""
    PDF_EXTENSION = '.pdf'
    PNG_EXTENSION = '.png'
    CSV_EXTENSION = '.csv'
    FRONT_SUFFIX = '_front.png'
    BACK_SUFFIX = '_back.png'
    FRONT_KEYWORDS_FILENAME = ['正面', 'front', '人像']
    BACK_KEYWORDS_FILENAME = ['反面', 'back', '国徽']


class DirectoryConstants:
    """Default directory structure"""
    DEFAULT_INPUT_DIR = "inputs"
    DEFAULT_OUTPUT_DIR = "outputs"
    DEFAULT_ARCHIVE_DIR = ".archive"
    DEFAULT_RESULTS_SUBDIR = "results"
    DEFAULT_LOGS_SUBDIR = "logs"
    DEFAULT_TEMP_SUBDIR = "temp_files"


class OutputConstants:
    """Constants for output generation"""
    CSV_OUTPUT_FILENAME = "id_card_results.csv"
    SUMMARY_OUTPUT_FILENAME = "processing_summary.txt"
    OCR_LOG_FILENAME = "ocr_processing.log"
    EXTRACTION_LOG_FILENAME = "id_extraction.log"
    CSV_ENCODING = "utf-8-sig"  # UTF-8 with BOM for Excel compatibility


class StatusMessages:
    """Status messages in bilingual format"""
    SUCCESS_BOTH = '✓ 成功 (SUCCESS)'
    SUCCESS_FRONT_ONLY = '⚠ 仅正面成功 (Front Only)'
    SUCCESS_BACK_ONLY = '⚠ 仅背面成功 (Back Only)'
    FAILED = '✗ 失败 (FAILED)'

    STATUS_SUCCESS = 'SUCCESS'
    STATUS_ERROR = 'ERROR'
    STATUS_EXCEPTION = 'EXCEPTION'
    STATUS_MISSING = 'MISSING'

    CARD_SIDE_FRONT = 'FRONT'
    CARD_SIDE_BACK = 'BACK'
