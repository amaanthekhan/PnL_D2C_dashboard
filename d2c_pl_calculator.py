import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="D2C P&L Calculator", layout="wide")

st.title("D2C P&L Calculator")
st.caption("ShopDeck framework — all metrics and charts update in real time")

st.divider()

# ─── INPUTS ──────────────────────────────────────────────────────
st.subheader("Inputs")

col1, col2, col3 = st.columns(3)
with col1:
    placed   = st.number_input("Placed Orders",          min_value=1,   value=200,    step=1)
    sp       = st.number_input("Selling Price (₹)",      min_value=1.0, value=699.0,  step=1.0)
with col2:
    cp       = st.number_input("Cost Price (₹)",         min_value=0.0, value=250.0,  step=1.0)
    mkt      = st.number_input("Total Marketing Spend (₹)", min_value=0.0, value=8000.0, step=100.0)
with col3:
    fwd_ship = st.number_input("Forward Shipping / Order (₹)",   min_value=0.0, value=75.0, step=1.0)
    rev_ship = st.number_input("Reverse Shipping / RTO Order (₹)", min_value=0.0, value=50.0, step=1.0)

st.divider()

# ─── CANCEL & RTO TOGGLE ─────────────────────────────────────────
st.subheader("Cancelled & RTO Orders")

use_pct = st.toggle("Use Percentage instead of Absolute Values", value=True)

col4, col5 = st.columns(2)
if use_pct:
    with col4:
        cancel_pct = st.slider("Cancel Rate (%)", 0, 100, 15)
        canceled   = round(placed * cancel_pct / 100)
        st.caption(f"→ {canceled} orders canceled")
    shipped = placed - canceled
    with col5:
        rto_pct    = st.slider("RTO Rate (%) — of shipped orders", 0, 100, 20)
        rto_orders = round(shipped * rto_pct / 100)
        st.caption(f"→ {rto_orders} RTO orders")
else:
    with col4:
        canceled   = st.number_input("Cancelled Orders", min_value=0, max_value=placed, value=min(30, placed), step=1)
        st.caption(f"→ Cancel rate: {(canceled/placed*100):.1f}%")
    shipped = placed - canceled
    with col5:
        rto_orders = st.number_input("RTO Orders", min_value=0, max_value=shipped, value=min(34, shipped), step=1)
        st.caption(f"→ RTO rate: {(rto_orders/shipped*100 if shipped else 0):.1f}% of shipped")

delivered = shipped - rto_orders

st.divider()

# ─── CORE CALCULATIONS ───────────────────────────────────────────
delivery_rate   = (delivered / placed  * 100) if placed  else 0
cancel_rate_pct = (canceled  / placed  * 100) if placed  else 0
rto_rate_pct    = (rto_orders / shipped * 100) if shipped else 0

mkt_per_del  = mkt / delivered if delivered else 0
fwd_total    = shipped * fwd_ship
rev_total    = rto_orders * rev_ship
ship_per_del = (fwd_total + rev_total) / delivered if delivered else 0
total_cost   = mkt_per_del + ship_per_del + cp
profit       = sp - total_cost
total_profit = profit * delivered
profit_pct   = (profit / sp * 100) if sp else 0

# ─── FUNNEL METRICS ──────────────────────────────────────────────
st.subheader("Order Funnel")
fc1, fc2, fc3, fc4, fc5 = st.columns(5)
fc1.metric("Placed",       f"{placed}")
fc2.metric("Canceled",     f"{canceled}",   delta=f"-{cancel_rate_pct:.1f}%",  delta_color="inverse")
fc3.metric("Shipped",      f"{shipped}")
fc4.metric("RTO",          f"{rto_orders}", delta=f"-{rto_rate_pct:.1f}%",     delta_color="inverse")
fc5.metric("Delivered ✓",  f"{delivered}",  delta=f"{delivery_rate:.1f}% delivery rate")

st.divider()

# ─── P&L TABLE ───────────────────────────────────────────────────
st.subheader("P&L per Delivered Order")

tl, tr = st.columns([2, 1])
with tl:
    st.table({
        "Item": [
            "Selling Price",
            "— Marketing Cost (adjusted)",
            "— Forward + Reverse Shipping (adjusted)",
            "— Cost Price",
            "Total Cost per Delivered Order",
            "Profit per Delivered Order",
        ],
        "Amount (₹)": [
            f"₹{sp:,.2f}", f"₹{mkt_per_del:,.2f}", f"₹{ship_per_del:,.2f}",
            f"₹{cp:,.2f}", f"₹{total_cost:,.2f}",  f"₹{profit:,.2f}",
        ],
    })
