const https = require('https');
const fs = require('fs');

const cred = JSON.parse(fs.readFileSync('D:/software/多agent协助/agent-collaboration/shared-credentials/test2-web-credential.json', 'utf8'));
const cookie = (cred.cookie || '').trim();

const get = (path) => new Promise(res => {
  const r = https.request({
    hostname: 'lowcode-test2.changhongit.com', path, method: 'GET',
    headers: { 'Cookie': cookie, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/155.0.0.0 Safari/537.36', 'Accept': 'text/html,application/json,*/*' }
  }, x => {
    let d = ''; x.on('data', c => d += c);
    x.on('end', () => {
      const h = x.headers;
      res({
        status: x.statusCode,
        setCookie: (h['set-cookie'] || []).map(s => s.split('=')[0] + '=' + (s.split('=')[1] || '').slice(0, 6) + '...').slice(0, 4),
        loc: h.location || '',
        len: d.length,
        isSpaShell: /<div id="root">\s*<\/div>/.test(d) || /<script src=/.test(d) && d.length < 15000,
        hasLoginForm: /password|密码登录|login-form/i.test(d),
        hint: (d.match(/<title>([^<]*)<\/title>/) || [])[1] || '',
        head: d.slice(0, 180).replace(/\s+/g, ' ')
      });
    });
  });
  r.on('error', e => res({ status: 0, err: e.message })); r.end();
});

(async () => {
  // 1. 无 cookie 对照
  const anon = await new Promise(res => {
    const r = https.request({ hostname: 'lowcode-test2.changhongit.com', path: '/main/portal', method: 'GET', headers: { 'User-Agent': 'Mozilla/5.0' } }, x => {
      let d = ''; x.on('data', c => d += c); x.on('end', () => res({ status: x.statusCode, loc: x.headers.location || '', len: d.length }));
    }); r.on('error', e => res({ status: 0, err: e.message })); r.end();
  });
  console.log('ANON /main/portal :', JSON.stringify(anon));

  const a = await get('/main/portal');
  console.log('AUTH /main/portal :', JSON.stringify({ status: a.status, loc: a.loc, len: a.len, hint: a.hint, hasLoginForm: a.hasLoginForm, setCookie: a.setCookie }));

  const b = await get('/main/child-frame/udc/app-design/entity?appId=8704025620829192834');
  console.log('AUTH /app-design  :', JSON.stringify({ status: b.status, loc: b.loc, len: b.len, hint: b.hint, hasLoginForm: b.hasLoginForm, setCookie: b.setCookie }));
  console.log('DIFF_LEN portal_vs_appdesign:', Math.abs(a.len - b.len));
  process.exit(0);
})();
