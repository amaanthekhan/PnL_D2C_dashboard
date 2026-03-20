import streamlit as st
import plotly.graph_objects as go
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io, os, tempfile
from datetime import date, timedelta
from fpdf import FPDF

st.set_page_config(page_title="D2C P&L Dash V3 · by Amaan", layout="wide")

# ── Colour palette ────────────────────────────────────────────────
BLUE    = "#378ADD"
GREEN   = "#1D9E75"
DKGREEN = "#0F6E56"
LGREEN  = "#639922"
AMBER   = "#F59E0B"
RED     = "#993C1D"
LGRAY   = "#f3f4f6"

# ════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════
st.title("D2C P&L Dash")
st.caption("Just plug in your numbers and see if your D2C business is profitable or not. — built by Amaan")
st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 0 — Report Details  (vertical, clean)
# ════════════════════════════════════════════════════════════════════
st.subheader("Who are we looking at?")

# Row 1 — Brand name (half width)
left, _ = st.columns([1, 1])
with left:
    company_name = st.text_input(
        "Brand / Company Name",
        placeholder="e.g. Bewakoof, Noise, The Souled Store…"
    )

# Row 2 — Date mode toggle (half width)
with left:
    use_custom_dates = st.toggle(
        "Use Custom Date Range instead of Monthly Mode", value=False
    )

month_names = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

# Row 3 — Date inputs (half width, varies by mode)
if use_custom_dates:
    d1, d2 = st.columns([1, 1])
    with d1:
        start_date = st.date_input("From", value=date.today().replace(day=1))
    with d2:
        end_date = st.date_input("To", value=date.today())
    if end_date < start_date:
        st.warning("End date can't be before start date.")
        end_date = start_date
    num_days        = (end_date - start_date).days + 1
    timeframe_label = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')} ({num_days} days)"
    days_factor     = num_days / 30.0
else:
    m1, m2 = st.columns([1, 1])
    with m1:
        sel_month = st.selectbox("Month", month_names, index=date.today().month - 1)
    with m2:
        sel_year = st.number_input("Year", min_value=2000, max_value=2100,
                                    value=date.today().year, step=1)
    month_idx  = month_names.index(sel_month) + 1
    last_day   = (date(int(sel_year) + (1 if month_idx == 12 else 0),
                       1 if month_idx == 12 else month_idx + 1, 1) - timedelta(days=1)).day
    num_days        = last_day
    days_factor     = 1.0
    timeframe_label = f"{sel_month} {int(sel_year)}"
    start_date      = date(int(sel_year), month_idx, 1)
    end_date        = date(int(sel_year), month_idx, last_day)

display_name = company_name.strip() if company_name.strip() else "This Brand"

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 1 — Core Inputs  (symmetric 3-col layout)
# ════════════════════════════════════════════════════════════════════
st.subheader("The Numbers")
st.caption("Fill in your brand's raw numbers.")

col1, col2, col3 = st.columns(3)

with col1:
    placed   = st.number_input("Placed Orders", min_value=1, value=200, step=1,
                                help="Total orders placed by customers during this period")
    sp       = st.number_input("Selling Price (₹)", min_value=1.0, value=699.0, step=1.0,
                                help="What the customer pays per order")

with col2:
    cp       = st.number_input("Cost Price (₹)", min_value=0.0, value=250.0, step=1.0,
                                help="What it costs you to make/source the product")
    fwd_ship = st.number_input("Forward Shipping / Order (₹)", min_value=0.0, value=75.0, step=1.0,
                                help="Cost to ship the order to the customer")

with col3:
    rev_ship = st.number_input("Reverse Shipping / RTO (₹)", min_value=0.0, value=50.0, step=1.0,
                                help="Cost to get the order back when customer refuses delivery")
    mkt_mode = st.toggle("Enter marketing as cost per placed order", value=False,
                          help="OFF = total spend  |  ON = cost per placed order")
    if mkt_mode:
        mkt_per_placed = st.number_input("Marketing Cost per Placed Order (₹)",
                                          min_value=0.0, value=40.0, step=1.0)
        mkt = mkt_per_placed * placed
        st.caption(f"→ Total marketing spend: ₹{mkt:,.0f}")
    else:
        mkt = st.number_input("Total Marketing Spend (₹)", min_value=0.0, value=8000.0, step=100.0)
        st.caption(f"→ Per placed order: ₹{mkt/placed:,.2f}")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 2 — Cancellations & RTO