with tr:
    st.markdown("**Cost breakdown**")
    if total_cost > 0:
        st.write(f"📣 Marketing:  **{mkt_per_del/total_cost*100:.1f}%**")
        st.write(f"🚚 Shipping:   **{ship_per_del/total_cost*100:.1f}%**")
        st.write(f"📦 Cost Price: **{cp/total_cost*100:.1f}%**")

st.divider()

# ─── SUMMARY METRICS ─────────────────────────────────────────────
st.subheader("Summary Dashboard")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Profit / Order",       f"₹{profit:,.2f}",       delta=f"{profit_pct:.1f}% of SP")
m2.metric("Total Monthly Profit", f"₹{total_profit:,.0f}", delta=f"{delivered} orders delivered")
m3.metric("Effective CAC",        f"₹{mkt_per_del:,.2f}",  delta="per delivered order", delta_color="off")
m4.metric("Delivery Rate",        f"{delivery_rate:.1f}%",  delta=f"{placed - delivered} orders lost")

st.divider()

# ═══════════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════════
st.subheader("Charts & Visualizations")

BLUE   = "#378ADD"
GREEN  = "#1D9E75"
DKGREEN= "#0F6E56"
LGREEN = "#639922"
AMBER  = "#F59E0B"
RED    = "#993C1D"
LGRAY  = "#f3f4f6"

# ── Row 1: Funnel + Donut ────────────────────────────────────────
r1l, r1r = st.columns(2)

with r1l:
    st.markdown("**Order Funnel**")
    fig_funnel = go.Figure(go.Funnel(
        y=["Placed", "Shipped", "Delivered"],
        x=[placed, shipped, delivered],
        textinfo="value+percent initial",
        marker=dict(color=[BLUE, GREEN, LGREEN]),
        connector=dict(line=dict(color=LGRAY, width=1))
    ))
    fig_funnel.update_layout(
        height=300, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(size=13)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

with r1r:
    st.markdown("**Cost vs Profit Breakdown per Order**")
    donut_labels = ["Marketing", "Shipping", "Cost Price", "Profit" if profit >= 0 else "Loss"]
    donut_values = [max(mkt_per_del,0), max(ship_per_del,0), max(cp,0), max(abs(profit),0)]
    donut_colors = [BLUE, GREEN, AMBER, DKGREEN if profit >= 0 else RED]
    fig_donut = go.Figure(go.Pie(
        labels=donut_labels, values=donut_values, hole=0.55,
        marker=dict(colors=donut_colors),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>₹%{value:.2f}<br>%{percent}<extra></extra>"
    ))
    fig_donut.update_layout(
        height=300, margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3)
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ── Row 2: Stacked bar + Waterfall ───────────────────────────────
r2l, r2r = st.columns(2)

with r2l:
    st.markdown("**Order Status Distribution**")
    fig_bar = go.Figure()
    for name, val, color in [
        ("Delivered", delivered,  LGREEN),
        ("RTO",       rto_orders, AMBER),
        ("Canceled",  canceled,   RED),
    ]:
        fig_bar.add_trace(go.Bar(
            name=name, x=["Orders"], y=[val],
            marker_color=color,
            text=[str(val)], textposition="inside"
        ))
    fig_bar.update_layout(
        barmode="stack", height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=LGRAY, title="Orders")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with r2r:
    st.markdown("**Selling Price Waterfall per Delivered Order**")
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Selling\nPrice", "Marketing", "Shipping", "Cost\nPrice", "Profit"],
        y=[sp, -mkt_per_del, -ship_per_del, -cp, 0],
        text=[f"₹{sp:.0f}", f"-₹{mkt_per_del:.0f}", f"-₹{ship_per_del:.0f}", f"-₹{cp:.0f}", f"₹{profit:.0f}"],
        textposition="outside",
        increasing=dict(marker=dict(color=GREEN)),
        decreasing=dict(marker=dict(color=RED)),
        totals=dict(marker=dict(color=DKGREEN if profit >= 0 else RED)),
        connector=dict(line=dict(color=LGRAY, width=1, dash="dot"))
    ))
    fig_wf.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor=LGRAY, title="₹"),
        xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_wf, use_container_width=True)

# ── Chart 5: RTO Sensitivity ─────────────────────────────────────
st.markdown("**Profit Sensitivity — How does profit change as RTO rate varies?**")

rto_range   = np.arange(0, 66, 5)
profit_rto  = []
for r in rto_range:
    rto_s = round(shipped * r / 100)
    del_s = shipped - rto_s
    if del_s <= 0:
        profit_rto.append(None)
        continue
    m  = mkt / del_s
    sh = (shipped * fwd_ship + rto_s * rev_ship) / del_s
    profit_rto.append(round(sp - m - sh - cp, 2))

