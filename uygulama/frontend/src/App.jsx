import { useEffect, useState } from 'react'
import './App.css'

const API = 'http://127.0.0.1:8899'

// ---------- Bileşenler ----------
function Adim({ no, baslik, aktif, tamam, children }) {
  return (
    <div className={`adim ${aktif ? 'aktif' : ''} ${tamam ? 'tamam' : ''}`}>
      <div className="adim-baslik">
        <span className="adim-no">{no}</span>
        <span className="adim-ad">{baslik}</span>
        {tamam && <span className="adim-ok">✓</span>}
      </div>
      <div className="adim-icerik">{children}</div>
    </div>
  )
}

function OranSatiri({ ad, oran, tutar, not }) {
  return (
    <div className="oran-satiri">
      <div className="oran-ad">
        <strong>{ad}</strong>
        {oran !== null && oran !== undefined && <span className="oran-yuzde">%{oran}</span>}
      </div>
      <div className="oran-tutar">{tutar !== null && tutar !== undefined ? `${tutar} €` : '—'}</div>
      {not && <div className="oran-not">{not}</div>}
    </div>
  )
}

// ---------- Ana Uygulama ----------
export default function App() {
  const [durum, setDurum] = useState(null)
  const [ulkeler, setUlkeler] = useState([])

  // iş akışı durumu
  const [urun, setUrun] = useState('')
  const [adaylar, setAdaylar] = useState([])
  const [secim, setSecim] = useState(null)
  const [ulke, setUlke] = useState('')
  const [hareket, setHareket] = useState('ithalat')
  const [cif, setCif] = useState(10000)
  const [rapor, setRapor] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState(null)

  // yedek / güncelleme
  const [yedekler, setYedekler] = useState([])
  const [guncelleLog, setGuncelleLog] = useState('')
  const [guncelleniyor, setGuncelleniyor] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/durum`).then(r => r.json()).then(setDurum).catch(() => setDurum({ hata: 'Backend çalışmıyor. uygulama/ klasöründe: uvicorn server:app --port 8899' }))
    fetch(`${API}/api/ulkeler`).then(r => r.json()).then(d => setUlkeler(d.ulkeler || []))
    fetch(`${API}/api/yedekler`).then(r => r.json()).then(d => setYedekler(d.yedekler || []))
  }, [])

  // Adım 1: ürün ara
  async function ara() {
    setYukleniyor(true); setHata(null); setRapor(null); setSecim(null)
    try {
      const r = await fetch(`${API}/api/ara?q=${encodeURIComponent(urun)}&limit=15`)
      const d = await r.json()
      setAdaylar(d.sonuclar || [])
      if (!d.sonuclar || d.sonuclar.length === 0) setHata(`"${urun}" için sonuç bulunamadı`)
    } catch (e) { setHata('Arama hatası: ' + e.message) }
    setYukleniyor(false)
  }

  // Adım 4: sorgula
  async function sorgula() {
    if (!secim) { setHata('Önce ürün seçin'); return }
    if (!ulke) { setHata('Ülke seçin'); return }
    setYukleniyor(true); setHata(null)
    try {
      const r = await fetch(`${API}/api/sorgula`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urun, ulke, hareket, cif: Number(cif), gtip_12: secim.gtip_12 })
      })
      const d = await r.json()
      if (d.hata) setHata(d.hata)
      else setRapor(d.rapor)
    } catch (e) { setHata('Sorgu hatası: ' + e.message) }
    setYukleniyor(false)
  }

  async function guncelle() {
    if (!confirm('Kaynakları yeniden indirip veritabanını yeniden kuracak. Devam?')) return
    setGuncelleniyor(true); setGuncelleLog('Güncelleme başlatıldı...')
    await fetch(`${API}/api/guncelle`, { method: 'POST' })
    const aralik = setInterval(async () => {
      const r = await fetch(`${API}/api/guncelle/durum`).then(r => r.json())
      setGuncelleLog(r.log || '')
      if (r.log && r.log.includes('TAMAM')) { clearInterval(aralik); setGuncelleniyor(false); window.location.reload() }
    }, 3000)
  }

  async function yedekle() {
    await fetch(`${API}/api/yedekle`, { method: 'POST' })
    const d = await fetch(`${API}/api/yedekler`).then(r => r.json())
    setYedekler(d.yedekler || [])
  }

  async function geriYukle(isim) {
    if (!confirm(`${isim} geri yüklenecek. Devam?`)) return
    await fetch(`${API}/api/geri_yukle/${encodeURIComponent(isim)}`, { method: 'POST' })
    window.location.reload()
  }

  return (
    <div className="app">
      <header className="ust">
        <div>
          <h1>🚢 GTİP / Vergi Sorgulama</h1>
          <p className="alt-baslik">Türkiye ithalat & ihracat ürün kodu + vergi hesaplama</p>
        </div>
        <div className="durum-kutu">
          {durum && !durum.hata ? (
            <>
              <span className="yeşil-nokta" /> ÇEVRİMDIŞI ✓
              <span className="durum-detay">v{durum.versiyon?.versiyon} · {durum.urun_kodlari} GTİP · {durum.igv} İGV</span>
            </>
          ) : (
            <span className="kırmızı">⚠ {durum?.hata || 'Bağlanıyor...'}</span>
          )}
        </div>
      </header>

      <div className="icerik">
        {/* ---- Adım 1: Ürün ---- */}
        <Adim no={1} baslik="Ürün sorgusu" aktif={!secim} tamam={!!secim}>
          <div className="satir">
            <input
              className="giris"
              value={urun}
              onChange={e => setUrun(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && ara()}
              placeholder="örn. gemi motoru parçaları, piston, ceviz..."
            />
            <button className="btn" onClick={ara} disabled={yukleniyor}>{yukleniyor ? '...' : '🔍 Ara'}</button>
          </div>
          {adaylar.length > 0 && (
            <div className="adaylar">
              <div className="aday-baslik">Adaylar — birini seçin:</div>
              {adaylar.map(a => (
                <button
                  key={a.gtip_12}
                  className={`aday ${secim?.gtip_12 === a.gtip_12 ? 'secil' : ''}`}
                  onClick={() => setSecim(a)}
                >
                  <span className="aday-kod">{a.gtip_12}</span>
                  <span className="aday-tanim">{a.aciklama_tr} {a.aciklama_en ? `· ${a.aciklama_en}` : ''}</span>
                  <span className="aday-vergi">{a.vergi_haddi ? `GV %${a.vergi_haddi}` : ''}</span>
                </button>
              ))}
            </div>
          )}
        </Adim>

        {/* ---- Adım 2-3: Ülke + Hareket ---- */}
        <Adim no={2} baslik="Ülke ve hareket tipi" aktif={!!secim && !rapor} tamam={!!rapor}>
          <div className="satir">
            <select className="giris" value={ulke} onChange={e => setUlke(e.target.value)}>
              <option value="">— Menşe / Varış ülkesi seçin —</option>
              {ulkeler.map(u => (
                <option key={u.ulke_kod} value={u.ulke_kod}>{u.ulke_kod} · {u.ulke_adi}</option>
              ))}
              <option value="__diger">(Diğer ülkeler — D.Ü.)</option>
            </select>
            <select className="giris" value={hareket} onChange={e => setHareket(e.target.value)}>
              <option value="ithalat">📥 İthalat</option>
              <option value="ihracat">📤 İhracat</option>
            </select>
            {hareket === 'ithalat' && (
              <input className="giris cif" type="number" value={cif} onChange={e => setCif(e.target.value)} placeholder="CIF (€)" title="CIF değer (EUR)" />
            )}
            <button className="btn birincil" onClick={sorgula} disabled={yukleniyor}>
              {yukleniyor ? '...' : '🔎 Sorgula'}
            </button>
          </div>
        </Adim>

        {hata && <div className="hata">❌ {hata}</div>}

        {/* ---- Adım 4: Rapor ---- */}
        {rapor && (
          <div className="rapor">
            <div className="rapor-baslik">
              <h2>{rapor.gtip_12 || rapor.gtip}</h2>
              <span className="hareket-rozet">{hareket.toUpperCase()}</span>
            </div>
            <p className="urun-tanim">
              <strong>TR:</strong> {rapor.urun?.aciklama_tr_4} — {rapor.urun?.aciklama_tr}<br />
              <strong>EN:</strong> {rapor.urun?.aciklama_en}
            </p>
            {hareket === 'ithalat' ? (
              <>
                <div className="rapor-bilgi">
                  <span>Menşe: <strong>{rapor.menşe}</strong> · İGV grubu: <strong>{rapor.igv_grubu}</strong></span>
                  <span>CIF: <strong>{rapor.cif} €</strong></span>
                </div>
                <div className="oranlar">
                  {rapor.kalemler.map((k, i) => (
                    <OranSatiri key={i} ad={k.ad} oran={k.oran} tutar={k.tutar} not={k.not} />
                  ))}
                  <div className="oran-satiri toplam">
                    <div className="oran-ad"><strong>TOPLAM VERGİ</strong></div>
                    <div className="oran-tutar"><strong>{rapor.toplam_vergi} €</strong></div>
                  </div>
                  <div className="oran-satiri genel-toplam">
                    <div className="oran-ad"><strong>TOPLAM MALİYET (CIF + vergiler)</strong></div>
                    <div className="oran-tutar"><strong>{rapor.toplam_maliyet} €</strong></div>
                  </div>
                </div>
                <div className="uyari">⚠ {rapor.uyari}</div>
              </>
            ) : (
              <div className="notlar">
                <h3>İhracat Notları</h3>
                <ul>
                  {rapor.notlar.map((n, i) => <li key={i}>{n}</li>)}
                </ul>
                <div className="uyari">⚠ {rapor.uyari}</div>
              </div>
            )}
            <button className="btn" onClick={() => setRapor(null)}>← Yeni sorgu</button>
          </div>
        )}

        {/* ---- Sistem: güncelleme + yedekleme ---- */}
        <div className="sistem">
          <h3>🛠 Sistem</h3>
          <div className="sistem-satir">
            <button className="btn" onClick={guncelle} disabled={guncelleniyor}>
              {guncelleniyor ? 'Güncelleniyor...' : '🔄 Güncelle (kaynakları yeniden indir + DB kur)'}
            </button>
            <button className="btn" onClick={yedekle}>💾 Yedek al</button>
          </div>
          {guncelleLog && <pre className="log">{guncelleLog}</pre>}
          {yedekler.length > 0 && (
            <div className="yedekler">
              <div className="aday-baslik">Yedekler (geri yüklemek için tıklayın):</div>
              {yedekler.map(y => (
                <div key={y} className="yedek-satir">
                  <span>{y}</span>
                  <button className="btn kucuk" onClick={() => geriYukle(y)}>↩ Geri yükle</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