# ════════════════════════════════════════════════════════════════════
st.subheader("Cancellations & RTO")
st.caption("Enter the Cancellations & RTO as exact numbers OR as percentages. Track it carefully.")

use_pct = st.toggle("Use percentages (slider) instead of exact numbers", value=True)

col4, col5 = st.columns(2)

if use_pct:
    with col4:
        cancel_pct = st.slider("Cancel Rate (%)", 0, 100, 15,
                                help="% of placed orders canceled before shipping")
        canceled   = round(placed * cancel_pct / 100)
    shipped = placed - canceled
    with col5:
        rto_pct    = st.slider("RTO Rate (%) — of shipped orders", 0, 100, 20,
                                help="% of shipped orders returned undelivered")
        rto_orders = round(shipped * rto_pct / 100)
else:
    with col4:
        canceled   = st.number_input("Cancelled Orders", min_value=0, max_value=placed,
                                      value=min(30, placed), step=1)
    shipped = placed - canceled
    with col5:
        rto_orders = st.number_input("RTO Orders", min_value=0, max_value=int(shipped),
                                      value=min(34, int(shipped)), step=1)

delivered = max(int(shipped) - int(rto_orders), 0)

st.divider()

# ════════════════════════════════════════════════════════════════════
# CORE CALCULATIONS
# ════════════════════════════════════════════════════════════════════
delivery_rate   = (delivered  / placed   * 100) if placed   else 0
cancel_rate_pct = (canceled   / placed   * 100) if placed   else 0
rto_rate_pct    = (rto_orders / shipped  * 100) if shipped  else 0

mkt_per_del  = mkt / delivered if delivered else 0
fwd_total    = shipped    * fwd_ship
rev_total    = rto_orders * rev_ship
ship_per_del = (fwd_total + rev_total) / delivered if delivered else 0
total_cost   = mkt_per_del + ship_per_del + cp
profit       = sp - total_cost
total_profit = profit * delivered * days_factor
profit_pct   = (profit / sp * 100) if sp else 0

# ── ROAS & CM2 ────────────────────────────────────────────────────
revenue_total = sp * delivered * days_factor
roas          = revenue_total / (mkt * days_factor) if mkt else 0
cm2           = sp - mkt_per_del - ship_per_del - cp   # same as profit, named formally
cm2_pct       = (cm2 / sp * 100) if sp else 0

# ════════════════════════════════════════════════════════════════════
# SECTION 3 — Order Funnel
# ════════════════════════════════════════════════════════════════════
st.subheader("Order Funnel")

fc1, fc2, fc3, fc4, fc5 = st.columns(5)
fc1.metric("Placed",      f"{placed}")
fc2.metric("Canceled",    f"{canceled}")
fc3.metric("Shipped",     f"{shipped}")
fc4.metric("RTO",         f"{rto_orders}")
fc5.metric("Delivered ✓", f"{delivered}")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 4 — P&L Table
# ════════════════════════════════════════════════════════════════════
st.subheader("P&L per Delivered Order")

