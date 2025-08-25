"""
Sitemap Generator Script.

This script is used to generate a sitemap by crawling the links of a given website.
"""

import email.utils
import html.parser
import logging
import os
import threading
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse

from config import (
    DOMAIN,
    MAX_DEPTH,
    MAX_WORKERS,
    OUTPUT_FILENAME,
    REQUEST_TIMEOUT,
    RESPECT_ROBOTS_TXT,
    RUN_LOCALLY,
    S3_BUCKET,
    S3_KEY,
    START_URL,
    TIME_FILTER_THRESHOLD,
    USE_TIME_FILTER,
    USER_AGENT,
)

# Using Python 3.10+ union syntax (|) instead of typing.Optional


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class LinkParser(html.parser.HTMLParser):
    """HTML parser to extract links from web pages."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


class SitemapGenerator:
    """Thread-safe sitemap generator with improved error handling."""

    def __init__(self):
        self.urlset = ET.Element(
            "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        )
        self.visited_urls: set[str] = set()
        self.lock = threading.Lock()
        self.rp = self._init_robots_parser()

    def _init_robots_parser(self) -> urllib.robotparser.RobotFileParser | None:
        """Initialize robots.txt parser with error handling."""
        if not RESPECT_ROBOTS_TXT:
            return None

        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(urljoin(START_URL, "/robots.txt"))
            rp.read()
            return rp
        except Exception as e:
            logging.warning("Failed to read robots.txt: %s", e)
            return None

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query parameters."""
        parsed = urlparse(url)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                "",
                "",  # Remove query and fragment
            )
        )

    def save_to_s3(self, filename: str) -> bool:
        """Upload the sitemap to S3 with error handling."""
        try:
            import boto3

            s3_client = boto3.client("s3")

            with open(filename, "rb") as file:
                s3_client.upload_fileobj(file, S3_BUCKET, S3_KEY)
            logging.info("Sitemap uploaded to S3: %s/%s", S3_BUCKET, S3_KEY)
            return True
        except Exception as e:
            logging.error("Failed to upload to S3: %s", e)
            return False

    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self.rp:
            return True
        try:
            return self.rp.can_fetch(USER_AGENT, url)
        except Exception as e:
            logging.warning("Error checking robots.txt for %s: %s", url, e)
            return True

    def process_page(self, url: str, lastmod: datetime) -> None:
        """Add page details to the sitemap in a thread-safe manner."""
        with self.lock:
            url_element = ET.SubElement(self.urlset, "url")
            ET.SubElement(url_element, "loc").text = url
            ET.SubElement(url_element, "lastmod").text = lastmod.isoformat()
            ET.SubElement(url_element, "changefreq").text = "daily"
            ET.SubElement(url_element, "priority").text = "1.0"

    def fetch_page(self, url: str) -> tuple[bytes, datetime] | None:
        """Fetch page content with improved error handling."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:

                if response.status != 200:
                    logging.warning("Non-200 status for %s: %s", url, response.status)
                    return None

                content = response.read()

                # Get last modification time
                lastmod_str = response.headers.get("last-modified")
                if lastmod_str:
                    try:
                        lastmod = email.utils.parsedate_to_datetime(lastmod_str)
                    except (ValueError, TypeError):
                        lastmod = datetime.now(timezone.utc)
                else:
                    lastmod = datetime.now(timezone.utc)

                return (content, lastmod)

        except (URLError, HTTPError, UnicodeDecodeError) as e:
            logging.warning("Error fetching %s: %s", url, e)
            return None

    def extract_links(self, content: bytes, base_url: str) -> list[str]:
        """Extract and normalize links from page content."""
        try:
            parser = LinkParser()
            parser.feed(content.decode("utf-8", errors="ignore"))

            links = []
            for href in parser.links:
                if href and not href.startswith("#") and not href.startswith("mailto:"):
                    full_url = urljoin(base_url, href)
                    normalized_url = self._normalize_url(full_url)

                    if urlparse(normalized_url).netloc == DOMAIN:
                        links.append(normalized_url)

            return links
        except Exception as e:
            logging.warning("Error parsing links from %s: %s", base_url, e)
            return []

    def crawl_page(self, url: str, depth: int) -> list[str]:
        """Crawl a single page and return new URLs to process."""
        if depth > MAX_DEPTH or not self.can_fetch(url):
            return []

        # Check if already visited
        with self.lock:
            if url in self.visited_urls:
                return []
            self.visited_urls.add(url)

        # Fetch page content
        result = self.fetch_page(url)
        if not result:
            return []

        content, lastmod = result

        # Apply time filter
        if USE_TIME_FILTER and lastmod <= TIME_FILTER_THRESHOLD:
            return []

        # Add to sitemap
        self.process_page(url, lastmod)
        logging.info("Added to sitemap: %s", url)

        # Extract new links
        return self.extract_links(content, url)

    def generate_sitemap(self) -> bool:
        """Generate sitemap using breadth-first crawling."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(OUTPUT_FILENAME)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            urls_to_process = [(START_URL, 0)]

            while urls_to_process:
                current_batch = urls_to_process[: MAX_WORKERS * 2]  # Process in batches
                urls_to_process = urls_to_process[MAX_WORKERS * 2 :]

                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    future_to_url = {
                        executor.submit(self.crawl_page, url, depth): (url, depth)
                        for url, depth in current_batch
                    }

                    for future in as_completed(future_to_url):
                        url, depth = future_to_url[future]
                        try:
                            new_links = future.result()
                            # Add new links for next depth level
                            for link in new_links:
                                if depth + 1 <= MAX_DEPTH:
                                    urls_to_process.append((link, depth + 1))
                        except Exception as e:
                            logging.error("Error processing %s: %s", url, e)

            # Write sitemap to file
            tree = ET.ElementTree(self.urlset)
            tree.write(OUTPUT_FILENAME, encoding="utf-8", xml_declaration=True)
            logging.info("Sitemap written to %s", OUTPUT_FILENAME)
            return True

        except Exception as e:
            logging.error("Error generating sitemap: %s", e)
            return False


def main():
    """Main function to generate and save/upload sitemap."""
    generator = SitemapGenerator()

    if not generator.generate_sitemap():
        logging.error("Failed to generate sitemap")
        return False

    if RUN_LOCALLY:
        logging.info("Sitemap saved locally to %s", OUTPUT_FILENAME)
        return True

    return generator.save_to_s3(OUTPUT_FILENAME)


def lambda_handler(event=None, context=None):
    """AWS Lambda handler function."""
    # pylint: disable=unused-argument
    success = main()
    return {
        "statusCode": 200 if success else 500,
        "body": (
            "Sitemap generation complete." if success else "Sitemap generation failed."
        ),
    }


# If running this script locally, call the main function
if __name__ == "__main__":
    main()
