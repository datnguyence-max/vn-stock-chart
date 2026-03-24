"""
=============================================================
  Biểu đồ Cổ Phiếu Việt Nam  —  vnstock + Plotly Dash
  Nguồn dữ liệu: TCBS / KBS qua thư viện vnstock
=============================================================
  Cài đặt (chạy 1 lần):
      pip install vnstock plotly dash pandas

  Chạy ứng dụng:
      python vn_stock_chart.py

  Sau đó mở trình duyệt tại:  http://127.0.0.1:8050
=============================================================
"""

# ── Tự động cài thư viện nếu thiếu ──────────────────────────
import sys
import subprocess

PACKAGES = {
    "vnstock": "vnstock==3.2.1",
    "plotly":  "plotly",
    "dash":    "dash",
    "pandas":  "pandas",
}

for pkg, install_name in PACKAGES.items():
    try:
        __import__(pkg)
    except ImportError:
        print(f"  Dang cai {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", install_name],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  Da cai xong {pkg}.")

print("  Tat ca thu vien san sang.")

# ── Import ───────────────────────────────────────────────────
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State, ctx

# ── Màu sắc ─────────────────────────────────────────────────
PALETTE    = ["#2563eb","#e05a2b","#1a9e6e","#a855f7",
              "#e8b800","#0ea5e9","#ec4899","#64748b"]
UP_COLOR   = "#1a9e6e"
DN_COLOR   = "#d94040"
BG         = "#0f1117"
PANEL_BG   = "#1a1d27"
GRID_CLR   = "rgba(255,255,255,0.06)"
TEXT_CLR   = "#e2e8f0"
MUTED      = "#64748b"

# ── Cấu hình khung thời gian ─────────────────────────────────
TF_CONFIG = {
    "1D":  {"interval": "1D",  "days": 1,    "label": "1 Ngay"},
    "1W":  {"interval": "1D",  "days": 7,    "label": "1 Tuan"},
    "1M":  {"interval": "1D",  "days": 30,   "label": "1 Thang"},
    "3M":  {"interval": "1D",  "days": 90,   "label": "3 Thang"},
    "6M":  {"interval": "1D",  "days": 180,  "label": "6 Thang"},
    "1Y":  {"interval": "1D",  "days": 365,  "label": "1 Nam"},
    "3Y":  {"interval": "1W",  "days": 1095, "label": "3 Nam"},
    "5Y":  {"interval": "1M",  "days": 1825, "label": "5 Nam"},
}

# ── Hàm lấy dữ liệu ─────────────────────────────────────────
def fetch_data(symbol: str, tf_key: str) -> pd.DataFrame:
    """Lay du lieu OHLCV tu vnstock (KBS -> TCBS fallback)."""
    from vnstock import Quote
    cfg   = TF_CONFIG[tf_key]
    end   = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=cfg["days"] + 30)).strftime("%Y-%m-%d")

    for source in ["KBS", "TCBS", "VCI"]:
        try:
            q  = Quote(symbol=symbol.upper(), source=source)
            df = q.history(start=start, end=end, interval=cfg["interval"])
            if df is not None and len(df) > 0:
                df = df.reset_index(drop=True)
                df.columns = [c.lower() for c in df.columns]
                for old, new in [("tradingdate","time"),("date","time"),("vol","volume")]:
                    if old in df.columns and new not in df.columns:
                        df = df.rename(columns={old: new})
                df["time"] = pd.to_datetime(df["time"])
                df = df.sort_values("time").tail(cfg["days"] + 10).reset_index(drop=True)
                print(f"  OK {symbol} — {source} — {len(df)} bars")
                return df
        except Exception as e:
            print(f"  FAIL {symbol} — {source}: {e}")
            continue
    return pd.DataFrame()

