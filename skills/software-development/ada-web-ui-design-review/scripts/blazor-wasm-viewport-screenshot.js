// Viewport-matrix screenshot + DOM assertion harness for web UI review.
// Works for Blazor WASM / SPA where `--headless --screenshot` captures only the loader page
// because the app bundle download is real network (not virtual time).
//
// Setup:   npm init -y && npm install puppeteer-core   (uses system Chrome, no Chromium download)
// Run:     node blazor-wasm-viewport-screenshot.js [baseUrl] [outDir]
// Example: node blazor-wasm-viewport-screenshot.js http://localhost:5088 /tmp/shots
const puppeteer = require('puppeteer-core');
const path = require('path');

// Adjust per OS: Windows Chrome / Edge, macOS, Linux chromium
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.argv[2] || 'http://localhost:5088';
const OUT = process.argv[3] || '.';

const viewports = [
  { name: 'mobile-320', width: 320, height: 700 },
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'mobile-430', width: 430, height: 932 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'laptop-1024', width: 1024, height: 768 },
  { name: 'desktop-1440', width: 1440, height: 900 },
];
const pages = ['/', '/about', '/projects'];

async function main() {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });

  for (const vp of viewports) {
    for (const pg of pages) {
      const page = await browser.newPage();
      await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
      try {
        await page.goto(BASE + pg, { waitUntil: 'networkidle2', timeout: 60000 });
        // KEY: wait for the app to render, not the loader. SPA/Blazor shows a loader div first.
        await page.waitForFunction(() => document.querySelector('main h1') !== null, { timeout: 45000 });
        await new Promise(r => setTimeout(r, 1200)); // settle after data load

        const info = await page.evaluate(() => ({
          overflowX: document.documentElement.scrollWidth > window.innerWidth,
          title: document.querySelector('main h1')?.textContent?.trim() ?? null,
        }));
        const file = path.join(OUT, `${vp.name}-${pg.replace('/', 'home')}.png`);
        await page.screenshot({ path: file, fullPage: true });
        console.log(`OK   ${vp.name} ${pg}: "${info.title}" | overflowX=${info.overflowX} | ${file}`);
      } catch (e) {
        console.log(`FAIL ${vp.name} ${pg}: ${e.message.slice(0, 140)}`);
      }
      await page.close();
    }
  }
  await browser.close();
}
main().catch(e => { console.error(e); process.exit(1); });
