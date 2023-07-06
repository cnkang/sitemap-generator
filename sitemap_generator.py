"""
Sitemap Generator Script.

This script is used to generate a sitemap by crawling the links of a given website.
"""

import email.utils
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import urllib.robotparser
import urllib.request
from urllib.error import URLError
import html.parser

# Global configuration variables

# AWS S3 bucket and key configuration
S3_BUCKET = 'example-s3-bucket'
S3_KEY = '/path/to/sitemap.xml'

# Set global variable RUN_LOCALLY
RUN_LOCALLY = 'False'

# Maximum depth of links to traverse
MAX_DEPTH = 10

# Only links from this domain will be included in the sitemap
DOMAIN = 'www.example.com'

# Maximum number of threads used for parallel processing
MAX_WORKERS = 5

# The file name of the generated sitemap
OUTPUT_FILENAME = 'tmp/sitemap.xml'

# The initial URL to start crawling from
START_URL = 'https://www.example.com/home'

# Whether to filter pages by modification time
USE_TIME_FILTER = True

# Only include pages modified after this date
TIME_FILTER_THRESHOLD = datetime(2022, 9, 20, tzinfo=timezone.utc)

# Whether to respect the rules in robots.txt
RESPECT_ROBOTS_TXT = True

# Initialize XML
urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

# Set to keep track of visited URLs
visited_urls = set()

# Lock to ensure thread safety
lock = threading.Lock()

# Initialize robots.txt parser
rp = urllib.robotparser.RobotFileParser()
rp.set_url(urljoin(START_URL, '/robots.txt'))
rp.read()

class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.links.append(attr[1])

def save_to_s3(filename):
    """
    Uploads the sitemap to S3.
    """
    import boto3
    s3_client = boto3.client('s3')
    
    with open(filename, 'rb') as file:
        s3_client.upload_fileobj(file, S3_BUCKET, S3_KEY)

def main():
    # Start generating the sitemap
    generate_sitemap(START_URL)

    # Upload sitemap to S3 or save it locally
    if RUN_LOCALLY:
        print(f"Sitemap saved to {OUTPUT_FILENAME}")
    else:
        save_to_s3(OUTPUT_FILENAME)
        print(f"Sitemap uploaded to S3: {S3_BUCKET}/{S3_KEY}")
# AWS Lambda handler function
def lambda_handler(event, context):
    main()
    return {
        'statusCode': 200,
        'body': 'Sitemap generation complete.'
    }



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
        response = urllib.request.urlopen(url)
    except URLError as exc:
        print(f"Error fetching {url}: {exc}")
        return

    # Short circuit if not a successful response
    if response.status != 200:
        print(f"Failed to retrieve {url}, status code: {response.status}")
        return

    # Parsing page contents
    parser = LinkParser()
    parser.feed(response.read().decode())

    # Retrieve the last modification time
    lastmod_str = response.headers.get('last-modified', datetime.now().isoformat())
    lastmod = email.utils.parsedate_to_datetime(lastmod_str)

    # Check last modification time if the filter is enabled
    if USE_TIME_FILTER and lastmod <= TIME_FILTER_THRESHOLD:
        return

    process_page(url, lastmod)

    # Collect and recursively process links
    links_to_process = []
    for href in parser.links:
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


# If running this script locally, call the main function
if __name__ == "__main__":
    main()