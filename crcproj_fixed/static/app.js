const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

// The dashboard must be served by Python (http://127.0.0.1:5000), not opened
// directly as a file or through VS Code Live Server. Using a relative /api path
// keeps the frontend and backend on the same origin.

async function fetchJson(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    throw new Error('Cannot connect to the Python backend. Start app.py and open http://127.0.0.1:5000');
  }

  const raw = await response.text();
  let data;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch (_) {
    throw new Error(`Backend returned a non-JSON response (HTTP ${response.status}). Make sure you opened the dashboard at http://127.0.0.1:5000, not index.html or Live Server.`);
  }

  if (!response.ok) {
    throw new Error(data?.error || `Request failed (HTTP ${response.status}).`);
  }
  if (!data) {
    throw new Error('Backend returned an empty response. Restart app.py and try again.');
  }
  return data;
}

document.addEventListener('DOMContentLoaded', () => {
  $('#today').textContent = new Date().toLocaleDateString(undefined, {day:'2-digit', month:'short', year:'numeric'});
  setupTabs(); setupSegments(); setupButtons(); loadAlgorithms(); loadHistory();
});

function setupTabs(){
  $$('.nav-btn').forEach(btn => btn.addEventListener('click', () => {
    $$('.nav-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active');
    $$('.tab-panel').forEach(p=>p.classList.remove('active')); $('#tab-'+btn.dataset.tab).classList.add('active');
    if(btn.dataset.tab==='history') loadHistory();
  }));
}

function setupSegments(){
  $$('#calc-input-type .seg').forEach(btn=>btn.addEventListener('click',()=>setCalcInput(btn.dataset.type)));
  $$('#verify-input-type .seg').forEach(btn=>btn.addEventListener('click',()=>setVerifyInput(btn.dataset.type)));
}
function setCalcInput(type){
  $$('#calc-input-type .seg').forEach(b=>b.classList.toggle('active',b.dataset.type===type));
  $('#calc-data-wrap').classList.toggle('hidden',type==='file'); $('#calc-file-wrap').classList.toggle('hidden',type!=='file');
  $('#calc-data-label').textContent = type==='binary' ? 'Binary data' : 'Text message';
  $('#calc-data').placeholder = type==='binary' ? 'Example: 101101' : 'Example: HELLO';
  $('.hint').textContent = type==='binary' ? 'Only 0 and 1 are accepted for binary mode.' : 'Text is converted to UTF-8 bytes before CRC processing.';
}
function setVerifyInput(type){
  $$('#verify-input-type .seg').forEach(b=>b.classList.toggle('active',b.dataset.type===type));
  $('#verify-text-fields').classList.toggle('hidden',type==='file'); $('#verify-file-fields').classList.toggle('hidden',type!=='file');
}

function setupButtons(){
  $('#calculate-btn').addEventListener('click', calculate);
  $('#verify-btn').addEventListener('click', verify);
}

async function calculate(){
  const type = $('#calc-input-type .seg.active').dataset.type;
  const fd = new FormData(); fd.append('input_type',type); fd.append('algorithm',$('#calc-algorithm').value);
  if(type==='file') { const file=$('#calc-file').files[0]; if(!file)return toast('Please select a file.', true); fd.append('file',file); }
  else fd.append('data',$('#calc-data').value);
  setBusy($('#calculate-btn'),true,'Calculating…');
  try{ const data=await fetchJson('/api/calculate',{method:'POST',body:fd}); if(!data.success) throw new Error(data.error || 'CRC calculation failed.'); showCalc(data); loadHistory(); }
  catch(e){ toast(e.message,true); } finally{setBusy($('#calculate-btn'),false,'Calculate CRC');}
}
function showCalc(d){
  $('#calc-placeholder').classList.add('hidden'); $('#calc-result').classList.remove('hidden'); $('#calc-status').textContent='CALCULATED'; $('#calc-status').className='status-badge good';
  $('#out-poly').textContent=d.polynomial; $('#out-crc').textContent=d.crc; $('#out-codeword').textContent=d.codeword; $('#out-bits').textContent=d.data_length_bits+' bits'; $('#out-crc-len').textContent=d.crc_length; $('#out-algo').textContent=d.algorithm;
}

