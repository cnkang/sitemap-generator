"""
Sitemap Generator Script.

This script is used to generate a sitemap by crawling the links of a given website.
"""

import email.utils
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urljoin, urlparse
import urllib.robotparser

import pytz
import requests
from bs4 import BeautifulSoup


# Global configuration variables

# Maximum depth of links to traverse
MAX_DEPTH = 10

# Only links from this domain will be included in the sitemap
DOMAIN = 'www.example.com'

# Maximum number of threads used for parallel processing
MAX_WORKERS = 5

# The file name of the generated sitemap
OUTPUT_FILENAME = 'sitemap.xml'

# The initial URL to start crawling from
START_URL = 'https://www.example.com/home'

# Whether to filter pages by modification time
USE_TIME_FILTER = True

# Only include pages modified after this date
TIME_FILTER_THRESHOLD = datetime(2022, 9, 20, tzinfo=pytz.UTC)

# Whether to respect the rules in robots.txt
RESPECT_ROBOTS_TXT = True

# Initialize XML
urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

# Set to keep track of visited URLs
visited_urls = set()

# Lock to ensure thread safety
lock = threading.Lock()

# Requests session for connection pooling
session = requests.Session()

# Initialize robots.txt parser
rp = urllib.robotparser.RobotFileParser()
rp.set_url(urljoin(START_URL, '/robots.txt'))
rp.read()


def can_fetch(url):
    """Return whether we can fetch the URL according to the robots.txt."""
    if RESPECT_ROBOTS_TXT:
        return rp.can_fetch('*', url)
    return True


def process_page(url, lastmod):
    """
    Adds page details to the sitemap.
    """
    with lock:  # Protecting the critical section with a lock
        url_element = ET.SubElement(urlset, 'url')
        ET.SubElement(url_element, 'loc').text = url
        ET.SubElement(url_element, 'lastmod').text = lastmod.isoformat()
        ET.SubElement(url_element, 'changefreq').text = 'daily'
        ET.SubElement(url_element, 'priority').text = '1.0'


def generate_sitemap(url, max_depth=MAX_DEPTH, depth=0):
    """
    Generates the sitemap by recursively crawling the links found in the pages.
    """
    if depth > max_depth or not can_fetch(url):
        return

    try:
        # Fetch the content of the page
        response = session.get(url)
    except requests.RequestException as exc:
        print(f"Error fetching {url}: {exc}")
        return

    # Short circuit if not a successful response
    if response.status_code != 200:
        print(f"Failed to retrieve {url}, status code: {response.status_code}")
        return

    # Parsing page contents
    soup = BeautifulSoup(response.content, 'lxml')

    # Retrieve the last modification time
    lastmod_str = response.headers.get('last-modified', datetime.now().isoformat())
    lastmod = email.utils.parsedate_to_datetime(lastmod_str)

    # Check last modification time if the filter is enabled
    if USE_TIME_FILTER and lastmod <= TIME_FILTER_THRESHOLD:
        return

    process_page(url, lastmod)

    # Collect and recursively process links
    links_to_process = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href.startswith('#'):
            full_url = urljoin(url, href)
            with lock:  # Protecting the critical section with a lock
                if full_url not in visited_urls and urlparse(full_url).netloc == DOMAIN:
                    visited_urls.add(full_url)
                    links_to_process.append(full_url)

    # Use multithreading to process links
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        params = ([max_depth] * len(links_to_process), [depth + 1] * len(links_to_process))
        executor.map(generate_sitemap, links_to_process, *params)

    # Write the generated sitemap to a file
    tree = ET.ElementTree(urlset)
    tree.write(OUTPUT_FILENAME, encoding='utf-8', xml_declaration=True)


if __name__ == "__main__":
    # Start generating the sitemap
    generate_sitemap(START_URL)