tl, tr = st.columns([2, 1])
with tl:
    st.table({
        "Item": [
            "Selling Price",
            "— Marketing Cost (adjusted to delivered)",
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
    st.markdown("**Breaking down the Total cost per delivered order**")
    if total_cost > 0:
        st.write(f"📣 Marketing:   **{mkt_per_del/total_cost*100:.1f}%** of total cost")
        st.write(f"🚚 Shipping:    **{ship_per_del/total_cost*100:.1f}%** of total cost")
        st.write(f"📦 Cost Price:  **{cp/total_cost*100:.1f}%** of total cost")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 5 — Summary Dashboard
# ════════════════════════════════════════════════════════════════════
st.subheader("Summary Dashboard")

m1, m2, m3 = st.columns(3)
m1.metric("CM2 / Order",
          f"₹{cm2:,.2f}",
          delta=f"{cm2_pct:.1f}% of selling price",
          help="Contribution Margin 2 = SP - Marketing - Shipping - COGS. ShopDeck's north star metric.")
m2.metric(f"Total Profit — {timeframe_label}",
          f"₹{total_profit:,.0f}",
          delta=f"{delivered} orders delivered")
m3.metric("ROAS",
          f"{roas:.2f}x",
          delta=f"{'Healthy' if roas >= 2.5 else 'Below benchmark'}",
          delta_color="normal" if roas >= 2.5 else "inverse",
          help="Return on Ad Spend = Revenue from delivered orders / Total marketing spend. Benchmark: 2.5x–4x for D2C.")

st.write("")

m4, m5, m6 = st.columns(3)
m4.metric("Effective CAC",
          f"₹{mkt_per_del:,.2f}",
          delta="per delivered order", delta_color="off",
          help="Customer Acquisition Cost adjusted to delivered order level.")
m5.metric("Delivery Rate",
          f"{delivery_rate:.1f}%",
          delta=f"{placed - delivered} orders lost", delta_color="inverse")
m6.metric("Profit Margin",
          f"{profit_pct:.1f}%",
          delta=f"₹{profit:,.2f} per order",
          delta_color="normal" if profit >= 0 else "inverse")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 6 — Charts   (all transparent bg)
# ════════════════════════════════════════════════════════════════════
st.subheader("Charts & Visualizations")

TRANSP = "rgba(0,0,0,0)"

def build_funnel_chart():
    fig = go.Figure(go.Funnel(
        y=["Placed", "Shipped", "Delivered"],
        x=[placed, shipped, delivered],
        textinfo="value+percent initial",
        marker=dict(color=[BLUE, GREEN, LGREEN]),
        connector=dict(line=dict(color=LGRAY, width=1))
    ))
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10),
                      paper_bgcolor=TRANSP, font=dict(size=13))
    return fig

def build_donut():
    labels = ["Marketing", "Shipping", "Cost Price", "Profit" if profit >= 0 else "Loss"]
    values = [max(mkt_per_del,0), max(ship_per_del,0), max(cp,0), max(abs(profit),0)]
    colors = [BLUE, GREEN, AMBER, DKGREEN if profit >= 0 else RED]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>₹%{value:.2f}<br>%{percent}<extra></extra>"
    ))
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=40),
                      paper_bgcolor=TRANSP,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.35))
    return fig

def build_bar():
    fig = go.Figure()
    for name, val, color in [("Delivered", delivered, LGREEN),
                               ("RTO", rto_orders, AMBER),
                               ("Canceled", canceled, RED)]:
        fig.add_trace(go.Bar(name=name, x=["Orders"], y=[val],
                             marker_color=color, text=[str(val)], textposition="inside"))
    fig.update_layout(barmode="stack", height=320,
                      margin=dict(l=10,r=10,t=10,b=10),
                      paper_bgcolor=TRANSP, plot_bgcolor=TRANSP,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                      xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=True, gridcolor=LGRAY, title="Orders"))
    return fig

def build_waterfall():
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","relative","relative","total"],
        x=["Selling\nPrice","Marketing","Shipping","Cost\nPrice","Profit"],
        y=[sp, -mkt_per_del, -ship_per_del, -cp, 0],
        text=[f"₹{sp:.0f}", f"-₹{mkt_per_del:.0f}", f"-₹{ship_per_del:.0f}",
              f"-₹{cp:.0f}", f"₹{profit:.0f}"],
        textposition="outside",
        increasing=dict(marker=dict(color=GREEN)),
        decreasing=dict(marker=dict(color=RED)),
        totals=dict(marker=dict(color=DKGREEN if profit >= 0 else RED)),
        connector=dict(line=dict(color=LGRAY, width=1, dash="dot"))
    ))
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10),
                      paper_bgcolor=TRANSP, plot_bgcolor=TRANSP,
                      showlegend=False,
                      yaxis=dict(showgrid=True, gridcolor=LGRAY, title="₹"),
                      xaxis=dict(showgrid=False))
    return fig

