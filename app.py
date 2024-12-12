from flask import Flask, render_template, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

# Constants
TOKEN_NAME = "kip"  # Hardcoded token name
TOTAL_TOKEN_OFFERED = 50000000  # Hardcoded total tokens offered
MOCA_API_URL = "https://api.staking.mocaverse.xyz/api/mocadrop/projects/kip-protocol"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# Global variable to store the token price
current_token_price = None  # Will be updated in the background thread

# Function to fetch staking power from Mocaverse
def get_pool_data():
    try:
        response = requests.get(MOCA_API_URL)
        response.raise_for_status()
        data = response.json()
        return float(data.get("stakingPowerBurnt", 0))
    except Exception as e:
        print(f"Error fetching Mocaverse data: {e}")
        return None

# Background function to fetch token price from CoinGecko
def update_token_price():
    global current_token_price
    while True:
        try:
            params = {"ids": TOKEN_NAME, "vs_currencies": "usd"}
            response = requests.get(COINGECKO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            current_token_price = data.get(TOKEN_NAME, {}).get("usd")
            print(f"Updated token price: {current_token_price}")
        except Exception as e:
            print(f"Error updating token price: {e}")
        
        # Wait for 60 seconds before fetching again
        time.sleep(60)

@app.route("/")
def index():
    return render_template("index.html", token_name=TOKEN_NAME, total_token_offered=TOTAL_TOKEN_OFFERED)

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        user_burn = float(request.form["user_burn"])
        total_burnt = get_pool_data()

        # Use the globally stored token price
        if current_token_price is None:
            return jsonify({"error": "Token price not available. Please try again later."}), 500

        if not total_burnt:
            return jsonify({"error": "Failed to fetch total staking power from Mocaverse."}), 500

        # Calculate results
        tokens_received = (TOTAL_TOKEN_OFFERED / total_burnt) * user_burn
        airdrop_value = tokens_received * current_token_price

        return jsonify({
            "token_name": TOKEN_NAME,
            "token_price": current_token_price,
            "tokens_received": tokens_received,
            "airdrop_value": airdrop_value,
        })
    except Exception as e:
        print(f"Error during calculation: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Start the background thread when the app starts
if __name__ == "__main__":
    # Start the background thread for updating token price
    price_thread = threading.Thread(target=update_token_price, daemon=True)
    price_thread.start()

    # Run the Flask app
    app.run(debug=True)
