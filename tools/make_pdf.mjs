// Print an HTML file to PDF with headless Chrome over the DevTools protocol.
// Usage: node tools/make_pdf.mjs <input.html> <output.pdf>
// (Plain `chrome --print-to-pdf` can hang on some Linux boxes; this route doesn't.)
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { pathToFileURL } from 'node:url';

const [input, output] = process.argv.slice(2);
if (!input || !output) { console.error('usage: node tools/make_pdf.mjs <input.html> <output.pdf>'); process.exit(2); }
const chromeBin = process.env.CHROME || 'google-chrome';
const port = 9400 + Math.floor(Math.random() * 400);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'pellory-pdf-'));
const chrome = spawn(chromeBin, ['--headless=new', '--no-sandbox', '--disable-gpu', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const done = (code) => { chrome.kill('SIGKILL'); fs.rmSync(profile, { recursive: true, force: true }); process.exit(code); };
setTimeout(() => { console.error('timed out'); done(1); }, 60000);

let wsUrl;
for (let i = 0; i < 100 && !wsUrl; i++) {
  try { const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); wsUrl = list.find((t) => t.type === 'page')?.webSocketDebuggerUrl; } catch {}
  if (!wsUrl) await sleep(150);
}
if (!wsUrl) { console.error('could not reach Chrome'); done(1); }
const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const waiting = {};
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && waiting[m.id]) { waiting[m.id](m); delete waiting[m.id]; } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; waiting[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });

await send('Page.enable');
await send('Page.navigate', { url: pathToFileURL(path.resolve(input)).href });
await sleep(1500);
await send('Runtime.evaluate', { expression: 'document.fonts.ready.then(() => true)', awaitPromise: true });
const res = await send('Page.printToPDF', { preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false });
if (!res.result) { console.error('printToPDF failed', JSON.stringify(res.error)); done(1); }
fs.writeFileSync(output, Buffer.from(res.result.data, 'base64'));
ws.close();
done(0);
