import ast
import json
import math
import os
import re
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
import opendartreader
from google import genai

# ====== 페이지 기본 설정 ======
st.set_page_config(
    page_title="DATAQUANT — Interactive Equity Terminal",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ====== API 키 로드 ======
DART_API_KEY = st.secrets.get("DART_API_KEY", "934f9c5cd12bf41dae6318eb1893687c1ee100e6")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")).strip()
GEMINI_MODEL = "gemini-2.5-flash"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://m.stock.naver.com/",
}
KEY_ACCOUNTS = ["자산총계", "부채총계", "자본총계", "매출액", "영업이익", "당기순이익", "당기순이익(손실)"]

# ====== 세션 상태 ======
if "entered" not in st.session_state:
    st.session_state.entered = False
if "active_code" not in st.session_state:
    st.session_state.active_code = ""

# ====== 하이엔드 다크 모션 CSS ======
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Pretendard', -apple-system, sans-serif;
    color: #F4F4F6;
}

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

.stApp {
    background-color: #0B0C10;
    color: #F4F4F6;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    max-width: 1260px !important;
    position: relative;
    z-index: 2;
}

@keyframes scatterIn {
    0% { opacity: 0; transform: scale(0.94) translateY(22px); }
    100% { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes floatSlow {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}

@keyframes pulseRing {
    0% { box-shadow: 0 0 0 0 rgba(217, 255, 84, 0.45); }
    70% { box-shadow: 0 0 0 18px rgba(217, 255, 84, 0); }
    100% { box-shadow: 0 0 0 0 rgba(217, 255, 84, 0); }
}

.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    margin-bottom: 1.8rem;
}
.nav-brand {
    font-family: 'Syne', sans-serif;
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
}
.nav-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
    letter-spacing: 0.08em;
}
.copy-url-btn {
    background: rgba(217, 255, 84, 0.12);
    border: 1px solid rgba(217, 255, 84, 0.55);
    color: #D9FF54;
    padding: 6px 16px;
    border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.22s ease;
    letter-spacing: 0.04em;
}
.copy-url-btn:hover {
    background: #D9FF54;
    color: #0B0C10;
    transform: scale(1.04);
}

.dv-hero {
    text-align: center;
    padding: 5.5rem 1rem 2.2rem 1rem;
    animation: scatterIn 0.85s cubic-bezier(0.16, 1, 0.3, 1);
}
.dv-wordmark {
    font-family: 'Syne', sans-serif;
    font-size: clamp(3rem, 7vw, 5.8rem);
    font-weight: 800;
    letter-spacing: 0.06em;
    line-height: 1;
    margin: 0;
    user-select: none;
}
.dv-solid { color: #FFFFFF; }
.dv-outline {
    color: transparent;
    -webkit-text-stroke: 1.6px rgba(255, 255, 255, 0.82);
}
.dv-tagline {
    font-size: 1.05rem;
    color: #9CA3AF;
    margin-top: 18px;
}

div.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #FFFFFF !important;
    border: 1.5px solid rgba(255, 255, 255, 0.45) !important;
    border-radius: 999px !important;
    padding: 0.75rem 2.2rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    animation: floatSlow 3s infinite ease-in-out, pulseRing 2.6s infinite;
    transition: all 0.28s ease !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: #D9FF54 !important;
    color: #0B0C10 !important;
    border-color: #D9FF54 !important;
}

div[data-testid="stForm"] {
    background: rgba(22, 24, 31, 0.88) !important;
    backdrop-filter: blur(16px);
    border: 1.5px solid rgba(255, 255, 255, 0.28) !important;
    border-radius: 999px !important;
    padding: 8px 10px 8px 22px !important;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.55);
}
div[data-testid="stTextInput"] > div > div {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stTextInput"] input {
    background-color: transparent !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #D9FF54 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.25rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em !important;
    border: none !important;
}
button[kind="primaryFormSubmit"] {
    background-color: #D9FF54 !important;
    color: #0B0C10 !important;
    border-radius: 999px !important;
    border: none !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 800 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.3rem !important;
}
button[kind="primaryFormSubmit"]:hover {
    background-color: #FFFFFF !important;
    color: #0B0C10 !important;
}

.glass-stage {
    background: rgba(18, 20, 27, 0.86);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 26px;
    padding: 2.2rem 2.5rem;
    margin: 1.6rem 0 2.2rem 0;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
    animation: scatterIn 0.6s ease-out;
}
.stage-kicker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
    letter-spacing: 0.08em;
}
.stage-title-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 16px;
    margin-top: 8px;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.stage-stock-name {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #FFFFFF;
    margin: 0;
}
.stage-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 800;
    color: #D9FF54;
}
.rings-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-top: 1.8rem;
}
.ring-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}
.score-circle {
    width: 94px;
    height: 94px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.45rem;
    font-weight: 800;
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.03);
    transition: transform 0.3s ease;
}
.score-circle:hover { transform: scale(1.1); }
.ring-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
    margin-top: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.verdict-strip {
    margin-top: 1.8rem;
    padding: 16px 22px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}
.verdict-tag {
    font-weight: 800;
    font-size: 1.05rem;
    padding: 7px 20px;
    border-radius: 999px;
}

.ed-section {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.18);
    padding-bottom: 10px;
    margin: 2.6rem 0 1.3rem 0;
}
.ed-section-title {
    font-family: 'Syne', 'Pretendard', sans-serif;
    font-size: 1.32rem;
    font-weight: 800;
    color: #FFFFFF;
}
.ed-section-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    color: #D9FF54;
}

.sub-head {
    font-family: 'JetBrains Mono', 'Pretendard', sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    color: #D1D5DB;
    letter-spacing: 0.02em;
    margin-bottom: 10px;
}

.ed-card {
    background: rgba(22, 24, 32, 0.82);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px;
    padding: 20px 22px;
    transition: all 0.25s ease;
}
.ed-card:hover {
    transform: translateY(-4px);
    border-color: #D9FF54;
}
.ed-card-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 700;
    color: #9CA3AF;
}
.ed-card-val {
    font-family: 'JetBrains Mono', 'Pretendard', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 6px 0;
}
.ed-card-sub {
    font-size: 0.82rem;
    font-weight: 600;
    color: #A5B4FC;
}

