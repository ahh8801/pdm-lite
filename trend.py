"""노이즈 vs 추세 판정 — 처음 12점 기준선, 상한 = 평균 + 3σ, 3번 연속 초과면 추세."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = Path(__file__).parent
COLS = ["진동(mm/s)", "온도(℃)", "압력(bar)"]

df = pd.read_csv(BASE / "data" / "Day5_설비센서_50건_가상.csv", encoding="utf-8-sig")
df["시각"] = df["시간"].str[11:]
df["설비명"] = df["설비"].str[:3]
out = BASE / "outputs"
out.mkdir(exist_ok=True)

# 2·3. 기준선 상한과 판정
rows, ul = [], {}
for eq, g in df.groupby("설비명", sort=False):
    g = g.reset_index(drop=True)
    for c in COLS:
        b = g[c].iloc[:12]
        limit = b.mean() + 3 * b.std()
        over = g[c] > limit
        start = ""
        for i in range(len(g) - 2):
            if over.iloc[i:i + 3].all():
                start = g["시각"].iloc[i]
                break
        n = int(over.sum())
        verdict = "추세" if start else ("노이즈" if n else "정상")
        rows.append({"설비": eq, "항목": c, "기준선 상한": round(limit, 3),
                     "상한 초과 점 수": n, "판정": verdict, "추세 시작": start})
        ul[(eq, c)] = limit
tj = pd.DataFrame(rows)
tj.to_csv(out / "trend_judgement.csv", index=False, encoding="utf-8-sig")

# 4. 하루치 전체 평균 ± 2σ로 설비B가 처음 잡힌 시각
b = df[df["설비명"] == "설비B"]
hits = []
for c in COLS:
    m, s = b[c].mean(), b[c].std()
    hits += b.loc[(b[c] > m + 2 * s) | (b[c] < m - 2 * s), "시각"].tolist()
first2 = min(hits)
start = tj.loc[tj["판정"] == "추세", "추세 시작"].min()
mins = lambda t: int(t[:2]) * 60 + int(t[3:])

# 1. 선 그래프 (위: 진동 A·B, 아래: 설비B 온도)
a = df[df["설비명"] == "설비A"]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
ax1.plot(a["시각"], a["진동(mm/s)"], color="#8a94a3", lw=2, label="설비A 진동")
ax1.plot(b["시각"], b["진동(mm/s)"], color="#c2410c", lw=2, label="설비B 진동")
ax1.axhline(ul[("설비B", "진동(mm/s)")], color="#c2410c", ls=":", lw=1, label="설비B 진동 기준선 상한")
ax1.set_ylabel("진동 (mm/s)"); ax1.legend(loc="upper left"); ax1.grid(alpha=.3)
ax2.plot(b["시각"], b["온도(℃)"], color="#c2410c", lw=2, label="설비B 온도")
ax2.axhline(ul[("설비B", "온도(℃)")], color="#b45309", ls="--", lw=1, label="기준선 상한(평균+3σ)")
for ax in (ax1, ax2):
    ax.axvline(start, color="#c2410c", ls=":", lw=1)
ax2.text(start, b["온도(℃)"].max(), f" 추세 시작 {start}", color="#c2410c")
ax2.set_ylabel("온도 (℃)"); ax2.legend(loc="upper left"); ax2.grid(alpha=.3)
ax2.set_xticks(range(0, 25, 3))
fig.suptitle("노이즈 vs 추세 — 설비 센서 (실습용 가상 데이터)")
fig.tight_layout()
fig.savefig(out / "trend_chart.png", dpi=110)

print(tj.to_string(index=False))
print(f"\n가장 이른 추세 시작: {start} / 평균±2σ 설비B 첫 이상 후보: {first2} / 차이 {mins(first2) - mins(start)}분")
