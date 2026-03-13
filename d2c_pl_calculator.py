import streamlit as st

st.set_page_config(page_title="D2C P&L Calculator", layout="wide")

st.title("D2C P&L Calculator")
st.caption("ShopDeck framework — all metrics update in real time")

st.divider()

# ─── INPUT SECTION ───────────────────────────────────────────────
st.subheader("Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    placed = st.number_input("Placed Orders", min_value=1, value=200, step=1)
    sp = st.number_input("Selling Price (₹)", min_value=1.0, value=699.0, step=1.0)

with col2:
    cp = st.number_input("Cost Price (₹)", min_value=0.0, value=250.0, step=1.0)
    mkt = st.number_input("Total Marketing Spend (₹)", min_value=0.0, value=8000.0, step=100.0)

with col3:
    fwd_ship = st.number_input("Forward Shipping / Order (₹)", min_value=0.0, value=75.0, step=1.0)
    rev_ship = st.number_input("Reverse Shipping / RTO Order (₹)", min_value=0.0, value=50.0, step=1.0)

st.divider()

# ─── CANCELLED & RTO TOGGLE ──────────────────────────────────────
st.subheader("Cancelled & RTO Orders")

input_mode = st.toggle(
    "Use Percentage instead of Absolute Values",
    value=True,
    help="Toggle ON to enter cancel/RTO as %, toggle OFF to enter exact order counts"
)

col4, col5 = st.columns(2)

if input_mode:
    with col4:
        cancel_pct = st.slider("Cancel Rate (%)", min_value=0, max_value=100, value=15, step=1)
        canceled = round(placed * cancel_pct / 100)
        st.caption(f"→ {canceled} orders canceled")

    shipped = placed - canceled

    with col5:
        rto_pct = st.slider("RTO Rate (%) — applied on shipped orders", min_value=0, max_value=100, value=20, step=1)
        rto_orders = round(shipped * rto_pct / 100)
        st.caption(f"→ {rto_orders} RTO orders")

else:
    with col4:
        canceled = st.number_input(
            "Cancelled Orders (absolute)",
            min_value=0,
            max_value=placed,
            value=min(30, placed),
            step=1
        )
        st.caption(f"→ Cancel rate: {(canceled/placed*100):.1f}%")

    shipped = placed - canceled

    with col5:
        rto_orders = st.number_input(
            "RTO Orders (absolute)",
            min_value=0,
            max_value=shipped,
            value=min(34, shipped),
            step=1
        )
        st.caption(f"→ RTO rate: {(rto_orders/shipped*100 if shipped else 0):.1f}% of shipped orders")

delivered = shipped - rto_orders

st.divider()

# ─── CALCULATIONS ────────────────────────────────────────────────
delivery_rate = (delivered / placed * 100) if placed else 0

mkt_per_del   = mkt / delivered if delivered else 0
fwd_total     = shipped * fwd_ship
rev_total     = rto_orders * rev_ship
ship_per_del  = (fwd_total + rev_total) / delivered if delivered else 0
total_cost    = mkt_per_del + ship_per_del + cp
profit        = sp - total_cost
total_profit  = profit * delivered
profit_pct    = (profit / sp * 100) if sp else 0

# ─── ORDER FUNNEL ────────────────────────────────────────────────
st.subheader("Order Funnel")

fc1, fc2, fc3, fc4, fc5 = st.columns(5)
fc1.metric("Placed", f"{placed}")
fc2.metric("Canceled", f"{canceled}", delta=f"-{(canceled/placed*100):.1f}%", delta_color="inverse")
fc3.metric("Shipped", f"{shipped}")
fc4.metric("RTO", f"{rto_orders}", delta=f"-{(rto_orders/shipped*100 if shipped else 0):.1f}%", delta_color="inverse")
fc5.metric("Delivered ✓", f"{delivered}", delta=f"{delivery_rate:.1f}% delivery rate")

st.divider()

# ─── P&L BREAKDOWN ───────────────────────────────────────────────
st.subheader("P&L per Delivered Order")

left, right = st.columns([2, 1])

with left:
    pl_data = {
        "Item": [
            "Selling Price",
            "— Marketing Cost (adjusted)",
            "— Forward + Reverse Shipping (adjusted)",
            "— Cost Price",
            "Total Cost per Delivered Order",
            "**Profit per Delivered Order**",
        ],
        "Amount (₹)": [
            f"₹{sp:,.2f}",
            f"₹{mkt_per_del:,.2f}",
            f"₹{ship_per_del:,.2f}",
            f"₹{cp:,.2f}",
            f"₹{total_cost:,.2f}",
            f"₹{profit:,.2f}",
        ],
    }
    st.table(pl_data)

with right:
    st.markdown("**Cost breakdown**")
    if total_cost > 0:
        mkt_share   = round(mkt_per_del / total_cost * 100, 1)
        ship_share  = round(ship_per_del / total_cost * 100, 1)
        cp_share    = round(cp / total_cost * 100, 1)
        st.write(f"📣 Marketing: **{mkt_share}%** of total cost")
        st.write(f"🚚 Shipping:  **{ship_share}%** of total cost")
        st.write(f"📦 Cost Price: **{cp_share}%** of total cost")

st.divider()

# ─── SUMMARY METRICS ─────────────────────────────────────────────
st.subheader("Summary Dashboard")

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Profit / Order",
    f"₹{profit:,.2f}",
    delta=f"{profit_pct:.1f}% of SP"
)
m2.metric(
    "Total Monthly Profit",
    f"₹{total_profit:,.0f}",
    delta=f"{delivered} orders delivered"
)
m3.metric(
    "Effective CAC",
    f"₹{mkt_per_del:,.2f}",
    delta="per delivered order",
    delta_color="off"
)
m4.metric(
    "Delivery Rate",
    f"{delivery_rate:.1f}%",
    delta=f"{placed - delivered} orders lost"
)

st.divider()

# ─── RECOMMENDATIONS ─────────────────────────────────────────────
st.subheader("Recommendations")

cancel_rate_pct = canceled / placed * 100 if placed else 0
rto_rate_pct    = rto_orders / shipped * 100 if shipped else 0

tips = []
if profit < 0:
    tips.append(("🔴", "This brand is **loss-making**. Immediate levers: reduce RTO rate, raise selling price, or cut ad spend until ROAS improves."))
if rto_rate_pct > 25:
    tips.append(("🟠", f"RTO rate is **{rto_rate_pct:.1f}%** — above the 25% danger threshold. Focus on prepaid order incentives and NDR (Non-Delivery Report) management."))
if cancel_rate_pct > 20:
    tips.append(("🟠", f"Cancel rate is **{cancel_rate_pct:.1f}%** — ads may be attracting low-intent audiences. Review targeting."))
if mkt_per_del > sp * 0.4:
    tips.append(("🟡", f"Marketing cost is **{(mkt_per_del/sp*100):.1f}%** of selling price — too high. Improve ROAS or increase AOV via bundles/upsells."))
if 0 < profit_pct < 10:
    tips.append(("🟡", f"Margins are thin at **{profit_pct:.1f}%**. A 5% increase in RTO rate would likely push this into loss."))
if delivery_rate < 60:
    tips.append(("🔴", f"Only **{delivery_rate:.1f}%** of placed orders are being delivered — severe funnel leakage."))
if not tips:
    tips.append(("🟢", "Unit economics look healthy! Scale ad spend on winning creatives and focus on increasing repeat purchase rate."))

for icon, tip in tips:
    st.markdown(f"{icon} {tip}")

st.divider()
st.caption("Built on the ShopDeck P&L framework | Adjust any input above — all metrics update in real time")