.ed-report-box {
    background: rgba(18, 20, 27, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 20px;
    padding: 24px 28px;
    line-height: 1.78;
    color: #E5E7EB;
}

.ed-news-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(22, 24, 32, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 15px 22px;
    margin-bottom: 10px;
    text-decoration: none !important;
    transition: all 0.24s ease;
}
.ed-news-row:hover {
    background: rgba(217, 255, 84, 0.1);
    border-color: #D9FF54;
    transform: translateX(6px);
}
.ed-news-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: #F9FAFB;
}
.ed-news-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #D9FF54;
    white-space: nowrap;
    margin-left: 16px;
}
</style>
""", unsafe_allow_html=True)

# ====== 파티클 배경 & URL 복사 스크립트 ======
components.html("""
<script>
(function() {
    const parentWin = window.parent;
    const parentDoc = parentWin.document;

    // 상단 우측 URL 복사 전역 함수 등록
    parentWin.copyAppShareUrl = function(btn) {
        const shareUrl = parentWin.location.origin + parentWin.location.pathname;
        if (parentWin.navigator && parentWin.navigator.clipboard) {
            parentWin.navigator.clipboard.writeText(shareUrl).then(() => {
                const orig = btn.innerText;
                btn.innerText = 'COPIED URL ✓';
                btn.style.background = '#D9FF54';
                btn.style.color = '#0B0C10';
                setTimeout(() => {
                    btn.innerText = orig;
                    btn.style.background = '';
                    btn.style.color = '';
                }, 2000);
            });
        } else {
            const tmp = parentDoc.createElement('input');
            tmp.value = shareUrl;
            parentDoc.body.appendChild(tmp);
            tmp.select();
            parentDoc.execCommand('copy');
            parentDoc.body.removeChild(tmp);
            btn.innerText = 'COPIED URL ✓';
        }
    };

    if (parentDoc.getElementById('dv-particle-canvas')) return;

    const canvas = parentDoc.createElement('canvas');
    canvas.id = 'dv-particle-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    parentDoc.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let w = canvas.width = parentWin.innerWidth;
    let h = canvas.height = parentWin.innerHeight;

    parentWin.addEventListener('resize', () => {
        w = canvas.width = parentWin.innerWidth;
        h = canvas.height = parentWin.innerHeight;
    });

    const mouse = { x: w / 2, y: h / 2, active: false };
    parentWin.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.active = true;
    });

    parentWin.addEventListener('click', (e) => {
        particles.forEach(p => {
            const dx = p.x - e.clientX;
            const dy = p.y - e.clientY;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 280) {
                const force = (280 - dist) / 280;
                p.vx += (dx / dist) * force * 6.5;
                p.vy += (dy / dist) * force * 6.5;
            }
        });
    });

    const count = 120;
    const particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        size: Math.random() * 2.0 + 0.8,
        alpha: Math.random() * 0.5 + 0.2
    }));

    function draw() {
        ctx.clearRect(0, 0, w, h);
        for (let i = 0; i < count; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vx *= 0.985;
            p.vy *= 0.985;

            if (Math.abs(p.vx) < 0.16) p.vx += (Math.random() - 0.5) * 0.08;
            if (Math.abs(p.vy) < 0.16) p.vy += (Math.random() - 0.5) * 0.08;

            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
            ctx.fill();

            if (mouse.active) {
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 145) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(217, 255, 84, ${(1 - dist / 145) * 0.35})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
})();
</script>
""", height=0, width=0)


@st.cache_resource
def init_dart_client(api_key):
    if hasattr(opendartreader, "OpenDartReader"):
        return opendartreader.OpenDartReader(api_key)
    if hasattr(opendartreader, "Dart"):
        return opendartreader.Dart(api_key)
    try:
        from opendartreader.dart import Dart
        return Dart(api_key)
    except ImportError:
        from opendartreader.dart import OpenDartReader
        return OpenDartReader(api_key)


def to_number(text):
    if text is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(text))
    try:
        return float(cleaned) if cleaned not in ("", "-", ".") else None
    except ValueError:
        return None


def format_krw_unit(val):
    if val is None or pd.isna(val):
        return "-"
    num = float(val)
    sign = "-" if num < 0 else ""
    num = abs(num)
    eok = num / 100_000_000
    if eok >= 10000:
        jo = int(eok // 10000)
        rem_eok = int(round(eok % 10000))
        return f"{sign}{jo}조 {rem_eok:,}억"
    return f"{sign}{int(round(eok)):,}억"


def calc_ema(values, period):
    ema = []
    k = 2 / (period + 1)
    for i, v in enumerate(values):
        if i == 0:
            ema.append(v)
        else:
            ema.append(v * k + ema[-1] * (1 - k))
    return ema


@st.cache_data(ttl=300)
def fetch_all_stock_data(stock_code):
    naver_data = {}
    try:
        r1 = requests.get(f"https://m.stock.naver.com/api/stock/{stock_code}/basic", headers=HEADERS, timeout=8)
        b_json = r1.json()
        if "stockName" in b_json:
            naver_data["종목명"] = b_json["stockName"]
        if "closePrice" in b_json:
            naver_data["현재가"] = to_number(b_json["closePrice"])
        if "fluctuationsRatio" in b_json:
            naver_data["전일대비등락률"] = f"{b_json['fluctuationsRatio']}%"
    except Exception:
        pass

    try:
        r2 = requests.get(f"https://m.stock.naver.com/api/stock/{stock_code}/integration", headers=HEADERS, timeout=8)
        i_json = r2.json()
        for item in i_json.get("totalInfos", []):
            key = item.get("key")
            val = item.get("value")
            if key and val:
                naver_data[key] = val
    except Exception:
        pass

    end_dt = datetime.now()
    day_start = (end_dt - timedelta(days=230)).strftime("%Y%m%d")
    month_start = (end_dt - timedelta(days=1200)).strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    def get_candles(tf, s_dt):
        url = f"https://api.finance.naver.com/siseJson.naver?symbol={stock_code}&requestType=1&startTime={s_dt}&endTime={end_str}&timeframe={tf}"
        recs = []
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            rows = ast.literal_eval(r.text.strip())
            for row in rows[1:]:
                if len(row) >= 6:
                    d_raw = str(row[0]).strip()
                    d_fmt = f"{d_raw[:4]}-{d_raw[4:6]}-{d_raw[6:8]}" if tf == "day" and len(d_raw) == 8 else (f"{d_raw[:4]}-{d_raw[4:6]}" if len(d_raw) >= 6 else d_raw)
                    cp = float(row[4])
                    if cp > 0:
                        recs.append({"날짜": d_fmt, "종가": cp})
        except Exception:
            pass
        return pd.DataFrame(recs)

    df_day = get_candles("day", day_start)
    df_month = get_candles("month", month_start)

    tech = {}
    if len(df_day) >= 26:
        closes = df_day["종가"].tolist()
        cur_p = closes[-1]

        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        recent_14 = deltas[-14:]
        avg_gain = sum([d for d in recent_14 if d > 0]) / 14
        avg_loss = sum([-d for d in recent_14 if d < 0]) / 14
        rsi_14 = 100.0 if avg_loss == 0 else round(100 - (100 / (1 + (avg_gain / avg_loss))), 2)
        rsi_label = "과매수 (단기과열)" if rsi_14 >= 70 else ("과매도 (저점영역)" if rsi_14 <= 30 else "중립 구간")

        ema12 = calc_ema(closes, 12)
        ema26 = calc_ema(closes, 26)
        macd_line = [a - b for a, b in zip(ema12, ema26)]
        signal_line = calc_ema(macd_line, 9)
        macd_now = round(macd_line[-1], 1)
        sig_now = round(signal_line[-1], 1)
        macd_hist = round(macd_now - sig_now, 1)
        macd_status = "상승 추세 (골든크로스)" if macd_hist > 0 else "하락 압력 (데드크로스)"

        df_day["20일선"] = df_day["종가"].rolling(20).mean()
        std20 = df_day["종가"].rolling(20).std()
        df_day["볼린저상단"] = df_day["20일선"] + (std20 * 2)
        df_day["볼린저하단"] = df_day["20일선"] - (std20 * 2)

        bb_upper = df_day["볼린저상단"].iloc[-1]
        bb_lower = df_day["볼린저하단"].iloc[-1]
        bb_pct = round(((cur_p - bb_lower) / (bb_upper - bb_lower)) * 100, 1) if (bb_upper - bb_lower) > 0 else 50.0

        tech = {
            "RSI": (rsi_14, rsi_label),
            "MACD": (macd_now, sig_now, macd_hist, macd_status),
            "볼린저밴드": (int(round(bb_upper)), int(round(bb_lower)), bb_pct, f"밴드 내 위치 {bb_pct}%"),
            "최근60일_최고가": int(max(closes[-60:])),
            "최근60일_최저가": int(min(closes[-60:])),
        }
        for period in [20, 60, 120]:
            if len(closes) >= period:
                ma = sum(closes[-period:]) / period
                disp = round((cur_p / ma) * 100, 2)
                tech[f"MA{period}"] = (int(round(ma)), disp, round(disp - 100, 2))

    if len(df_month) >= 12:
        df_month["12개월선"] = df_month["종가"].rolling(12).mean()
        std12 = df_month["종가"].rolling(12).std()
        df_month["볼린저상단"] = df_month["12개월선"] + (std12 * 2)
        df_month["볼린저하단"] = df_month["12개월선"] - (std12 * 2)

    dart = init_dart_client(DART_API_KEY)
    fin_3yr, latest_year = {}, None
    current_year = datetime.now().year
    for target_year in [current_year - 1, current_year - 2]:
        try:
            df_d = dart.finstate(stock_code, target_year)
        except Exception:
            continue
        if df_d is not None and len(df_d) > 0:
            if "fs_div" in df_d.columns and "CFS" in df_d["fs_div"].values:
                df_d = df_d[df_d["fs_div"] == "CFS"]
            res = {f"{target_year}년": {}, f"{target_year - 1}년": {}, f"{target_year - 2}년": {}}
            for _, row in df_d.iterrows():
                nm = row.get("account_nm")
                if nm in KEY_ACCOUNTS:
                    std_nm = "당기순이익" if "당기순이익" in nm else nm
                    res[f"{target_year}년"].setdefault(std_nm, to_number(row.get("thstrm_amount")))
                    res[f"{target_year - 1}년"].setdefault(std_nm, to_number(row.get("frmtrm_amount")))
                    res[f"{target_year - 2}년"].setdefault(std_nm, to_number(row.get("bfefrmtrm_amount")))
            if res[f"{target_year}년"]:
                fin_3yr, latest_year = res, f"{target_year}년"
                break

    news_list = []
    seen_titles = set()
    try:
        r_n = requests.get(f"https://m.stock.naver.com/api/news/stock/{stock_code}?pageSize=10&page=1", headers=HEADERS, timeout=8)
        for grp in r_n.json():
            for item in grp.get("items", []):
                raw_title = str(item.get("title", "")).strip()
                title = raw_title.replace("&quot;", '"').replace("&amp;", "&").replace("<b>", "").replace("</b>", "")
                oid = str(item.get("officeId", "")).strip()
                aid = str(item.get("articleId", "")).strip()
                press = str(item.get("officeName", "")).strip()
                if not title or not press or title in seen_titles:
                    continue
                seen_titles.add(title)
                dt_raw = str(item.get("datetime", "")).strip()
                date_fmt = f"{dt_raw[:4]}.{dt_raw[4:6]}.{dt_raw[6:8]}" if len(dt_raw) >= 8 else ""
                link = f"https://n.news.naver.com/mnews/article/{oid}/{aid}" if (oid and aid) else f"https://m.stock.naver.com/domestic/stock/{stock_code}/news"
                news_list.append({"title": title, "url": link, "press": press, "date": date_fmt})
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
    except Exception:
        pass

    return naver_data, tech, df_day.tail(60), df_month.tail(36), fin_3yr, latest_year, news_list


def compute_valuation_and_rating(fin_3yr, latest_year, naver_data, tech_data):
    formulas = {}
    val_score, prof_score, mom_score = 50, 50, 50
    reasons = []

    latest = fin_3yr.get(latest_year, {}) if latest_year else {}
    sales = latest.get("매출액")
    op_profit = latest.get("영업이익")
    net_income = latest.get("당기순이익")
    debt = latest.get("부채총계")
    equity = latest.get("자본총계")

    if sales and op_profit is not None:
        opm = round((op_profit / sales) * 100, 2)
        formulas["영업이익률"] = opm
        if opm >= 15:
            prof_score += 22
            reasons.append("높은 영업이익률(15% 이상)")
        elif opm > 0:
            prof_score += 8
        else:
            prof_score -= 22
            reasons.append("영업적자 상태")

    if sales and net_income is not None:
        formulas["순이익률"] = round((net_income / sales) * 100, 2)

    if debt and equity and equity > 0:
        debt_ratio = round((debt / equity) * 100, 2)
        formulas["부채비율"] = debt_ratio
        if debt_ratio <= 80:
            prof_score += 14
            reasons.append("우수한 재무건전성(부채비율 80% 이하)")
        elif debt_ratio >= 200:
            prof_score -= 18
            reasons.append("높은 부채부담(200% 이상)")

    roe_val = None
    if net_income is not None and equity and equity > 0:
        roe_val = round((net_income / equity) * 100, 2)
    elif "ROE" in naver_data:
        roe_val = to_number(naver_data["ROE"])

    if roe_val is not None:
        formulas["ROE"] = roe_val
        if roe_val >= 12:
            prof_score += 18
            reasons.append(f"우수한 ROE ({roe_val}%)")
        elif roe_val < 0:
            prof_score -= 18
            reasons.append("마이너스 ROE")

    per_val = to_number(naver_data.get("PER"))
    pbr_val = to_number(naver_data.get("PBR"))
    eps_val = to_number(naver_data.get("EPS"))
    bps_val = to_number(naver_data.get("BPS"))

    formulas["PER"] = per_val
    formulas["PBR"] = pbr_val

    if per_val and per_val > 0:
        if per_val <= 12:
            val_score += 20
            reasons.append(f"저PER 매력 구간 ({per_val}배)")
        elif per_val >= 40:
            val_score -= 15
            reasons.append(f"높은 PER 부담 ({per_val}배)")

    if pbr_val and pbr_val > 0 and pbr_val < 1.0:
        val_score += 15
        reasons.append(f"자산가치 저평가 (PBR {pbr_val}배)")

    current_price = naver_data.get("현재가")
    if eps_val and bps_val and eps_val > 0 and bps_val > 0:
        graham_price = int(round(math.sqrt(22.5 * eps_val * bps_val)))
        diff_pct = round(((graham_price - current_price) / current_price) * 100, 1) if current_price else 0
        formulas["그레이엄 적정주가"] = (graham_price, diff_pct)
        if diff_pct >= 20:
            val_score += 15
            reasons.append("그레이엄 적정가 대비 상승 여력")

    macd_info = tech_data.get("MACD")
    if macd_info:
        if macd_info[2] > 0:
            mom_score += 18
            reasons.append("MACD 상승 추세 유지")
        else:
            mom_score -= 12
            reasons.append("MACD 단기 하락 추세")

    rsi_val = tech_data.get("RSI", (None, ""))[0]
    if rsi_val is not None:
        if rsi_val <= 32:
            mom_score += 16
            reasons.append("RSI 과매도 저점 구간")
        elif rsi_val >= 72:
            mom_score -= 16
            reasons.append("RSI 단기 과열 구간")

    val_score = max(10, min(99, val_score))
    prof_score = max(10, min(99, prof_score))
    mom_score = max(10, min(99, mom_score))
    total_score = round((val_score + prof_score + mom_score) / 3)

    if total_score >= 75:
        grade, en_grade, pill_bg, pill_fg = "적극매수", "STRONG BUY", "#D9FF54", "#0B0C10"
    elif total_score >= 60:
        grade, en_grade, pill_bg, pill_fg = "매수", "BUY", "#38BDF8", "#0B0C10"
    elif total_score >= 45:
        grade, en_grade, pill_bg, pill_fg = "보류", "HOLD", "#FBBF24", "#0B0C10"
    elif total_score >= 30:
        grade, en_grade, pill_bg, pill_fg = "위험", "UNDERPERFORM", "#FB923C", "#0B0C10"
    else:
        grade, en_grade, pill_bg, pill_fg = "매우 위험", "HIGH RISK", "#F43F5E", "#FFFFFF"

    return formulas, {
        "grade": grade,
        "en_grade": en_grade,
        "total_score": total_score,
        "val_score": val_score,
        "prof_score": prof_score,
        "mom_score": mom_score,
        "pill_bg": pill_bg,
        "pill_fg": pill_fg,
        "reasons": reasons[:3] if reasons else ["주요 지표가 중립 구간에 위치"],
    }


def ask_gemini_ai(api_key, system_instruction, payload_json):
    if not api_key:
        return "GEMINI_API_KEY가 비어 있습니다. Streamlit Secrets에 Google AI Studio API 키(AIza...)를 저장해 주세요."
    prompt = f"{system_instruction}\n\n[정량 데이터]\n{payload_json}"
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"AI 호출 오류 (API 키 형식을 확인해 주세요 — Google AI Studio의 'AIza...' 키가 필요합니다): {e}"


# ================= 상단 내비게이션 바 (우측 상단 원클릭 URL 복사 버튼 탑재) =================
today_str = datetime.now().strftime("%b %d, %Y").upper()
st.markdown(
    f'<div class="top-nav">'
    f'<div class="nav-brand">q.terminal.</div>'
    f'<div class="nav-meta">HUMAN — DATA EQUITY INTERFACE &nbsp;/&nbsp; {today_str}</div>'
    f'<button class="copy-url-btn" onclick="window.copyAppShareUrl(this)">SHARE URL ↗</button>'
    f'</div>',
    unsafe_allow_html=True,
)

# ================= [1단계] 클릭 전환 인터랙티브 인트로 스테이지 =================
if not st.session_state.entered:
    st.markdown(
        '<div class="dv-hero">'
        '<h1 class="dv-wordmark"><span class="dv-solid">DATA</span><span class="dv-outline">QUANT</span></h1>'
        '<p class="dv-tagline">Interactions Investisseur — Données &nbsp;·&nbsp; 클릭하여 정량 리서치 터미널을 여세요</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, enter_col, _ = st.columns([1.6, 1, 1.6])
    with enter_col:
        if st.button("ENTER TERMINAL  ↓", use_container_width=True):
            st.session_state.entered = True
            st.rerun()

# ================= [2단계] 종목코드 입력 & 리포트 스테이지 =================
else:
    st.markdown(
        '<div style="text-align:center; padding: 0.5rem 0 1.4rem 0;">'
        '<div style="font-family:\'Syne\',sans-serif; font-size:2.1rem; font-weight:800; letter-spacing:0.04em;">'
        '<span class="dv-solid">DATA</span><span class="dv-outline">QUANT</span>'
        '<span style="font-size:1rem; color:#D9FF54; font-family:\'JetBrains Mono\',monospace; vertical-align:middle; margin-left:8px;">// TERMINAL</span>'
        '</div>'
        '<p style="color:#9CA3AF; font-size:0.92rem; margin-top:6px;">분석할 한국 주식 종목코드 6자리를 입력하고 ENTER 또는 ANALYZE를 누르세요</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1.15, 2.1, 1.15])
    with center_col:
        with st.form("search_form", clear_on_submit=False):
            in_col, btn_col = st.columns([3.1, 1.3])
            with in_col:
                stock_code = st.text_input(
                    "종목코드",
                    value=st.session_state.active_code or "003000",
                    max_chars=6,
                    placeholder="003000",
                    label_visibility="collapsed",
                )
            with btn_col:
                submitted = st.form_submit_button("ANALYZE →", type="primary", use_container_width=True)

        st.markdown(
            '<div style="text-align:center; color:#9CA3AF; font-family:\'JetBrains Mono\',monospace; font-size:0.78rem; margin-top:8px;">'
            'QUICK TICKERS: <b style="color:#D9FF54;">003000</b> 부광약품 · <b style="color:#D9FF54;">005930</b> 삼성전자 · <b style="color:#D9FF54;">000660</b> SK하이닉스 · <b style="color:#D9FF54;">035420</b> NAVER'
            '</div>',
            unsafe_allow_html=True,
        )

    if submitted and stock_code:
        st.session_state.active_code = stock_code.strip().zfill(6)

    if st.session_state.active_code:
        code = st.session_state.active_code

        with st.spinner("실시간 주가 차트, 기술적 지표, DART 3개년 재무, 최신 뉴스를 분석 중입니다..."):
            naver_data, tech_data, df_day, df_month, fin_3yr, latest_year, news_top5 = fetch_all_stock_data(code)
            stock_name = naver_data.get("종목명") or f"종목_{code}"
            formulas, rating = compute_valuation_and_rating(fin_3yr, latest_year, naver_data, tech_data)

        cur_p = naver_data.get("현재가")
        chg_r = naver_data.get("전일대비등락률", "")
        cur_p_str = f"{int(cur_p):,} KRW ({chg_r})" if cur_p else "N/A"
        reasons_text = " · ".join(rating["reasons"])

        stage_html = (
            f'<div class="glass-stage">'
            f'<div class="stage-kicker">EQUITY DOSSIER &nbsp;/&nbsp; KRX : {code}</div>'
            f'<div class="stage-title-row">'
            f'<h2 class="stage-stock-name">{stock_name}</h2>'
            f'<div class="stage-price">{cur_p_str}</div>'
            f'</div>'
            f'<div class="rings-grid">'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #D9FF54;">{rating["total_score"] / 10:.2f}</div><div class="ring-label">TOTAL INDEX / 10</div></div>'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #38BDF8;">{rating["val_score"] / 10:.2f}</div><div class="ring-label">VALUATION</div></div>'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #A78BFA;">{rating["prof_score"] / 10:.2f}</div><div class="ring-label">PROFITABILITY</div></div>'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #34D399;">{rating["mom_score"] / 10:.2f}</div><div class="ring-label">MOMENTUM</div></div>'
            f'</div>'
            f'<div class="verdict-strip">'
            f'<div><span style="font-family:\'JetBrains Mono\',monospace; font-size:0.75rem; color:#9CA3AF; display:block;">KEY QUANT DRIVERS</span>'
            f'<span style="font-size:0.98rem; font-weight:600; color:#F4F4F6;">{reasons_text}</span></div>'
            f'<div class="verdict-tag" style="background:{rating["pill_bg"]}; color:{rating["pill_fg"]};">{rating["en_grade"]} &nbsp;·&nbsp; {rating["grade"]}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(stage_html, unsafe_allow_html=True)

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">01. PRICE ACTION & TECHNICAL CHART</div>'
            '<div class="ed-section-num">INTERACTIVE CHART</div></div>',
            unsafe_allow_html=True,
        )

        g_col, t_col = st.columns([1.48, 1])

        with g_col:
            ctrl1, ctrl2 = st.columns([1.2, 1])
            with ctrl1:
                timeframe_opt = st.radio(
                    "차트 기준",
                    ["일별 (최근 60일)", "월별 (최근 3년)"],
                    horizontal=True,
                    label_visibility="collapsed",
                )
            with ctrl2:
                show_bb = st.toggle("볼린저밴드 상·하단 표시", value=True)

            is_daily = timeframe_opt.startswith("일별")
            src_df = df_day.copy() if is_daily else df_month.copy()
            ma_col_name = "20일선" if is_daily else "12개월선"

            if not src_df.empty:
                plot_cols = ["종가"]
                if ma_col_name in src_df.columns:
                    plot_cols.append(ma_col_name)
                if show_bb and "볼린저상단" in src_df.columns and "볼린저하단" in src_df.columns:
                    plot_cols.extend(["볼린저상단", "볼린저하단"])

                melted = src_df[["날짜"] + plot_cols].melt("날짜", var_name="지표", value_name="가격")
                color_domain = ["종가", ma_col_name, "볼린저상단", "볼린저하단"]
                color_range = ["#D9FF54", "#38BDF8", "#F43F5E", "#10B981"]

                dates_list = src_df["날짜"].tolist()
                step = max(1, len(dates_list) // 7)
                tick_vals = dates_list[::step]

                price_chart = (
                    alt.Chart(melted)
                    .mark_line(strokeWidth=2.3)
                    .encode(
                        x=alt.X(
                            "날짜:N",
                            sort=None,
                            axis=alt.Axis(
                                values=tick_vals,
                                labelAngle=0,
                                labelColor="#9CA3AF",
                                title=None,
                                grid=False,
                            ),
                        ),
                        y=alt.Y(
                            "가격:Q",
                            scale=alt.Scale(zero=False),
                            axis=alt.Axis(
                                format=",.0f",
                                labelColor="#9CA3AF",
                                title=None,
                                gridColor="rgba(255,255,255,0.08)",
                            ),
                        ),
                        color=alt.Color(
                            "지표:N",
                            scale=alt.Scale(domain=color_domain, range=color_range),
                            legend=alt.Legend(orient="bottom", title=None, labelColor="#E5E7EB"),
                        ),
                        tooltip=["날짜", "지표", alt.Tooltip("가격:Q", format=",.0f")],
                    )
                    .properties(height=340)
                    .configure_view(strokeWidth=0)
                    .configure(background="transparent")
                )
                st.altair_chart(price_chart, use_container_width=True)
            else:
                st.info("주가 차트 데이터를 불러오지 못했습니다.")

        with t_col:
            st.markdown('<div class="sub-head">TECHNICAL TREND & SUPPORT / RESISTANCE</div>', unsafe_allow_html=True)
            chart_payload = json.dumps(
                {"종목": f"{stock_name} ({code})", "현재가": cur_p_str, "기술적지표": tech_data},
                ensure_ascii=False,
                indent=2,
            )
            with st.spinner("차트 추세와 지지·저항선을 분석하는 중..."):
                chart_analysis = ask_gemini_ai(
                    GEMINI_API_KEY,
                    "당신은 전문 차트 테크니컬 애널리스트입니다. 이모지는 절대 사용하지 마세요. 제공된 20·60·120일 이동평균선 이격도, RSI(14일), MACD 추세, 볼린저밴드 위치, 60일 최고/최저가 수치만 근거로 현재 주가 차트의 추세 방향, 단기 지지선과 저항선 가격대, 과열/침체 여부를 4~5줄의 명확한 불릿 포인트로 분석해 주세요.",
                    chart_payload,
                )
            st.markdown(f'<div class="ed-report-box">{chart_analysis}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">02. VALUATION & MOMENTUM METRICS</div>'
            '<div class="ed-section-num">QUANT INDICATORS</div></div>',
            unsafe_allow_html=True,
        )

        per_str = f"{formulas['PER']}배" if formulas.get("PER") else "적자 / N/A"
        pbr_str = f"{formulas['PBR']}배" if formulas.get("PBR") else "N/A"
        roe_val = f"{formulas['ROE']}%" if formulas.get("ROE") is not None else "N/A"
        debt_val = f"{formulas['부채비율']}%" if formulas.get("부채비율") is not None else "N/A"
        opm_val = f"{formulas['영업이익률']}%" if formulas.get("영업이익률") is not None else "N/A"

        rsi_val, rsi_stat = tech_data.get("RSI", (None, "-"))
        macd_info = tech_data.get("MACD")
        macd_str = f"{macd_info[0]}" if macd_info else "N/A"
        macd_sub = macd_info[3] if macd_info else "-"

        if "그레이엄 적정주가" in formulas:
            g_p, g_diff = formulas["그레이엄 적정주가"]
            graham_str = f"{g_p:,}원"
            graham_sub = f"현재가 대비 {g_diff:+.1f}%"
        else:
            graham_str = "산출 불가"
            graham_sub = "EPS/BPS 적자 구간"

        cards_row1 = [
            ("PER · 주가수익비율", per_str, f"EPS {naver_data.get('EPS', 'N/A')}"),
            ("PBR · 주가순자산비율", pbr_str, f"BPS {naver_data.get('BPS', 'N/A')}"),
            ("RSI (14D) · 과열도", f"{rsi_val if rsi_val is not None else 'N/A'}", rsi_stat),
            ("MACD · 추세 시그널", macd_str, macd_sub),
        ]
        cols1 = st.columns(4)
        for col, (lbl, val, sub) in zip(cols1, cards_row1):
            col.markdown(
                f'<div class="ed-card"><div class="ed-card-lbl">{lbl}</div>'
                f'<div class="ed-card-val">{val}</div><div class="ed-card-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        cards_row2 = [
            ("ROE · 자기자본이익률", roe_val, "기준: 10% 이상 우수"),
            ("DEBT RATIO · 부채비율", debt_val, "기준: 100% 이하 안정"),
            ("OP MARGIN · 영업이익률", opm_val, "본업 수익창출력"),
            ("GRAHAM VALUE · 적정가", graham_str, graham_sub),
        ]
        cols2 = st.columns(4)
        for col, (lbl, val, sub) in zip(cols2, cards_row2):
            col.markdown(
                f'<div class="ed-card"><div class="ed-card-lbl">{lbl}</div>'
                f'<div class="ed-card-val">{val}</div><div class="ed-card-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        ind_payload_str = json.dumps(
            {"종목": f"{stock_name} ({code})", "핵심지표": formulas, "기술지표": tech_data, "시장밸류에이션": naver_data},
            ensure_ascii=False,
            indent=2,
        )
        with st.spinner("밸류에이션 및 재무 비율 지표를 해석하는 중..."):
            ind_analysis = ask_gemini_ai(
                GEMINI_API_KEY,
                "당신은 객관적 퀀트 애널리스트입니다. 이모지는 절대 사용하지 마세요. 제공된 PER, PBR, ROE, 부채비율, 영업이익률, 그레이엄 적정주가 수치만 근거로 현재 주가의 밸류에이션 매력도와 재무 건전성을 4줄 내외의 명확한 불릿 포인트로 해석해 주세요.",
                ind_payload_str,
            )
        st.markdown(f'<div class="ed-report-box" style="margin-top:14px;">{ind_analysis}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">03. FINANCIAL STATEMENTS & ANNUAL CHARTS</div>'
            '<div class="ed-section-num">UNIT: 100M KRW (억 원)</div></div>',
            unsafe_allow_html=True,
        )

        def make_slim_vertical_bar(df_bar, bar_color):
            base = alt.Chart(df_bar).encode(
                x=alt.X("연도:N", axis=alt.Axis(labelAngle=0, labelColor="#E5E7EB", title=None)),
                y=alt.Y("금액:Q", axis=alt.Axis(format=",.0f", labelColor="#9CA3AF", title=None, gridColor="rgba(255,255,255,0.08)")),
                tooltip=["연도", alt.Tooltip("금액:Q", format=",.1f")],
            )
            bars = base.mark_bar(size=26, cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=bar_color)
            labels = base.mark_text(dy=-8, color="#F4F4F6", fontSize=11, fontWeight="bold").encode(
                text=alt.Text("금액:Q", format=",.0f")
            )
            return (
                (bars + labels)
                .properties(height=240)
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )

        if fin_3yr:
            years_sorted = sorted(fin_3yr.keys())
            sales_rows, op_rows, net_rows = [], [], []
            for yr in years_sorted:
                vals = fin_3yr[yr]
                sales_rows.append({"연도": yr, "금액": round((vals.get("매출액") or 0) / 100_000_000, 1)})
                op_rows.append({"연도": yr, "금액": round((vals.get("영업이익") or 0) / 100_000_000, 1)})
                net_rows.append({"연도": yr, "금액": round((vals.get("당기순이익") or 0) / 100_000_000, 1)})

            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                st.markdown('<div class="sub-head">REVENUE · 연간 매출액 (억 원)</div>', unsafe_allow_html=True)
                st.altair_chart(make_slim_vertical_bar(pd.DataFrame(sales_rows), "#D9FF54"), use_container_width=True)
            with b_col2:
                st.markdown('<div class="sub-head">OPERATING INCOME · 연간 영업이익 (억 원)</div>', unsafe_allow_html=True)
                st.altair_chart(make_slim_vertical_bar(pd.DataFrame(op_rows), "#10B981"), use_container_width=True)
            with b_col3:
                st.markdown('<div class="sub-head">NET INCOME · 연간 당기순이익 (억 원)</div>', unsafe_allow_html=True)
                st.altair_chart(make_slim_vertical_bar(pd.DataFrame(net_rows), "#38BDF8"), use_container_width=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        t_left, t_right = st.columns([1.15, 1])
        with t_left:
            st.markdown('<div class="sub-head">DART 3-YEAR FINANCIAL STATEMENTS</div>', unsafe_allow_html=True)
            if fin_3yr:
                df_fin = pd.DataFrame(fin_3yr)[sorted(fin_3yr.keys())]
                st.dataframe(df_fin.map(format_krw_unit), use_container_width=True, height=255)
            else:
                st.info("DART 재무제표 데이터를 불러오지 못했습니다.")

        with t_right:
            st.markdown('<div class="sub-head">MARKET INVESTMENT METRICS</div>', unsafe_allow_html=True)
            if naver_data:
                clean_naver = {k: str(v) for k, v in naver_data.items() if k not in ("종목명", "현재가")}
                df_nv = pd.DataFrame(list(clean_naver.items()), columns=["지표명", "수치"])
                st.dataframe(df_nv, hide_index=True, use_container_width=True, height=255)

        st.markdown(
            f'<div class="ed-section"><div class="ed-section-title">04. LATEST HEADLINES — {stock_name}</div>'
            '<div class="ed-section-num">TOP 5 NEWS</div></div>',
            unsafe_allow_html=True,
        )

        if news_top5:
            news_html_blocks = []
            for idx, item in enumerate(news_top5, 1):
                news_html_blocks.append(
                    f'<a href="{item["url"]}" target="_blank" class="ed-news-row">'
                    f'<div class="ed-news-title">0{idx}. &nbsp;{item["title"]} &nbsp;↗</div>'
                    f'<div class="ed-news-meta">{item["press"]} &nbsp;·&nbsp; {item["date"]}</div>'
                    f'</a>'
                )
            st.markdown("".join(news_html_blocks), unsafe_allow_html=True)
        else:
            st.info("최신 뉴스 목록을 가져오지 못했습니다.")

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">05. FINAL RESEARCH VERDICT</div>'
            '<div class="ed-section-num">OBJECTIVE SYNTHESIS</div></div>',
            unsafe_allow_html=True,
        )

        fin_eok_dict = {
            yr: {k: format_krw_unit(v) for k, v in vals.items()}
            for yr, vals in fin_3yr.items()
        }
        full_payload_str = json.dumps(
            {
                "종목": f"{stock_name} ({code})",
                "정량_산출_투자등급": f"{rating['en_grade']} ({rating['grade']})",
                "정량_점수": f"{rating['total_score']}점 / 100점",
                "등급_산출_핵심근거": rating["reasons"],
                "3개년_재무추이_억환산": fin_eok_dict,
                "밸류_및_차트지표": json.loads(ind_payload_str),
                "최근뉴스제목": [n["title"] for n in news_top5],
            },
            ensure_ascii=False,
            indent=2,
        )

        final_prompt = f"""당신은 냉철하고 객관적인 수석 리서치 애널리스트입니다.
