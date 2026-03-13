import streamlit as st

st.title("D2C Profit & Loss Calculator")

st.header("Input Values")

placed_orders = st.number_input("Placed Orders", value=100)

mode = st.radio("Input Mode", ["Absolute", "Percentage"])

if mode == "Absolute":
    cancelled = st.number_input("Cancelled Orders", value=10)
    rto = st.number_input("RTO Orders", value=20)
else:
    cancel_rate = st.slider("Cancellation Rate (%)", 0,100,10)
    rto_rate = st.slider("RTO Rate (%)", 0,100,20)

    cancelled = int(placed_orders * cancel_rate / 100)
    rto = int((placed_orders - cancelled) * rto_rate / 100)

marketing = st.number_input("Marketing Cost per Placed Order", value=50)
shipping = st.number_input("Shipping Cost per Shipped Order", value=50)
cost_price = st.number_input("Product Cost", value=100)
selling_price = st.number_input("Selling Price", value=250)

non_cancelled = placed_orders - cancelled
delivered = non_cancelled - rto

total_marketing = marketing * placed_orders
total_shipping = shipping * non_cancelled

marketing_per_order = total_marketing / delivered
shipping_per_order = total_shipping / delivered

total_cost = marketing_per_order + shipping_per_order + cost_price
profit = selling_price - total_cost
margin = (profit / selling_price) * 100

st.header("Order Funnel")

st.write("Placed Orders:", placed_orders)
st.write("Cancelled Orders:", cancelled)
st.write("Shipped Orders:", non_cancelled)
st.write("RTO Orders:", rto)
st.write("Delivered Orders:", delivered)

st.header("Profitability")

st.metric("Profit per Delivered Order", round(profit,2))
st.metric("Profit Margin (%)", round(margin,2))
