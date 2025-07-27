import asyncio
import scrapy
from datetime import datetime
from scrapy_playwright.page import PageMethod


class ClimbingSpider(scrapy.Spider):
    name = "climbing"
    start_urls = [
        # "https://climpingrose.com",
        # "https://climpingrose.com/feedbacks",
        # "https://climpingrose.com/cart",
        # "https://climpingrose.com/payment-instruction",
        # "https://climpingrose.com/paintings/phong-c-nh-ph-t-quan-th-m-b-t-c-20250626151336",
        "https://climpingrose.com/payment?orderId=88cf1864-7d96-453c-8cb4-8e09ad244593"
    ]

    def start_requests(self):
        self.logger.info(f"🟡 start_urls count: {len(self.start_urls)}")
        for url in self.start_urls:
            self.logger.info(f"🔍 Crawling: {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_selector", "body")],
                    "playwright_page_options": {
                        "wait_until": "domcontentloaded",
                        "timeout": 20000
                    },
                },
                errback=self.errback
            )

    def parse(self, response):
        self.logger.info(f"📄 Crawled: {response.url}")

        # Nếu bật playwright_include_page thì mới cần close
        page = response.meta.get("playwright_page")
        if page:
            page.close()

        yield {
            "url": response.url,
            "title": response.css("title::text").get(),
            "timestamp": datetime.now().isoformat(),
            "text": " ".join(response.css("body *:not(script):not(style):not(noscript)::text").getall()).strip()
        }

    def errback(self, failure):
        self.logger.error(f"❌ Request failed: {failure.request.url}")
        self.logger.error(repr(failure))