# ── Tạo biểu đồ Plotly ──────────────────────────────────────
def build_figure(symbols, tf_key, chart_type, show_ma, show_volume, compare_mode):
    n_rows  = 2 if show_volume else 1
    row_hts = [0.75, 0.25] if show_volume else [1.0]
    data_map = {}

    for sym in symbols:
        df = fetch_data(sym, tf_key)
        if not df.empty:
            data_map[sym] = df

    if not data_map:
        fig = go.Figure()
        fig.add_annotation(text="Khong tim thay du lieu. Kiem tra lai ma chung khoan.",
                           x=0.5, y=0.5, xref="paper", yref="paper",
                           showarrow=False, font=dict(size=14, color=MUTED))
        fig.update_layout(**_base_layout())
        return fig

    fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True,
                        row_heights=row_hts, vertical_spacing=0.03)

    for i, (sym, df) in enumerate(data_map.items()):
        color = PALETTE[i % len(PALETTE)]

        if compare_mode and len(data_map) > 1:
            base  = df["close"].iloc[0]
            y_val = ((df["close"] - base) / base * 100).round(2)
        else:
            y_val = df["close"]

        if chart_type == "candle" and not compare_mode:
            fig.add_trace(go.Candlestick(
                x=df["time"], open=df["open"], high=df["high"],
                low=df["low"], close=df["close"], name=sym,
                increasing_line_color=UP_COLOR, decreasing_line_color=DN_COLOR,
                increasing_fillcolor=UP_COLOR, decreasing_fillcolor=DN_COLOR,
                line_width=1), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=df["time"], y=y_val, name=sym, mode="lines",
                line=dict(color=color, width=1.8),
                hovertemplate=f"<b>{sym}</b><br>%{{x|%d/%m/%Y}}<br>%{{y:,.2f}}<extra></extra>"),
                row=1, col=1)

        for ma_p in [int(m) for m in (show_ma or [])]:
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["close"].rolling(ma_p).mean(),
                name=f"MA{ma_p} {sym}", mode="lines",
                line=dict(width=1, dash="dot", color=color), opacity=0.7,
                hoverinfo="skip"), row=1, col=1)

        if show_volume and n_rows == 2 and "volume" in df.columns:
            vol_colors = [UP_COLOR if c >= o else DN_COLOR
                          for c, o in zip(df["close"], df["open"])]
            fig.add_trace(go.Bar(
                x=df["time"], y=df["volume"], name=f"KL {sym}",
                marker_color=vol_colors, opacity=0.6, showlegend=False),
                row=2, col=1)

    layout = _base_layout()
    layout.update(
        yaxis=dict(title=dict(text="% thay doi" if compare_mode else "Gia (VND)",
                              font=dict(size=11, color=MUTED)),
                   gridcolor=GRID_CLR, tickfont=dict(color=TEXT_CLR, size=11),
                   side="right", tickformat=",.0f"),
        xaxis=dict(gridcolor=GRID_CLR, tickfont=dict(color=TEXT_CLR, size=10),
                   rangeslider_visible=False),
    )
    if show_volume and n_rows == 2:
        layout["yaxis2"] = dict(gridcolor=GRID_CLR, tickfont=dict(color=MUTED, size=9),
                                side="right", tickformat=".2s")
        layout["xaxis2"] = dict(gridcolor=GRID_CLR, tickfont=dict(color=TEXT_CLR, size=10))
    fig.update_layout(**layout)
    fig.update_xaxes(showspikes=True, spikecolor=MUTED, spikethickness=1)
    fig.update_yaxes(showspikes=True, spikecolor=MUTED, spikethickness=1)
    return fig

def _base_layout():
    return dict(
        plot_bgcolor=PANEL_BG, paper_bgcolor=BG,
        font=dict(family="'Segoe UI', Arial, sans-serif", color=TEXT_CLR),
        margin=dict(l=10, r=65, t=20, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID_CLR,
                    borderwidth=1, font=dict(size=11)),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=PANEL_BG, font_size=12, bordercolor=MUTED),
    )

# ── Dash App ─────────────────────────────────────────────────
app = dash.Dash(__name__, title="VN Stock Chart",
                meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}])

STYLE_BASE = dict(fontFamily="'Segoe UI',Arial,sans-serif",
                  backgroundColor=BG, minHeight="100vh", padding="16px 20px")

