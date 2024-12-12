from flask import Flask, render_template, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

# Constants
TOKEN_NAME = "kip"  # Hardcoded token name
TOTAL_TOKEN_OFFERED = 50000000  # Hardcoded total tokens offered
MOCA_API_URL = "https://api.staking.mocaverse.xyz/api/mocadrop/projects/kip-protocol"
COINGECKO_24H_URL = "https://www.coingecko.com/price_charts/52585/usd/24_hours.json"

# Global variable to store the token price
current_token_price = 0.0  # Default value

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

# Background function to fetch token price from Coingecko (24h stats endpoint)
def update_token_price():
    global current_token_price
    print("Background thread for updating token price has started...")
    while True:
        try:
            print("Fetching token price from Coingecko 24-hour stats endpoint...")
            response = requests.get(COINGECKO_24H_URL)
            response.raise_for_status()
            data = response.json()
            stats = data.get("stats", [])

            if stats:
                # Get the final price from the last entry in stats
                current_token_price = stats[-1][1]  # [timestamp, price]
                print(f"Updated token price: {current_token_price}")
            else:
                print("Failed to fetch a valid token price from Coingecko.")
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
        print(f"User Burn Input: {user_burn}")

        total_burnt = get_pool_data()
        print(f"Total Burnt from Mocaverse: {total_burnt}")

        if current_token_price is None or current_token_price <= 0:
            print("Invalid token price. Waiting for a valid price.")
            return jsonify({"error": "Token price is still being fetched. Please try again later."}), 500

        if not total_burnt:
            print("Failed to fetch total staking power.")
            return jsonify({"error": "Failed to fetch total staking power from Mocaverse."}), 500

        # Calculate results
        tokens_received = (TOTAL_TOKEN_OFFERED / total_burnt) * user_burn
        airdrop_value = tokens_received * current_token_price

        print(f"Tokens Received: {tokens_received}, Airdrop Value: {airdrop_value}")
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
    print("Starting Flask application and fetching initial token price...")
    try:
        print("Fetching initial token price from Coingecko 24-hour stats endpoint...")
        response = requests.get(COINGECKO_24H_URL)
        response.raise_for_status()
        data = response.json()
        stats = data.get("stats", [])

        if stats:
            # Get the final price from the last entry in stats
            current_token_price = stats[-1][1]  # [timestamp, price]
            print(f"Initial token price fetched successfully: {current_token_price}")
        else:
            print("Failed to fetch an initial token price.")
    except Exception as e:
        print(f"Error fetching initial token price: {e}")

    # Start the background thread for updating token price
    print("Starting background thread for token price updates...")
    price_thread = threading.Thread(target=update_token_price, daemon=True)
    price_thread.start()

    # Run the Flask app
    print("Starting Flask app...")
    app.run(debug=True)
