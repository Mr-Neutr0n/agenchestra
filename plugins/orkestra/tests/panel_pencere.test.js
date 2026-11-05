// node tests/panel_pencere.test.js — I-389: pencere seçimi tek depolama anahtarında; mod göstergeleri bağlı; konumsal dilim geri gelmez.
const fs = require('fs'), path = require('path'), assert = require('assert');
const dir = path.join(__dirname, '..', 'assets');
const app = fs.readFileSync(path.join(dir, 'app.js'), 'utf8'), gorsel = fs.readFileSync(path.join(dir, 'gorsel.js'), 'utf8');
// klasik sayfalar v2 anahtarını kullanır, alan başına anahtar kalmadı
assert(/PENCERE_ANAHTAR = \(\) => 'orkestra\.v2\.pencere'/.test(gorsel), 'gorsel.js v2 anahtarını kullanmalı');
assert(!/'orkestra\.pencere\./.test(gorsel.replace(/\/\/.*$/gm, '')), 'gorsel.js eski alan başına anahtarı kullanmamalı');
assert(/depo\.al\('orkestra\.v2\.pencere'\)/.test(app), 'app.js aynı anahtarı okumalı');
// gerileme koruması: günlük dizi konumla kesilmez
assert(!/gun\.slice\(-/.test(app), 'app.js günlük diziyi konumla kesmemeli');
// mod göstergeleri: üst çubuk rozeti, satır ve ayrıntı, ayar yolu temel kayıtlarda
assert(/\$\{g\.sag \|\| ''\}\$\{modRozeti\(\)\}/.test(app), 'üst çubukta mod rozeti olmalı');
assert(/modMini\(i\)/.test(app) && /modMini\(i, true\)/.test(app), 'satır ve ayrıntıda iş modu olmalı');
assert(/TEMEL = \[[^\]]*'\/api\/ayarlar'/.test(app), '/api/ayarlar temel kayıtlarda olmalı');
console.log('pencere/mod testleri: geçti');
