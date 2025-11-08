#!/usr/bin/env python3
"""
ID Card Extractor
Extracts front and back images from Chinese ID card PDFs in two formats:
- Format 1: 2-page PDF (page 1 = front, page 2 = back)
- Format 2: 1-page PDF (both sides on same page)
"""

import io
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Tuple

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError as e:
    print("\nERROR: Required dependencies not installed.")
    print("\nPlease install required packages:")
    print("  pip install PyMuPDF Pillow")
    print("\nOr if using uv:")
    print("  uv pip install PyMuPDF Pillow")
    print("\nFor PDF processing with OCR, also install:")
    print("  pip install pytesseract")
    print("  # Plus Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki")
    print(f"\nOriginal error: {e}\n")
    sys.exit(1)

# Optional: pytesseract for OCR-based side detection
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from .constants import (
    CardDetectionConstants,
    FileConstants,
    ImageConstants,
)


# Type aliases
CardSide = Literal['front', 'back', 'unknown']
PDFFormat = Literal['format1', 'format2']


def setup_logging(log_dir: Path) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_dir: Directory for log files

    Returns:
        Configured logger instance
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "id_extraction.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def detect_card_side(page: fitz.Page) -> CardSide:
    """
    Detect if a page is the front or back of an ID card.

    Uses keyword matching on extracted text. Falls back to OCR if text
    extraction yields insufficient results.

    Args:
        page: PyMuPDF page object to analyze

    Returns:
        'front' if front side detected, 'back' if back side, 'unknown' if uncertain
    """
    try:
        # First try to get text directly
        text = page.get_text()

        # If very little text found, it's likely a scanned image - try OCR
        if len(text.strip()) < ImageConstants.MIN_TEXT_LENGTH_FOR_DETECTION:
            if PYTESSERACT_AVAILABLE:
                try:
                    # Convert page to image and run OCR
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(
                            CardDetectionConstants.OCR_HIGH_RESOLUTION_SCALE,
                            CardDetectionConstants.OCR_HIGH_RESOLUTION_SCALE
                        )
                    )
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # Run OCR with Chinese language support
                    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                    logging.debug(f"Used OCR, extracted text length: {len(text)}")
                except Exception as ocr_error:
                    logging.debug(f"OCR failed: {str(ocr_error)}")
            else:
                logging.debug("Tesseract not available, using text extraction only")

        # Count indicators for each side
        front_indicators = sum(
            1 for keyword in CardDetectionConstants.FRONT_KEYWORDS
            if keyword in text
        )
        back_indicators = sum(
            1 for keyword in CardDetectionConstants.BACK_KEYWORDS
            if keyword in text
        )

        # Special check: if it has validity dates pattern (YYYY.MM.DD-YYYY.MM.DD)
        if re.search(CardDetectionConstants.VALIDITY_DATE_PATTERN, text):
            back_indicators += 2

        logging.debug(f"Front indicators: {front_indicators}, Back indicators: {back_indicators}")

        # Determine side based on indicators
        if front_indicators > back_indicators:
            return 'front'
        elif back_indicators > front_indicators:
            return 'back'
        else:
            return 'unknown'

    except Exception as e:
        logging.error(f"Error detecting card side: {str(e)}")
        return 'unknown'


def detect_pdf_format(pdf_path: Path) -> Optional[PDFFormat]:
    """
    Detect which format the PDF is in.

    Args:
        pdf_path: Path to PDF file

    Returns:
        'format1' (2 pages), 'format2' (1 page), or None if invalid
    """
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        doc.close()

        if page_count == 2:
            return 'format1'
        elif page_count == 1:
            return 'format2'
        else:
            return None

    except Exception as e:
        logging.error(f"Error detecting format for {pdf_path}: {str(e)}")
        return None


