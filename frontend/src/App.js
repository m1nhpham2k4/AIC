import React, { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

/* -------------------- ICONS (bạn đã có) -------------------- */
const FALLBACK_ICONS = [
  'airplane.png','apple.png','backpack.png','banana.png','baseball bat.png',
  'baseball glove.png','bus.png','car.png','cat.png','cell phone.png','dog.png',
  'giraffe.png','keyboard.png','knife.png','laptop.png','microwave.png',
  'motorcycle.png','pizza.png','potted plant.png','scissors.png','skateboard.png',
  'stop sign.png','suitcase.png','traffic light.png','train.png','umbrella.png'
];
const COLORS = ['Black','Blue','Brown','Gray','Green','Pink','Purple','Red','White'];
const TAGS = [
  '3d','abacus','accessory','accident','accordion','acorn','actor',
  'adjust','adult','aerial','air','alarm','alley','animal','apartment',
  'apron','arch','arm','art'
];

/* -------------------- BASES -------------------- */
const VIDEO_BASE = '/videos'; // junction -> Data_extraction/Videos_test
const MAP_BASE   = '/map-keyframes';   // junction -> Data_extraction/map-keyframes

/* -------------------- KEYFRAMES helpers -------------------- */
function splitPath(p) { return (p || '').split('/').filter(Boolean); }

function buildTree(flatObj) {
  const root = { name: 'Keyframes', path: '', type: 'folder', children: [] };
  const map = { '': root };
  Object.keys(flatObj || {}).forEach(key => {
    const parts = splitPath(key);
    let cur = '';
    parts.forEach((part, idx) => {
      const next = cur ? `${cur}/${part}` : part;
      const isLeaf = idx === parts.length - 1;
      if (!map[next]) {
        const node = { name: part, path: next, type: isLeaf ? 'leaf' : 'folder', children: [] };
        map[cur].children.push(node);
        map[next] = node;
      }
      cur = next;
      if (isLeaf) map[next].images = flatObj[key];
    });
  });
  const sortRec = (n) => {
    if (!n.children) return;
    n.children.sort((a,b) => (a.type !== b.type) ? (a.type === 'folder' ? -1 : 1) : a.name.localeCompare(b.name));
    n.children.forEach(sortRec);
  };
  sortRec(root);
  return root;
}

// Bỏ tiền tố 'Keyframes/' nếu có (để L01..L05 cùng cấp)
function normalizeManifestKeys(flat) {
  const out = {};
  for (const k of Object.keys(flat || {})) {
    const segs = k.split('/').filter(Boolean);
    if (segs[0] && segs[0].toLowerCase() === 'keyframes') segs.shift();
    out[segs.join('/')] = flat[k];
  }
  return out;
}

// Làm phẳng folder trung gian tên 'keyframes' trong UI
function flattenKeyframesFolder(node) {
  if (!node || !node.children) return node;
  node.children = node.children.map(flattenKeyframesFolder);
  const next = [];
  for (const c of node.children) {
    if (c.type === 'folder' && !c.images && c.name.toLowerCase() === 'keyframes') {
      next.push(...(c.children || []));
    } else next.push(c);
  }
  node.children = next;
  return node;
}

// Từ leaf path suy ra { level: 'L02', clip: 'L02_V001' }
function extractClipFromLeaf(leafPath) {
  if (!leafPath) return { level: null, clip: null };
  const parts = splitPath(leafPath);
  const clip = parts[parts.length - 1] || '';
  const m = clip.match(/^(L\d{2})_/i);
  const level = m ? m[1] : null;
  return { level, clip };
}

// Ứng viên đường dẫn video (có nơi là 'Videos_L02 video', nơi khác 'Videos_L02')
function candidateVideoUrls(level, clip) {
  if (!level || !clip) return [];
  const file = encodeURIComponent(`${clip}.mp4`);
  return [
    `${VIDEO_BASE}/Videos_${level}%20video/video/${file}`,
    `${VIDEO_BASE}/Videos_${level}/video/${file}`,
  ];
}

// Parse CSV map n,pts_time,fps,frame_idx
function parseMapCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const [n, pts_time, fps, frame_idx] = lines[i].split(',');
    if (!n) continue;
    rows.push({
      n: parseInt(n, 10),
      pts_time: parseFloat(pts_time),
      fps: parseFloat(fps),
      frame_idx: parseInt(frame_idx, 10),
    });
  }
  return rows;
}

