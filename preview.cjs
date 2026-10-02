// Run with: node preview.cjs
// Open http://127.0.0.1:4173/program_materials.html (not the file:// version).
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');

const types = {
  '.html': 'text/html; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.pdf': 'application/pdf',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp'
};

http.createServer(async (request, response) => {
  response.setHeader('Cache-Control', 'no-store');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  if (!['GET', 'HEAD'].includes(request.method)) {
    response.writeHead(405, { Allow: 'GET, HEAD' }).end();
    return;
  }
  try {
    const name = decodeURIComponent(new URL(request.url, 'http://localhost').pathname).slice(1) || 'index.html';
    // This static site uses root-level assets. Never expose directories or code.
    if (name.includes('/') || name.includes('\\') || name.includes(':') || name.startsWith('.') || !types[path.extname(name)]) {
      response.writeHead(404).end();
      return;
    }
    const content = await fs.readFile(path.join(__dirname, name));
    response.writeHead(200, { 'Content-Type': types[path.extname(name)] });
    response.end(request.method === 'HEAD' ? undefined : content);
  } catch {
    response.writeHead(404).end();
  }
}).listen(4173, '127.0.0.1', () => {
  console.log('Program Materials preview: http://127.0.0.1:4173/program_materials.html');
  console.log('Edit weekoftheprogram.txt and refresh the page to apply changes.');
});
