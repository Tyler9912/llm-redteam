"""
redteam/dashboard.py
---------------------
Generates a stunning HTML dashboard from red team results JSON.

Run: python -m redteam.dashboard --results redteam/results/redteam_TIMESTAMP.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def generate_dashboard(results_file: str) -> str:
    data = json.loads(Path(results_file).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    results = data.get("results", [])
    cat_summary = summary.get("category_summary", {})

    robustness   = summary.get("robustness_score", 0)
    bypass_rate  = summary.get("bypass_rate", 0)
    avg_score    = summary.get("avg_judge_score", 0)
    total        = summary.get("total_prompts", 0)
    total_bypass = summary.get("total_bypassed", 0)
    run_id       = data.get("run_id", "unknown")

    # Robustness color
    if robustness >= 85:
        rob_color = "#00ff88"
        rob_label = "ROBUST"
    elif robustness >= 70:
        rob_color = "#ffcc00"
        rob_label = "MODERATE"
    else:
        rob_color = "#ff4444"
        rob_label = "VULNERABLE"

    # Category bars
    cat_bars = ""
    for cat, stats in cat_summary.items():
        br = stats["bypass_rate"]
        color = "#00ff88" if br < 15 else "#ffcc00" if br < 30 else "#ff4444"
        cat_bars += f"""
        <div class="cat-row">
          <div class="cat-label">{cat}</div>
          <div class="cat-bar-wrap">
            <div class="cat-bar" style="width:{min(br,100)}%; background:{color}"></div>
          </div>
          <div class="cat-stats">
            <span style="color:{color}">{br}% bypass</span>
            <span class="cat-detail">{stats['bypassed']}/{stats['total']} | avg {stats['avg_score']}/5</span>
          </div>
        </div>"""

    # Top bypasses table
    bypassed = [r for r in results if r.get("bypassed")]
    bypassed_sorted = sorted(bypassed, key=lambda x: x["score"], reverse=True)[:15]
    bypass_rows = ""
    for r in bypassed_sorted:
        sev_color = {"CRITICAL": "#ff4444", "HIGH": "#ff8800", "MEDIUM": "#ffcc00", "LOW": "#00ff88"}.get(r["severity"], "#888")
        bypass_rows += f"""
        <tr>
          <td><span class="sev-badge" style="border-color:{sev_color};color:{sev_color}">{r['severity']}</span></td>
          <td class="cat-cell">{r['category']}</td>
          <td class="prompt-cell">{r['prompt'][:80]}...</td>
          <td><span class="score-badge score-{r['score']}">{r['score']}/5</span></td>
          <td class="reasoning-cell">{r['reasoning']}</td>
        </tr>"""

    # Score distribution
    score_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in results:
        s = r.get("score", 1)
        if s in score_dist:
            score_dist[s] += 1
    max_count = max(score_dist.values()) or 1
    dist_bars = ""
    score_colors = {1: "#00ff88", 2: "#44cc88", 3: "#ffcc00", 4: "#ff8800", 5: "#ff4444"}
    score_labels = {1: "SAFE", 2: "MOSTLY SAFE", 3: "PARTIAL", 4: "SIGNIFICANT", 5: "FULL BYPASS"}
    for score, count in score_dist.items():
        pct = count / max_count * 100
        dist_bars += f"""
        <div class="dist-row">
          <div class="dist-label" style="color:{score_colors[score]}">{score} — {score_labels[score]}</div>
          <div class="dist-bar-wrap">
            <div class="dist-bar" style="width:{pct}%;background:{score_colors[score]}"></div>
          </div>
          <div class="dist-count">{count}</div>
        </div>"""

    # Severity breakdown
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    sev_bypassed = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        sev = r.get("severity", "LOW")
        if sev in sev_counts:
            sev_counts[sev] += 1
            if r.get("bypassed"):
                sev_bypassed[sev] += 1

    sev_rows = ""
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        total_sev = sev_counts[sev]
        byp = sev_bypassed[sev]
        rate = round(byp / total_sev * 100, 1) if total_sev > 0 else 0
        sev_color = {"CRITICAL": "#ff4444", "HIGH": "#ff8800", "MEDIUM": "#ffcc00", "LOW": "#00ff88"}[sev]
        sev_rows += f"""
        <tr>
          <td><span class="sev-badge" style="border-color:{sev_color};color:{sev_color}">{sev}</span></td>
          <td style="color:#ccc">{total_sev}</td>
          <td style="color:{sev_color}">{byp}</td>
          <td style="color:{sev_color}">{rate}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Red Team Report | {run_id}</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #050810;
    --surface: #0a0f1e;
    --surface2: #0f1728;
    --border: #1a2a4a;
    --accent: #00aaff;
    --accent2: #00ff88;
    --danger: #ff4444;
    --warn: #ffcc00;
    --text: #c8d8f0;
    --muted: #4a6080;
    --font-mono: 'Share Tech Mono', monospace;
    --font-main: 'Rajdhani', sans-serif;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-main);
    min-height: 100vh;
    overflow-x: hidden;
  }}

  /* Scanline effect */
  body::before {{
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,170,255,0.015) 2px,
      rgba(0,170,255,0.015) 4px
    );
    pointer-events: none;
    z-index: 1000;
  }}

  /* Grid background */
  body::after {{
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
      linear-gradient(rgba(0,170,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,170,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }}

  .container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
    position: relative;
    z-index: 1;
  }}

  /* Header */
  header {{
    border-bottom: 1px solid var(--border);
    padding: 32px 0 24px;
    margin-bottom: 40px;
    position: relative;
  }}

  header::after {{
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 200px; height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
  }}

  .header-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
  }}

  .header-title {{
    font-size: 11px;
    letter-spacing: 4px;
    color: var(--accent);
    font-family: var(--font-mono);
    margin-bottom: 8px;
    opacity: 0.8;
  }}

  h1 {{
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 2px;
    line-height: 1;
    color: #fff;
  }}

  h1 span {{ color: var(--accent); }}

  .header-meta {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--muted);
    text-align: right;
    line-height: 1.8;
  }}

  .header-meta strong {{ color: var(--accent); }}

  /* Hero metrics */
  .metrics-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 16px;
    margin-bottom: 40px;
  }}

  .metric-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 28px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
  }}

  .metric-card:hover {{ border-color: var(--accent); }}

  .metric-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }}

  .metric-card.robustness::before {{ background: {rob_color}; }}
  .metric-card.bypass::before {{ background: var(--danger); }}
  .metric-card.score::before {{ background: var(--warn); }}
  .metric-card.total::before {{ background: var(--accent); }}

  .metric-label {{
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 3px;
    color: var(--muted);
    margin-bottom: 12px;
    text-transform: uppercase;
  }}

  .metric-value {{
    font-size: 52px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -1px;
  }}

  .metric-unit {{
    font-size: 20px;
    opacity: 0.6;
  }}

  .metric-sub {{
    font-family: var(--font-mono);
    font-size: 11px;
    margin-top: 8px;
  }}

  .robustness-badge {{
    display: inline-block;
    padding: 3px 10px;
    border: 1px solid {rob_color};
    color: {rob_color};
    font-size: 11px;
    letter-spacing: 2px;
    font-family: var(--font-mono);
  }}

  /* Sections */
  .section {{
    margin-bottom: 40px;
  }}

  .section-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}

  .section-num {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    opacity: 0.6;
  }}

  h2 {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #fff;
    text-transform: uppercase;
  }}

  .panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 24px;
  }}

  /* Category bars */
  .cat-row {{
    display: grid;
    grid-template-columns: 200px 1fr auto;
    align-items: center;
    gap: 16px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(26,42,74,0.5);
  }}

  .cat-row:last-child {{ border-bottom: none; }}

  .cat-label {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text);
  }}

  .cat-bar-wrap {{
    background: rgba(255,255,255,0.04);
    height: 8px;
    position: relative;
  }}

  .cat-bar {{
    height: 100%;
    transition: width 1s ease;
    position: relative;
  }}

  .cat-bar::after {{
    content: '';
    position: absolute;
    right: 0; top: 0; bottom: 0;
    width: 2px;
    background: rgba(255,255,255,0.4);
    box-shadow: 0 0 6px currentColor;
  }}

  .cat-stats {{
    font-family: var(--font-mono);
    font-size: 11px;
    text-align: right;
    min-width: 180px;
  }}

  .cat-detail {{ color: var(--muted); margin-left: 8px; }}

  /* Two col */
  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}

  /* Distribution bars */
  .dist-row {{
    display: grid;
    grid-template-columns: 180px 1fr 60px;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
  }}

  .dist-label {{
    font-family: var(--font-mono);
    font-size: 11px;
  }}

  .dist-bar-wrap {{
    background: rgba(255,255,255,0.04);
    height: 6px;
  }}

  .dist-bar {{ height: 100%; }}

  .dist-count {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--muted);
    text-align: right;
  }}

  /* Table */
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}

  .data-table th {{
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 2px;
    color: var(--muted);
    text-align: left;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    text-transform: uppercase;
  }}

  .data-table td {{
    padding: 12px 16px;
    border-bottom: 1px solid rgba(26,42,74,0.4);
    vertical-align: top;
    font-family: var(--font-mono);
    font-size: 12px;
  }}

  .data-table tr:hover td {{
    background: rgba(0,170,255,0.03);
  }}

  .sev-badge {{
    display: inline-block;
    padding: 2px 8px;
    border: 1px solid;
    font-size: 10px;
    letter-spacing: 1px;
    font-family: var(--font-mono);
  }}

  .score-badge {{
    display: inline-block;
    padding: 3px 10px;
    font-size: 13px;
    font-weight: 700;
    font-family: var(--font-main);
  }}

  .score-1 {{ background: rgba(0,255,136,0.15); color: #00ff88; }}
  .score-2 {{ background: rgba(68,204,136,0.15); color: #44cc88; }}
  .score-3 {{ background: rgba(255,204,0,0.15); color: #ffcc00; }}
  .score-4 {{ background: rgba(255,136,0,0.15); color: #ff8800; }}
  .score-5 {{ background: rgba(255,68,68,0.2); color: #ff4444; }}

  .cat-cell {{ color: var(--accent); opacity: 0.8; }}
  .prompt-cell {{ color: #8899bb; max-width: 300px; }}
  .reasoning-cell {{ color: var(--muted); max-width: 250px; font-size: 11px; }}

  /* Footer */
  footer {{
    border-top: 1px solid var(--border);
    padding: 24px 0;
    margin-top: 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .footer-text {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted);
  }}

  .footer-badge {{
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 2px;
    color: var(--accent);
    border: 1px solid var(--border);
    padding: 4px 12px;
  }}

  /* Animations */
  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  .metric-card {{ animation: fadeIn 0.6s ease both; }}
  .metric-card:nth-child(1) {{ animation-delay: 0.1s; }}
  .metric-card:nth-child(2) {{ animation-delay: 0.2s; }}
  .metric-card:nth-child(3) {{ animation-delay: 0.3s; }}
  .metric-card:nth-child(4) {{ animation-delay: 0.4s; }}

  @media (max-width: 900px) {{
    .metrics-grid {{ grid-template-columns: 1fr 1fr; }}
    .two-col {{ grid-template-columns: 1fr; }}
    .cat-row {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <header>
    <div class="header-top">
      <div>
        <div class="header-title">// AUTOMATED ADVERSARIAL EVALUATION REPORT</div>
        <h1>LLM <span>RED TEAM</span> REPORT</h1>
      </div>
      <div class="header-meta">
        <div>RUN ID: <strong>{run_id}</strong></div>
        <div>TARGET: <strong>Security RAG API</strong></div>
        <div>JUDGE: <strong>GPT-4o-mini</strong></div>
        <div>TOTAL PROMPTS: <strong>{total}</strong></div>
      </div>
    </div>
  </header>

  <!-- Metrics -->
  <div class="metrics-grid">
    <div class="metric-card robustness">
      <div class="metric-label">// Robustness Score</div>
      <div class="metric-value" style="color:{rob_color}">{robustness}<span class="metric-unit">%</span></div>
      <div class="metric-sub"><span class="robustness-badge">{rob_label}</span></div>
    </div>
    <div class="metric-card bypass">
      <div class="metric-label">// Bypass Rate</div>
      <div class="metric-value" style="color:var(--danger)">{bypass_rate}<span class="metric-unit">%</span></div>
      <div class="metric-sub" style="color:var(--muted);font-family:var(--font-mono);font-size:11px">{total_bypass} of {total} prompts bypassed</div>
    </div>
    <div class="metric-card score">
      <div class="metric-label">// Avg Judge Score</div>
      <div class="metric-value" style="color:var(--warn)">{avg_score}<span class="metric-unit">/5</span></div>
      <div class="metric-sub" style="color:var(--muted);font-family:var(--font-mono);font-size:11px">1=safe, 5=full bypass</div>
    </div>
    <div class="metric-card total">
      <div class="metric-label">// Attack Categories</div>
      <div class="metric-value" style="color:var(--accent)">{len(cat_summary)}</div>
      <div class="metric-sub" style="color:var(--muted);font-family:var(--font-mono);font-size:11px">Most vulnerable: {summary.get('most_vulnerable_category','N/A')[:20]}</div>
    </div>
  </div>

  <!-- Category breakdown -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">01</span>
      <h2>Attack Category Breakdown</h2>
    </div>
    <div class="panel">
      {cat_bars}
    </div>
  </div>

  <!-- Score dist + Severity -->
  <div class="two-col section">
    <div>
      <div class="section-header">
        <span class="section-num">02</span>
        <h2>Score Distribution</h2>
      </div>
      <div class="panel">
        {dist_bars}
      </div>
    </div>
    <div>
      <div class="section-header">
        <span class="section-num">03</span>
        <h2>Severity Analysis</h2>
      </div>
      <div class="panel">
        <table class="data-table">
          <thead>
            <tr>
              <th>Severity</th><th>Total</th><th>Bypassed</th><th>Rate</th>
            </tr>
          </thead>
          <tbody>{sev_rows}</tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Top bypasses -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">04</span>
      <h2>Most Successful Attack Prompts</h2>
    </div>
    <div class="panel" style="overflow-x:auto">
      <table class="data-table">
        <thead>
          <tr>
            <th>Severity</th><th>Category</th><th>Prompt</th><th>Score</th><th>Reasoning</th>
          </tr>
        </thead>
        <tbody>{bypass_rows if bypass_rows else '<tr><td colspan="5" style="text-align:center;color:var(--accent2);padding:40px">NO BYPASSES DETECTED — SYSTEM IS ROBUST</td></tr>'}</tbody>
      </table>
    </div>
  </div>

  <!-- Footer -->
  <footer>
    <div class="footer-text">
      Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
      Security Engineering Portfolio &nbsp;|&nbsp;
      Automated Red Team Evaluation Framework
    </div>
    <div class="footer-badge">CONFIDENTIAL // INTERNAL USE ONLY</div>
  </footer>

</div>
</body>
</html>"""

    out_path = Path(results_file).with_suffix(".html")
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate red team dashboard")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    args = parser.parse_args()
    generate_dashboard(args.results)
