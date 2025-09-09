import streamlit as st
import json
import time
from basic_bot import BasicBot, API_KEY, API_SECRET  # Import your bot

st.set_page_config(page_title="Binance Futures Testnet Trader", page_icon="📈", layout="centered")

st.title("📈 Binance Futures Testnet Trader")

# Input form
with st.form("order_form"):
    symbol = st.text_input("Trading Symbol (e.g., BTCUSDT)", "BTCUSDT")
    side = st.selectbox("Order Side", ["BUY", "SELL"])
    order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
    quantity = st.number_input("Quantity", value=0.001, step=0.001)
    price = None
    if order_type == "LIMIT":
        price = st.number_input("Price", value=20000.0, step=100.0)

    submitted = st.form_submit_button("🚀 Place Order")

if submitted:
    bot = BasicBot(API_KEY, API_SECRET)

    try:
        # Place order
        result = bot.place_order(symbol, side, quantity, order_type=order_type, price=price)

        if "orderId" in result:
            st.success(f"✅ Order Sent Successfully! (Order ID: {result['orderId']})")

            # Show key details
            key_fields = {
                "Order ID": result.get("orderId"),
                "Symbol": result.get("symbol"),
                "Side": result.get("side"),
                "Type": result.get("type"),
                "Status": result.get("status"),
                "Quantity": result.get("origQty"),
                "Executed": result.get("executedQty"),
                "Price": result.get("price"),
                "Avg. Price": result.get("avgPrice")
            }
            st.table([key_fields])

            # Expandable full JSON
            with st.expander("📜 Full API Response"):
                st.json(result)

            # 🔄 Live Order Status Refresh
            st.info("⏳ Tracking order status...")

            status_placeholder = st.empty()

            for i in range(10):  # check 10 times (20s max)
                status = bot.get_order_status(symbol, result["orderId"])

                if "status" in status:
                    status_placeholder.write(f"🔄 Current Status: **{status['status']}**")

                    if status["status"] in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                        st.success(f"✅ Final Status: {status['status']}")
                        st.json(status)
                        break
                else:
                    status_placeholder.error("⚠️ Failed to fetch order status")
                    break

                time.sleep(2)

        else:
            st.error("❌ Order Failed")
            st.json(result)

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