// Lấy chỉ số từ tên file ảnh .../001.jpg -> 1
function keyframeIndexFromUrl(u) {
  const m = (u || '').match(/(\d+)\.(?:jpg|jpeg|png)$/i);
  return m ? parseInt(m[1], 10) : null;
}

/* -------------------- Sidebar Tree -------------------- */
function TreeNode({ node, open, onToggle, onSelect, selected }) {
  const isOpen = !!open[node.path];
  const isSel  = selected === node.path;

  if (node.type === 'leaf') {
    return (
      <li>
        <button
          className={`tree-leaf ${isSel ? 'is-active' : ''}`}
          title={node.path}
          onClick={() => onSelect(node.path)}
          type="button"
        >
          <span className="mr">🖼️</span>{node.name}
        </button>
      </li>
    );
  }

  return (
    <li>
      <div className="tree-folder" onClick={() => onToggle(node.path)} title={node.path || 'Keyframes'}>
        <span className="mr">{isOpen ? '▾' : '▸'}</span>📁 {node.name}
      </div>
      {isOpen && (
        <ul className="tree-children">
          {(node.children || []).map(c => (
            <TreeNode
              key={c.path}
              node={c}
              open={open}
              onToggle={onToggle}
              onSelect={onSelect}
              selected={selected}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

function KeyframesSidebar({ tree, selected, onSelect }) {
  const [open, setOpen] = useState({ '': true });

  useEffect(() => {
    if (!selected) return;
    const parts = splitPath(selected);
    let cur = '';
    const m = { '': true };
    for (let i = 0; i < parts.length - 1; i++) {
      cur = cur ? `${cur}/${parts[i]}` : parts[i];
      m[cur] = true;
    }
    setOpen(prev => ({ ...prev, ...m }));
  }, [selected]);

  const onToggle = (p) => setOpen(m => ({ ...m, [p]: !m[p] }));

  return (
    <div className="panel">
      <div className="panel-title">Keyframes</div>
      {!tree ? (
        <div className="muted">Loading...</div>
      ) : (
        <ul className="tree-root">
          <TreeNode node={tree} open={open} onToggle={onToggle} onSelect={onSelect} selected={selected} />
        </ul>
      )}
    </div>
  );
}

/* -------------------- MAIN APP -------------------- */
export default function App() {
  // Search controls (giữ nguyên)
  const items = useMemo(() => Array.from({ length: 30 }, (_, i) => ({ id: 100000 + i * 1234 })), []);
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    asr:false, ocr:false, open:false, eva:false,
    caption:false, nextScene:false, extra:true, noExtra:false,
  });

  const [colorQuery, setColorQuery] = useState('');
  const [tagQuery, setTagQuery] = useState('');
  const [selectedColors, setSelectedColors] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);

  function toggleColor(c) {
    setSelectedColors(prev => prev.includes(c) ? prev.filter(x=>x!==c) : [...prev, c]);
  }
  function toggleTag(t) {
    setSelectedTags(prev => prev.includes(t) ? prev.filter(x=>x!==t) : [...prev, t]);
  }


  function handleToggle(key){ setFilters(prev => ({ ...prev, [key]: !prev[key] })); }
  function handleSearch(){ console.log('Search:', { query, filters }); }
  function handleKeyDown(e){ if (e.key === 'Enter') handleSearch(); }

  const [active, setActive] = useState(null);

  // ICONS
  const [iconFiles, setIconFiles] = useState([]);
  const [objectQuery, setObjectQuery] = useState('');
  useEffect(() => {
    fetch(`${process.env.PUBLIC_URL}/objects/manifest.json`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(arr => Array.isArray(arr) ? setIconFiles(arr) : setIconFiles([]))
      .catch(() => setIconFiles([]));
  }, []);
  const iconsToShow = useMemo(() => {
    const list = iconFiles.length ? iconFiles : FALLBACK_ICONS;
    return list.filter(n => n.toLowerCase().includes(objectQuery.toLowerCase()));
  }, [iconFiles, objectQuery]);

  // KEYFRAMES state
  const [manifest, setManifest] = useState(null);
  const [kfTree, setKfTree] = useState(null);
  const [selectedKF, setSelectedKF] = useState('');
  const [errKF, setErrKF] = useState('');
  const [cols, setCols] = useState(6);

  // VIDEO state
  const [videoUrls, setVideoUrls] = useState([]); // candidates
  const [videoSrc, setVideoSrc]   = useState(''); // current src
  const videoRef = useRef(null);
  const [mapRows, setMapRows] = useState([]);     // CSV rows for seek

  // Load manifest & build tree
  useEffect(() => {
    fetch('http://localhost:8000/keyframes/manifest?_=' + Date.now())
      .then(res => { if (!res.ok) throw new Error('Cannot fetch /api/keyframes/manifest'); return res.json(); })
      .then(json => {
        const normalized = normalizeManifestKeys(json);
        setManifest(normalized);
        let t = buildTree(normalized);
        t = flattenKeyframesFolder(t);
        setKfTree(t);
        const findLeaf = (n) => !n ? '' : (n.type === 'leaf' ? n.path : ((n.children || []).map(findLeaf).find(Boolean) || ''));
        setSelectedKF(findLeaf(t));
      })
      .catch(e => setErrKF(String(e?.message || e)));
  }, []);

  // Khi đổi thư mục keyframes -> đoán video + load CSV map
  useEffect(() => {
    if (!selectedKF) { setVideoUrls([]); setVideoSrc(''); setMapRows([]); return; }
    const { level, clip } = extractClipFromLeaf(selectedKF);
    if (!level || !clip) { setVideoUrls([]); setVideoSrc(''); setMapRows([]); return; }

    fetch(`http://localhost:8000/keyframes/video?level=${encodeURIComponent(level)}&clip=${encodeURIComponent(clip)}&ttl=3600`)
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(data => {
      const urls = Array.isArray(data?.urls) ? data.urls : [];
      const fallback = candidateVideoUrls(level, clip);
      const all = urls.length ? urls : fallback;
      setVideoUrls(all);
      setVideoSrc(all[0] || '');
    })
    .catch(() => {
      const fallback = candidateVideoUrls(level, clip);
      setVideoUrls(fallback);
      setVideoSrc(fallback[0] || '');
    });
    // load CSV map
    fetch(`${MAP_BASE}/Keyframes_${level}/keyframes/${encodeURIComponent(clip)}.csv`)
      .then(r => r.ok ? r.text() : Promise.reject())
      .then(txt => setMapRows(parseMapCsv(txt)))
      .catch(() => setMapRows([]));
  }, [selectedKF]);

  // URL ảnh theo folder  
  const keyframeUrls = useMemo(
    () => (manifest && selectedKF ? manifest[selectedKF] : []),
    [manifest, selectedKF]
  );

  // Click ảnh -> seek video theo map CSV
  function handleThumbClick(u) {
    setActive(u);
    const idx = keyframeIndexFromUrl(u);
    if (!idx) return;
    const row = mapRows.find(r => r.n === idx);
    if (!row || !videoRef.current) return;

    const doSeek = () => {
      try {
        videoRef.current.currentTime = Math.max(0, row.pts_time || 0);
        videoRef.current.play().catch(() => {});
      } catch {}
    };

    if (videoRef.current.readyState >= 1) doSeek();
    else {
      const h = () => { doSeek(); videoRef.current.removeEventListener('loadedmetadata', h); };
      videoRef.current.addEventListener('loadedmetadata', h);
    }
  }

  // Nếu src hiện tại lỗi, chuyển sang candidate tiếp theo
  function onVideoError() {
    setVideoSrc(prev => {
      const i = videoUrls.indexOf(prev);
      const next = videoUrls[i + 1];
      return next || prev;
    });
  }

  return (
    <div className="app">
      {/* TOP BAR */}
      <header className="topbar">
        <div className="brand">THE KING</div>

        <div className="search-wrap">
          <input
            className="search-input"
            placeholder="Input query text here"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Search query"
          />
          <button id="search-btn" type="button" className="search-btn" aria-label="Run search" onClick={handleSearch}>
            Search
          </button>
        </div>

        <div className="toolbar">
          <div className="chip">100</div>
          {['asr','ocr','open','eva','caption','nextScene','extra','noExtra'].map(k => (
            <label key={k} className="chk">
              <input type="checkbox" checked={!!filters[k]} onChange={() => handleToggle(k)} /> {k}
            </label>
          ))}
          <button className="btn" type="button">Re-rank</button>
          <button className="btn ghost" type="button">Feedback</button>
          <div className="chip round">Q&A</div>
        </div>
      </header>

      {/* BODY */}
      <div className="layout">
        {/* LEFT: sidebar */}
        <aside className="left">
          <KeyframesSidebar tree={kfTree} selected={selectedKF} onSelect={setSelectedKF} />
          {errKF ? <div className="panel"><div className="error">{errKF}</div></div> : null}

          <div className="panel">
            <input className="input" placeholder="Search object..." value={objectQuery} onChange={(e) => setObjectQuery(e.target.value)} />
            <div className="icon-grid">
              {iconsToShow.map((name) => (
                <div key={name} className="icon-item" title={name.replace('.png','')}>
                  <img className="icon-img" src={`${process.env.PUBLIC_URL}/objects/${encodeURIComponent(name)}`} alt={name} loading="lazy" />
                  <div className="icon-txt">{name.replace('.png','')}</div>
                </div>
              ))}
            </div>
          </div>

          {/* COLORS */}
          <div className="panel">
            <input
              className="input"
              placeholder="Search color..."
              value={colorQuery}
              onChange={(e) => setColorQuery(e.target.value)}
            />
            <div className="color-row">
              {COLORS
                .filter(c => c.toLowerCase().includes(colorQuery.toLowerCase()))
                .map((c) => (
                  <button
                    key={c}
                    type="button"
                    title={c}
                    onClick={() => toggleColor(c)}
                    className={`swatch ${c.toLowerCase()} ${selectedColors.includes(c) ? 'on' : ''}`}
                  />
                ))}
            </div>
          </div>

          {/* TAGS */}
          <div className="panel">
            <input
              className="input"
              placeholder="Search tag..."
              value={tagQuery}
              onChange={(e) => setTagQuery(e.target.value)}
            />
            <div className="tag-list">
              {TAGS
                .filter(t => t.toLowerCase().includes(tagQuery.toLowerCase()))
                .map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => toggleTag(t)}
                    className={`tag-item ${selectedTags.includes(t) ? 'on' : ''}`}
                  >
                    {t}
                  </button>
                ))}
            </div>
          </div>

        </aside>

        {/* CENTER: grid ảnh keyframes */}
        <main className="center">
          <div className="panel">
            <div className="panel-title">
              {selectedKF ? `Folder: ${selectedKF}` : 'Select a folder on the left'}
              <span className="right muted">Images: {keyframeUrls.length}</span>
            </div>
            <div className="row">
              <label className="muted">Columns:</label>
              <input type="range" min="1" max="8" value={cols} onChange={(e)=>setCols(parseInt(e.target.value,10))} />
            </div>
            <div className="grid" style={{ gridTemplateColumns: `repeat(${Math.max(1, Math.min(8, cols))}, minmax(0, 1fr))` }}>
              {keyframeUrls.map((u, idx) => (
                <div key={u} className={`card ${active === u ? 'active' : ''}`} onClick={() => handleThumbClick(u)} title={u}>
                  <div className="thumb" style={{ paddingTop: '56%', position: 'relative', overflow: 'hidden' }}>
                    <img src={u} alt="" loading="lazy" style={{ position:'absolute', inset:0, width:'100%', height:'100%', objectFit:'cover' }} />
                  </div>
                  <div className="meta">
                    <span className="id">#{idx+1}</span>
                    <span className="icons"><span className="dot"/><span className="dot"/><span className="dot"/></span>
                  </div>
                </div>
              ))}
              {!keyframeUrls.length && items.map(v => (
                <div key={v.id} className="card"><div className="thumb" /></div>
              ))}
            </div>
          </div>
        </main>

        {/* RIGHT: Video player + info */}
        <aside className="right">
          <div className="detail">
            <div className="panel-title">Video</div>
            {videoSrc ? (
              <>
                <video
                  ref={videoRef}
                  src={videoSrc}
                  controls
                  onError={onVideoError}
                  style={{ width: '100%', height: 'auto', borderRadius: 8, outline: 'none' }}
                />
                <div className="muted" style={{ marginTop: 6, wordBreak: 'break-all' }}>
                  Source: <a href={videoSrc} target="_blank" rel="noreferrer">{videoSrc}</a>
                </div>
              </>
            ) : (
              <div className="muted">Chưa tìm thấy video cho thư mục này.</div>
            )}

            <div className="detail-row">
              <div className="k">Clip:</div>
              <div className="v">{extractClipFromLeaf(selectedKF).clip || '-'}</div>
            </div>
            <div className="detail-row">
              <div className="k">Map rows:</div>
              <div className="v">{mapRows.length}</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
