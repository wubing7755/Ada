// 临时 SPA 静态服务器：无扩展名路径回退 index.html，模拟 GitHub Pages 404.html 兜底行为。
// 用途：本地实测 Blazor WASM 发布产物（PublishTrimmed 后）的 SPA 子路由与资源加载。
// 用法：node spa-server.js <发布产物 wwwroot 目录> <端口>
//   例：node spa-server.js publish/wwwroot 5091
// python http.server 无 SPA 回退（/blog 返回 404 而非 index.html），不要用它验证发布产物。
const http = require('http');
const fs = require('fs');
const path = require('path');

const root = process.argv[2];
const port = Number(process.argv[3] || 5091);
const mime = {
    '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.wasm': 'application/wasm', '.dll': 'application/octet-stream',
    '.png': 'image/png', '.ico': 'image/x-icon', '.pdf': 'application/pdf',
    '.xml': 'application/xml', '.br': 'application/octet-stream', '.gz': 'application/gzip',
    '.blat': 'application/octet-stream', '.pdb': 'application/octet-stream',
    '.svg': 'image/svg+xml', '.woff': 'font/woff', '.woff2': 'font/woff2',
};

http.createServer((req, res) => {
    const urlPath = decodeURIComponent(req.url.split('?')[0]);
    let filePath = path.join(root, urlPath);
    if (urlPath === '/') filePath = path.join(root, 'index.html');

    fs.readFile(filePath, (err, data) => {
        if (!err) {
            res.writeHead(200, { 'Content-Type': mime[path.extname(filePath).toLowerCase()] || 'application/octet-stream' });
            res.end(data);
            return;
        }
        if (!path.extname(urlPath)) {
            fs.readFile(path.join(root, 'index.html'), (err2, index) => {
                if (!err2) { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(index); return; }
                res.writeHead(404); res.end('not found');
            });
            return;
        }
        res.writeHead(404); res.end('not found');
    });
}).listen(port, () => console.log(`SPA serving ${root} on ${port}`));
