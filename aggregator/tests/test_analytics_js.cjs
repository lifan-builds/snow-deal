const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('aggregator/aggregator/web/static/analytics.js', 'utf8');
function browser({gpc=false, path='/products/model', search='?q=private%40example.com&utm_source=x&utm_campaign=2026_winter'}={}) {
  const calls=[]; const storage=new Map(); const listeners={}; const win={};
  vm.runInNewContext(code, {
    window:win, navigator:{globalPrivacyControl:gpc}, location:{pathname:path,search,hostname:'freshpowder.clifan.com'},
    URL, URLSearchParams, Promise, Set,
    document:{referrer:'https://other.example/?token=secret',body:{addEventListener:(name,fn)=>listeners[name]=fn},querySelector:()=>null},
    sessionStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},
    fetch:async(url,options)=>{calls.push({url,body:JSON.parse(options.body)});return {ok:true};},
  });
  return {calls,win,listeners};
}
test('records a page before its click, without raw query or full referrer',async()=>{
  const b=browser(); await b.win.fpTrack('click',{deal_url:'https://merchant.example/product'});
  assert.deepEqual(b.calls.map(c=>c.body.event_type),['page_view','click']);
  const meta=JSON.parse(b.calls[0].body.metadata);
  assert.equal(meta.source,'x'); assert.equal(meta.campaign,'2026_winter');
  assert.ok(!JSON.stringify(b.calls).includes('private')); assert.ok(!JSON.stringify(b.calls).includes('secret'));
});
test('GPC and private URLs do not initialize tracking',()=>{
  for(const options of [{gpc:true},{path:'/alerts/remove/private-token'},{path:'/admin/stats'},{search:'?admin_key=private'}]) {
    const b=browser(options); assert.equal(b.win.fpTrack,undefined); assert.equal(b.calls.length,0);
  }
});