app.layout = html.Div(style=STYLE_BASE, children=[

    # Header
    html.Div(style=dict(display="flex", alignItems="center", gap="12px",
                         marginBottom="16px", flexWrap="wrap"), children=[
        html.Div("Bieu do Co Phieu Viet Nam",
                 style=dict(fontSize="18px", fontWeight="600", color="#f1f5f9")),
        html.Div("Nguon: vnstock (KBS / TCBS)",
                 style=dict(fontSize="11px", color=MUTED, marginRight="auto")),
        dcc.Input(id="sym-input", type="text", placeholder="DCM, VRE, FPT...",
                  value="", debounce=False,
                  style=dict(width="150px", padding="5px 10px", fontSize="13px",
                             background="#1e293b", color="#f1f5f9",
                             border="1px solid #334155", borderRadius="6px")),
        html.Button("+ Them", id="btn-add", n_clicks=0,
                    style=dict(padding="5px 14px", fontSize="13px",
                               background="#2563eb", color="#fff",
                               border="none", borderRadius="6px", cursor="pointer")),
        html.Button("Lam moi", id="btn-refresh", n_clicks=0,
                    style=dict(padding="5px 12px", fontSize="12px",
                               background="transparent", color="#94a3b8",
                               border="1px solid #334155", borderRadius="6px",
                               cursor="pointer")),
    ]),

    # Chips
    html.Div(id="chips-area", style=dict(marginBottom="12px",
                                          display="flex", flexWrap="wrap", gap="6px")),

    # Toolbar
    html.Div(style=dict(display="flex", gap="5px", flexWrap="wrap",
                         marginBottom="10px", alignItems="center"), children=[
        html.Span("Khung:", style=dict(fontSize="11px", color=MUTED)),
        *[html.Button(v["label"], id=f"tf-{k}", n_clicks=0,
                      style=dict(padding="3px 10px", fontSize="11px",
                                 cursor="pointer", border="1px solid #334155",
                                 borderRadius="20px",
                                 background="#2563eb" if k=="1M" else "transparent",
                                 color="#fff" if k=="1M" else "#94a3b8",
                                 marginRight="2px"))
          for k, v in TF_CONFIG.items()],
        html.Div(style=dict(width="1px",height="18px",background="#334155",margin="0 6px")),
        html.Span("Loai:", style=dict(fontSize="11px", color=MUTED)),
        html.Button("Nen Nhat", id="btn-candle", n_clicks=1,
                    style=dict(padding="3px 10px", fontSize="11px",
                               cursor="pointer", border="1px solid #334155",
                               borderRadius="20px", background="#2563eb",
                               color="#fff", marginRight="2px")),
        html.Button("Duong", id="btn-line", n_clicks=0,
                    style=dict(padding="3px 10px", fontSize="11px",
                               cursor="pointer", border="1px solid #334155",
                               borderRadius="20px", background="transparent",
                               color="#94a3b8", marginRight="2px")),
        html.Div(style=dict(width="1px",height="18px",background="#334155",margin="0 6px")),
        html.Span("MA:", style=dict(fontSize="11px", color=MUTED)),
        dcc.Checklist(id="ma-check",
                      options=[{"label":" MA20","value":"20"},
                               {"label":" MA50","value":"50"},
                               {"label":" MA200","value":"200"}],
                      value=[], inline=True,
                      style=dict(fontSize="11px", color="#94a3b8"),
                      labelStyle=dict(marginRight="10px", cursor="pointer")),
        html.Div(style=dict(width="1px",height="18px",background="#334155",margin="0 6px")),
        dcc.Checklist(id="extra-check",
                      options=[{"label":" Volume","value":"volume"},
                               {"label":" So sanh %","value":"compare"}],
                      value=["volume"], inline=True,
                      style=dict(fontSize="11px", color="#94a3b8"),
                      labelStyle=dict(marginRight="10px", cursor="pointer")),
    ]),

    html.Div(id="err-msg",
             style=dict(fontSize="12px", color=DN_COLOR, minHeight="14px", marginBottom="6px")),

    dcc.Loading(type="circle", color="#2563eb", children=
        dcc.Graph(id="main-chart",
                  config=dict(displayModeBar=True, scrollZoom=True,
                              modeBarButtonsToRemove=["lasso2d","select2d"],
                              toImageButtonOptions=dict(format="png", scale=2)),
                  style=dict(height="520px"))),

    html.Div(id="stats-area",
             style=dict(display="flex", gap="10px", flexWrap="wrap", marginTop="10px")),

    html.Div(style=dict(marginTop="8px", fontSize="11px", color=MUTED,
                         display="flex", justifyContent="space-between", flexWrap="wrap"),
             children=[
        html.Span(id="status-txt"),
        html.Span("Nhap ma -> Enter hoac + Them  |  Ctrl+scroll de zoom  |  Double-click de reset"),
    ]),

    dcc.Store(id="store-syms", data=["DCM", "DPM"]),
    dcc.Store(id="store-tf",   data="1M"),
    dcc.Store(id="store-mode", data="candle"),
    dcc.Interval(id="auto-refresh", interval=5*60*1000, n_intervals=0),
])

# ── Callbacks ────────────────────────────────────────────────
@app.callback(
    Output("store-syms", "data"),
    Output("sym-input",  "value"),
    Output("err-msg",    "children", allow_duplicate=True),
    Input("btn-add",     "n_clicks"),
    Input("sym-input",   "n_submit"),
    State("sym-input",   "value"),
    State("store-syms",  "data"),
    prevent_initial_call=True,
)
def add_symbol(n1, n2, value, syms):
    if not value or not value.strip():
        return syms, "", ""
    sym = value.strip().upper()
    if sym in syms:
        return syms, "", f"{sym} da co trong danh sach"
    if len(syms) >= 8:
        return syms, "", "Toi da 8 ma cung luc"
    return syms + [sym], "", ""

