import React, { useEffect, useMemo, useState } from 'react'
import './App.css'

const FALLBACK_ICONS = [
  'airplane.png','apple.png','backpack.png','banana.png','baseball bat.png',
  'baseball glove.png','bus.png','car.png','cat.png','cell phone.png','dog.png',
  'giraffe.png','keyboard.png','knife.png','laptop.png','microwave.png',
  'motorcycle.png','pizza.png','potted plant.png','scissors.png','skateboard.png',
  'stop sign.png','suitcase.png','traffic light.png','train.png','umbrella.png'
]

export default function App() {
  // mock 30 items (lưới kết quả trung tâm)
  const items = useMemo(
    () => Array.from({ length: 30 }, (_, i) => ({ id: 100000 + i * 1234 })), []
  )

  const [query, setQuery] = useState('');
const [filters, setFilters] = useState({
  asr: false, ocr: false, open: false, eva: false,
  caption: false, nextScene: false, extra: true, noExtra: false,
});

function handleToggle(key) {
  setFilters(prev => ({ ...prev, [key]: !prev[key] }));
}

function handleSearch() {
  // TODO: gọi hàm search của bạn
  console.log('Search:', {
    query,
    filters
  });
}

function handleKeyDown(e) {
  if (e.key === 'Enter') handleSearch();
}

  const [active, setActive] = useState(null)

  // ICONS
  const [iconFiles, setIconFiles] = useState([])
  const [objectQuery, setObjectQuery] = useState('')

  useEffect(() => {
    fetch(`${process.env.PUBLIC_URL}/objects/manifest.json`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(arr => Array.isArray(arr) ? setIconFiles(arr) : setIconFiles([]))
      .catch(() => setIconFiles([])) // nếu chưa có manifest, dùng fallback
  }, [])

  const iconsToShow = useMemo(() => {
    const list = iconFiles.length ? iconFiles : FALLBACK_ICONS
    return list.filter(n => n.toLowerCase().includes(objectQuery.toLowerCase()))
  }, [iconFiles, objectQuery])

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
          <button
            id="search-btn"
            type="button"
            className="search-btn"
            aria-label="Run search"
            onClick={handleSearch}
          >
            Search
          </button>
        </div>

        <div className="toolbar">
          <div className="chip">100</div>

          <label className="chk">
            <input type="checkbox" checked={filters.asr} onChange={() => handleToggle('asr')} /> ASR
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.ocr} onChange={() => handleToggle('ocr')} /> OCR
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.open} onChange={() => handleToggle('open')} /> Open
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.eva} onChange={() => handleToggle('eva')} /> Eva
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.caption} onChange={() => handleToggle('caption')} /> Caption
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.nextScene} onChange={() => handleToggle('nextScene')} /> Next scene
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.extra} onChange={() => handleToggle('extra')} /> Extra
          </label>
          <label className="chk">
            <input type="checkbox" checked={filters.noExtra} onChange={() => handleToggle('noExtra')} /> No extra
          </label>

          <button className="btn" type="button">Re-rank</button>
          <button className="btn ghost" type="button">Feedback</button>
          <div className="chip round">Q&A</div>
        </div>
      </header>

      {/* BODY */}
      <div className="layout">
        {/* LEFT SIDEBAR */}
        <aside className="left">
          <div className="panel">
            <input
              className="input"
              placeholder="Search object..."
              value={objectQuery}
              onChange={(e) => setObjectQuery(e.target.value)}
            />
            <div className="icon-grid">
              {iconsToShow.map((name) => (
                <div key={name} className="icon-item" title={name.replace('.png','')}>
                  <img
                    className="icon-img"
                    src={`${process.env.PUBLIC_URL}/objects/${encodeURIComponent(name)}`}
                    alt={name}
                    loading="lazy"
                  />
                  <div className="icon-txt">{name.replace('.png','')}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <input className="input" placeholder="Search color..." />
            <div className="color-row">
              {['Black','Blue','Brown','Gray','Green','Pink','Purple','Red','White'].map((c) => (
                <div key={c} className={`swatch ${c.toLowerCase()}`} title={c} />
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">Objects &amp; colors</div>
            <div className="grid-7x7">
              {Array.from({ length: 49 }).map((_, i) => <div key={i} className="cell" />)}
            </div>
          </div>

          <div className="panel">
            <input className="input" placeholder="Search tag..." />
            <div className="tag-list">
              {[
                '3d','abacus','accessory','accident','accordion','acorn','actor',
                'adjust','adult','aerial','air','alarm','alley','animal','apartment',
                'apron','arch','arm','art'
              ].map((t) => <div key={t} className="tag-item">{t}</div>)}
            </div>
          </div>
        </aside>

        {/* CENTER GRID */}
        <main className="center">
          <div className="grid">
            {items.map((v) => (
              <div
                key={v.id}
                className={`card ${active === v.id ? 'active' : ''}`}
                onClick={() => setActive(v.id)}
              >
                <div className="thumb" />
                <div className="badges">
                  <div className="badge small" />
                  <div className="badge small" />
                </div>
                <div className="meta">
                  <span className="id">{v.id}</span>
                  <span className="icons">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </main>

        {/* RIGHT SIDEBAR */}
        <aside className="right">
          <div className="detail">
            <div className="detail-thumb" />
            <div className="detail-row">
              <div className="k">Title:</div>
              <div className="v">{active ? `Video có ID ${active}` : '[Chưa chọn video]'}</div>
            </div>
            <div className="detail-row">
              <div className="k">Author:</div>
              <div className="v">[Kênh/Người đăng]</div>
            </div>
            <div className="detail-row">
              <div className="k">Length:</div>
              <div className="v">[xxx seconds]</div>
            </div>
            <div className="detail-row">
              <div className="k">Channel url:</div>
              <div className="v url">[https://youtube.com/... ]</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
