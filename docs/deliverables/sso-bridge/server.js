// SSO 跳板页本地联调静态服务
// 用途：把 sso-bridge/index.html 挂在本地端口，供钉钉 iframe 配置联调
// 启动：node server.js [端口]   默认 8090
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.argv[2]) || 8090;
const ROOT = path.join(__dirname, 'public');
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png', '.ico': 'image/x-icon'
};

http.createServer((req, res) => {
  const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  let filePath = path.normalize(path.join(ROOT, urlPath === '/' ? '/index.html' : urlPath));
  if (!filePath.startsWith(ROOT)) { res.writeHead(403); return res.end('Forbidden'); }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      // /oauth/home → 本地桩页面（联调用，真实环境该路径由 V8 前端处理）
      if (urlPath.startsWith('/oauth/home')) {
        return fs.readFile(path.join(ROOT, 'oauth-home-stub.html'), (e3, sbuf) => {
          if (e3) { res.writeHead(404); return res.end('Stub Not Found'); }
          res.writeHead(200, { 'Content-Type': MIME['.html'] });
          res.end(sbuf);
        });
      }
      // 其他未命中路径回落到跳板页，任意 /sso-bridge/xxx 都能进流程
      fs.readFile(path.join(ROOT, 'index.html'), (e2, buf) => {
        if (e2) { res.writeHead(404); return res.end('Not Found'); }
        res.writeHead(200, { 'Content-Type': MIME['.html'] });
        res.end(buf);
      });
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(PORT, '0.0.0.0', () => {
  console.log('[sso-bridge] serving ' + ROOT);
  console.log('[sso-bridge] URL: http://<本机IP>:' + PORT + '/sso-bridge/index.html?webUrl=%2Fmain%2Fportal&debug=1');
});