def extract_format1(
    pdf_path: Path,
    output_dir: Path,
    base_name: str,
    dpi: int = ImageConstants.DEFAULT_DPI
) -> bool:
    """
    Extract from Format 1: 2-page PDF.
    Automatically detects which page is front or back.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for images
        base_name: Base name for output files
        dpi: DPI for image extraction

    Returns:
        True if successful, False otherwise
    """
    try:
        doc = fitz.open(str(pdf_path))

        # Detect which page is which
        page1_side = detect_card_side(doc[0])
        page2_side = detect_card_side(doc[1])

        logging.info(f"Page 1 detected as: {page1_side}")
        logging.info(f"Page 2 detected as: {page2_side}")

        # Create mapping of page index to side
        if page1_side == 'front':
            page_mapping = {'front': 0, 'back': 1}
        elif page1_side == 'back':
            page_mapping = {'front': 1, 'back': 0}
        elif page2_side == 'front':
            page_mapping = {'front': 1, 'back': 0}
        elif page2_side == 'back':
            page_mapping = {'front': 0, 'back': 1}
        else:
            # If we can't detect, default to page 1 = front, page 2 = back
            logging.warning(
                "Could not definitively detect card sides, "
                "using default order (page 1=front, page 2=back)"
            )
            page_mapping = {'front': 0, 'back': 1}

        # Extract front
        dpi_scale = dpi / 72
        page = doc[page_mapping['front']]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale))
        front_path = output_dir / f"{base_name}{FileConstants.FRONT_SUFFIX}"
        pix.save(str(front_path))
        logging.info(f"Saved front (from page {page_mapping['front'] + 1}): {front_path}")

        # Extract back
        page = doc[page_mapping['back']]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale))
        back_path = output_dir / f"{base_name}{FileConstants.BACK_SUFFIX}"
        pix.save(str(back_path))
        logging.info(f"Saved back (from page {page_mapping['back'] + 1}): {back_path}")

        doc.close()
        return True

    except Exception as e:
        logging.error(f"Error extracting Format 1 from {pdf_path}: {str(e)}")
        return False


def extract_format2(
    pdf_path: Path,
    output_dir: Path,
    base_name: str,
    dpi: int = ImageConstants.DEFAULT_DPI
) -> bool:
    """
    Extract from Format 2: 1-page PDF with both sides.
    Automatically detects which half is front or back.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for images
        base_name: Base name for output files
        dpi: DPI for image extraction

    Returns:
        True if successful, False otherwise
    """
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[0]

        # Get full page as image
        dpi_scale = dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        width, height = img.size
        mid_height = height // 2

        # Try to detect which half is which by analyzing text in each half
        rect_top = fitz.Rect(0, 0, page.rect.width, page.rect.height / 2)
        rect_bottom = fitz.Rect(0, page.rect.height / 2, page.rect.width, page.rect.height)

        text_top = page.get_text(clip=rect_top)
        text_bottom = page.get_text(clip=rect_bottom)

        # If very little text, try OCR on image crops
        if (len(text_top.strip()) < ImageConstants.MIN_TEXT_LENGTH_FOR_DETECTION or
            len(text_bottom.strip()) < ImageConstants.MIN_TEXT_LENGTH_FOR_DETECTION):
            if PYTESSERACT_AVAILABLE:
                try:
                    # OCR top half
                    top_img = img.crop((0, 0, width, mid_height))
                    text_top = pytesseract.image_to_string(top_img, lang='chi_sim+eng')

                    # OCR bottom half
                    bottom_img = img.crop((0, mid_height, width, height))
                    text_bottom = pytesseract.image_to_string(bottom_img, lang='chi_sim+eng')

                    logging.debug("Used OCR for Format 2 detection")
                except Exception as ocr_error:
                    logging.debug(f"OCR not available for Format 2: {str(ocr_error)}")

        # Analyze each half
        top_indicators = sum(
            1 for keyword in CardDetectionConstants.FRONT_KEYWORDS
            if keyword in text_top
        )
        bottom_indicators = sum(
            1 for keyword in CardDetectionConstants.FRONT_KEYWORDS
            if keyword in text_bottom
        )

        # Check for back indicators (these reduce the score)
        top_indicators -= sum(
            1 for keyword in CardDetectionConstants.BACK_KEYWORDS
            if keyword in text_top
        )
        bottom_indicators -= sum(
            1 for keyword in CardDetectionConstants.BACK_KEYWORDS
            if keyword in text_bottom
        )

        # Check for validity date pattern
        if re.search(CardDetectionConstants.VALIDITY_DATE_PATTERN, text_top):
            top_indicators -= 2
        if re.search(CardDetectionConstants.VALIDITY_DATE_PATTERN, text_bottom):
            bottom_indicators -= 2

        logging.info(f"Top half score: {top_indicators}, Bottom half score: {bottom_indicators}")

        # Determine which half is front
        margin = int(height * ImageConstants.MARGIN_PERCENTAGE)

        if top_indicators > bottom_indicators:
            # Top is front, bottom is back
            logging.info("Detected: Top half = front, Bottom half = back")
            front_img = img.crop((0, 0, width, mid_height + margin))
            back_img = img.crop((0, mid_height - margin, width, height))
        else:
            if top_indicators == bottom_indicators:
                logging.warning(
                    "Could not definitively detect card sides, "
                    "using default order (top=front, bottom=back)"
                )
                front_img = img.crop((0, 0, width, mid_height + margin))
                back_img = img.crop((0, mid_height - margin, width, height))
            else:
                # Bottom is front, top is back
                logging.info("Detected: Bottom half = front, Top half = back")
                front_img = img.crop((0, mid_height - margin, width, height))
                back_img = img.crop((0, 0, width, mid_height + margin))

        # Save images
        front_path = output_dir / f"{base_name}{FileConstants.FRONT_SUFFIX}"
        front_img.save(str(front_path))
        logging.info(f"Saved front: {front_path}")

        back_path = output_dir / f"{base_name}{FileConstants.BACK_SUFFIX}"
        back_img.save(str(back_path))
        logging.info(f"Saved back: {back_path}")

        doc.close()
        return True

    except Exception as e:
        logging.error(f"Error extracting Format 2 from {pdf_path}: {str(e)}")
        return False


