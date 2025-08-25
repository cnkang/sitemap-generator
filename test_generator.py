#!/usr/bin/env python3
"""Simple test script for the sitemap generator."""

import os
import tempfile

from sitemap_generator import SitemapGenerator


def test_basic_functionality():
    """Test basic sitemap generation functionality."""
    # Set test environment variables
    os.environ.update(
        {
            "DOMAIN": "httpbin.org",
            "START_URL": "https://httpbin.org",
            "MAX_DEPTH": "1",
            "MAX_WORKERS": "2",
            "USE_TIME_FILTER": "false",
            "RESPECT_ROBOTS_TXT": "false",
        }
    )

    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        os.environ["OUTPUT_FILENAME"] = tmp.name

        try:
            generator = SitemapGenerator()
            success = generator.generate_sitemap()

            if success and os.path.exists(tmp.name):
                print(f"✅ Test passed! Sitemap generated: {tmp.name}")
                with open(tmp.name, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"Sitemap size: {len(content)} characters")
            else:
                print("❌ Test failed! No sitemap generated")

        finally:
            # Clean up
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


if __name__ == "__main__":
    test_basic_functionality()
