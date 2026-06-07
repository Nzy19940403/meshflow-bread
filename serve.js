const http = require('http');
const fs = require('fs');
const path = require('path');
const mime = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.json': 'application/json',
};
http.createServer((req, res) => {
  let url = req.url === '/' ? '/index.html' : req.url;
  // Strip query string
  url = url.split('?')[0];
  const filePath = path.join(__dirname, 'dist', url);
  try {
    const content = fs.readFileSync(filePath);
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': mime[ext] || 'text/plain' });
    res.end(content);
  } catch (e) {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found: ' + url);
  }
}).listen(8082, () => {
  console.log('Static server: http://localhost:8082');
});
