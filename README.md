# Sitemap Generator

This script is used to generate a sitemap for a given website. It crawls the website recursively up to a specified depth and creates an XML sitemap which includes the URLs of the pages on the website.

## Features

- Recursive crawling
- Multithreading for improved performance
- Optional filtering by page last modification time
- Thread-safe
- Generates sitemap in standard XML format

## Requirements

- Python 3.6 or higher

## Dependencies

- requests
- beautifulsoup4
- lxml
- pytz

## Installation

To install the necessary dependencies, run the following command:
```
pip install requests beautifulsoup4 lxml pytz
```

## Usage

Before running the script, you need to configure the following global variables at the beginning of the script according to your requirements:

- `MAX_DEPTH`: Maximum depth of links to traverse. Default is 10.
- `DOMAIN`: Only links from this domain will be included in the sitemap. For example: 'www.example.com'.
- `MAX_WORKERS`: Maximum number of threads used for parallel processing. Default is 5.
- `OUTPUT_FILENAME`: The filename of the generated sitemap. Default is 'sitemap.xml'.
- `START_URL`: The initial URL to start crawling from. For example: 'https://www.example.com/home'.
- `USE_TIME_FILTER`: Whether to filter pages by modification time. Set to `True` or `False`. Default is `True`.
- `TIME_FILTER_THRESHOLD`: Only include pages modified after this date. It is a `datetime` object. Default is `datetime(2022, 9, 20, tzinfo=pytz.UTC)`.

Once you have configured these variables, you can run the script by executing it with Python:
```
python sitemap_generator.py
```

This will create a sitemap XML file with the name specified in `OUTPUT_FILENAME`.

## Note

- Be cautious with increasing the number of workers (`MAX_WORKERS`) as it can lead to aggressively crawling websites, which might be considered impolite or even violate some websites' terms of service.
- Make sure the domain and starting URL are set correctly. Otherwise, the script will not generate a meaningful sitemap.