이모지는 단 하나도 사용하지 마세요.
제공된 [정량 데이터]의 사실적 재무 추이, 밸류에이션, 차트 기술적 지표, 최신 뉴스 헤드라인만을 바탕으로 종합 리포트를 작성하세요.
정량 알고리즘이 산출한 종합 투자 의견 등급은 **[{rating['en_grade']} · {rating['grade']}]** (5단계 기준: 적극매수 > 매수 > 보류 > 위험 > 매우 위험)입니다.

아래 양식대로 깔끔하게 작성하세요:

### 최종 종합 투자 의견: **{rating['en_grade']} · {rating['grade']}** (종합 점수 {rating['total_score']}점 / 100점)
* **의견 결정의 핵심 근거:** (실적 추세, 밸류에이션, 차트 추세를 종합해 왜 '{rating['grade']}' 의견이 도출되었는지 2~3문장으로 객관적 서술)

#### 1. 실적 및 재무 팩트 체크
* (최근 3개년 매출·영업이익·순이익 증감 흐름과 부채비율 등 객관적 사실 요약)

#### 2. 긍정적 모멘텀 (상승 요인)
* (재무·차트·뉴스에서 확인되는 강점 2가지)

#### 3. 잠재 리스크 (주의 요인)
* (데이터상 확인되는 약점 또는 주의할 지표 2가지)

