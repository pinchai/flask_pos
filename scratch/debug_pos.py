import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Listen for console messages
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: [{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
        
        # Login
        print("Navigating to login page...")
        await page.goto("http://127.0.0.1:5000/login")
        await page.fill("input[name='username']", "admin")
        await page.fill("input[name='password']", "admin")
        print("Submitting login form...")
        await page.click("button[type='submit']")
        await page.wait_for_timeout(2000)
        
        # Go to POS page
        print("Navigating to POS page...")
        await page.goto("http://127.0.0.1:5000/admin/pos")
        await page.wait_for_timeout(2000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
