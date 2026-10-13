"""Simple local browser demo for the M4 single-agent baseline."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from .agent import GeneralistAgent
from .providers import LLMProvider, ProviderError
from .schema import ContractError

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hajj Risk Baseline</title>
<style>
*{box-sizing:border-box}body{font:15px/1.55 Arial,sans-serif;background:#f8f9fa;color:#27313b;margin:0}
main{max-width:720px;margin:45px auto;padding:0 18px}h1{font-size:25px;font-weight:600;margin:0 0 3px}
.sub{color:#66727b;font-size:13px;margin:0 0 22px}.card{background:#fff;border:1px solid #e1e5e8;border-radius:6px;padding:25px;margin:13px 0}
h2{font-size:16px;margin:0 0 15px;font-weight:600}label{font-size:13px;display:block;margin:0 0 7px;font-weight:600}
select{padding:10px;width:100%;font:inherit;background:white;border:1px solid #cbd2d8;border-radius:4px}
button{background:#344957;border:0;color:white;padding:11px 20px;border-radius:4px;font:inherit;cursor:pointer;margin-top:16px}
button:disabled{opacity:.5;cursor:wait}.data{font-size:13px;color:#53616b;margin:14px 0;line-height:1.8}
.result{font-size:21px;font-weight:600;margin:4px 0 10px}.action{font-weight:600;font-size:14px}
p{margin:9px 0}details{border-top:1px solid #eceef0;margin-top:20px;padding-top:12px}
summary{font-size:13px;color:#53616b;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;background:#f3f5f6;padding:12px;border-radius:4px}
table{width:100%;border-collapse:collapse;margin-top:12px}td,th{font-size:13px;text-align:left;border-bottom:1px solid #eef0f1;padding:7px}
ul{font-size:13px;padding-left:19px}.muted{color:#6c7882;font-size:13px}footer{color:#89939b;font-size:12px;margin-top:17px}
@media(max-width:520px){main{margin-top:22px}.card{padding:18px}}
</style></head><body><main>
<h1>Hajj Risk Baseline</h1><p class="sub">CPCS 683 · Single-agent demo</p>
<section class="card">
<h2>1. Select a case</h2>
<label for="samples">Example case</label>
<select id="samples">
<option value="case_high.json">High indicators</option>
<option value="case_medium.json">Mixed indicators</option>
<option value="case_low.json">Low indicators</option>
<option value="case_missing.json">Missing information</option>
<option value="case_conflict.json">Conflicting information</option>
</select>
<div id="overview" class="data"></div>
<button id="run">Run analysis</button>
<p class="muted" id="status" role="status"></p>
<details><summary>View all input fields</summary>
<table><thead><tr><th>Field</th><th>Value</th><th>Quality</th></tr></thead><tbody id="fields"></tbody></table>
</details>
</section>
<section class="card">
<h2>2. Result</h2>
<div id="result" class="muted">Run a case to see the result.</div>
<details><summary>Evidence and run information</summary>
<div id="evidence"></div><p id="trace" class="muted"></p>
<details><summary>Full JSON result</summary><pre id="raw"></pre></details>
</details>
</section>
<footer>Illustrative cases only. Not for real-world safety decisions.</footer>
</main><script>
const $=id=>document.getElementById(id);
const fields=[['crowd','density_people_per_m2','Crowd density','/m²'],['crowd','queue_minutes','Queue time','min'],['crowd','distance_km','Distance','km'],['health','fatigue_1_to_5','Fatigue','/5'],['health','stress_1_to_5','Stress','/5'],['health','emergency_event','Emergency event',''],['environment','temperature_c','Temperature','°C']];
let current=null,busy=false;
function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function value(o,u){return !o||o.value==null?'Missing':typeof o.value==='boolean'?(o.value?'Yes':'No'):String(o.value)+' '+u}
async function api(url,body){const r=await fetch(url,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
async function load(){
try{current=await api('/api/cases/'+$('samples').value);const x=current.domains;
$('overview').innerHTML='Crowd density: <b>'+esc(value(x.crowd.density_people_per_m2,'/m²'))+'</b> &nbsp; Temperature: <b>'+esc(value(x.environment.temperature_c,'°C'))+'</b> &nbsp; Emergency: <b>'+esc(value(x.health.emergency_event,''))+'</b>';
$('fields').innerHTML=fields.map(([d,f,label,u])=>'<tr><td>'+esc(label)+'</td><td>'+esc(value(x[d][f],u))+'</td><td>'+esc(x[d][f].quality)+'</td></tr>').join('');
$('result').className='muted';$('result').textContent='Run a case to see the result.';$('evidence').textContent='';$('trace').textContent='';$('raw').textContent='';$('status').textContent='';
}catch(e){$('status').textContent='Could not load case: '+e.message}
}
$('samples').addEventListener('change',load);
$('run').addEventListener('click',async()=>{
if(!current||busy)return;busy=true;$('run').disabled=true;$('status').textContent='Analyzing...';
try{const r=await api('/api/analyze',{case:current});const d=r.result.decision,t=r.result.trace;
$('result').className='';
$('result').innerHTML='<div class="result">'+esc(d.status==='ABSTAIN'?'More information needed':'Risk: '+d.risk_level)+'</div>'+
'<div class="action">'+esc(d.recommended_action.replaceAll('_',' '))+'</div><p>'+esc(d.summary)+'</p>'+
(d.verify_fields.length?'<p class="muted">Fields to check: '+esc(d.verify_fields.join(', '))+'</p>':'');
$('evidence').innerHTML='<p><b>Evidence used</b></p>'+(d.evidence_used.length?'<ul>'+d.evidence_used.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'<p class="muted">None</p>');
$('trace').textContent='Model: '+t.model+' · Calls: 1 · Time: '+(t.latency_ms_this_pass/1000).toFixed(1)+' s · Output valid: '+(t.schema_valid?'Yes':'No');
$('raw').textContent=JSON.stringify(r.result,null,2);$('status').textContent='Completed.';
}catch(e){$('status').textContent='Error: '+e.message}finally{busy=false;$('run').disabled=false}
});
load();
</script></body></html>'''


def make_handler(provider: LLMProvider):
    agent = GeneralistAgent(provider)

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, data, status=200):
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == "/":
                payload = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            elif self.path.startswith("/api/cases/"):
                name = self.path.removeprefix("/api/cases/")
                if name not in {p.name for p in EXAMPLES.glob("case_*.json")}:
                    return self.send_json({"error": "Case not found"}, 404)
                self.send_json(json.loads((EXAMPLES / name).read_text(encoding="utf-8")))
            else:
                self.send_json({"error": "Not found"}, 404)

        def do_POST(self):
            if self.path != "/api/analyze":
                return self.send_json({"error": "Not found"}, 404)
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 2_000_000:
                    return self.send_json({"error": "Invalid request size"}, 400)
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
                result = agent.evaluate(payload["case"])
                self.send_json({"result": result.as_dict()})
            except (ContractError, ValueError, KeyError, TypeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except ProviderError as exc:
                self.send_json({"error": str(exc)}, 503)

        def log_message(self, fmt, *args):
            print("[webapp]", fmt % args)

    return Handler


def main():
    provider = LLMProvider()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), make_handler(provider))
    print("Hajj Risk Baseline: http://127.0.0.1:8765")
    print("Model: " + provider.model + ". Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