*(마지막 줄에 "※ 본 리포트는 DART 공시 및 시장 지표의 정량 분석 결과이며, 최종 투자 판단의 책임은 투자자 본인에게 있습니다." 표기)*"""

        with st.spinner("모든 재무 팩트, 차트, 뉴스를 종합하여 최종 투자 의견을 작성 중입니다..."):
            final_report = ask_gemini_ai(GEMINI_API_KEY, final_prompt, full_payload_str)

        st.markdown(f'<div class="ed-report-box">{final_report}</div>', unsafe_allow_html=True)import ast
import json
import math
import os
import re
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
import opendartreader
from google import genai

# ====== 페이지 기본 설정 ======
st.set_page_config(
    page_title="DATAQUANT — Interactive Equity Terminal",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ====== API 키 로드 ======
DART_API_KEY = st.secrets.get("DART_API_KEY", "934f9c5cd12bf41dae6318eb1893687c1ee100e6")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")).strip()
GEMINI_MODEL = "gemini-2.5-flash"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://m.stock.naver.com/",
}
KEY_ACCOUNTS = ["자산총계", "부채총계", "자본총계", "매출액", "영업이익", "당기순이익", "당기순이익(손실)"]

# ====== 세션 상태 ======
if "entered" not in st.session_state:
    st.session_state.entered = False
if "active_code" not in st.session_state:
    st.session_state.active_code = ""

# ====== 하이엔드 다크 모션 CSS ======
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Pretendard', -apple-system, sans-serif;
    color: #F4F4F6;
}

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

.stApp {
    background-color: #0B0C10;
    color: #F4F4F6;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    max-width: 1260px !important;
    position: relative;
    z-index: 2;
}

@keyframes scatterIn {
    0% { opacity: 0; transform: scale(0.94) translateY(22px); }
    100% { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes floatSlow {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}

@keyframes pulseRing {
    0% { box-shadow: 0 0 0 0 rgba(217, 255, 84, 0.45); }
    70% { box-shadow: 0 0 0 18px rgba(217, 255, 84, 0); }
    100% { box-shadow: 0 0 0 0 rgba(217, 255, 84, 0); }
}

.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    margin-bottom: 1.8rem;
}
.nav-brand {
    font-family: 'Syne', sans-serif;
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
}
.nav-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
    letter-spacing: 0.08em;
}
.copy-url-btn {
    background: rgba(217, 255, 84, 0.12);
    border: 1px solid rgba(217, 255, 84, 0.55);
    color: #D9FF54;
    padding: 6px 16px;
    border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.22s ease;
    letter-spacing: 0.04em;
}
.copy-url-btn:hover {
    background: #D9FF54;
    color: #0B0C10;
    transform: scale(1.04);
}

.dv-hero {
    text-align: center;
    padding: 5.5rem 1rem 2.2rem 1rem;
    animation: scatterIn 0.85s cubic-bezier(0.16, 1, 0.3, 1);
}
.dv-wordmark {
    font-family: 'Syne', sans-serif;
    font-size: clamp(3rem, 7vw, 5.8rem);
    font-weight: 800;
    letter-spacing: 0.06em;
    line-height: 1;
    margin: 0;
    user-select: none;
}
.dv-solid { color: #FFFFFF; }
.dv-outline {
    color: transparent;
    -webkit-text-stroke: 1.6px rgba(255, 255, 255, 0.82);
}
.dv-tagline {
    font-size: 1.05rem;
    color: #9CA3AF;
    margin-top: 18px;
}

div.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #FFFFFF !important;
    border: 1.5px solid rgba(255, 255, 255, 0.45) !important;
    border-radius: 999px !important;
    padding: 0.75rem 2.2rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    animation: floatSlow 3s infinite ease-in-out, pulseRing 2.6s infinite;
    transition: all 0.28s ease !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: #D9FF54 !important;
    color: #0B0C10 !important;
    border-color: #D9FF54 !important;
}

div[data-testid="stForm"] {
    background: rgba(22, 24, 31, 0.88) !important;
    backdrop-filter: blur(16px);
    border: 1.5px solid rgba(255, 255, 255, 0.28) !important;
    border-radius: 999px !important;
    padding: 8px 10px 8px 22px !important;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.55);
}
div[data-testid="stTextInput"] > div > div {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stTextInput"] input {
    background-color: transparent !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #D9FF54 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.25rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em !important;
    border: none !important;
}
button[kind="primaryFormSubmit"] {
    background-color: #D9FF54 !important;
    color: #0B0C10 !important;
    border-radius: 999px !important;
    border: none !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 800 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.3rem !important;
}
button[kind="primaryFormSubmit"]:hover {
    background-color: #FFFFFF !important;
    color: #0B0C10 !important;
}

.glass-stage {
    background: rgba(18, 20, 27, 0.86);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 26px;
    padding: 2.2rem 2.5rem;
    margin: 1.6rem 0 2.2rem 0;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
    animation: scatterIn 0.6s ease-out;
}
.stage-kicker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
    letter-spacing: 0.08em;
}
.stage-title-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 16px;
    margin-top: 8px;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.stage-stock-name {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #FFFFFF;
    margin: 0;
}
.stage-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 800;
    color: #D9FF54;
}
.rings-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-top: 1.8rem;
}
.ring-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}
.score-circle {
    width: 94px;
    height: 94px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.45rem;
    font-weight: 800;
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.03);
    transition: transform 0.3s ease;
}
.score-circle:hover { transform: scale(1.1); }
.ring-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
    margin-top: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.verdict-strip {
    margin-top: 1.8rem;
    padding: 16px 22px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}
.verdict-tag {
    font-weight: 800;
    font-size: 1.05rem;
    padding: 7px 20px;
    border-radius: 999px;
}

.ed-section {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.18);
    padding-bottom: 10px;
    margin: 2.6rem 0 1.3rem 0;
}
.ed-section-title {
    font-family: 'Syne', 'Pretendard', sans-serif;
    font-size: 1.32rem;
    font-weight: 800;
    color: #FFFFFF;
}
.ed-section-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    color: #D9FF54;
}

.sub-head {
    font-family: 'JetBrains Mono', 'Pretendard', sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    color: #D1D5DB;
    letter-spacing: 0.02em;
    margin-bottom: 10px;
}

.ed-card {
    background: rgba(22, 24, 32, 0.82);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px;
    padding: 20px 22px;
    transition: all 0.25s ease;
}
.ed-card:hover {
    transform: translateY(-4px);
    border-color: #D9FF54;
}
.ed-card-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 700;
    color: #9CA3AF;
}
.ed-card-val {
    font-family: 'JetBrains Mono', 'Pretendard', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 6px 0;
}
.ed-card-sub {
    font-size: 0.82rem;
    font-weight: 600;
    color: #A5B4FC;
}

.ed-report-box {
    background: rgba(18, 20, 27, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 20px;
    padding: 24px 28px;
    line-height: 1.78;
    color: #E5E7EB;
}

.ed-news-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(22, 24, 32, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 15px 22px;
    margin-bottom: 10px;
    text-decoration: none !important;
    transition: all 0.24s ease;
}
.ed-news-row:hover {
    background: rgba(217, 255, 84, 0.1);
    border-color: #D9FF54;
    transform: translateX(6px);
}
.ed-news-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: #F9FAFB;
}
.ed-news-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #D9FF54;
    white-space: nowrap;
    margin-left: 16px;
}
</style>
""", unsafe_allow_html=True)

