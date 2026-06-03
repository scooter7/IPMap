"""HTML template for the Colorado click->employer GIS dashboard.

Placeholders (replaced by build_colorado_map.py):
  /*__POINTS__*/       - array of IP click points (each matched to nearest employer)
  /*__EMPLOYERS__*/    - array of geocoded employers (target locations)
  /*__EMP_SUMMARY__*/  - [[employer, clicks, ips], ...] sorted by clicks
  /*__STATS__*/        - header stat counts
"""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Colorado Clicks &rarr; Employer Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e4e8; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
  header { background: #161b22; border-bottom: 1px solid #30363d; padding: 10px 20px; display: flex; align-items: center; gap: 18px; flex-shrink: 0; flex-wrap: wrap; }
  header h1 { font-size: 16px; font-weight: 600; color: #f0f6fc; white-space: nowrap; }
  .stat { background: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 5px 12px; font-size: 12px; color: #8b949e; white-space: nowrap; }
  .stat span { color: #58a6ff; font-weight: 700; font-size: 14px; }
  .main { display: flex; flex: 1; overflow: hidden; }
  #map { flex: 1; }
  .sidebar { width: 460px; background: #161b22; border-left: 1px solid #30363d; display: flex; flex-direction: column; flex-shrink: 0; }
  .tabs { display: flex; border-bottom: 1px solid #30363d; }
  .tab { flex: 1; padding: 10px; text-align: center; font-size: 12px; font-weight: 600; color: #8b949e; cursor: pointer; border-bottom: 2px solid transparent; user-select: none; }
  .tab:hover { color: #f0f6fc; }
  .tab.active { color: #58a6ff; border-bottom-color: #58a6ff; }
  .controls { padding: 10px 14px; border-bottom: 1px solid #30363d; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .controls input, .controls select { background: #0d1117; border: 1px solid #30363d; color: #e1e4e8; border-radius: 6px; padding: 6px 9px; font-size: 12px; }
  #search { flex: 1; min-width: 130px; }
  .controls input:focus, .controls select:focus { outline: none; border-color: #58a6ff; }
  .controls label { font-size: 11px; color: #8b949e; display: flex; align-items: center; gap: 5px; }
  #download-btn { background: #238636; border: 1px solid #2ea043; color: #fff; border-radius: 6px; padding: 6px 11px; font-size: 12px; cursor: pointer; white-space: nowrap; }
  #download-btn:hover { background: #2ea043; }
  .result-count { font-size: 11px; color: #8b949e; padding: 6px 14px 0; }
  .table-wrap { overflow-y: auto; flex: 1; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  thead th { position: sticky; top: 0; background: #21262d; padding: 8px 10px; text-align: left; color: #8b949e; font-weight: 600; border-bottom: 1px solid #30363d; cursor: pointer; user-select: none; white-space: nowrap; z-index: 5; }
  thead th:hover { color: #f0f6fc; }
  thead th.sorted { color: #58a6ff; }
  tbody tr { border-bottom: 1px solid #21262d; cursor: pointer; }
  tbody tr:hover { background: #21262d; }
  tbody tr.active { background: #1c2a3e; }
  td { padding: 7px 10px; vertical-align: middle; }
  td.ip { font-family: 'Courier New', monospace; color: #79c0ff; white-space: nowrap; font-size: 11px; }
  td.clicks { font-weight: 700; text-align: right; white-space: nowrap; width: 48px; }
  td.clicks .badge { display: inline-block; background: #2ea04322; color: #56d364; border: 1px solid #2ea04344; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 700; }
  td.emp { max-width: 230px; }
  td.emp .name { color: #f0f6fc; font-size: 11px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  td.emp .addr { color: #adbac7; font-size: 10px; margin-top: 1px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  td.emp .meta { color: #8b949e; font-size: 10px; margin-top: 1px; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
  .c-high  { background: #3fb950; } .c-medium { background: #d29922; }
  .c-low   { background: #db6d28; } .c-very-low { background: #f85149; } .c-none { background: #6e7681; }
  .conf-label { font-size: 10px; text-transform: capitalize; }
  .legend { position: absolute; bottom: 18px; left: 12px; background: rgba(22,27,34,0.92); border: 1px solid #30363d; border-radius: 8px; padding: 10px 12px; font-size: 11px; z-index: 1000; }
  .legend div { margin: 3px 0; color: #c9d1d9; }
  .legend b { color: #f0f6fc; display: block; margin-bottom: 5px; }
  .popup-ip { font-family: monospace; font-size: 13px; font-weight: 700; color: #1a6fb5; }
  .popup-emp { font-size: 13px; font-weight: 700; color: #111; margin-top: 4px; }
  .popup-detail { font-size: 11px; color: #555; margin-top: 2px; }
  .popup-clicks { font-size: 13px; font-weight: 700; color: #1a7f37; margin-top: 4px; }
  .popup-conf { font-size: 11px; margin-top: 4px; font-weight: 600; }
</style>
</head>
<body>
<header>
  <h1>&#127758; Colorado Clicks &rarr; Employer Map</h1>
  <div class="stat">Total Clicks <span id="s-clicks"></span></div>
  <div class="stat">Total Impressions <span id="s-impr"></span></div>
  <div class="stat">Unique IPs <span id="s-ips"></span></div>
  <div class="stat">Mapped <span id="s-mapped"></span></div>
  <div class="stat">Employers <span id="s-emp"></span></div>
  <div class="stat">Matched <span id="s-matched"></span></div>
</header>
<div class="main">
  <div id="map">
    <div class="legend">
      <b>Match confidence (IP&nbsp;&rarr;&nbsp;employer)</b>
      <div><span class="dot c-high"></span>High &mdash; within 2&nbsp;km</div>
      <div><span class="dot c-medium"></span>Medium &mdash; 2&ndash;10&nbsp;km</div>
      <div><span class="dot c-low"></span>Low &mdash; 10&ndash;40&nbsp;km</div>
      <div><span class="dot c-very-low"></span>Very low &mdash; &gt;40&nbsp;km</div>
    </div>
  </div>
  <div class="sidebar">
    <div class="tabs">
      <div class="tab active" data-tab="ips">Clicks by IP</div>
      <div class="tab" data-tab="emps">By Employer</div>
    </div>
    <div class="controls">
      <input id="search" type="text" placeholder="Search IP / employer / city..."/>
      <select id="conf-filter" title="Filter by match confidence">
        <option value="">All confidence</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
        <option value="very-low">Very low</option>
      </select>
      <button id="download-btn">&#11015; CSV</button>
    </div>
    <div class="result-count" id="result-count"></div>
    <div class="table-wrap">
      <table id="ip-table">
        <thead id="thead-ips">
          <tr>
            <th data-col="ip">IP</th>
            <th data-col="employer">Matched Employer</th>
            <th data-col="impr">Impr</th>
            <th data-col="clicks" class="sorted">Clicks &#9660;</th>
          </tr>
        </thead>
        <thead id="thead-emps" style="display:none">
          <tr>
            <th data-col="employer">Employer</th>
            <th data-col="ips">IPs</th>
            <th data-col="impr">Impr</th>
            <th data-col="clicks" class="sorted">Clicks &#9660;</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const DATA = /*__POINTS__*/;
const EMPLOYERS = /*__EMPLOYERS__*/;
const EMP_SUMMARY = /*__EMP_SUMMARY__*/;
const STATS = /*__STATS__*/;

const fmtImpr = v => (v == null || v === 0) ? '—' : Number(v).toLocaleString();
document.getElementById('s-clicks').textContent  = STATS.total_clicks.toLocaleString();
document.getElementById('s-impr').textContent    = (STATS.total_impr || 0).toLocaleString();
document.getElementById('s-ips').textContent     = STATS.unique_ips.toLocaleString();
document.getElementById('s-mapped').textContent  = STATS.mapped_ips.toLocaleString();
document.getElementById('s-emp').textContent     = STATS.geocoded_employers.toLocaleString();
document.getElementById('s-matched').textContent = STATS.matched.toLocaleString();

const CONF_COLOR = { 'high':'#3fb950', 'medium':'#d29922', 'low':'#db6d28', 'very-low':'#f85149', 'none':'#6e7681' };
const CONF_LABEL = { 'high':'High', 'medium':'Medium', 'low':'Low', 'very-low':'Very low', 'none':'None' };

const map = L.map('map', { zoomControl: true, preferCanvas: true }).setView([39.0, -105.5], 7);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://carto.com/">CARTO</a>', maxZoom: 19
}).addTo(map);

// Employer (target) location layer — toggleable
const empLayer = L.layerGroup();
EMPLOYERS.forEach(e => {
  L.circleMarker([e.lat, e.lon], {
    radius: 5, fillColor: '#f0f6fc', color: '#8b949e', weight: 1, fillOpacity: 0.55
  }).bindPopup(`<div class="popup-emp">${e.name}</div><div class="popup-detail">${e.address}, ${e.city}, CO ${e.zip}</div><div class="popup-detail">Targeted employer location</div>`)
    .addTo(empLayer);
});

// Click markers, clustered
const markers = L.markerClusterGroup({
  maxClusterRadius: 45, showCoverageOnHover: false,
  iconCreateFunction: c => {
    const n = c.getChildCount();
    const size = n < 10 ? 36 : n < 50 ? 44 : 52;
    return L.divIcon({
      html: `<div style="width:${size}px;height:${size}px;background:#388bfd;border:2px solid #58a6ff;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">${n}</div>`,
      className: '', iconSize: [size, size]
    });
  }
});

const markerMap = {};
let connectLine = null;

DATA.forEach((d, i) => {
  d._id = i;
  const radius = Math.max(7, Math.min(22, 7 + d.clicks * 2.5));
  const color = CONF_COLOR[d.conf] || '#6e7681';
  const m = L.circleMarker([d.lat, d.lon], {
    radius, fillColor: color, color: '#0f1117', weight: 1, opacity: 1, fillOpacity: 0.8
  });
  const loc = [d.city, d.region].filter(Boolean).join(', ');
  m.bindPopup(`
    <div class="popup-ip">${d.ip}</div>
    <div class="popup-detail">${loc}${d.org ? ' &middot; ' + d.org : ''}</div>
    ${d.employer ? `<div class="popup-emp">${d.employer}</div><div class="popup-detail">${d.emp_addr}${d.emp_precision === 'zip' ? ' <i>(approx. ZIP-level)</i>' : ''}</div>` : ''}
    <div class="popup-clicks">&#128432; ${d.clicks} click${d.clicks !== 1 ? 's' : ''}</div>
    <div class="popup-conf" style="color:${color}">${CONF_LABEL[d.conf]} match${d.dist_mi != null ? ' &middot; ' + d.dist_mi + ' mi away' : ''}</div>
  `, { maxWidth: 320 });
  markers.addLayer(m);
  markerMap[i] = m;
});
map.addLayer(markers);

L.control.layers(null, { 'Click locations': markers, 'Targeted employers': empLayer }, { collapsed: false, position: 'topright' }).addTo(map);

function drawConnector(d) {
  if (connectLine) { map.removeLayer(connectLine); connectLine = null; }
  if (d.emp_lat != null) {
    connectLine = L.polyline([[d.lat, d.lon], [d.emp_lat, d.emp_lon]], {
      color: CONF_COLOR[d.conf], weight: 2, dashArray: '5,6', opacity: 0.8
    }).addTo(map);
  }
}

// ── Table state ───────────────────────────────────────────────────────────
let view = 'ips';
let sortCol = 'clicks', sortAsc = false, activeId = null;

function currentRows() {
  const q = document.getElementById('search').value.toLowerCase().trim();
  const cf = document.getElementById('conf-filter').value;
  if (view === 'ips') {
    let rows = DATA.filter(d => {
      if (cf && d.conf !== cf) return false;
      if (!q) return true;
      return d.ip.toLowerCase().includes(q)
        || (d.employer || '').toLowerCase().includes(q)
        || (d.city || '').toLowerCase().includes(q)
        || (d.org || '').toLowerCase().includes(q);
    });
    const kf = d => sortCol === 'ip' ? d.ip : sortCol === 'employer' ? (d.employer||'') : sortCol === 'impr' ? (d.impr||0) : d.clicks;
    rows.sort((a, b) => cmp(kf(a), kf(b)));
    return rows;
  } else {
    let rows = EMP_SUMMARY.slice();
    if (q) rows = rows.filter(r =>
      r.employer.toLowerCase().includes(q)
      || (r.address || '').toLowerCase().includes(q)
      || (r.city || '').toLowerCase().includes(q));
    const kf = d => sortCol === 'employer' ? d.employer : sortCol === 'ips' ? d.ips : sortCol === 'impr' ? (d.impr||0) : d.clicks;
    rows.sort((a, b) => cmp(kf(a), kf(b)));
    return rows;
  }
}
function cmp(av, bv) {
  if (av < bv) return sortAsc ? -1 : 1;
  if (av > bv) return sortAsc ? 1 : -1;
  return 0;
}

function render() {
  const rows = currentRows();
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';
  document.getElementById('result-count').textContent =
    view === 'ips'
      ? `${rows.length} IP${rows.length !== 1 ? 's' : ''} · ${rows.reduce((s,r)=>s+r.clicks,0)} clicks`
      : `${rows.length} employer${rows.length !== 1 ? 's' : ''} · ${rows.filter(r=>r.clicks>0).length} with matched clicks`;
  const frag = document.createDocumentFragment();
  rows.forEach(d => {
    const tr = document.createElement('tr');
    if (view === 'ips') {
      if (d._id === activeId) tr.classList.add('active');
      tr.innerHTML = `
        <td class="ip">${d.ip}</td>
        <td class="emp">
          <div class="name" title="${d.employer || '—'}">${d.employer || '—'}</div>
          <div class="addr" title="${d.emp_addr || ''}">${d.emp_addr || ''}${d.emp_precision === 'zip' ? ' (approx.)' : ''}</div>
          <div class="meta"><span class="dot c-${d.conf}"></span><span class="conf-label">${CONF_LABEL[d.conf]}</span>${d.dist_mi != null ? ' · ' + d.dist_mi + ' mi' : ''}</div>
        </td>
        <td class="clicks" style="color:#8b949e">${fmtImpr(d.impr)}</td>
        <td class="clicks"><span class="badge">${d.clicks}</span></td>`;
      tr.addEventListener('click', () => {
        activeId = d._id;
        document.querySelectorAll('#tbody tr').forEach(r => r.classList.remove('active'));
        tr.classList.add('active');
        const m = markerMap[d._id];
        if (m) { map.setView([d.lat, d.lon], 12, { animate: true }); markers.zoomToShowLayer(m, () => m.openPopup()); drawConnector(d); }
      });
    } else {
      const eaddr = [d.address, d.city, d.state, [d.zip, d.zip4].filter(Boolean).join('-')].filter(Boolean).join(', ');
      tr.innerHTML = `
        <td class="emp">
          <div class="name" title="${d.employer}">${d.employer}</div>
          <div class="addr" title="${eaddr}">${eaddr}</div>
        </td>
        <td class="clicks" style="color:#8b949e">${d.ips}</td>
        <td class="clicks" style="color:#8b949e">${fmtImpr(d.impr)}</td>
        <td class="clicks"><span class="badge">${d.clicks}</span></td>`;
      tr.addEventListener('click', () => {
        document.getElementById('search').value = d.employer;
        view = 'ips'; switchTabUI(); sortCol = 'clicks'; sortAsc = false; render();
      });
    }
    frag.appendChild(tr);
  });
  tbody.appendChild(frag);
  markHeader();
}

function markHeader() {
  const thead = document.getElementById(view === 'ips' ? 'thead-ips' : 'thead-emps');
  thead.querySelectorAll('th').forEach(th => {
    th.classList.toggle('sorted', th.dataset.col === sortCol);
    const base = th.textContent.replace(/[▲▼]/g, '').trim();
    th.innerHTML = th.dataset.col === sortCol ? base + ' ' + (sortAsc ? '▲' : '▼') : base;
  });
}

function bindHeader(id) {
  document.getElementById(id).querySelectorAll('th').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (sortCol === col) sortAsc = !sortAsc;
      else { sortCol = col; sortAsc = !['clicks','ips','impr'].includes(col); }
      render();
    });
  });
}
bindHeader('thead-ips'); bindHeader('thead-emps');

function switchTabUI() {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === (view === 'ips' ? 'ips' : 'emps')));
  document.getElementById('thead-ips').style.display = view === 'ips' ? '' : 'none';
  document.getElementById('thead-emps').style.display = view === 'emps' ? '' : 'none';
  document.getElementById('conf-filter').style.display = view === 'ips' ? '' : 'none';
}
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
  view = t.dataset.tab === 'ips' ? 'ips' : 'emps';
  sortCol = 'clicks'; sortAsc = false; activeId = null;
  switchTabUI(); render();
}));

document.getElementById('search').addEventListener('input', render);
document.getElementById('conf-filter').addEventListener('change', render);

document.getElementById('download-btn').addEventListener('click', () => {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  let headers, lines;
  if (view === 'ips') {
    headers = ['IP','Clicks','Impressions','Matched Employer (Company Name)','Employer Address','Employer City','Employer State','Employer Zip','Employer Zip4','Match Distance (mi)','Match Confidence','Employer Geocode Precision','IP City','IP Region','IP Org / ISP','IP Latitude','IP Longitude','Employer Latitude','Employer Longitude'];
    lines = currentRows().map(d => [d.ip, d.clicks, d.impr, d.employer, d.emp_address, d.emp_city, d.emp_state, d.emp_zip, d.emp_zip4, d.dist_mi, CONF_LABEL[d.conf], d.emp_precision, d.city, d.region, d.org, d.lat, d.lon, d.emp_lat, d.emp_lon].map(esc).join(','));
  } else {
    headers = ['Employer (Company Name)','Employer Address','Employer City','Employer State','Employer Zip','Employer Zip4','Matched IPs','Total Clicks','Total Impressions'];
    lines = currentRows().map(d => [d.employer, d.address, d.city, d.state, d.zip, d.zip4, d.ips, d.clicks, d.impr].map(esc).join(','));
  }
  const csv = [headers.join(','), ...lines].join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = view === 'ips' ? 'colorado_ip_employer_matches.csv' : 'colorado_clicks_by_employer.csv';
  a.click();
});

switchTabUI();
render();
</script>
</body>
</html>"""