fig_sens = go.Figure()
fig_sens.add_trace(go.Scatter(
    x=rto_range, y=profit_rto,
    mode="lines+markers",
    line=dict(color=BLUE, width=2),
    marker=dict(size=7, color=[DKGREEN if (p and p >= 0) else RED for p in profit_rto]),
    hovertemplate="RTO: %{x}%<br>Profit/Order: ₹%{y}<extra></extra>"
))
fig_sens.add_hline(y=0, line_dash="dash", line_color=RED, annotation_text="Break-even", annotation_position="bottom right")
fig_sens.add_vline(x=rto_rate_pct, line_dash="dot", line_color=AMBER,
                   annotation_text=f"Current RTO: {rto_rate_pct:.1f}%", annotation_position="top right")
fig_sens.update_layout(
    height=340, margin=dict(l=10, r=10, t=20, b=40),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(title="RTO Rate (%)", showgrid=True, gridcolor=LGRAY),
    yaxis=dict(title="Profit per Delivered Order (₹)", showgrid=True, gridcolor=LGRAY)
)
st.plotly_chart(fig_sens, use_container_width=True)

# ── Chart 6: Monthly Profit Projection ───────────────────────────
st.markdown("**Monthly Profit Projection — What if order volume scales?**")

scale_range    = np.arange(100, 2100, 100)
scaled_profits = []
for scale in scale_range:
    sc_can  = round(scale * cancel_rate_pct / 100)
    sc_ship = scale - sc_can
    sc_rto  = round(sc_ship * rto_rate_pct / 100)
    sc_del  = sc_ship - sc_rto
    if sc_del <= 0:
        scaled_profits.append(0)
        continue
    sc_mkt_spend = mkt * (scale / placed) if placed else 0
    sc_m  = sc_mkt_spend / sc_del
    sc_sh = (sc_ship * fwd_ship + sc_rto * rev_ship) / sc_del
    scaled_profits.append(round((sp - sc_m - sc_sh - cp) * sc_del, 0))

fig_proj = go.Figure(go.Bar(
    x=scale_range, y=scaled_profits,
    marker_color=[DKGREEN if p >= 0 else RED for p in scaled_profits],
    hovertemplate="Orders: %{x}<br>Total Profit: ₹%{y:,.0f}<extra></extra>"
))
fig_proj.add_vline(x=placed, line_dash="dot", line_color=AMBER,
                   annotation_text=f"Current: {placed} orders", annotation_position="top right")
fig_proj.add_hline(y=0, line_dash="dash", line_color=RED)
fig_proj.update_layout(
    height=340, margin=dict(l=10, r=10, t=20, b=40),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(title="Total Placed Orders", showgrid=False),
    yaxis=dict(title="Total Monthly Profit (₹)", showgrid=True, gridcolor=LGRAY)
)
st.plotly_chart(fig_proj, use_container_width=True)

st.divider()

# ─── RECOMMENDATIONS ─────────────────────────────────────────────
st.subheader("Recommendations")

tips = []
if profit < 0:
    tips.append(("🔴", "This brand is **loss-making**. Levers: reduce RTO rate, raise selling price, or cut ad spend until ROAS improves."))
if rto_rate_pct > 25:
    tips.append(("🟠", f"RTO rate is **{rto_rate_pct:.1f}%** — above the 25% danger threshold. Push prepaid incentives and NDR management."))
if cancel_rate_pct > 20:
    tips.append(("🟠", f"Cancel rate **{cancel_rate_pct:.1f}%** is high — ads may be attracting low-intent audiences."))
if mkt_per_del > sp * 0.4:
    tips.append(("🟡", f"Marketing cost is **{mkt_per_del/sp*100:.1f}%** of SP — improve ROAS or increase AOV via bundles."))
if 0 < profit_pct < 10:
    tips.append(("🟡", f"Margins are thin at **{profit_pct:.1f}%**. A 5% RTO spike could push this into loss."))
if delivery_rate < 60:
    tips.append(("🔴", f"Only **{delivery_rate:.1f}%** of placed orders delivered — severe funnel leakage."))
if not tips:
    tips.append(("🟢", "Unit economics look healthy! Scale ad spend on winning creatives and focus on repeat purchase rate."))

for icon, tip in tips:
    st.markdown(f"{icon} {tip}")

st.divider()
st.caption("Built on the ShopDeck P&L framework | All metrics and charts update in real time")
