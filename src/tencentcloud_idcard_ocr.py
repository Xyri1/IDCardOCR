# -*- coding: utf-8 -*-
"""
Tencent Cloud ID Card OCR API Client

This module implements TC3-HMAC-SHA256 authentication for Tencent Cloud API.
Based on: https://cloud.tencent.com/document/product/213/30654
"""

import base64
import hashlib
import hmac
import io
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

from .constants import APIConstants, ImageConstants

# Try to import requests, fall back to http.client
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    import sys
    if sys.version_info[0] <= 2:
        from httplib import HTTPSConnection
    else:
        from http.client import HTTPSConnection
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def sign(key: bytes, msg: str) -> bytes:
    """
    Generate HMAC-SHA256 signature.

    Args:
        key: Secret key bytes
        msg: Message to sign

    Returns:
        Signature bytes
    """
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def compress_image_binary_search(
    img: Image.Image,
    target_size_mb: float = ImageConstants.MAX_IMAGE_SIZE_MB
) -> bytes:
    """
    Compress image using binary search to find optimal quality.

    Uses binary search algorithm to quickly find the best quality setting
    that keeps the image under the target size. Much faster than linear search.

    Args:
        img: PIL Image object to compress
        target_size_mb: Target size in megabytes

    Returns:
        Compressed image bytes

    Raises:
        ValueError: If image cannot be compressed to target size
    """
    # Convert RGBA/LA/P modes to RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    quality_min = ImageConstants.COMPRESSION_QUALITY_MIN
    quality_max = ImageConstants.COMPRESSION_QUALITY_START
    best_quality = None
    best_data = None
    attempts = 0

    logger.info("Starting binary search compression...")

    while quality_min <= quality_max:
        quality = (quality_min + quality_max) // 2
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()
        size_mb = len(base64.b64encode(compressed_data)) / (1024 * 1024)

        attempts += 1
        logger.info(f"  Attempt {attempts}: quality={quality}, size={size_mb:.2f}MB")

        if size_mb <= target_size_mb:
            best_quality = quality
            best_data = compressed_data
            quality_min = quality + 1  # Try higher quality
        else:
            quality_max = quality - 1  # Need lower quality

    if best_data is None:
        # If even minimum quality is too large, try resizing
        logger.warning("Minimum quality still too large, attempting resize...")
        width, height = img.size
        img = img.resize(
            (int(width * ImageConstants.RESIZE_FACTOR),
             int(height * ImageConstants.RESIZE_FACTOR)),
            Image.Resampling.LANCZOS
        )
        return compress_image_binary_search(img, target_size_mb)

    logger.info(f"✓ Compression successful: quality={best_quality}, attempts={attempts}")
    return best_data


