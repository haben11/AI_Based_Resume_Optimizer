import os
import asyncio
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from app.utils.cv_parser import parse_optimized_cv
from app.utils.template_factory import template_factory

async def generate_premium_pdf(markdown_content: str, template_id: str = "modern-1-blue") -> BytesIO:
    """
    Generates a high-fidelity PDF using Playwright and the Template Factory.
    """
    try:
        # 1. Parse Markdown to structured data
        structured_data = parse_optimized_cv(markdown_content)
        
        # 2. Render HTML via Template Factory
        html_content = template_factory.render(template_id, structured_data)

        # 3. Use Playwright to print to PDF
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set content and wait for Tailwind CDN to potentially load (though it's usually fast)
            await page.set_content(html_content, wait_until="networkidle")
            
            # Emulate screen for CSS rendering then print to PDF
            pdf_bytes = await page.pdf(
                format="Letter",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                display_header_footer=False
            )
            
            await browser.close()

        buffer = BytesIO(pdf_bytes)
        buffer.seek(0)
        return buffer
    except Exception as e:
        from app.core.logging import logger
        logger.error("pdf_generation_error", error=str(e), template_id=template_id)
        raise
