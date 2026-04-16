// frontend/src/pages/Home.jsx
import { useNavigate } from 'react-router-dom';
import { useEffect, useState, useCallback, useRef } from 'react';
import {
  Camera, Sparkles, BarChart3, Edit, PlusCircle, FileText,
  BookOpen, ArrowRight, Sun, Focus, Layers, Crop,
  XCircle, Check, X, Utensils, Info, RefreshCw,
} from 'lucide-react';
import { ROUTES } from '../constants/routes';
import { useTour } from '../hooks/useTour';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/* ─── Helpers ─── */
const flex = (extra = {}) => ({ display: 'flex', ...extra });
const center = (extra = {}) => ({ display: 'flex', alignItems: 'center', justifyContent: 'center', ...extra });

/* ══ Photo Tips Data ══ */
const TIPS_DO = [
  { icon: Sun,    title: 'Pencahayaan', text: 'Gunakan cahaya alami atau ruangan yang terang.' },
  { icon: Focus,  title: 'Jarak & Fokus', text: 'Jarak ideal 20–35 cm agar detail makanan terlihat jelas dan tajam.' },
  { icon: Layers, title: 'Komposisi', text: 'Satu jenis makanan per foto untuk akurasi AI yang lebih baik.' },
  { icon: Crop,   title: 'Sudut Pandang', text: 'Foto dari atas (top-view) agar seluruh porsi makanan terlihat penuh.' },
];
const TIPS_DONT = [
  'Latar belakang yang terlalu ramai, berantakan, atau bermotif mencolok.',
  'Kondisi gelap (kurang cahaya) atau terlalu terang (silau/overexposure).',
  'Menggunakan piring dengan warna yang sangat mirip dengan warna makanan.',
  'Zoom terlalu dekat hingga gambar menjadi buram (pixelated) atau terpotong.',
];

