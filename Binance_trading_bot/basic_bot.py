import argparse
import logging
import time
import hmac
import hashlib
import requests
import os

# ==============================
# CONFIGURE LOGGING
# ==============================
os.makedirs("logs", exist_ok=True)  # ensure logs folder exists

logging.basicConfig(
    level=logging.DEBUG,  # use INFO if you want less detail
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/trading_bot.txt"),  # save logs to file
        logging.StreamHandler()  # also print logs to console
    ]
)

# Binance Futures Testnet base URL
BASE_URL = "https://testnet.binancefuture.com"

# 🔑 Testnet API Keys (replace with your own keys if needed)
API_KEY = "6904bc527f04c2ff167c88e060a6690a18484f1503d49556b4d5fd30c3340363"
API_SECRET = "6fef1896f9c8a79fe106e2a8f692f67f1a5bb2666e578e89ce71975f92609e0f"


class BasicBot:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def _sign(self, params):
        """Sign parameters with HMAC SHA256"""
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def place_order(self, symbol, side, quantity, order_type="MARKET", price=None):
        """Place an order on Binance Futures Testnet"""
        endpoint = "/fapi/v1/order"
        url = BASE_URL + endpoint

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }

        if order_type.upper() == "LIMIT":
            if not price:
                raise ValueError("Price required for LIMIT order")
            params["price"] = price
            params["timeInForce"] = "GTC"

        signed_params = self._sign(params)
        headers = {"X-MBX-APIKEY": self.api_key}

        try:
            response = requests.post(url, headers=headers, params=signed_params)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return {"error": str(e)}

        logging.info("Request sent to Binance")
        logging.debug(f"URL: {url}")
        logging.debug(f"Params: {signed_params}")
        logging.debug(f"Headers: {headers}")

        print("\n=== API Response (Order Placed) ===")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text, "\n")

        if response.status_code != 200:
            logging.error(f"Order failed: {response.text}")
            return {"error": response.text}

        try:
            return response.json()
        except Exception:
            return {"error": response.text}

    def get_order_status(self, symbol, order_id):
        """Check status of a specific order"""
        endpoint = "/fapi/v1/order"
        url = BASE_URL + endpoint

        params = {
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(time.time() * 1000)
        }

        signed_params = self._sign(params)
        headers = {"X-MBX-APIKEY": self.api_key}

        try:
            response = requests.get(url, headers=headers, params=signed_params)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return {"error": str(e)}

        print("\n=== API Response (Order Status) ===")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text, "\n")

        if response.status_code != 200:
            logging.error(f"Status check failed: {response.text}")
            return {"error": response.text}

        try:
            return response.json()
        except Exception:
            return {"error": response.text}


def main():
    parser = argparse.ArgumentParser(description="Simplified Trading Bot")
    parser.add_argument("action", choices=["market", "limit"], help="Order type")
    parser.add_argument("--symbol", required=True, help="Trading symbol (e.g., BTCUSDT)")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity")
    parser.add_argument("--price", type=float, help="Order price (for LIMIT only)")

    args = parser.parse_args()

    bot = BasicBot(API_KEY, API_SECRET)

    # Place order
    if args.action == "market":
        result = bot.place_order(args.symbol, args.side, args.quantity, order_type="MARKET")
    elif args.action == "limit":
        if not args.price:
            raise ValueError("Price required for LIMIT order")
        result = bot.place_order(args.symbol, args.side, args.quantity, order_type="LIMIT", price=args.price)
    else:
        result = {"error": "Invalid action"}

    # If order was placed, check status
    if result and "orderId" in result:
        time.sleep(1)  # wait a second before checking
        bot.get_order_status(args.symbol, result["orderId"])


if __name__ == "__main__":
    main()