@app.callback(
    Output("store-syms", "data", allow_duplicate=True),
    [Input(f"rm-{i}", "n_clicks") for i in range(8)],
    State("store-syms", "data"),
    prevent_initial_call=True,
)
def remove_symbol(*args):
    syms    = args[-1]
    triggered = ctx.triggered_id
    if not triggered or not str(triggered).startswith("rm-"):
        return syms
    idx = int(str(triggered).split("-")[1])
    new_syms = [s for j,s in enumerate(syms) if j != idx]
    return new_syms if new_syms else ["DCM"]

@app.callback(
    Output("chips-area", "children"),
    Input("store-syms",  "data"),
)
def render_chips(syms):
    chips = []
    for i, s in enumerate(syms[:8]):
        col = PALETTE[i % len(PALETTE)]
        chips.append(html.Span(
            style=dict(display="inline-flex", alignItems="center", gap="5px",
                       padding="3px 10px", borderRadius="20px",
                       border=f"1px solid {col}55",
                       background=f"{col}22", color=col,
                       fontSize="12px", fontWeight="500"),
            children=[s, html.Span("x", id=f"rm-{i}",
                                   style=dict(cursor="pointer", opacity=".6",
                                              fontSize="14px", lineHeight="1"))]))
    for i in range(len(syms), 8):
        chips.append(html.Span(id=f"rm-{i}", style=dict(display="none")))
    return chips

@app.callback(
    Output("store-tf", "data"),
    [Input(f"tf-{k}", "n_clicks") for k in TF_CONFIG],
    prevent_initial_call=True,
)
def set_tf(*args):
    triggered = ctx.triggered_id
    return str(triggered)[3:] if triggered and str(triggered).startswith("tf-") else "1M"

@app.callback(
    Output("store-mode", "data"),
    Input("btn-candle",  "n_clicks"),
    Input("btn-line",    "n_clicks"),
    prevent_initial_call=True,
)
def set_mode(nc, nl):
    return "candle" if ctx.triggered_id == "btn-candle" else "line"

@app.callback(
    Output("main-chart",  "figure"),
    Output("stats-area",  "children"),
    Output("status-txt",  "children"),
    Output("err-msg",     "children"),
    Input("store-syms",   "data"),
    Input("store-tf",     "data"),
    Input("store-mode",   "data"),
    Input("ma-check",     "value"),
    Input("extra-check",  "value"),
    Input("btn-refresh",  "n_clicks"),
    Input("auto-refresh", "n_intervals"),
)
def update_chart(syms, tf_key, mode, ma_vals, extras, _r, _i):
    show_vol     = "volume"  in (extras or [])
    compare_mode = "compare" in (extras or [])
    print(f"\n-> Tai du lieu: {syms}  TF={tf_key}  mode={mode}")

    try:
        fig = build_figure(syms, tf_key, mode, ma_vals, show_vol, compare_mode)
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(**_base_layout())
        return fig, [], "", f"Loi: {e}"

    cards = []
    for i, sym in enumerate(syms):
        try:
            df = fetch_data(sym, tf_key)
            if df.empty:
                continue
            last  = df.iloc[-1]
            prev  = df.iloc[-2] if len(df) > 1 else last
            price = last["close"]
            chg   = price - prev["close"]
            pct   = chg / prev["close"] * 100 if prev["close"] else 0
            col_c = UP_COLOR if chg >= 0 else DN_COLOR
            sym_c = PALETTE[i % len(PALETTE)]
            vol_v = last.get("volume", 0) or 0
            vol_s = (f"{vol_v/1e6:.2f}M" if vol_v >= 1e6
                     else f"{vol_v/1e3:.0f}K" if vol_v >= 1e3
                     else str(int(vol_v)))
            cards.append(html.Div(
                style=dict(background=PANEL_BG, borderRadius="8px",
                           padding="10px 14px", minWidth="130px",
                           border=f"1px solid {sym_c}33"),
                children=[
                    html.Div(sym, style=dict(fontSize="11px", color=sym_c,
                                             fontWeight="600", marginBottom="3px")),
                    html.Div(f"{price:,.0f}",
                             style=dict(fontSize="16px", fontWeight="600", color=TEXT_CLR)),
                    html.Div(f"{'+' if chg>=0 else ''}{chg:,.0f}  "
                             f"({'+'if pct>=0 else ''}{pct:.2f}%)",
                             style=dict(fontSize="11px", color=col_c)),
                    html.Div(f"KL: {vol_s}",
                             style=dict(fontSize="10px", color=MUTED, marginTop="2px")),
                ]))
        except Exception:
            pass

    status = f"Cap nhat luc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
    return fig, cards, status, ""

# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  VN Stock Chart — khoi dong server...")
    print("  Mo trinh duyet tai:  http://127.0.0.1:8050")
    print("  Nhan Ctrl+C de thoat")
    print("=" * 60)
    app.run(debug=False, host="127.0.0.1", port=8050)
