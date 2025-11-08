"""
Configuration management for IDCardOCR application.
Loads configuration from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .constants import (
    APIConstants,
    DirectoryConstants,
    ImageConstants,
    OutputConstants,
)


@dataclass
class Config:
    """Application configuration loaded from environment variables"""

    # Paths
    project_root: Path
    input_dir: Path
    output_dir: Path
    archive_dir: Path
    results_dir: Path
    logs_dir: Path
    temp_dir: Path

    # API Configuration
    secret_id: str
    secret_key: str
    rate_limit: int = APIConstants.DEFAULT_RATE_LIMIT
    api_timeout: int = APIConstants.REQUEST_TIMEOUT_SECONDS
    max_retries: int = APIConstants.MAX_RETRIES

    # Image Processing
    dpi: int = ImageConstants.DEFAULT_DPI
    max_image_size_mb: float = ImageConstants.MAX_IMAGE_SIZE_MB

    # Output Files
    output_csv_name: str = OutputConstants.CSV_OUTPUT_FILENAME
    summary_file_name: str = OutputConstants.SUMMARY_OUTPUT_FILENAME

    # Logging
    log_level: str = "INFO"

    # Processing
    max_concurrent_requests: int = 10

    @property
    def output_csv_path(self) -> Path:
        """Full path to output CSV file"""
        return self.results_dir / self.output_csv_name

    @property
    def summary_file_path(self) -> Path:
        """Full path to summary file"""
        return self.results_dir / self.summary_file_name

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> 'Config':
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file. If None, looks in project root.

        Returns:
            Config instance with values loaded from environment

        Raises:
            ValueError: If required environment variables are missing or invalid
        """
        # Determine project root
        project_root = Path(__file__).parent.parent

        # Load .env file if it exists
        if env_file is None:
            env_file = project_root / ".env"

        if env_file.exists():
            load_dotenv(env_file)

        # Load required credentials
        secret_id = os.getenv("TENCENTCLOUD_SECRET_ID", "")
        secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY", "")

        if not secret_id or not secret_key:
            raise ValueError(
                "Missing required environment variables: "
                "TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY"
            )

        # Validate credentials
        cls._validate_credentials(secret_id, secret_key)

        # Load paths with defaults
        input_dir = Path(os.getenv(
            "INPUT_DIR",
            str(project_root / DirectoryConstants.DEFAULT_OUTPUT_DIR)
        ))
        archive_dir = Path(os.getenv(
            "ARCHIVE_DIR",
            str(project_root / DirectoryConstants.DEFAULT_ARCHIVE_DIR)
        ))

        # Construct derived paths
        results_dir = archive_dir / DirectoryConstants.DEFAULT_RESULTS_SUBDIR
        logs_dir = archive_dir / DirectoryConstants.DEFAULT_LOGS_SUBDIR
        temp_dir = archive_dir / DirectoryConstants.DEFAULT_TEMP_SUBDIR
        output_dir = project_root / DirectoryConstants.DEFAULT_OUTPUT_DIR

        # Load optional configuration
        rate_limit = int(os.getenv("RATE_LIMIT", str(APIConstants.DEFAULT_RATE_LIMIT)))
        api_timeout = int(os.getenv("API_TIMEOUT", str(APIConstants.REQUEST_TIMEOUT_SECONDS)))
        max_retries = int(os.getenv("MAX_RETRIES", str(APIConstants.MAX_RETRIES)))
        dpi = int(os.getenv("DPI", str(ImageConstants.DEFAULT_DPI)))
        max_image_size_mb = float(os.getenv("MAX_IMAGE_SIZE_MB", str(ImageConstants.MAX_IMAGE_SIZE_MB)))
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))

        return cls(
            project_root=project_root,
            input_dir=input_dir,
            output_dir=output_dir,
            archive_dir=archive_dir,
            results_dir=results_dir,
            logs_dir=logs_dir,
            temp_dir=temp_dir,
            secret_id=secret_id,
            secret_key=secret_key,
            rate_limit=rate_limit,
            api_timeout=api_timeout,
            max_retries=max_retries,
            dpi=dpi,
            max_image_size_mb=max_image_size_mb,
            log_level=log_level,
            max_concurrent_requests=max_concurrent,
        )

    @staticmethod
    def _validate_credentials(secret_id: str, secret_key: str) -> None:
        """
        Validate credential format.

        Args:
            secret_id: Tencent Cloud Secret ID
            secret_key: Tencent Cloud Secret Key

        Raises:
            ValueError: If credentials appear invalid
        """
        if len(secret_id) < 20:
            raise ValueError(
                f"TENCENTCLOUD_SECRET_ID appears invalid (too short: {len(secret_id)} chars)"
            )

        if len(secret_key) < 20:
            raise ValueError(
                f"TENCENTCLOUD_SECRET_KEY appears invalid (too short: {len(secret_key)} chars)"
            )

        # Basic character validation (alphanumeric + common special chars)
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        if not set(secret_id).issubset(allowed_chars):
            raise ValueError("TENCENTCLOUD_SECRET_ID contains invalid characters")

        if not set(secret_key).issubset(allowed_chars):
            raise ValueError("TENCENTCLOUD_SECRET_KEY contains invalid characters")

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist"""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate_input_path(self, path: Path) -> Path:
        """
        Validate that a path is safe and within allowed directories.

        Args:
            path: Path to validate

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path is outside allowed directories
        """
        resolved_path = path.resolve()

        # Check if path is within project directory
        try:
            resolved_path.relative_to(self.project_root)
        except ValueError:
            raise ValueError(
                f"Path '{path}' is outside project directory '{self.project_root}'"
            )

        return resolved_path