def build_sensitivity():
    rto_range, profit_rto = np.arange(0, 66, 5), []
    for r in rto_range:
        rto_s = round(shipped * r / 100)
        del_s = shipped - rto_s
        if del_s <= 0:
            profit_rto.append(None); continue
        m  = mkt / del_s
        sh = (shipped * fwd_ship + rto_s * rev_ship) / del_s
        profit_rto.append(round(sp - m - sh - cp, 2))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rto_range, y=profit_rto, mode="lines+markers",
        line=dict(color=BLUE, width=2),
        marker=dict(size=8, color=[DKGREEN if (p is not None and p >= 0) else RED
                                    for p in profit_rto]),
        hovertemplate="RTO Rate: %{x}%<br>Profit/Order: ₹%{y}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=RED,
                  annotation_text="Break-even", annotation_position="bottom right")
    fig.add_vline(x=rto_rate_pct, line_dash="dot", line_color=AMBER,
                  annotation_text=f"You're here ({rto_rate_pct:.1f}%)",
                  annotation_position="top right")
    fig.update_layout(height=360, margin=dict(l=10,r=10,t=20,b=50),
                      paper_bgcolor=TRANSP, plot_bgcolor=TRANSP,
                      xaxis=dict(title="RTO Rate (%)", showgrid=True, gridcolor=LGRAY),
                      yaxis=dict(title="Profit per Delivered Order (₹)",
                                 showgrid=True, gridcolor=LGRAY))
    return fig

# Row 1
r1l, r1r = st.columns(2)
with r1l:
    st.markdown("**Order Funnel**")
    st.plotly_chart(build_funnel_chart(), use_container_width=True)
with r1r:
    st.markdown("**Cost vs Profit Breakdown per Order**")
    st.plotly_chart(build_donut(), use_container_width=True)

st.write("")

# Row 2
r2l, r2r = st.columns(2)
with r2l:
    st.markdown("**Order Status Distribution**")
    st.plotly_chart(build_bar(), use_container_width=True)
with r2r:
    st.markdown("**Where does the selling price go? (Waterfall)**")
    st.plotly_chart(build_waterfall(), use_container_width=True)

st.write("")

