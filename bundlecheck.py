import requests
from datetime import datetime, timedelta

# Constants
PUMP_PROGRAM_ADDRESS = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # not sure if this is correct 
TRANSFER_AMOUNT_SOL = 0.02  
TRANSFER_AMOUNT_LAMPORTS = int(TRANSFER_AMOUNT_SOL * 1_000_000_000)  
LIMIT = 100  
TIME_WINDOW_MINUTES = 5  


API_URL = "https://public-api.solanabeach.io/v1"

def fetch_recent_transactions(address, limit=LIMIT):
    url = f"{API_URL}/accounts/{address}/transactions?limit={limit}"
    print(f"Fetching transactions for address: {address}")
    response = requests.get(url)
    if response.status_code == 200:
        try:
            transactions = response.json()
            return transactions
        except ValueError:
            print("Error decoding JSON response:")
            print(response.text)
            return None
    else:
        print(f"Error fetching transactions: {response.status_code}")
        print(response.text)
        return None

def fetch_transaction_details(signature):
    url = f"{API_URL}/tx/{signature}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Error decoding JSON response:")
            print(response.text)
            return None
    else:
        print(f"Error fetching transaction details: {response.status_code}")
        return None

def get_wallets_that_sent_to_pump_program(transactions):
    dev_wallets = []
    for tx in transactions:
        if 'amount' in tx and tx['amount'] == TRANSFER_AMOUNT_LAMPORTS:
            if tx.get('to', '') == PUMP_PROGRAM_ADDRESS:
                dev_wallet = tx['from']
                dev_wallet_signature = tx['signature']
                dev_wallets.append((dev_wallet, dev_wallet_signature))
    return dev_wallets

def find_buyers_before_dev_wallet(dev_wallets, coin_address):
    buyers = []
    for dev_wallet, dev_tx_signature in dev_wallets:
        
        dev_wallet_tx_details = fetch_transaction_details(dev_tx_signature)
        if dev_wallet_tx_details and 'data' in dev_wallet_tx_details:
            dev_wallet_time = datetime.fromtimestamp(dev_wallet_tx_details['data']['blockTime'])
            print(f"Dev Wallet: {dev_wallet}, Transaction Time: {dev_wallet_time}")

            
            coin_transactions = fetch_recent_transactions(coin_address, limit=1000)  
            if not coin_transactions:
                print("Failed to fetch transactions for coin address.")
                return

            for tx in coin_transactions:
                
                coin_tx_details = fetch_transaction_details(tx['signature'])
                if coin_tx_details and 'data' in coin_tx_details:
                    coin_tx_time = datetime.fromtimestamp(coin_tx_details['data']['blockTime'])
                    if coin_tx_time < dev_wallet_time and (dev_wallet_time - coin_tx_time) <= timedelta(minutes=TIME_WINDOW_MINUTES):
                        buyers.append((tx['signature'], tx['from'], coin_tx_time))

    return buyers

def main():
    
    coin_address = input("Please enter the coin address: ")

    
    coin_transactions = fetch_recent_transactions(coin_address, limit=1000)  
    if not coin_transactions:
        print("Failed to fetch transactions from the coin address. Exiting.")
        return

    
    wallets = [tx['from'] for tx in coin_transactions]

    if not wallets:
        print("No wallets found holding the coin.")
        return

    
    dev_wallets = []
    for wallet in wallets:
        wallet_transactions = fetch_recent_transactions(wallet, limit=100)  
        if wallet_transactions:
            dev_wallets.extend(get_wallets_that_sent_to_pump_program(wallet_transactions))

    if not dev_wallets:
        print("No dev wallets found.")
        return

    
    buyers = find_buyers_before_dev_wallet(dev_wallets, coin_address)

    
    if buyers:
        print(f"Found {len(buyers)} buyers who purchased the coin before a dev wallet:")
        for signature, buyer, tx_time in buyers:
            print(f"Buyer Transaction Signature: {signature}")
            print(f"Buyer Address: {buyer}")
            print(f"Transaction Time: {tx_time}")
            print(f"Transaction URL: https://solanabeach.io/tx/{signature}")
    else:
        print("No buyers found who purchased the coin before a dev wallet.")

if __name__ == "__main__":
    main()