/* ═══════════════════════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════════════════════ */
export default function Home() {
  const navigate = useNavigate();
  const [detectableFoods, setDetectableFoods] = useState([]);
  const [loadingFoods, setLoadingFoods]       = useState(true);
  const [foodsError, setFoodsError]           = useState(false);
  const [tipsTab, setTipsTab]                 = useState('do');

  const { startTour, shouldAutoStart, isTourActive } = useTour();

  /* ── Fetch with retry ── */
  const fetchFoods = useCallback(async (retries = 3) => {
    setLoadingFoods(true);
    setFoodsError(false);
    for (let i = 0; i < retries; i++) {
      try {
        const res = await fetch(`${API_BASE}/api/v1/detectable-foods`);
        const data = await res.json();
        setDetectableFoods(data.foods || []);
        setLoadingFoods(false);
        return;
      } catch {
        if (i < retries - 1) await new Promise((r) => setTimeout(r, 2000));
      }
    }
    setDetectableFoods([]);
    setFoodsError(true);
    setLoadingFoods(false);
  }, []);

  useEffect(() => { fetchFoods(); }, [fetchFoods]);

  useEffect(() => {
    if (shouldAutoStart()) {
      const timer = setTimeout(() => startTour(false), 500);
      return () => clearTimeout(timer);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleReplayTour = () => startTour(true);

  return (
    <div style={{ 
      fontFamily: "'Inter', sans-serif", 
      minHeight: '100vh', 
      color: '#171717',
      backgroundColor: '#f0fdf8', // Base off-white greenish
      overflowX: 'hidden'
    }}>
      
      {/* ── Background Canvas Blob Animations ── */}
      <CanvasBackground />

      {/* ── Global CSS ── */}
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        
        @keyframes ctaPulse { 
          0% { box-shadow: 0 0 0 0 rgba(16,185,129,0.6); } 
          70% { box-shadow: 0 0 0 16px rgba(16,185,129,0); } 
          100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); } 
        }

        .hover-card { 
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
        }
        .hover-card:hover { 
          transform: translateY(-6px); 
          box-shadow: 0 20px 40px -12px rgba(16, 185, 129, 0.15); 
        }

        .cta-btn {
          animation: ctaPulse 2.5s infinite cubic-bezier(0.4, 0, 0.2, 1);
          transition: all 0.3s ease;
        }
        .cta-btn:hover { transform: translateY(-3px) scale(1.02); }
        .cta-btn:active { transform: translateY(0) scale(1); }

        .btn-hover { transition: all 0.2s ease; }
        .btn-hover:hover { transform: translateY(-2px); box-shadow: 0 8px 20px -4px rgba(16,185,129,0.3); }

        .section-box {
          position: relative;
          z-index: 10;
        }
      `}</style>

      {/* ── Floating Panduan Button ── */}
      {!isTourActive && (
        <button onClick={handleReplayTour} className="btn-hover" aria-label="Lihat Panduan" style={{
          position:'fixed', bottom:32, right:32, zIndex:100,
          background:'#10B981', color:'#fff', border:'none', borderRadius:50,
          padding:'14px 24px', fontSize:14, fontWeight:600, cursor:'pointer',
          ...flex({ alignItems:'center', gap:8 }),
          boxShadow:'0 4px 12px rgba(16,185,129,0.3)'
        }}>
          <BookOpen size={18} /> Panduan
        </button>
      )}

      {/* ═══════════════════════════════════════════════════════════
          HERO SECTION (Base: #f0fdf8)
      ═══════════════════════════════════════════════════════════ */}
      <section className="section-box" style={{ paddingTop: '160px', paddingBottom: '80px', textAlign:'center', background: 'transparent' }}>
        <Reveal>
          <div style={{ maxWidth:800, margin:'0 auto', padding: '0 24px' }}>
            <div style={{
              display:'inline-flex', alignItems:'center', gap:6,
              background:'rgba(209, 250, 229, 0.8)', color:'#047857', fontSize:13, fontWeight:700,
              padding:'8px 20px', borderRadius:50, marginBottom:32,
              backdropFilter: 'blur(8px)', border: '1px solid rgba(16,185,129,0.2)'
            }}>
              <Sparkles size={14} /> Teknologi AI & Database TKPI 2020
            </div>

            <h1 style={{
              fontSize:'clamp(40px, 6vw, 64px)', fontWeight:900,
              color:'#0f172a', margin:'0 auto 24px', lineHeight:1.15,
              letterSpacing:'-0.03em',
            }}>
              Ketahui Gizi Makananmu<br/>
              <span style={{ color: '#10B981' }}>Hanya dari Foto</span>
            </h1>

            <p style={{
              fontSize:'clamp(16px, 2vw, 19px)', color:'#475569', margin:'0 auto 48px',
              maxWidth:560, lineHeight:1.7,
            }}>
              Cara praktis dan modern untuk memantau asupan kalori dan nutrisi harian.
              Ambil foto, biarkan AI kami mengidentifikasi makananmu.
            </p>

            <div>
              <button onClick={() => navigate(ROUTES.ANALYZE)} className="cta-btn" style={{
                background:'linear-gradient(135deg, #10B981 0%, #059669 100%)', color:'#fff', fontWeight:600, fontSize:17,
                padding:'18px 44px', borderRadius:50, border:'none', cursor:'pointer',
                display:'inline-flex', alignItems:'center', gap:12,
              }}>
                <Camera size={22} /> Mulai Pindai Makanan
              </button>
            </div>
          </div>
        </Reveal>
      </section>

      {/* Divider Hero -> Penggunaan */}
      <WaveDivider fill="#ffffff" path="M0,30 C360,70 1080,-10 1440,30 L1440,60 L0,60 Z" />

      {/* ═══════════════════════════════════════════════════════════
          CARA PENGGUNAAN (Base: #ffffff)
      ═══════════════════════════════════════════════════════════ */}
      <section className="section-box" style={{ background: '#ffffff', padding: '80px 24px' }}>
        <div style={{ maxWidth:1000, margin:'0 auto', textAlign:'center' }}>
          <Reveal>
            <SectionHeader
              subtitle="Alur Penggunaan"
              title="Sangat Mudah Digunakan"
              desc="Dapatkan informasi gizi lengkap hanya dalam 3 langkah sederhana."
            />
          </Reveal>

          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(280px, 1fr))', gap:32, marginTop:56 }}>
            {[
              { step:'01', icon: Camera,   title:'Ambil Foto',    desc:'Unggah foto makananmu dengan jelas dan pencahayaan yang cukup.',         color:'#10B981', bg:'#ECFDF5' },
              { step:'02', icon: Sparkles, title:'Analisis AI',   desc:'Sistem pintar kami akan mengenali jenis makanan di piringmu.',            color:'#8B5CF6', bg:'#F5F3FF' },
              { step:'03', icon: BarChart3, title:'Hasil Nutrisi', desc:'Lihat takaran kalori, protein, lemak, dan karbohidrat secara instan.', color:'#F59E0B', bg:'#FFFBEB' },
            ].map((item, idx) => (
              <Reveal key={idx} delay={idx * 150}>
                <div className="hover-card" style={{
                  borderRadius:28, padding:'48px 36px', background: '#FAFAFA',
                  border:'1px solid #F1F5F9', position:'relative', textAlign:'left',
                }}>
                  <div style={{ fontSize:60, fontWeight:900, color:'#E2E8F0', position:'absolute', top:24, right:32, lineHeight:1, zIndex:0, opacity: 0.5 }}>
                    {item.step}
                  </div>
                  <div style={{ background:item.bg, color:item.color, borderRadius:20, width:64, height:64, position:'relative', zIndex:1, ...center({ marginBottom:28 }) }}>
                    <item.icon size={30} />
                  </div>
                  <h3 style={{ fontSize:22, fontWeight:700, color:'#0f172a', marginBottom:12 }}>{item.title}</h3>
                  <p style={{ fontSize:15, color:'#475569', margin:0, lineHeight:1.7 }}>{item.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Divider Penggunaan -> Tips */}
      <WaveDivider fill="#f0fdf8" path="M0,20 C480,-20 960,80 1440,20 L1440,60 L0,60 Z" />

      {/* ═══════════════════════════════════════════════════════════
          TIPS PENGAMBILAN GAMBAR (Base: #f0fdf8)
      ═══════════════════════════════════════════════════════════ */}
      <section className="section-box" style={{ background: '#f0fdf8', padding: '80px 24px' }}>
        <div style={{ maxWidth:840, margin:'0 auto' }}>
          <Reveal>
            <div style={{ textAlign:'center', marginBottom:48 }}>
              <SectionHeader
                subtitle="Panduan Akurasi"
                title="Tips Kamera & Pencahayaan"
                desc="Ikuti panduan ini agar sistem AI dapat mengenali makananmu dengan akurasi maksimal."
              />
            </div>
          </Reveal>

          <Reveal delay={100}>
            {/* Toggle Tabs */}
            <div style={{ 
              display:'flex', background:'#E2E8F0', borderRadius:16, padding:6, 
              maxWidth:440, margin:'0 auto 48px'
            }}>
              {[
                { key:'do',   label:'Posisi Tepat',    Icon: Check, activeColor:'#10B981' },
                { key:'dont', label:'Perlu Dihindari', Icon: X,     activeColor:'#EF4444' },
              ].map(({ key, label, Icon, activeColor }) => (
                <button key={key} onClick={() => setTipsTab(key)} style={{
                  flex:1, padding:'14px 20px', borderRadius:12, border:'none', cursor:'pointer',
                  fontSize:15, fontWeight:600, ...center({ gap:10 }), transition:'all 0.3s',
                  background: tipsTab === key ? '#FFF' : 'transparent',
                  color:      tipsTab === key ? activeColor : '#64748b',
                  boxShadow:  tipsTab === key ? '0 4px 12px rgba(0,0,0,0.05)' : 'none',
                }}>
                  <Icon size={20} /> {label}
                </button>
              ))}
            </div>
          </Reveal>

          {/* DO */}
          {tipsTab === 'do' && (
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(320px, 1fr))', gap:24 }}>
              {TIPS_DO.map((item, i) => (
                <Reveal key={i} delay={i * 100}>
                  <div className="hover-card" style={{
                    borderRadius:20, padding:28, background: '#ffffff',
                    border:'1px solid #E2E8F0', ...flex({ gap:20, alignItems:'flex-start' }),
                  }}>
                    <div style={{ background:'#ECFDF5', color:'#10B981', padding:14, borderRadius:14 }}>
                      <item.icon size={26} />
                    </div>
                    <div>
                      <h4 style={{ margin:'0 0 8px', fontSize:17, fontWeight:700, color:'#0f172a' }}>{item.title}</h4>
                      <p style={{ margin:0, fontSize:15, color:'#475569', lineHeight:1.6 }}>{item.text}</p>
                    </div>
                  </div>
                </Reveal>
              ))}
            </div>
          )}

          {/* DONT */}
          {tipsTab === 'dont' && (
            <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
              {TIPS_DONT.map((text, i) => (
                <Reveal key={i} delay={i * 100}>
                  <div className="hover-card" style={{
                    borderRadius:20, padding:'24px 28px', background: '#ffffff',
                    border:'1px solid #E2E8F0', ...flex({ gap:20, alignItems:'center' }),
                  }}>
                    <div style={{ background:'#FEF2F2', color:'#EF4444', padding:12, borderRadius:12 }}>
                      <XCircle size={22} />
                    </div>
                    <p style={{ margin:0, fontSize:15, color:'#334155', lineHeight:1.6 }}>{text}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          )}

          {/* Note Banner */}
          <Reveal delay={300}>
            <div style={{
              marginTop:48, background:'#FFFBEB', borderRadius:20, padding:28,
              border:'1px solid #FDE68A', ...flex({ gap:20, alignItems:'flex-start' }),
            }}>
              <div style={{ color:'#D97706', paddingTop:2 }}><Info size={28} /></div>
              <div>
                <h4 style={{ margin:'0 0 8px', fontSize:17, fontWeight:700, color:'#92400E' }}>Catatan Penting</h4>
                <p style={{ margin:0, fontSize:15, color:'#B45309', lineHeight:1.6 }}>
                  Jika makanan dibungkus plastik atau daun, sebaiknya buka terlebih dahulu agar terlihat jelas.
                  Makanan dengan tampilan yang tertutup akan lebih sulit dikenali oleh sistem.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* Divider Tips -> Alternatif */}
      <WaveDivider fill="#ffffff" path="M0,40 C360,-20 1080,80 1440,40 L1440,60 L0,60 Z" />

      {/* ═══════════════════════════════════════════════════════════
          ALTERNATIF & BANTUAN (Base: #ffffff)
      ═══════════════════════════════════════════════════════════ */}
      <section className="section-box" style={{ background: '#ffffff', padding: '80px 24px' }}>
        <div style={{ maxWidth:900, margin:'0 auto' }}>
          <Reveal>
            <div style={{ textAlign:'center', marginBottom:56 }}>
              <SectionHeader
                subtitle="Opsi Lanjutan"
                title="Jika AI Belum Mengenali"
                desc="Kami menyediakan jalur alternatif agar Anda tetap bisa mendapatkan data nutrisi yang akurat."
              />
            </div>
          </Reveal>

          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(260px, 1fr))', gap:28 }}>
            {[
              { icon: Edit,       title:'Koreksi Data',     desc:'Ubah hasil deteksi secara manual ke nama makanan yang tepat.',        color:'#3B82F6', bg: '#EFF6FF' },
              { icon: PlusCircle, title:'Pencarian Manual',  desc:'Cari makanan langsung dari dalam pangkalan data TKPI.',              color:'#10B981', bg: '#ECFDF5' },
              { icon: FileText,   title:'Ajukan Makanan',    desc:'Kirimkan foto makanan baru untuk dipelajari oleh model AI.',         color:'#F59E0B', bg: '#FFFBEB' },
            ].map((item, idx) => (
              <Reveal key={idx} delay={idx * 150}>
                <div className="hover-card" style={{
                  border:'1px solid #E2E8F0', borderRadius:24, background: '#FAFAFA',
                  padding:'40px 28px', textAlign:'center',
                }}>
                  <div style={{ background:item.bg, color:item.color, width:64, height:64, borderRadius:20, ...center({ margin:'0 auto 24px' }) }}>
                    <item.icon size={28} />
                  </div>
                  <h3 style={{ fontSize:20, fontWeight:700, color:'#0f172a', marginBottom:12 }}>{item.title}</h3>
                  <p style={{ fontSize:15, color:'#64748b', lineHeight:1.6, margin:0 }}>{item.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Divider Alternatif -> Database */}
      <WaveDivider fill="#f0fdf8" path="M0,30 C480,80 960,-20 1440,30 L1440,60 L0,60 Z" />

      {/* ═══════════════════════════════════════════════════════════
          DATABASE MAKANAN (Base: #f0fdf8)
      ═══════════════════════════════════════════════════════════ */}
      <section className="section-box" style={{ background: '#f0fdf8', padding: '80px 24px' }}>
        <div style={{ maxWidth:1000, margin:'0 auto' }}>
          <Reveal>
            <div style={{ textAlign:'center', marginBottom:56 }}>
              <SectionHeader
                subtitle="Kapasitas Sistem"
                title="Database Makanan Tersedia"
                desc={
                  loadingFoods
                    ? 'Memuat data sistem...'
                    : foodsError
                      ? 'Gagal memuat data. Silakan coba lagi.'
                      : `Saat ini sistem mampu mendeteksi ${detectableFoods.length} jenis masakan dan hidangan nusantara.`
                }
              />
            </div>
          </Reveal>

          <Reveal delay={200}>
            {loadingFoods ? (
              <div style={{ textAlign:'center', padding:'60px 0' }}>
                <div style={{
                  width:48, height:48, border:'3px solid rgba(16,185,129,0.2)', borderTopColor:'#10B981',
                  borderRadius:'50%', animation:'spin 1s linear infinite', margin:'0 auto',
                }} />
              </div>
            ) : foodsError || detectableFoods.length === 0 ? (
              <div style={{ textAlign:'center', padding:60 }}>
                <p style={{ color:'#94a3b8', marginBottom:20, fontSize: 16 }}>
                  {foodsError ? 'Koneksi ke server gagal.' : 'Data belum tersedia.'}
                </p>
                <button onClick={() => fetchFoods()} className="btn-hover" style={{
                  background:'#10B981', color:'#fff', border:'none', borderRadius:50,
                  padding:'12px 28px', fontSize:15, fontWeight:600, cursor:'pointer',
                  ...flex({ alignItems:'center', gap:10, display:'inline-flex' }),
                }}>
                  <RefreshCw size={18} /> Coba Lagi
                </button>
              </div>
            ) : (
              <div style={{ 
                display:'flex', flexWrap:'wrap', gap:14, justifyContent:'center',
                background: '#ffffff', padding: '40px', borderRadius: 32,
                border: '1px solid #E2E8F0'
              }}>
                {detectableFoods.map((food, idx) => (
                  <div key={food.yolo_label} style={{
                    background:'#FAFAFA', border:'1px solid #E2E8F0', borderRadius:50,
                    padding:'10px 20px', ...flex({ alignItems:'center', gap:10 }),
                    fontSize:14, fontWeight:600, color:'#334155',
                    transition:'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                    onMouseEnter={(e) => { 
                      e.currentTarget.style.borderColor='#10B981'; 
                      e.currentTarget.style.color='#10B981';
                      e.currentTarget.style.transform='translateY(-2px)';
                      e.currentTarget.style.background='#ECFDF5';
                    }}
                    onMouseLeave={(e) => { 
                      e.currentTarget.style.borderColor='#E2E8F0'; 
                      e.currentTarget.style.color='#334155';
                      e.currentTarget.style.transform='translateY(0)';
                      e.currentTarget.style.background='#FAFAFA';
                    }}
                  >
                    <Utensils size={16} style={{ opacity: 0.7 }} />
                    {food.yolo_label.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </div>
                ))}
              </div>
            )}
          </Reveal>
        </div>
      </section>

      {/* Divider Database -> Bottom CTA */}
      <WaveDivider fill="#ffffff" path="M0,20 C360,60 1080,0 1440,20 L1440,60 L0,60 Z" />

      {/* ═══════════════════════════════════════════════════════════
          BOTTOM CTA (Base: #ffffff)
      ═══════════════════════════════════════════════════════════ */}
      <section className="section-box" style={{ background: '#ffffff', textAlign:'center', paddingTop: '80px', paddingBottom: '160px' }}>
        <Reveal>
          <div style={{ maxWidth:600, margin:'0 auto' }}>
            <h2 style={{ fontSize:36, fontWeight:800, color:'#0f172a', marginBottom:20 }}>Siap Memulai?</h2>
            <p style={{ fontSize:17, color:'#475569', marginBottom:48, lineHeight:1.7 }}>
              Cobalah sekarang dan rasakan kemudahan mengecek nilai gizi harian Anda melalui kamera gawai.
            </p>
            <button onClick={() => navigate(ROUTES.ANALYZE)} className="cta-btn" style={{
              background:'#0f172a', color:'#FFF', fontWeight:600, fontSize:17,
              padding:'18px 48px', borderRadius:50, border:'none', cursor:'pointer',
              display:'inline-flex', alignItems:'center', gap:12,
            }}>
              Buka Pindai Makanan <ArrowRight size={22} />
            </button>
          </div>
        </Reveal>
      </section>

    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
    Reusable Components
═══════════════════════════════════════════════════════════ */

// Main headings standardizer
function SectionHeader({ subtitle, title, desc }) {
  return (
    <>
      <div style={{ 
        color:'#10B981', fontSize:14, fontWeight:700, textTransform:'uppercase', 
        letterSpacing:'0.08em', marginBottom:16 
      }}>
        {subtitle}
      </div>
      <h2 style={{ 
        fontSize:'clamp(28px, 4vw, 36px)', fontWeight:800, color:'#0f172a', 
        margin:'0 0 20px 0', letterSpacing:'-0.02em' 
      }}>
        {title}
      </h2>
      <p style={{ 
        fontSize:'clamp(15px, 2vw, 17px)', color:'#475569', margin:0, 
        lineHeight:1.7, maxWidth:540, marginLeft:'auto', marginRight:'auto' 
      }}>
        {desc}
      </p>
    </>
  );
}

// SVG Wave Divider for seamless section transitions
function WaveDivider({ fill, path }) {
  return (
    <div style={{ position: 'relative', zIndex: 5, marginTop: '-1px', marginBottom: '-1px' }}>
      <svg viewBox="0 0 1440 60" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: '100%', height: 'auto', display: 'block' }}>
        <path d={path} fill={fill} />
      </svg>
    </div>
  );
}

// IntersecionObserver wrapper for scroll reveal animations
function Reveal({ children, delay = 0 }) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.unobserve(entry.target);
      }
    }, { rootMargin: '0px 0px -50px 0px', threshold: 0.1 });

    const currentRef = ref.current;
    if (currentRef) observer.observe(currentRef);

    return () => {
      if (currentRef) observer.unobserve(currentRef);
    };
  }, []);

  return (
    <div ref={ref} style={{
      opacity: isVisible ? 1 : 0,
      transform: isVisible ? 'translateY(0)' : 'translateY(24px)',
      transition: 'opacity 0.5s ease-out, transform 0.5s ease-out',
      transitionDelay: `${delay}ms`,
      willChange: 'opacity, transform'
    }}>
      {children}
    </div>
  );
}

// Canvas-based Animated Organic Radial Blobs
function CanvasBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resize);
    resize();

    // Init 5 blobs with random parameters
    const blobs = Array.from({ length: 5 }).map(() => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      radius: (Math.max(canvas.width, canvas.height) * 0.25) + Math.random() * 200,
      vx: (Math.random() - 0.5) * 1.2,
      vy: (Math.random() - 0.5) * 1.2,
      phaseX: Math.random() * Math.PI * 2,
      phaseY: Math.random() * Math.PI * 2,
      color: 'rgba(16,185,129,0.07)' // Pastel mint green
    }));

    let time = 0;
    const render = () => {
      time += 0.005; // speed of sin/cos oscillation
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      blobs.forEach(b => {
        // Natural oscillation mixed with velocity
        b.x += b.vx + Math.sin(time + b.phaseX) * 0.8;
        b.y += b.vy + Math.cos(time + b.phaseY) * 0.8;

        // Bounce off walls smoothly
        if (b.x < -b.radius) b.x = canvas.width + b.radius;
        if (b.x > canvas.width + b.radius) b.x = -b.radius;
        if (b.y < -b.radius) b.y = canvas.height + b.radius;
        if (b.y > canvas.height + b.radius) b.y = -b.radius;

        // Draw organic gradient sphere
        const gradient = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.radius);
        gradient.addColorStop(0, b.color);
        gradient.addColorStop(1, 'rgba(16,185,129,0)');
        
        ctx.beginPath();
        ctx.fillStyle = gradient;
        ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', background: '#f0fdf8' }}>
      <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />
    </div>
  );
}