def process_pdf(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = ImageConstants.DEFAULT_DPI
) -> bool:
    """
    Process a single PDF file.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for images
        dpi: DPI for image extraction

    Returns:
        True if successful, False otherwise
    """
    try:
        if not pdf_path.exists():
            logging.error(f"File not found: {pdf_path}")
            return False

        if pdf_path.suffix.lower() != FileConstants.PDF_EXTENSION:
            logging.warning(f"Skipping non-PDF file: {pdf_path}")
            return False

        base_name = pdf_path.stem
        logging.info(f"Processing: {pdf_path.name}")

        # Detect format
        format_type = detect_pdf_format(pdf_path)

        if format_type is None:
            logging.error(
                f"UNSUPPORTED FORMAT: {pdf_path.name} - "
                "PDF must have exactly 1 or 2 pages"
            )
            return False

        logging.info(f"Detected format: {format_type}")

        # Extract based on format
        if format_type == 'format1':
            success = extract_format1(pdf_path, output_dir, base_name, dpi)
        elif format_type == 'format2':
            success = extract_format2(pdf_path, output_dir, base_name, dpi)
        else:
            logging.error(f"Unknown format type: {format_type}")
            return False

        if success:
            logging.info(f"Successfully processed: {pdf_path.name}\n")
        else:
            logging.error(f"Failed to process: {pdf_path.name}\n")

        return success

    except Exception as e:
        logging.error(f"Unexpected error processing {pdf_path}: {str(e)}\n")
        return False


def process_directory(
    input_dir: Path,
    output_dir: Path,
    dpi: int = ImageConstants.DEFAULT_DPI
) -> Tuple[int, int]:
    """
    Process all PDF files in a directory.

    Args:
        input_dir: Directory containing PDF files
        output_dir: Output directory for extracted images
        dpi: DPI for image extraction

    Returns:
        Tuple of (success_count, error_count)
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.info("=" * 60)
    logging.info(f"ID Card Extraction Started - {datetime.now()}")
    logging.info(f"Input directory: {input_dir}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"DPI: {dpi}")
    logging.info("=" * 60 + "\n")

    # Get all PDF files
    pdf_files = list(input_dir.glob(f"*{FileConstants.PDF_EXTENSION}"))

    if not pdf_files:
        logging.warning(f"No PDF files found in {input_dir}")
        return 0, 0

    logging.info(f"Found {len(pdf_files)} PDF file(s)\n")

    # Process each PDF
    success_count = 0
    error_count = 0

    for pdf_file in pdf_files:
        if process_pdf(pdf_file, output_dir, dpi):
            success_count += 1
        else:
            error_count += 1

    # Summary
    logging.info("=" * 60)
    logging.info("SUMMARY")
    logging.info(f"Total PDFs: {len(pdf_files)}")
    logging.info(f"Successfully processed: {success_count}")
    logging.info(f"Failed/Skipped: {error_count}")
    logging.info("=" * 60)

    return success_count, error_count


if __name__ == "__main__":
    # Get project root directory (parent of src directory)
    PROJECT_ROOT = Path(__file__).parent.parent

    # Configuration
    INPUT_DIR = PROJECT_ROOT / "inputs"
    OUTPUT_DIR = PROJECT_ROOT / "outputs"
    LOG_DIR = PROJECT_ROOT / ".archive" / "logs"

    # Setup logging
    logger = setup_logging(LOG_DIR)

    # Ensure directories exist
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run the extraction
    success, errors = process_directory(INPUT_DIR, OUTPUT_DIR)

    if errors > 0:
        logging.info(f"\nCheck log file for details: {LOG_DIR / 'id_extraction.log'}")

    sys.exit(0 if errors == 0 else 1)
