"""Configuration settings for the sitemap generator.

Requires Python 3.11+ for modern type annotations.
"""

import os
from datetime import datetime, timezone

# AWS S3 configuration
S3_BUCKET: str = os.getenv("S3_BUCKET", "example-s3-bucket")
S3_KEY: str = os.getenv("S3_KEY", "/path/to/sitemap.xml")

# Runtime configuration
RUN_LOCALLY: bool = os.getenv("RUN_LOCALLY", "true").lower() == "true"

# Crawling configuration
MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", "10"))
DOMAIN: str = os.getenv("DOMAIN", "www.example.com")
MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "5"))
OUTPUT_FILENAME: str = os.getenv("OUTPUT_FILENAME", "sitemap.xml")
START_URL: str = os.getenv("START_URL", "https://www.example.com/home")

# Filtering configuration
USE_TIME_FILTER: bool = os.getenv("USE_TIME_FILTER", "true").lower() == "true"
TIME_FILTER_THRESHOLD: datetime = datetime(2022, 9, 20, tzinfo=timezone.utc)
RESPECT_ROBOTS_TXT: bool = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"

# Request configuration
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
USER_AGENT: str = os.getenv("USER_AGENT", "SitemapGenerator/1.0")