def validate_and_compress_image(image_path: Path) -> str:
    """
    Read, validate, and compress image if necessary.

    Args:
        image_path: Path to image file

    Returns:
        Base64-encoded image string

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image cannot be compressed to acceptable size
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Read image and encode to Base64
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')

    # Check Base64 size
    base64_size_mb = len(image_base64) / (1024 * 1024)

    if base64_size_mb > ImageConstants.MAX_IMAGE_SIZE_MB:
        logger.warning(
            f"Image Base64 size {base64_size_mb:.2f}MB exceeds "
            f"{ImageConstants.MAX_IMAGE_SIZE_MB}MB limit"
        )
        logger.info("Compressing image...")

        img = Image.open(image_path)
        compressed_data = compress_image_binary_search(img, ImageConstants.MAX_IMAGE_SIZE_MB)

        # Re-encode to Base64
        image_base64 = base64.b64encode(compressed_data).decode('utf-8')
        compressed_size_mb = len(image_base64) / (1024 * 1024)
        logger.info(f"Compressed: {base64_size_mb:.2f}MB → {compressed_size_mb:.2f}MB")

    return image_base64


def build_authorization_header(
    payload: str,
    secret_id: str,
    secret_key: str,
    timestamp: int
) -> Dict[str, Any]:
    """
    Build authorization header for Tencent Cloud API v3.

    Args:
        payload: JSON request payload
        secret_id: Tencent Cloud Secret ID
        secret_key: Tencent Cloud Secret Key
        timestamp: Unix timestamp

    Returns:
        Dictionary of HTTP headers
    """
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    # Step 1: Build canonical request
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    content_type = "application/json; charset=utf-8"
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{APIConstants.HOST}\n"
        f"x-tc-action:{APIConstants.ACTION.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (
        http_request_method + "\n" +
        canonical_uri + "\n" +
        canonical_querystring + "\n" +
        canonical_headers + "\n" +
        signed_headers + "\n" +
        hashed_request_payload
    )

    # Step 2: Build string to sign
    credential_scope = f"{date}/{APIConstants.SERVICE}/tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (
        f"{APIConstants.ALGORITHM}\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )

    # Step 3: Calculate signature
    secret_date = sign(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = sign(secret_date, APIConstants.SERVICE)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing,
        string_to_sign.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Step 4: Build Authorization header
    authorization = (
        f"{APIConstants.ALGORITHM} "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    # Step 5: Construct headers
    headers = {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": APIConstants.HOST,
        "X-TC-Action": APIConstants.ACTION,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": APIConstants.VERSION
    }

    if APIConstants.REGION:
        headers["X-TC-Region"] = APIConstants.REGION

    return headers


def call_api_with_retry(
    payload: str,
    headers: Dict[str, Any],
    max_retries: int = APIConstants.MAX_RETRIES
) -> Dict[str, Any]:
    """
    Call Tencent Cloud API with automatic retry on failure.

    Args:
        payload: JSON request payload
        headers: HTTP headers
        max_retries: Maximum number of retry attempts

    Returns:
        Parsed JSON response

    Raises:
        ConnectionError: If all retry attempts fail
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            if REQUESTS_AVAILABLE:
                # Use requests library (preferred)
                response = requests.post(
                    APIConstants.ENDPOINT,
                    headers=headers,
                    data=payload.encode("utf-8"),
                    verify=True,  # Verify SSL certificates
                    timeout=APIConstants.REQUEST_TIMEOUT_SECONDS
                )

                if response.status_code >= 500:
                    raise ConnectionError(f"Server error: {response.status_code}")

                return response.json()
            else:
                # Fall back to http.client
                conn = HTTPSConnection(APIConstants.HOST, timeout=APIConstants.REQUEST_TIMEOUT_SECONDS)
                conn.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
                resp = conn.getresponse()

                if resp.status >= 500:
                    raise ConnectionError(f"Server error: {resp.status}")

                response_data = resp.read()
                return json.loads(response_data.decode('utf-8'))

        except (ConnectionError, TimeoutError, Exception) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = APIConstants.RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"API call failed after {max_retries} attempts")

    raise ConnectionError(f"API call failed after {max_retries} attempts: {last_error}")


def idcard_ocr(
    image: str,
    card_side: Optional[str] = None,
    secret_id: Optional[str] = None,
    secret_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call Tencent Cloud ID Card OCR API.

    Args:
        image: Path to image file
        card_side: Card side ('FRONT' or 'BACK'). Auto-detected from filename if not provided
        secret_id: Tencent Cloud Secret ID (reads from env if not provided)
        secret_key: Tencent Cloud Secret Key (reads from env if not provided)

    Returns:
        Parsed JSON response dictionary

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If credentials are missing or invalid
        ConnectionError: If API call fails after retries
    """
    image_path = Path(image)

    # Validate and compress image
    image_base64 = validate_and_compress_image(image_path)

    # Auto-detect card side from filename if not provided
    if card_side is None:
        filename = image_path.name.lower()
        if any(kw in filename for kw in ['正面', 'front', '人像']):
            card_side = "FRONT"
        elif any(kw in filename for kw in ['反面', 'back', '国徽']):
            card_side = "BACK"

    # Build request parameters
    params: Dict[str, Any] = {"ImageBase64": image_base64}

    if card_side is not None:
        params["CardSide"] = card_side

    # Config parameters
    config = {
        "CropIdCard": False,
        "CropPortrait": False
    }
    params["Config"] = json.dumps(config)

    payload = json.dumps(params)

    # Get credentials from environment or parameters
    if secret_id is None:
        secret_id = os.getenv("TENCENTCLOUD_SECRET_ID", "")
    if secret_key is None:
        secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY", "")

    if not secret_id or not secret_key:
        raise ValueError(
            "Missing Tencent Cloud credentials. "
            "Set TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY environment variables"
        )

    # Build authorization headers
    timestamp = int(time.time())
    headers = build_authorization_header(payload, secret_id, secret_key, timestamp)

    # Call API with retry logic
    return call_api_with_retry(payload, headers)