async function verify(){
  const type=$('#verify-input-type .seg.active').dataset.type; const fd=new FormData(); fd.append('input_type',type); fd.append('algorithm',$('#verify-algorithm').value); fd.append('simulate_error',$('#simulate-error').checked?'true':'false');
  if(type==='file'){const a=$('#original-file').files[0],b=$('#backup-file').files[0]; if(!a||!b)return toast('Select both the original and backup files.', true); fd.append('original_file',a);fd.append('backup_file',b);}
  else {fd.append('original',$('#original').value);fd.append('received',$('#received').value);}
  setBusy($('#verify-btn'),true,'Verifying…');
  try{const d=await fetchJson('/api/verify',{method:'POST',body:fd});if(!d.success)throw new Error(d.error || 'Verification failed.');showVerify(d);loadHistory();}
  catch(e){ toast(e.message,true)}finally{setBusy($('#verify-btn'),false,'Verify Backup');}
}
function showVerify(d){
  const good=d.status==='NO ERROR DETECTED'; const box=$('#verify-status'); box.className='verification-status '+(good?'good':'bad'); $('#verify-status h2').textContent=d.status; $('#verify-status p').textContent=d.simulated_error?`Demonstration error injected at bit ${d.changed_index}.`:good?'The CRC check found no detected error.':'The CRC check detected a mismatch.'; $('#verify-status .verify-symbol').textContent=good?'✓':'!';
  $('#original-crc').textContent=d.original_crc||'—'; $('#backup-crc').textContent=d.backup_crc||d.received_crc||'—'; $('#verify-remainder').textContent=d.verification_remainder||'—'; $('#byte-match').textContent=d.byte_match?'MATCH':'DIFFERENT';
}

async function loadHistory(){
  try{
    const rows=await fetchJson('/api/history');
    const body=$('#history-body');
    if(!Array.isArray(rows) || !rows.length){body.innerHTML='<tr><td colspan="5" class="empty">No operations yet.</td></tr>';return}
    body.innerHTML=rows.map(x=>`<tr><td>${x.time}</td><td>${x.operation}</td><td>${x.algorithm}</td><td>${escapeHtml(x.filename||x.source)}</td><td><b>${escapeHtml(x.result)}</b></td></tr>`).join('');
  }catch(e){ console.warn(e.message); }
}
async function loadAlgorithms(){
  try{
    const d=await fetchJson('/api/algorithms');
    $('#algorithm-list').innerHTML=Object.entries(d).map(([k,v])=>`<div><b>${escapeHtml(k)}</b><code>${escapeHtml(v)}</code></div>`).join('');
  }catch(e){ console.warn(e.message); }
}
function setBusy(btn,busy,label){btn.disabled=busy;btn.querySelector('span').textContent=busy?'…':(label==='Verify Backup'?'✓':'→');btn.childNodes[0].textContent=label+' ';}
function toast(msg,error=false){let t=document.querySelector('.toast');if(!t){t=document.createElement('div');t.className='toast';document.body.appendChild(t)}t.textContent=msg;t.style.background=error?'#b52f43':'#15213a';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),4200)}
function escapeHtml(s){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
const style=document.createElement('style');style.textContent='.toast{position:fixed;right:24px;bottom:24px;color:white;padding:12px 16px;border-radius:9px;font:600 10px Inter,sans-serif;box-shadow:0 12px 30px rgba(0,0,0,.2);transform:translateY(15px);opacity:0;transition:.2s;z-index:99;max-width:520px}.toast.show{transform:none;opacity:1}button:disabled{opacity:.65;cursor:wait}';document.head.appendChild(style);