# ====== 파티클 배경 & URL 복사 스크립트 ======
components.html("""
<script>
(function() {
    const parentWin = window.parent;
    const parentDoc = parentWin.document;

    // 상단 우측 URL 복사 전역 함수 등록
    parentWin.copyAppShareUrl = function(btn) {
        const shareUrl = parentWin.location.origin + parentWin.location.pathname;
        if (parentWin.navigator && parentWin.navigator.clipboard) {
            parentWin.navigator.clipboard.writeText(shareUrl).then(() => {
                const orig = btn.innerText;
                btn.innerText = 'COPIED URL ✓';
                btn.style.background = '#D9FF54';
                btn.style.color = '#0B0C10';
                setTimeout(() => {
                    btn.innerText = orig;
                    btn.style.background = '';
                    btn.style.color = '';
                }, 2000);
            });
        } else {
            const tmp = parentDoc.createElement('input');
            tmp.value = shareUrl;
            parentDoc.body.appendChild(tmp);
            tmp.select();
            parentDoc.execCommand('copy');
            parentDoc.body.removeChild(tmp);
            btn.innerText = 'COPIED URL ✓';
        }
    };

    if (parentDoc.getElementById('dv-particle-canvas')) return;

    const canvas = parentDoc.createElement('canvas');
    canvas.id = 'dv-particle-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    parentDoc.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let w = canvas.width = parentWin.innerWidth;
    let h = canvas.height = parentWin.innerHeight;

    parentWin.addEventListener('resize', () => {
        w = canvas.width = parentWin.innerWidth;
        h = canvas.height = parentWin.innerHeight;
    });

    const mouse = { x: w / 2, y: h / 2, active: false };
    parentWin.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.active = true;
    });

    parentWin.addEventListener('click', (e) => {
        particles.forEach(p => {
            const dx = p.x - e.clientX;
            const dy = p.y - e.clientY;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 280) {
                const force = (280 - dist) / 280;
                p.vx += (dx / dist) * force * 6.5;
                p.vy += (dy / dist) * force * 6.5;
            }
        });
    });

    const count = 120;
    const particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        size: Math.random() * 2.0 + 0.8,
        alpha: Math.random() * 0.5 + 0.2
    }));

    function draw() {
        ctx.clearRect(0, 0, w, h);
        for (let i = 0; i < count; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vx *= 0.985;
            p.vy *= 0.985;

            if (Math.abs(p.vx) < 0.16) p.vx += (Math.random() - 0.5) * 0.08;
            if (Math.abs(p.vy) < 0.16) p.vy += (Math.random() - 0.5) * 0.08;

            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
            ctx.fill();

            if (mouse.active) {
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 145) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(217, 255, 84, ${(1 - dist / 145) * 0.35})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
})();
</script>
""", height=0, width=0)


@st.cache_resource
def init_dart_client(api_key):
    if hasattr(opendartreader, "OpenDartReader"):
        return opendartreader.OpenDartReader(api_key)
    if hasattr(opendartreader, "Dart"):
        return opendartreader.Dart(api_key)
    try:
        from opendartreader.dart import Dart
        return Dart(api_key)
    except ImportError:
        from opendartreader.dart import OpenDartReader
        return OpenDartReader(api_key)


def to_number(text):
    if text is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(text))
    try:
        return float(cleaned) if cleaned not in ("", "-", ".") else None
    except ValueError:
        return None


