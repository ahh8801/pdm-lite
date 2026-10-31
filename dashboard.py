"""그래프 한 장 대시보드(index.html) — 외부 라이브러리 없이 SVG로 그린다."""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
REPO = "https://github.com/keerhee/kma-auto-genai-3-1"

df = pd.read_csv(BASE / "data" / "Day5_설비센서_50건_가상.csv", encoding="utf-8-sig")
df["시각"] = df["시간"].str[11:]
tj = pd.read_csv(BASE / "outputs" / "trend_judgement.csv", encoding="utf-8-sig")
a = df[df["설비"].str.startswith("설비A")].reset_index(drop=True)
b = df[df["설비"].str.startswith("설비B")].reset_index(drop=True)
row = lambda eq, c: tj[(tj["설비"] == eq) & (tj["항목"] == c)].iloc[0]
start = row("설비B", "온도(℃)")["추세 시작"]
ul_t = row("설비B", "온도(℃)")["기준선 상한"]
j = int(a["진동(mm/s)"].idxmax())
a_time, a_val = a["시각"][j], a["진동(mm/s)"][j]

# SVG: 위 칸 진동(설비A·B), 아래 칸 설비B 온도. x축 공유
W, H, L, R = 720, 440, 56, 16
n = len(a)
x = lambda i: L + i * (W - L - R) / (n - 1)
def ymap(lo, hi, top, bot):
    return lambda v: bot - (v - lo) / (hi - lo) * (bot - top)

svg = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="설비 센서 그래프">']
panels = [((24, 200), 0, 4, 1, "진동 (mm/s)",
           [("설비A 진동", a["진동(mm/s)"], "var(--a)"), ("설비B 진동", b["진동(mm/s)"], "var(--b)")], None),
          ((250, 400), 52, 66, 2, "설비B 온도 (℃)", [("설비B 온도", b["온도(℃)"], "var(--b)")], ul_t)]
for (top, bot), lo, hi, step, title, series, ul in panels:
    y = ymap(lo, hi, top, bot)
    svg.append(f'<text x="{L}" y="{top - 8}" class="t">{title}</text>')
    for v in range(lo, hi + 1, step):
        svg.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="g"/>'
                   f'<text x="{L - 6}" y="{y(v) + 4:.1f}" class="yl">{v}</text>')
    if ul is not None:
        svg.append(f'<line x1="{L}" x2="{W - R}" y1="{y(ul):.1f}" y2="{y(ul):.1f}" class="ul"/>'
                   f'<text x="{W - R}" y="{y(ul) - 6:.1f}" class="ull">기준선 상한 {ul:.1f}℃</text>')
    for name, s, color in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s))
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2"><title>{name}</title></polyline>')
i0 = int(a.index[a["시각"] == start][0])
svg.append(f'<line x1="{x(i0):.1f}" x2="{x(i0):.1f}" y1="24" y2="400" class="mk"/>'
           f'<text x="{x(i0) + 4:.1f}" y="262" class="mkl">추세 시작 {start}</text>')
yv = ymap(0, 4, 24, 200)
svg.append(f'<text x="{x(j) - 8:.1f}" y="{yv(a_val) + 4:.1f}" class="nl">설비A {a_time} 한 번 튐 = 노이즈</text>')
for i in range(0, n, 3):
    svg.append(f'<text x="{x(i):.1f}" y="{H - 18}" class="xl">{a["시각"][i]}</text>')
svg.append("</svg>")

html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>노이즈 vs 추세</title>
<style>
:root{{--bg:#fafaf7;--fg:#1f2328;--mute:#5f6670;--line:#d9dce1;--a:#8a94a3;--b:#c2410c;--ul:#b45309;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181c;--fg:#e8eaed;--mute:#a1a7b0;--line:#33373e;--a:#7d8796;--b:#fb923c;--ul:#fbbf24;--card:#1e2126}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,"Malgun Gothic",sans-serif}}
main{{max-width:780px;margin:0 auto;padding:24px 16px}}h1{{font-size:1.4rem;margin:0 0 4px}}
.sum{{font-size:1.05rem;margin:0 0 16px}}.sum b{{color:var(--b)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}}
svg{{width:100%;height:auto;display:block}}
.t{{font-size:13px;font-weight:600;fill:var(--fg)}}.g{{stroke:var(--line)}}.yl{{font-size:11px;fill:var(--mute);text-anchor:end}}
.xl{{font-size:11px;fill:var(--mute);text-anchor:middle}}.ul{{stroke:var(--ul);stroke-dasharray:6 4}}
.ull{{font-size:11px;fill:var(--ul);text-anchor:end}}.mk{{stroke:var(--b);stroke-dasharray:2 3}}
.mkl{{font-size:12px;fill:var(--b);font-weight:600}}.nl{{font-size:11px;fill:var(--mute);text-anchor:end}}
.lg{{display:flex;gap:16px;flex-wrap:wrap;font-size:.9rem;color:var(--mute);margin-top:8px}}
.lg i{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:6px}}
footer{{font-size:.85rem;color:var(--mute);margin-top:16px}}a{{color:inherit}}
</style></head><body><main>
<h1>노이즈 vs 추세 — 설비 2대 센서</h1>
<p class="sum">설비B 온도가 <b>{start}</b>부터 기준선 상한을 연속으로 넘으며 오른다(추세 → 정비 신호). 설비A 진동은 {a_time}에 {a_val} mm/s로 한 번 튀었다가 돌아왔다(노이즈).</p>
<div class="card">{chr(10).join(svg)}
<div class="lg"><span><i style="background:var(--a)"></i>설비A 프레스 메인모터</span><span><i style="background:var(--b)"></i>설비B 차체 용접로봇 감속기</span><span><i style="border-top:2px dashed var(--ul);height:0"></i>기준선 상한(처음 12점 평균 + 3σ)</span></div></div>
<footer>센서 값은 <b>실습용 가상 데이터</b>(2026-09-15 08:00~16:00, 20분 간격)다. 판정: 기준선 상한을 3번 연속 넘으면 추세.<br>
원본: 「자동차산업과 생성형 AI 3-1」 Day5 예지보전 · <a href="{REPO}">{REPO}</a></footer>
</main></body></html>
"""
(BASE / "index.html").write_text(html, encoding="utf-8")
print("index.html 저장")