# RTO Sensitivity
st.markdown("**What happens to profit if RTO rate changes?**")
st.caption("The Indian markets problem!")
st.plotly_chart(build_sensitivity(), use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 7 — Verdict
# ════════════════════════════════════════════════════════════════════
st.subheader("Verdict")

verdicts = []
if profit < 0:
    verdicts.append(("🔴", f"{display_name} is losing money on every order right now. "
                           f"Spending ₹{abs(profit):.0f} more than earned per delivery. "
                           f"Priority: reduce RTO or cut ad spend."))
elif profit_pct < 10:
    verdicts.append(("🟡", f"{display_name} is profitable but margins are very thin at {profit_pct:.1f}%. "
                           f"One bad month of high RTO could flip this to a loss."))
else:
    verdicts.append(("🟢", f"{display_name} looks healthy — earning ₹{profit:.0f} per delivered order "
                           f"({profit_pct:.1f}% margin). Good time to scale ad spend on what's working."))

if rto_rate_pct > 25:
    verdicts.append(("🔴", f"RTO is at {rto_rate_pct:.1f}% — more than 1 in 4 shipped orders are coming back. "
                           f"Focus on prepaid incentives, better NDR calling, and targeting quality."))
elif rto_rate_pct > 15:
    verdicts.append(("🟡", f"RTO at {rto_rate_pct:.1f}% is manageable but worth watching. "
                           f"Getting it under 15% would noticeably improve per-order profit."))

if cancel_rate_pct > 20:
    verdicts.append(("🟠", f"Cancel rate of {cancel_rate_pct:.1f}% is high. "
                           f"Ads may be reaching people who aren't ready to buy."))

if mkt_per_del > sp * 0.4:
    verdicts.append(("🟡", f"Marketing is eating {mkt_per_del/sp*100:.1f}% of the selling price. "
                           f"Improve ROAS or increase AOV through bundles."))

if delivery_rate < 60:
    verdicts.append(("🔴", f"Only {delivery_rate:.1f}% of placed orders are delivered. "
                           f"Nearly half of every marketing rupee is being wasted."))

for icon, text in verdicts:
    st.markdown(f"{icon} {text}")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 8 — What-if Simulator
# ════════════════════════════════════════════════════════════════════
st.subheader("What-if Simulator")
st.caption("Tweak variables and instantly see how it changes our profit. Great for merchant conversations.")

with st.expander("Open the What-if Simulator", expanded=False):
    wi1, wi2 = st.columns(2)

    with wi1:
        st.markdown("**Adjust a variable**")
        what_if_var = st.selectbox(
            "Which variable do you want to change?",
            ["RTO Rate (%)", "Selling Price (₹)", "Marketing Spend (₹)",
             "Cancel Rate (%)", "Forward Shipping (₹)", "Cost Price (₹)"]
        )

        if what_if_var == "RTO Rate (%)":
            wi_val = st.slider("New RTO Rate (%)", 0, 100,
                                max(0, int(rto_rate_pct) - 5),
                                help="Try reducing RTO and watch the profit jump")
            wi_rto_orders = round(shipped * wi_val / 100)
            wi_delivered  = max(shipped - wi_rto_orders, 0)
            wi_mkt        = mkt / wi_delivered if wi_delivered else 0
            wi_ship       = (shipped * fwd_ship + wi_rto_orders * rev_ship) / wi_delivered if wi_delivered else 0
            wi_profit     = sp - wi_mkt - wi_ship - cp
            wi_roas       = (sp * wi_delivered) / mkt if mkt else 0
            wi_cm2        = wi_profit

        elif what_if_var == "Selling Price (₹)":
            wi_val    = st.number_input("New Selling Price (₹)", min_value=1.0,
                                         value=round(sp + 50), step=1.0)
            wi_profit = wi_val - mkt_per_del - ship_per_del - cp
            wi_roas   = (wi_val * delivered) / mkt if mkt else 0
            wi_cm2    = wi_profit

        elif what_if_var == "Marketing Spend (₹)":
            wi_val    = st.number_input("New Total Marketing Spend (₹)", min_value=0.0,
                                         value=round(mkt * 0.8), step=100.0)
            wi_mkt_pd = wi_val / delivered if delivered else 0
            wi_profit = sp - wi_mkt_pd - ship_per_del - cp
            wi_roas   = (sp * delivered) / wi_val if wi_val else 0
            wi_cm2    = wi_profit

        elif what_if_var == "Cancel Rate (%)":
            wi_val        = st.slider("New Cancel Rate (%)", 0, 100,
                                       max(0, int(cancel_rate_pct) - 5))
            wi_canceled   = round(placed * wi_val / 100)
            wi_shipped    = placed - wi_canceled
            wi_rto_n      = round(wi_shipped * rto_rate_pct / 100)
            wi_delivered  = max(wi_shipped - wi_rto_n, 0)
            wi_mkt_pd     = mkt / wi_delivered if wi_delivered else 0
            wi_ship       = (wi_shipped * fwd_ship + wi_rto_n * rev_ship) / wi_delivered if wi_delivered else 0
            wi_profit     = sp - wi_mkt_pd - wi_ship - cp
            wi_roas       = (sp * wi_delivered) / mkt if mkt else 0
            wi_cm2        = wi_profit

        elif what_if_var == "Forward Shipping (₹)":
            wi_val    = st.number_input("New Forward Shipping / Order (₹)", min_value=0.0,
                                         value=max(0.0, fwd_ship - 10), step=1.0)
            wi_ship   = (shipped * wi_val + rto_orders * rev_ship) / delivered if delivered else 0
            wi_profit = sp - mkt_per_del - wi_ship - cp
            wi_roas   = roas
            wi_cm2    = wi_profit

        else:  # Cost Price
            wi_val    = st.number_input("New Cost Price (₹)", min_value=0.0,
                                         value=max(0.0, cp - 20), step=1.0)
            wi_profit = sp - mkt_per_del - ship_per_del - wi_val
            wi_roas   = roas
            wi_cm2    = wi_profit

    with wi2:
        st.markdown("**Impact**")

        delta_profit = wi_profit - profit
        delta_cm2    = wi_cm2 - cm2
        delta_roas   = wi_roas - roas if what_if_var not in ["Forward Shipping (₹)", "Cost Price (₹)"] else 0

        profit_color = "green" if wi_profit >= profit else "red"
        arrow        = "▲" if delta_profit >= 0 else "▼"

        st.metric("New Profit / Order",
                  f"₹{wi_profit:,.2f}",
                  delta=f"{arrow} ₹{abs(delta_profit):,.2f} vs current",
                  delta_color="normal" if delta_profit >= 0 else "inverse")

        st.metric("New CM2 / Order",
                  f"₹{wi_cm2:,.2f}",
                  delta=f"{'+' if delta_cm2 >= 0 else ''}{delta_cm2:,.2f} vs current",
                  delta_color="normal" if delta_cm2 >= 0 else "inverse")

        if what_if_var not in ["Forward Shipping (₹)", "Cost Price (₹)"]:
            st.metric("New ROAS",
                      f"{wi_roas:.2f}x",
                      delta=f"{'+' if delta_roas >= 0 else ''}{delta_roas:.2f}x vs current",
                      delta_color="normal" if delta_roas >= 0 else "inverse")

        wi_total = wi_profit * delivered * days_factor
        delta_total = wi_total - total_profit
        st.metric(f"New Total Profit — {timeframe_label}",
                  f"₹{wi_total:,.0f}",
                  delta=f"{'+' if delta_total >= 0 else ''}₹{delta_total:,.0f} vs current",
                  delta_color="normal" if delta_total >= 0 else "inverse")

        st.caption(f"Currently: ₹{profit:,.2f}/order  |  CM2: ₹{cm2:,.2f}  |  ROAS: {roas:.2f}x")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 9 — PDF  (matplotlib for chart images — no Chrome needed)
# ════════════════════════════════════════════════════════════════════
st.subheader("Download Report")
st.caption("Includes full P&L, summary numbers, pie-chart, waterfall graph, and the suggestions.")

def mpl_donut(path):
    """Donut chart via matplotlib — works on Streamlit Cloud."""
    labels = ["Marketing", "Shipping", "Cost Price", "Profit" if profit >= 0 else "Loss"]
    values = [max(mkt_per_del,0), max(ship_per_del,0), max(cp,0), max(abs(profit),0)]
    colors = [BLUE, GREEN, AMBER, DKGREEN if profit >= 0 else RED]

    fig, ax = plt.subplots(figsize=(6, 4), facecolor="white")
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=90,
        wedgeprops=dict(width=0.5),
        textprops=dict(fontsize=10)
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax.set_title("Cost vs Profit Breakdown per Order", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

def mpl_waterfall(path):
    """Waterfall chart via matplotlib — works on Streamlit Cloud."""
    labels    = ["Selling\nPrice", "Marketing", "Shipping", "Cost\nPrice", "Profit"]
    values    = [sp, -mkt_per_del, -ship_per_del, -cp, profit]
    bar_colors= [GREEN, RED, RED, RED, DKGREEN if profit >= 0 else RED]

    # running bottom for waterfall effect
    running   = [0, sp, sp - mkt_per_del, sp - mkt_per_del - ship_per_del,
                 sp - mkt_per_del - ship_per_del - cp]
    bottoms   = [0, sp - mkt_per_del, sp - mkt_per_del - ship_per_del,
                 sp - mkt_per_del - ship_per_del - cp, 0]
    heights   = [sp, mkt_per_del, ship_per_del, cp, profit]
    bots      = [0, sp - mkt_per_del, sp - mkt_per_del - ship_per_del,
                 sp - mkt_per_del - ship_per_del - cp, 0]

    fig, ax = plt.subplots(figsize=(7, 4), facecolor="white")
    for i, (label, height, bot, color) in enumerate(zip(labels, heights, bots, bar_colors)):
        ax.bar(i, height, bottom=bot, color=color, width=0.5, alpha=0.9)
        sign = "+" if height >= 0 else ""
        ax.text(i, bot + height + sp * 0.01, f"₹{height:.0f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("₹", fontsize=10)
    ax.axhline(0, color="#999", linewidth=0.8, linestyle="--")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("Selling Price Waterfall per Delivered Order", fontsize=12,
                 fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

def generate_pdf():
    tmp   = tempfile.mkdtemp()
    dp    = os.path.join(tmp, "donut.png")
    wp    = os.path.join(tmp, "waterfall.png")
    mpl_donut(dp)
    mpl_waterfall(wp)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Header ────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, company_name.strip() or "D2C P&L Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"Period: {timeframe_label}", ln=True, align="C")
    pdf.cell(0, 7, "D2C P&L Dash  ·  built by Amaan Khan", ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # ── Order Funnel ──────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Order Funnel", ln=True)
    pdf.ln(2)
    for label, val in [("Placed", placed), ("Canceled", canceled),
                        ("Shipped", shipped), ("RTO", rto_orders),
                        ("Delivered", delivered)]:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(90, 7, label)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, str(val), ln=True)
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # ── P&L Breakdown ─────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "P&L per Delivered Order", ln=True)
    pdf.ln(2)
    pl_rows = [
        ("Selling Price",                          sp,           False),
        ("Marketing Cost (adjusted)",              mkt_per_del,  False),
        ("Fwd + Rev Shipping (adjusted)",          ship_per_del, False),
        ("Cost Price",                             cp,           False),
        ("Total Cost per Delivered Order",         total_cost,   True),
        ("Profit per Delivered Order",             profit,       True),
    ]
    for label, val, bold in pl_rows:
        pdf.set_font("Helvetica", "B" if bold else "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(120, 7, label)
        if "Profit" in label:
            r, g, b = (15,110,86) if val >= 0 else (153,60,29)
            pdf.set_text_color(r, g, b)
        else:
            pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, f"Rs {val:,.2f}", ln=True)
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # ── Summary ───────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.ln(2)
    for label, val in [
        ("CM2 per Order",                      f"Rs {cm2:,.2f}  ({cm2_pct:.1f}% of SP)"),
        ("ROAS",                               f"{roas:.2f}x"),
        (f"Total Profit ({timeframe_label})",  f"Rs {total_profit:,.0f}"),
        ("Effective CAC (per delivered order)",f"Rs {mkt_per_del:,.2f}"),
        ("Delivery Rate",                      f"{delivery_rate:.1f}%"),
        ("Cancel Rate",                        f"{cancel_rate_pct:.1f}%"),
        ("RTO Rate",                           f"{rto_rate_pct:.1f}%"),
    ]:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(120, 7, label)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, val, ln=True)
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # ── Chart 1: Donut ────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Chart: Cost vs Profit Breakdown per Order", ln=True)
    pdf.ln(2)
    pdf.image(dp, x=15, w=180)
    pdf.ln(6)

    # ── Chart 2: Waterfall ────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Chart: Selling Price Waterfall per Delivered Order", ln=True)
    pdf.ln(2)
    pdf.image(wp, x=15, w=180)
    pdf.ln(6)

    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # ── Footer ────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 6,
             "Generated by D2C P&L Dash  ·  built by Amaan Khan  ·  khanamaan2203@gmail.com",
             ln=True, align="C")

    os.remove(dp); os.remove(wp); os.rmdir(tmp)
    return bytes(pdf.output())


if st.button("Generate & Download PDF"):
    if not company_name.strip():
        st.warning("Please enter a brand/company name before downloading.")
    else:
        with st.spinner("Building your PDF… usually done in 3–5 seconds."):
            try:
                pdf_bytes = generate_pdf()
                fname = (f"PnL_{company_name.strip().replace(' ','_')}"
                         f"_{timeframe_label.replace(' ','_')}.pdf")
                st.download_button("Save PDF", data=pdf_bytes,
                                   file_name=fname, mime="application/pdf")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

st.divider()
st.caption("D2C P&L Dash · built by Amaan Khan")
