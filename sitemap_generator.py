import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import threading
import email.utils
import pytz

# Global configuration variables
MAX_DEPTH = 10
DOMAIN = 'www.example.com'
MAX_WORKERS = 5
OUTPUT_FILENAME = 'sitemap.xml'
START_URL = 'https://www.example.com/home'
USE_TIME_FILTER = True
TIME_FILTER_THRESHOLD = datetime(2022, 9, 20, tzinfo=pytz.UTC)

# Initialize XML
urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

# Set to keep track of visited URLs
visited_urls = set()

# Lock to ensure thread safety
lock = threading.Lock()

# Requests session for connection pooling
session = requests.Session()

def process_page(url, lastmod):
    """
    Adds page details to the sitemap
    """
    with lock: # Protecting the critical section with a lock
        url_element = ET.SubElement(urlset, 'url')
        ET.SubElement(url_element, 'loc').text = url
        ET.SubElement(url_element, 'lastmod').text = lastmod.isoformat()
        ET.SubElement(url_element, 'changefreq').text = 'daily'
        ET.SubElement(url_element, 'priority').text = '1.0'

# Function to generate the sitemap
def generate_sitemap(url, max_depth=MAX_DEPTH, depth=0):
    if depth > max_depth:
        return

    try:
        # Fetch the content of the page
        response = session.get(url)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return

    if response.status_code != 200:
        print(f"Failed to retrieve {url}, status code: {response.status_code}")
        return

    # Using lxml parser for faster parsing
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
    base_url = url
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href.startswith('#'):
            full_url = urljoin(base_url, href)
            domain = urlparse(full_url).netloc
            with lock: # Protecting the critical section with a lock
                if full_url not in visited_urls and domain == DOMAIN:
                    visited_urls.add(full_url)
                    links_to_process.append(full_url)

    # Use multithreading to process links
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(generate_sitemap, links_to_process, [max_depth] * len(links_to_process), [depth + 1] * len(links_to_process))

# Start generating the sitemap
generate_sitemap(START_URL)

# Write the generated sitemap to a file
tree = ET.ElementTree(urlset)
tree.write(OUTPUT_FILENAME, encoding='utf-8', xml_declaration=True)
