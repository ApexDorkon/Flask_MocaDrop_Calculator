from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Constants
TOKEN_NAME = "kip"  # Hardcoded token name
TOTAL_TOKEN_OFFERED = 50000000  # Hardcoded total tokens offered
MOCA_API_URL = "https://api.staking.mocaverse.xyz/api/mocadrop/projects/kip-protocol"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


# Function to fetch the pool data from Mocaverse API
def get_pool_data():
    try:
        # Make a GET request to the Mocaverse API
        response = requests.get(MOCA_API_URL)
        response.raise_for_status()  # Raise error for HTTP issues
        data = response.json()  # Parse JSON response
        
        # Extract the stakingPowerBurnt value
        staking_power_burnt = float(data.get("stakingPowerBurnt", 0))
        return staking_power_burnt
    except Exception as e:
        print(f"Error fetching Mocaverse data: {e}")
        return None


# Function to fetch token price from CoinGecko API
def get_token_price():
    try:
        params = {"ids": TOKEN_NAME, "vs_currencies": "usd"}
        response = requests.get(COINGECKO_URL, params=params)
        response.raise_for_status()  # Raise error for HTTP issues
        data = response.json()
        return data.get(TOKEN_NAME, {}).get("usd")
    except Exception as e:
        print(f"Error fetching token price: {e}")
        return None


@app.route("/")
def index():
    return render_template("index.html", token_name=TOKEN_NAME, total_token_offered=TOTAL_TOKEN_OFFERED)


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        # Get the user's input from the form
        user_burn = float(request.form["user_burn"])

        # Fetch data from Mocaverse and CoinGecko APIs
        total_burnt = get_pool_data()
        token_price = get_token_price()

        # Handle errors in fetching data
        if not total_burnt:
            print("Failed to fetch total staking power.")
            return jsonify({"error": "Failed to fetch total staking power from Mocaverse."}), 500
        if not token_price:
            print("Failed to fetch token price.")
            return jsonify({"error": "Failed to fetch token price from CoinGecko."}), 500

        # Perform calculations
        tokens_received = (TOTAL_TOKEN_OFFERED / total_burnt) * user_burn
        airdrop_value = tokens_received * token_price

        # Return the results as JSON, including Total Burnt
        return jsonify({
            "token_name": TOKEN_NAME,
            "token_price": token_price,
            "total_burnt": total_burnt,  # Add this line
            "tokens_received": tokens_received,
            "airdrop_value": airdrop_value,
        })
    except Exception as e:
        print(f"Error during calculation: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
