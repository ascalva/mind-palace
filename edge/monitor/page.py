"""The dashboard's static HTML/CSS/JS template (an embedded asset, not logic).

Kept separate from `server.py` so the server's Python stays fully lint-covered while these long
asset lines are exempted (E501) in one asset-only place (see pyproject per-file-ignores).
`render_dashboard` fills `{{BODY}}` and `{{GEN}}`.
"""

from __future__ import annotations

CHAT = """
<div class="panel">
  <h2>Talk to it</h2>
  <div id="log" class="log"></div>
  <form id="chat" onsubmit="return send(event)">
    <input id="msg" autocomplete="off" placeholder="ask, recall, or capture a thought…" />
    <button type="submit">Send</button>
  </form>
</div>
<script>
async function send(e){
  e.preventDefault();
  const i=document.getElementById('msg'), log=document.getElementById('log');
  const text=i.value.trim(); if(!text) return false;
  add(log,'you',text); i.value=''; i.disabled=true;
  try{
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text})});
    const j=await r.json(); add(log,'palace', j.reply || j.error || '(no reply)');
  }catch(err){ add(log,'palace','(could not reach the monitor)'); }
  i.disabled=false; i.focus(); return false;
}
function add(log,who,text){
  const d=document.createElement('div'); d.className='turn '+who;
  d.innerHTML='<b>'+who+':</b> '+text.replace(/&/g,'&amp;').replace(/</g,'&lt;');
  log.appendChild(d); log.scrollTop=log.scrollHeight;
}
async function refresh(){
  try{ const r=await fetch('/status.json'); const s=await r.json();
    if(s && s.generated_at){ document.getElementById('gen').textContent=s.generated_at; } }catch(e){}
}
setInterval(refresh, 5000);
</script>
"""

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mind-palace</title>
<style>
:root{color-scheme:dark}
body{font:15px/1.5 -apple-system,system-ui,sans-serif;margin:0;background:#0e1116;color:#d7dce3}
header{padding:18px 22px;border-bottom:1px solid #232934;display:flex;
  justify-content:space-between;align-items:baseline}
header h1{font-size:18px;margin:0;letter-spacing:.3px}
.muted{color:#7a8595}.sub{color:#7a8595;font-size:12px}
main{padding:22px;max-width:920px;margin:0 auto}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.card{background:#161b22;border:1px solid #232934;border-radius:10px;padding:14px}
.card .label{color:#7a8595;font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.card .value{font-size:20px;margin-top:6px}
.pill{padding:3px 10px;border-radius:999px;font-size:14px}
.pill.ok{background:#0f3d2e;color:#5fe3a1}.pill.warn{background:#3d340f;color:#e3c95f}
.pill.bad{background:#3d1414;color:#ff8a8a}
.panel{background:#161b22;border:1px solid #232934;border-radius:10px;padding:16px;margin-top:16px}
.panel h2{font-size:13px;text-transform:uppercase;letter-spacing:.5px;color:#7a8595;margin:0 0 10px}
.warnbox{border-color:#5a4a16}
ul{margin:0;padding:0;list-style:none}
.activity li{padding:5px 0;border-bottom:1px solid #1c222b}
.role{color:#8ab4ff}
.log{max-height:300px;overflow:auto;margin-bottom:10px}
.turn{padding:6px 0}.turn.you b{color:#8ab4ff}.turn.palace b{color:#5fe3a1}
form{display:flex;gap:8px}
input{flex:1;background:#0e1116;border:1px solid #232934;border-radius:8px;padding:10px;
  color:#d7dce3}
button{background:#1f6feb;border:0;border-radius:8px;color:#fff;padding:10px 16px;cursor:pointer}
</style></head><body>
<header><h1>🧠 mind-palace</h1>
<span class="sub">snapshot <span id="gen">{{GEN}}</span></span></header>
<main>{{BODY}}</main></body></html>"""