def format_krw_unit(val):
    if val is None or pd.isna(val):
        return "-"
    num = float(val)
    sign = "-" if num < 0 else ""
    num = abs(num)
    eok = num / 100_000_000
    if eok >= 10000:
        jo = int(eok // 10000)
        rem_eok = int(round(eok % 10000))
        return f"{sign}{jo}조 {rem_eok:,}억"
    return f"{sign}{int(round(eok)):,}억"


def calc_ema(values, period):
    ema = []
    k = 2 / (period + 1)
    for i, v in enumerate(values):
        if i == 0:
            ema.append(v)
        else:
            ema.append(v * k + ema[-1] * (1 - k))
    return ema


@st.cache_data(ttl=300)
def fetch_all_stock_data(stock_code):
    naver_data = {}
    try:
        r1 = requests.get(f"https://m.stock.naver.com/api/stock/{stock_code}/basic", headers=HEADERS, timeout=8)
        b_json = r1.json()
        if "stockName" in b_json:
            naver_data["종목명"] = b_json["stockName"]
        if "closePrice" in b_json:
            naver_data["현재가"] = to_number(b_json["closePrice"])
        if "fluctuationsRatio" in b_json:
            naver_data["전일대비등락률"] = f"{b_json['fluctuationsRatio']}%"
    except Exception:
        pass

    try:
        r2 = requests.get(f"https://m.stock.naver.com/api/stock/{stock_code}/integration", headers=HEADERS, timeout=8)
        i_json = r2.json()
        for item in i_json.get("totalInfos", []):
            key = item.get("key")
            val = item.get("value")
            if key and val:
                naver_data[key] = val
    except Exception:
        pass

    end_dt = datetime.now()
    day_start = (end_dt - timedelta(days=230)).strftime("%Y%m%d")
    month_start = (end_dt - timedelta(days=1200)).strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    def get_candles(tf, s_dt):
        url = f"https://api.finance.naver.com/siseJson.naver?symbol={stock_code}&requestType=1&startTime={s_dt}&endTime={end_str}&timeframe={tf}"
        recs = []
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            rows = ast.literal_eval(r.text.strip())
            for row in rows[1:]:
                if len(row) >= 6:
                    d_raw = str(row[0]).strip()
                    d_fmt = f"{d_raw[:4]}-{d_raw[4:6]}-{d_raw[6:8]}" if tf == "day" and len(d_raw) == 8 else (f"{d_raw[:4]}-{d_raw[4:6]}" if len(d_raw) >= 6 else d_raw)
                    cp = float(row[4])
                    if cp > 0:
                        recs.append({"날짜": d_fmt, "종가": cp})
        except Exception:
            pass
        return pd.DataFrame(recs)

    df_day = get_candles("day", day_start)
    df_month = get_candles("month", month_start)

    tech = {}
    if len(df_day) >= 26:
        closes = df_day["종가"].tolist()
        cur_p = closes[-1]

        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        recent_14 = deltas[-14:]
        avg_gain = sum([d for d in recent_14 if d > 0]) / 14
        avg_loss = sum([-d for d in recent_14 if d < 0]) / 14
        rsi_14 = 100.0 if avg_loss == 0 else round(100 - (100 / (1 + (avg_gain / avg_loss))), 2)
        rsi_label = "과매수 (단기과열)" if rsi_14 >= 70 else ("과매도 (저점영역)" if rsi_14 <= 30 else "중립 구간")

        ema12 = calc_ema(closes, 12)
        ema26 = calc_ema(closes, 26)
        macd_line = [a - b for a, b in zip(ema12, ema26)]
        signal_line = calc_ema(macd_line, 9)
        macd_now = round(macd_line[-1], 1)
        sig_now = round(signal_line[-1], 1)
        macd_hist = round(macd_now - sig_now, 1)
        macd_status = "상승 추세 (골든크로스)" if macd_hist > 0 else "하락 압력 (데드크로스)"

        df_day["20일선"] = df_day["종가"].rolling(20).mean()
        std20 = df_day["종가"].rolling(20).std()
        df_day["볼린저상단"] = df_day["20일선"] + (std20 * 2)
        df_day["볼린저하단"] = df_day["20일선"] - (std20 * 2)

        bb_upper = df_day["볼린저상단"].iloc[-1]
        bb_lower = df_day["볼린저하단"].iloc[-1]
        bb_pct = round(((cur_p - bb_lower) / (bb_upper - bb_lower)) * 100, 1) if (bb_upper - bb_lower) > 0 else 50.0

        tech = {
            "RSI": (rsi_14, rsi_label),
            "MACD": (macd_now, sig_now, macd_hist, macd_status),
            "볼린저밴드": (int(round(bb_upper)), int(round(bb_lower)), bb_pct, f"밴드 내 위치 {bb_pct}%"),
            "최근60일_최고가": int(max(closes[-60:])),
            "최근60일_최저가": int(min(closes[-60:])),
        }
        for period in [20, 60, 120]:
            if len(closes) >= period:
                ma = sum(closes[-period:]) / period
                disp = round((cur_p / ma) * 100, 2)
                tech[f"MA{period}"] = (int(round(ma)), disp, round(disp - 100, 2))

    if len(df_month) >= 12:
        df_month["12개월선"] = df_month["종가"].rolling(12).mean()
        std12 = df_month["종가"].rolling(12).std()
        df_month["볼린저상단"] = df_month["12개월선"] + (std12 * 2)
        df_month["볼린저하단"] = df_month["12개월선"] - (std12 * 2)

    dart = init_dart_client(DART_API_KEY)
    fin_3yr, latest_year = {}, None
    current_year = datetime.now().year
    for target_year in [current_year - 1, current_year - 2]:
        try:
            df_d = dart.finstate(stock_code, target_year)
        except Exception:
            continue
        if df_d is not None and len(df_d) > 0:
            if "fs_div" in df_d.columns and "CFS" in df_d["fs_div"].values:
                df_d = df_d[df_d["fs_div"] == "CFS"]
            res = {f"{target_year}년": {}, f"{target_year - 1}년": {}, f"{target_year - 2}년": {}}
            for _, row in df_d.iterrows():
                nm = row.get("account_nm")
                if nm in KEY_ACCOUNTS:
                    std_nm = "당기순이익" if "당기순이익" in nm else nm
                    res[f"{target_year}년"].setdefault(std_nm, to_number(row.get("thstrm_amount")))
                    res[f"{target_year - 1}년"].setdefault(std_nm, to_number(row.get("frmtrm_amount")))
                    res[f"{target_year - 2}년"].setdefault(std_nm, to_number(row.get("bfefrmtrm_amount")))
            if res[f"{target_year}년"]:
                fin_3yr, latest_year = res, f"{target_year}년"
                break

    news_list = []
    seen_titles = set()
    try:
        r_n = requests.get(f"https://m.stock.naver.com/api/news/stock/{stock_code}?pageSize=10&page=1", headers=HEADERS, timeout=8)
        for grp in r_n.json():
            for item in grp.get("items", []):
                raw_title = str(item.get("title", "")).strip()
                title = raw_title.replace("&quot;", '"').replace("&amp;", "&").replace("<b>", "").replace("</b>", "")
                oid = str(item.get("officeId", "")).strip()
                aid = str(item.get("articleId", "")).strip()
                press = str(item.get("officeName", "")).strip()
                if not title or not press or title in seen_titles:
                    continue
                seen_titles.add(title)
                dt_raw = str(item.get("datetime", "")).strip()
                date_fmt = f"{dt_raw[:4]}.{dt_raw[4:6]}.{dt_raw[6:8]}" if len(dt_raw) >= 8 else ""
                link = f"https://n.news.naver.com/mnews/article/{oid}/{aid}" if (oid and aid) else f"https://m.stock.naver.com/domestic/stock/{stock_code}/news"
                news_list.append({"title": title, "url": link, "press": press, "date": date_fmt})
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
    except Exception:
        pass

    return naver_data, tech, df_day.tail(60), df_month.tail(36), fin_3yr, latest_year, news_list


def compute_valuation_and_rating(fin_3yr, latest_year, naver_data, tech_data):
    formulas = {}
    val_score, prof_score, mom_score = 50, 50, 50
    reasons = []

    latest = fin_3yr.get(latest_year, {}) if latest_year else {}
    sales = latest.get("매출액")
    op_profit = latest.get("영업이익")
    net_income = latest.get("당기순이익")
    debt = latest.get("부채총계")
    equity = latest.get("자본총계")

    if sales and op_profit is not None:
        opm = round((op_profit / sales) * 100, 2)
        formulas["영업이익률"] = opm
        if opm >= 15:
            prof_score += 22
            reasons.append("높은 영업이익률(15% 이상)")
        elif opm > 0:
            prof_score += 8
        else:
            prof_score -= 22
            reasons.append("영업적자 상태")

    if sales and net_income is not None:
        formulas["순이익률"] = round((net_income / sales) * 100, 2)

    if debt and equity and equity > 0:
        debt_ratio = round((debt / equity) * 100, 2)
        formulas["부채비율"] = debt_ratio
        if debt_ratio <= 80:
            prof_score += 14
            reasons.append("우수한 재무건전성(부채비율 80% 이하)")
        elif debt_ratio >= 200:
            prof_score -= 18
            reasons.append("높은 부채부담(200% 이상)")

    roe_val = None
    if net_income is not None and equity and equity > 0:
        roe_val = round((net_income / equity) * 100, 2)
    elif "ROE" in naver_data:
        roe_val = to_number(naver_data["ROE"])

    if roe_val is not None:
        formulas["ROE"] = roe_val
        if roe_val >= 12:
            prof_score += 18
            reasons.append(f"우수한 ROE ({roe_val}%)")
        elif roe_val < 0:
            prof_score -= 18
            reasons.append("마이너스 ROE")

    per_val = to_number(naver_data.get("PER"))
    pbr_val = to_number(naver_data.get("PBR"))
    eps_val = to_number(naver_data.get("EPS"))
    bps_val = to_number(naver_data.get("BPS"))

    formulas["PER"] = per_val
    formulas["PBR"] = pbr_val

    if per_val and per_val > 0:
        if per_val <= 12:
            val_score += 20
            reasons.append(f"저PER 매력 구간 ({per_val}배)")
        elif per_val >= 40:
            val_score -= 15
            reasons.append(f"높은 PER 부담 ({per_val}배)")

    if pbr_val and pbr_val > 0 and pbr_val < 1.0:
        val_score += 15
        reasons.append(f"자산가치 저평가 (PBR {pbr_val}배)")

    current_price = naver_data.get("현재가")
    if eps_val and bps_val and eps_val > 0 and bps_val > 0:
        graham_price = int(round(math.sqrt(22.5 * eps_val * bps_val)))
        diff_pct = round(((graham_price - current_price) / current_price) * 100, 1) if current_price else 0
        formulas["그레이엄 적정주가"] = (graham_price, diff_pct)
        if diff_pct >= 20:
            val_score += 15
            reasons.append("그레이엄 적정가 대비 상승 여력")

    macd_info = tech_data.get("MACD")
    if macd_info:
        if macd_info[2] > 0:
            mom_score += 18
            reasons.append("MACD 상승 추세 유지")
        else:
            mom_score -= 12
            reasons.append("MACD 단기 하락 추세")

    rsi_val = tech_data.get("RSI", (None, ""))[0]
    if rsi_val is not None:
        if rsi_val <= 32:
            mom_score += 16
            reasons.append("RSI 과매도 저점 구간")
        elif rsi_val >= 72:
            mom_score -= 16
            reasons.append("RSI 단기 과열 구간")

    val_score = max(10, min(99, val_score))
    prof_score = max(10, min(99, prof_score))
    mom_score = max(10, min(99, mom_score))
    total_score = round((val_score + prof_score + mom_score) / 3)

    if total_score >= 75:
        grade, en_grade, pill_bg, pill_fg = "적극매수", "STRONG BUY", "#D9FF54", "#0B0C10"
    elif total_score >= 60:
        grade, en_grade, pill_bg, pill_fg = "매수", "BUY", "#38BDF8", "#0B0C10"
    elif total_score >= 45:
        grade, en_grade, pill_bg, pill_fg = "보류", "HOLD", "#FBBF24", "#0B0C10"
    elif total_score >= 30:
        grade, en_grade, pill_bg, pill_fg = "위험", "UNDERPERFORM", "#FB923C", "#0B0C10"
    else:
        grade, en_grade, pill_bg, pill_fg = "매우 위험", "HIGH RISK", "#F43F5E", "#FFFFFF"

    return formulas, {
        "grade": grade,
        "en_grade": en_grade,
        "total_score": total_score,
        "val_score": val_score,
        "prof_score": prof_score,
        "mom_score": mom_score,
        "pill_bg": pill_bg,
        "pill_fg": pill_fg,
        "reasons": reasons[:3] if reasons else ["주요 지표가 중립 구간에 위치"],
    }


def ask_gemini_ai(api_key, system_instruction, payload_json):
    if not api_key:
        return "GEMINI_API_KEY가 비어 있습니다. Streamlit Secrets에 Google AI Studio API 키(AIza...)를 저장해 주세요."
    prompt = f"{system_instruction}\n\n[정량 데이터]\n{payload_json}"
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"AI 호출 오류 (API 키 형식을 확인해 주세요 — Google AI Studio의 'AIza...' 키가 필요합니다): {e}"


# ================= 상단 내비게이션 바 (우측 상단 원클릭 URL 복사 버튼 탑재) =================
today_str = datetime.now().strftime("%b %d, %Y").upper()
st.markdown(
    f'<div class="top-nav">'
    f'<div class="nav-brand">q.terminal.</div>'
    f'<div class="nav-meta">HUMAN — DATA EQUITY INTERFACE &nbsp;/&nbsp; {today_str}</div>'
    f'<button class="copy-url-btn" onclick="window.copyAppShareUrl(this)">SHARE URL ↗</button>'
    f'</div>',
    unsafe_allow_html=True,
)

# ================= [1단계] 클릭 전환 인터랙티브 인트로 스테이지 =================
if not st.session_state.entered:
    st.markdown(
        '<div class="dv-hero">'
        '<h1 class="dv-wordmark"><span class="dv-solid">DATA</span><span class="dv-outline">QUANT</span></h1>'
        '<p class="dv-tagline">Interactions Investisseur — Données &nbsp;·&nbsp; 클릭하여 정량 리서치 터미널을 여세요</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, enter_col, _ = st.columns([1.6, 1, 1.6])
    with enter_col:
        if st.button("ENTER TERMINAL  ↓", use_container_width=True):
            st.session_state.entered = True
            st.rerun()

# ================= [2단계] 종목코드 입력 & 리포트 스테이지 =================
else:
    st.markdown(
        '<div style="text-align:center; padding: 0.5rem 0 1.4rem 0;">'
        '<div style="font-family:\'Syne\',sans-serif; font-size:2.1rem; font-weight:800; letter-spacing:0.04em;">'
        '<span class="dv-solid">DATA</span><span class="dv-outline">QUANT</span>'
        '<span style="font-size:1rem; color:#D9FF54; font-family:\'JetBrains Mono\',monospace; vertical-align:middle; margin-left:8px;">// TERMINAL</span>'
        '</div>'
        '<p style="color:#9CA3AF; font-size:0.92rem; margin-top:6px;">분석할 한국 주식 종목코드 6자리를 입력하고 ENTER 또는 ANALYZE를 누르세요</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1.15, 2.1, 1.15])
    with center_col:
        with st.form("search_form", clear_on_submit=False):
            in_col, btn_col = st.columns([3.1, 1.3])
            with in_col:
                stock_code = st.text_input(
                    "종목코드",
                    value=st.session_state.active_code or "003000",
                    max_chars=6,
                    placeholder="003000",
                    label_visibility="collapsed",
                )
            with btn_col:
                submitted = st.form_submit_button("ANALYZE →", type="primary", use_container_width=True)

        st.markdown(
            '<div style="text-align:center; color:#9CA3AF; font-family:\'JetBrains Mono\',monospace; font-size:0.78rem; margin-top:8px;">'
            'QUICK TICKERS: <b style="color:#D9FF54;">003000</b> 부광약품 · <b style="color:#D9FF54;">005930</b> 삼성전자 · <b style="color:#D9FF54;">000660</b> SK하이닉스 · <b style="color:#D9FF54;">035420</b> NAVER'
            '</div>',
            unsafe_allow_html=True,
        )

    if submitted and stock_code:
        st.session_state.active_code = stock_code.strip().zfill(6)

    if st.session_state.active_code:
        code = st.session_state.active_code

        with st.spinner("실시간 주가 차트, 기술적 지표, DART 3개년 재무, 최신 뉴스를 분석 중입니다..."):
            naver_data, tech_data, df_day, df_month, fin_3yr, latest_year, news_top5 = fetch_all_stock_data(code)
            stock_name = naver_data.get("종목명") or f"종목_{code}"
            formulas, rating = compute_valuation_and_rating(fin_3yr, latest_year, naver_data, tech_data)

        cur_p = naver_data.get("현재가")
        chg_r = naver_data.get("전일대비등락률", "")
        cur_p_str = f"{int(cur_p):,} KRW ({chg_r})" if cur_p else "N/A"
        reasons_text = " · ".join(rating["reasons"])

        stage_html = (
            f'<div class="glass-stage">'
            f'<div class="stage-kicker">EQUITY DOSSIER &nbsp;/&nbsp; KRX : {code}</div>'
            f'<div class="stage-title-row">'
            f'<h2 class="stage-stock-name">{stock_name}</h2>'
            f'<div class="stage-price">{cur_p_str}</div>'
            f'</div>'
            f'<div class="rings-grid">'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #D9FF54;">{rating["total_score"] / 10:.2f}</div><div class="ring-label">TOTAL INDEX / 10</div></div>'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #38BDF8;">{rating["val_score"] / 10:.2f}</div><div class="ring-label">VALUATION</div></div>'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #A78BFA;">{rating["prof_score"] / 10:.2f}</div><div class="ring-label">PROFITABILITY</div></div>'
            f'<div class="ring-item"><div class="score-circle" style="border: 3px solid #34D399;">{rating["mom_score"] / 10:.2f}</div><div class="ring-label">MOMENTUM</div></div>'
            f'</div>'
            f'<div class="verdict-strip">'
            f'<div><span style="font-family:\'JetBrains Mono\',monospace; font-size:0.75rem; color:#9CA3AF; display:block;">KEY QUANT DRIVERS</span>'
            f'<span style="font-size:0.98rem; font-weight:600; color:#F4F4F6;">{reasons_text}</span></div>'
            f'<div class="verdict-tag" style="background:{rating["pill_bg"]}; color:{rating["pill_fg"]};">{rating["en_grade"]} &nbsp;·&nbsp; {rating["grade"]}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(stage_html, unsafe_allow_html=True)

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">01. PRICE ACTION & TECHNICAL CHART</div>'
            '<div class="ed-section-num">INTERACTIVE CHART</div></div>',
            unsafe_allow_html=True,
        )

        g_col, t_col = st.columns([1.48, 1])

        with g_col:
            ctrl1, ctrl2 = st.columns([1.2, 1])
            with ctrl1:
                timeframe_opt = st.radio(
                    "차트 기준",
                    ["일별 (최근 60일)", "월별 (최근 3년)"],
                    horizontal=True,
                    label_visibility="collapsed",
                )
            with ctrl2:
                show_bb = st.toggle("볼린저밴드 상·하단 표시", value=True)

            is_daily = timeframe_opt.startswith("일별")
            src_df = df_day.copy() if is_daily else df_month.copy()
            ma_col_name = "20일선" if is_daily else "12개월선"

            if not src_df.empty:
                plot_cols = ["종가"]
                if ma_col_name in src_df.columns:
                    plot_cols.append(ma_col_name)
                if show_bb and "볼린저상단" in src_df.columns and "볼린저하단" in src_df.columns:
                    plot_cols.extend(["볼린저상단", "볼린저하단"])

                melted = src_df[["날짜"] + plot_cols].melt("날짜", var_name="지표", value_name="가격")
                color_domain = ["종가", ma_col_name, "볼린저상단", "볼린저하단"]
                color_range = ["#D9FF54", "#38BDF8", "#F43F5E", "#10B981"]

                dates_list = src_df["날짜"].tolist()
                step = max(1, len(dates_list) // 7)
                tick_vals = dates_list[::step]

                price_chart = (
                    alt.Chart(melted)
                    .mark_line(strokeWidth=2.3)
                    .encode(
                        x=alt.X(
                            "날짜:N",
                            sort=None,
                            axis=alt.Axis(
                                values=tick_vals,
                                labelAngle=0,
                                labelColor="#9CA3AF",
                                title=None,
                                grid=False,
                            ),
                        ),
                        y=alt.Y(
                            "가격:Q",
                            scale=alt.Scale(zero=False),
                            axis=alt.Axis(
                                format=",.0f",
                                labelColor="#9CA3AF",
                                title=None,
                                gridColor="rgba(255,255,255,0.08)",
                            ),
                        ),
                        color=alt.Color(
                            "지표:N",
                            scale=alt.Scale(domain=color_domain, range=color_range),
                            legend=alt.Legend(orient="bottom", title=None, labelColor="#E5E7EB"),
                        ),
                        tooltip=["날짜", "지표", alt.Tooltip("가격:Q", format=",.0f")],
                    )
                    .properties(height=340)
                    .configure_view(strokeWidth=0)
                    .configure(background="transparent")
                )
                st.altair_chart(price_chart, use_container_width=True)
            else:
                st.info("주가 차트 데이터를 불러오지 못했습니다.")

        with t_col:
            st.markdown('<div class="sub-head">TECHNICAL TREND & SUPPORT / RESISTANCE</div>', unsafe_allow_html=True)
            chart_payload = json.dumps(
                {"종목": f"{stock_name} ({code})", "현재가": cur_p_str, "기술적지표": tech_data},
                ensure_ascii=False,
                indent=2,
            )
            with st.spinner("차트 추세와 지지·저항선을 분석하는 중..."):
                chart_analysis = ask_gemini_ai(
                    GEMINI_API_KEY,
                    "당신은 전문 차트 테크니컬 애널리스트입니다. 이모지는 절대 사용하지 마세요. 제공된 20·60·120일 이동평균선 이격도, RSI(14일), MACD 추세, 볼린저밴드 위치, 60일 최고/최저가 수치만 근거로 현재 주가 차트의 추세 방향, 단기 지지선과 저항선 가격대, 과열/침체 여부를 4~5줄의 명확한 불릿 포인트로 분석해 주세요.",
                    chart_payload,
                )
            st.markdown(f'<div class="ed-report-box">{chart_analysis}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">02. VALUATION & MOMENTUM METRICS</div>'
            '<div class="ed-section-num">QUANT INDICATORS</div></div>',
            unsafe_allow_html=True,
        )

        per_str = f"{formulas['PER']}배" if formulas.get("PER") else "적자 / N/A"
        pbr_str = f"{formulas['PBR']}배" if formulas.get("PBR") else "N/A"
        roe_val = f"{formulas['ROE']}%" if formulas.get("ROE") is not None else "N/A"
        debt_val = f"{formulas['부채비율']}%" if formulas.get("부채비율") is not None else "N/A"
        opm_val = f"{formulas['영업이익률']}%" if formulas.get("영업이익률") is not None else "N/A"

        rsi_val, rsi_stat = tech_data.get("RSI", (None, "-"))
        macd_info = tech_data.get("MACD")
        macd_str = f"{macd_info[0]}" if macd_info else "N/A"
        macd_sub = macd_info[3] if macd_info else "-"

        if "그레이엄 적정주가" in formulas:
            g_p, g_diff = formulas["그레이엄 적정주가"]
            graham_str = f"{g_p:,}원"
            graham_sub = f"현재가 대비 {g_diff:+.1f}%"
        else:
            graham_str = "산출 불가"
            graham_sub = "EPS/BPS 적자 구간"

        cards_row1 = [
            ("PER · 주가수익비율", per_str, f"EPS {naver_data.get('EPS', 'N/A')}"),
            ("PBR · 주가순자산비율", pbr_str, f"BPS {naver_data.get('BPS', 'N/A')}"),
            ("RSI (14D) · 과열도", f"{rsi_val if rsi_val is not None else 'N/A'}", rsi_stat),
            ("MACD · 추세 시그널", macd_str, macd_sub),
        ]
        cols1 = st.columns(4)
        for col, (lbl, val, sub) in zip(cols1, cards_row1):
            col.markdown(
                f'<div class="ed-card"><div class="ed-card-lbl">{lbl}</div>'
                f'<div class="ed-card-val">{val}</div><div class="ed-card-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        cards_row2 = [
            ("ROE · 자기자본이익률", roe_val, "기준: 10% 이상 우수"),
            ("DEBT RATIO · 부채비율", debt_val, "기준: 100% 이하 안정"),
            ("OP MARGIN · 영업이익률", opm_val, "본업 수익창출력"),
            ("GRAHAM VALUE · 적정가", graham_str, graham_sub),
        ]
        cols2 = st.columns(4)
        for col, (lbl, val, sub) in zip(cols2, cards_row2):
            col.markdown(
                f'<div class="ed-card"><div class="ed-card-lbl">{lbl}</div>'
                f'<div class="ed-card-val">{val}</div><div class="ed-card-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        ind_payload_str = json.dumps(
            {"종목": f"{stock_name} ({code})", "핵심지표": formulas, "기술지표": tech_data, "시장밸류에이션": naver_data},
            ensure_ascii=False,
            indent=2,
        )
        with st.spinner("밸류에이션 및 재무 비율 지표를 해석하는 중..."):
            ind_analysis = ask_gemini_ai(
                GEMINI_API_KEY,
                "당신은 객관적 퀀트 애널리스트입니다. 이모지는 절대 사용하지 마세요. 제공된 PER, PBR, ROE, 부채비율, 영업이익률, 그레이엄 적정주가 수치만 근거로 현재 주가의 밸류에이션 매력도와 재무 건전성을 4줄 내외의 명확한 불릿 포인트로 해석해 주세요.",
                ind_payload_str,
            )
        st.markdown(f'<div class="ed-report-box" style="margin-top:14px;">{ind_analysis}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">03. FINANCIAL STATEMENTS & ANNUAL CHARTS</div>'
            '<div class="ed-section-num">UNIT: 100M KRW (억 원)</div></div>',
            unsafe_allow_html=True,
        )

        def make_slim_vertical_bar(df_bar, bar_color):
            base = alt.Chart(df_bar).encode(
                x=alt.X("연도:N", axis=alt.Axis(labelAngle=0, labelColor="#E5E7EB", title=None)),
                y=alt.Y("금액:Q", axis=alt.Axis(format=",.0f", labelColor="#9CA3AF", title=None, gridColor="rgba(255,255,255,0.08)")),
                tooltip=["연도", alt.Tooltip("금액:Q", format=",.1f")],
            )
            bars = base.mark_bar(size=26, cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=bar_color)
            labels = base.mark_text(dy=-8, color="#F4F4F6", fontSize=11, fontWeight="bold").encode(
                text=alt.Text("금액:Q", format=",.0f")
            )
            return (
                (bars + labels)
                .properties(height=240)
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )

        if fin_3yr:
            years_sorted = sorted(fin_3yr.keys())
            sales_rows, op_rows, net_rows = [], [], []
            for yr in years_sorted:
                vals = fin_3yr[yr]
                sales_rows.append({"연도": yr, "금액": round((vals.get("매출액") or 0) / 100_000_000, 1)})
                op_rows.append({"연도": yr, "금액": round((vals.get("영업이익") or 0) / 100_000_000, 1)})
                net_rows.append({"연도": yr, "금액": round((vals.get("당기순이익") or 0) / 100_000_000, 1)})

            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                st.markdown('<div class="sub-head">REVENUE · 연간 매출액 (억 원)</div>', unsafe_allow_html=True)
                st.altair_chart(make_slim_vertical_bar(pd.DataFrame(sales_rows), "#D9FF54"), use_container_width=True)
            with b_col2:
                st.markdown('<div class="sub-head">OPERATING INCOME · 연간 영업이익 (억 원)</div>', unsafe_allow_html=True)
                st.altair_chart(make_slim_vertical_bar(pd.DataFrame(op_rows), "#10B981"), use_container_width=True)
            with b_col3:
                st.markdown('<div class="sub-head">NET INCOME · 연간 당기순이익 (억 원)</div>', unsafe_allow_html=True)
                st.altair_chart(make_slim_vertical_bar(pd.DataFrame(net_rows), "#38BDF8"), use_container_width=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        t_left, t_right = st.columns([1.15, 1])
        with t_left:
            st.markdown('<div class="sub-head">DART 3-YEAR FINANCIAL STATEMENTS</div>', unsafe_allow_html=True)
            if fin_3yr:
                df_fin = pd.DataFrame(fin_3yr)[sorted(fin_3yr.keys())]
                st.dataframe(df_fin.map(format_krw_unit), use_container_width=True, height=255)
            else:
                st.info("DART 재무제표 데이터를 불러오지 못했습니다.")

        with t_right:
            st.markdown('<div class="sub-head">MARKET INVESTMENT METRICS</div>', unsafe_allow_html=True)
            if naver_data:
                clean_naver = {k: str(v) for k, v in naver_data.items() if k not in ("종목명", "현재가")}
                df_nv = pd.DataFrame(list(clean_naver.items()), columns=["지표명", "수치"])
                st.dataframe(df_nv, hide_index=True, use_container_width=True, height=255)

        st.markdown(
            f'<div class="ed-section"><div class="ed-section-title">04. LATEST HEADLINES — {stock_name}</div>'
            '<div class="ed-section-num">TOP 5 NEWS</div></div>',
            unsafe_allow_html=True,
        )

        if news_top5:
            news_html_blocks = []
            for idx, item in enumerate(news_top5, 1):
                news_html_blocks.append(
                    f'<a href="{item["url"]}" target="_blank" class="ed-news-row">'
                    f'<div class="ed-news-title">0{idx}. &nbsp;{item["title"]} &nbsp;↗</div>'
                    f'<div class="ed-news-meta">{item["press"]} &nbsp;·&nbsp; {item["date"]}</div>'
                    f'</a>'
                )
            st.markdown("".join(news_html_blocks), unsafe_allow_html=True)
        else:
            st.info("최신 뉴스 목록을 가져오지 못했습니다.")

        st.markdown(
            '<div class="ed-section"><div class="ed-section-title">05. FINAL RESEARCH VERDICT</div>'
            '<div class="ed-section-num">OBJECTIVE SYNTHESIS</div></div>',
            unsafe_allow_html=True,
        )

        fin_eok_dict = {
            yr: {k: format_krw_unit(v) for k, v in vals.items()}
            for yr, vals in fin_3yr.items()
        }
        full_payload_str = json.dumps(
            {
                "종목": f"{stock_name} ({code})",
                "정량_산출_투자등급": f"{rating['en_grade']} ({rating['grade']})",
                "정량_점수": f"{rating['total_score']}점 / 100점",
                "등급_산출_핵심근거": rating["reasons"],
                "3개년_재무추이_억환산": fin_eok_dict,
                "밸류_및_차트지표": json.loads(ind_payload_str),
                "최근뉴스제목": [n["title"] for n in news_top5],
            },
            ensure_ascii=False,
            indent=2,
        )

        final_prompt = f"""당신은 냉철하고 객관적인 수석 리서치 애널리스트입니다.
이모지는 단 하나도 사용하지 마세요.
제공된 [정량 데이터]의 사실적 재무 추이, 밸류에이션, 차트 기술적 지표, 최신 뉴스 헤드라인만을 바탕으로 종합 리포트를 작성하세요.
정량 알고리즘이 산출한 종합 투자 의견 등급은 **[{rating['en_grade']} · {rating['grade']}]** (5단계 기준: 적극매수 > 매수 > 보류 > 위험 > 매우 위험)입니다.

아래 양식대로 깔끔하게 작성하세요:

### 최종 종합 투자 의견: **{rating['en_grade']} · {rating['grade']}** (종합 점수 {rating['total_score']}점 / 100점)
* **의견 결정의 핵심 근거:** (실적 추세, 밸류에이션, 차트 추세를 종합해 왜 '{rating['grade']}' 의견이 도출되었는지 2~3문장으로 객관적 서술)

#### 1. 실적 및 재무 팩트 체크
* (최근 3개년 매출·영업이익·순이익 증감 흐름과 부채비율 등 객관적 사실 요약)

#### 2. 긍정적 모멘텀 (상승 요인)
* (재무·차트·뉴스에서 확인되는 강점 2가지)

#### 3. 잠재 리스크 (주의 요인)
* (데이터상 확인되는 약점 또는 주의할 지표 2가지)

*(마지막 줄에 "※ 본 리포트는 DART 공시 및 시장 지표의 정량 분석 결과이며, 최종 투자 판단의 책임은 투자자 본인에게 있습니다." 표기)*"""

        with st.spinner("모든 재무 팩트, 차트, 뉴스를 종합하여 최종 투자 의견을 작성 중입니다..."):
            final_report = ask_gemini_ai(GEMINI_API_KEY, final_prompt, full_payload_str)

        st.markdown(f'<div class="ed-report-box">{final_report}</div>', unsafe_allow_html=True)
