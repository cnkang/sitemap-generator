# Sitemap Generator

A robust, thread-safe sitemap generator that crawls websites and creates XML sitemaps. Supports both local execution and AWS Lambda deployment.

## Features

- **Thread-safe crawling** with configurable worker threads
- **Breadth-first crawling** for better performance
- **Robust error handling** with comprehensive logging
- **Environment-based configuration** (no more hardcoded values)
- **AWS S3 integration** for cloud deployment
- **Robots.txt compliance** with fallback handling
- **URL normalization** and deduplication
- **Time-based filtering** for content freshness
- **Request timeout handling** to prevent hanging

## Requirements

- Python 3.11 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cnkang/sitemap-generator.git
cd sitemap-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

The generator uses environment variables for configuration. Copy `.env.example` to `.env` and modify:

### Basic Configuration
- `DOMAIN`: Target domain (e.g., 'www.example.com')
- `START_URL`: Starting URL for crawling
- `OUTPUT_FILENAME`: Output sitemap filename
- `MAX_DEPTH`: Maximum crawling depth (default: 10)
- `MAX_WORKERS`: Number of concurrent threads (default: 5)

### Advanced Options
- `USE_TIME_FILTER`: Filter by modification time (true/false)
- `RESPECT_ROBOTS_TXT`: Follow robots.txt rules (true/false)
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 30)
- `USER_AGENT`: Custom user agent string

### AWS Configuration (for Lambda deployment)
- `RUN_LOCALLY`: Set to 'false' for S3 upload
- `S3_BUCKET`: Target S3 bucket name
- `S3_KEY`: S3 object key for the sitemap

## Usage

### Local Execution
```bash
python sitemap_generator.py
```

### AWS Lambda Deployment
The script includes a `lambda_handler` function for AWS Lambda deployment. Set `RUN_LOCALLY=false` to enable S3 upload.

## Example Configuration

```bash
# Basic setup for crawling example.com
DOMAIN=example.com
START_URL=https://example.com
OUTPUT_FILENAME=sitemap.xml
MAX_DEPTH=5
MAX_WORKERS=3
```

## Best Practices

- **Start small**: Begin with `MAX_DEPTH=3` and `MAX_WORKERS=3` for testing
- **Respect rate limits**: Don't set `MAX_WORKERS` too high to avoid overwhelming servers
- **Monitor logs**: The script provides detailed logging for troubleshooting
- **Test robots.txt**: Ensure your crawler respects the target site's crawling policies
- **Use time filters**: Enable `USE_TIME_FILTER` to focus on recently updated content

## Improvements Made

This version includes several optimizations over the original:

- **Fixed syntax errors** and improved code structure
- **Modern Python 3.11+ features** with union syntax and built-in generics
- **Added comprehensive error handling** with proper logging
- **Implemented environment-based configuration** instead of hardcoded values
- **Improved thread safety** and performance
- **Added URL normalization** to prevent duplicates
- **Better robots.txt handling** with fallback options
- **Enhanced AWS integration** with proper error handling
- **Type-safe code** with modern type annotations
