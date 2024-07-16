import cloudscraper
from datetime import datetime, timedelta

# Constants
OWNER_ADDRESS = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"  
LIMIT = 100  
TIME_WINDOW_MINUTES = 5  

scraper = cloudscraper.create_scraper()

def fetch_recent_transactions(address, limit=LIMIT):
    url = f"https://api.solscan.io/account/transactions?address={address}&limit={limit}"
    response = scraper.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Error decoding JSON response:")
            print(response.text)
            return None
    else:
        print(f"Error fetching transactions: {response.status_code}")
        print(response.text)
        return None

def fetch_transaction_details(signature):
    url = f"https://api.solscan.io/transaction?tx={signature}"
    response = scraper.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Error decoding JSON response:")
            print(response.text)
            return None
    else:
        print(f"Error fetching transaction details: {response.status_code}")
        print(response.text)
        return None

def identify_wallets_involved(transactions):
    wallets = set()
    if transactions and 'data' in transactions:
        for tx in transactions['data']:
            for instruction in tx.get('instructions', []):
                wallets.add(tx['signer'])
    return list(wallets)

def check_wallet_transactions(wallet_address, contract_address):
    dev_wallets = []
    wallet_transactions = fetch_recent_transactions(wallet_address)
    contract_transactions = fetch_recent_transactions(contract_address)
    
    if wallet_transactions and 'data' in wallet_transactions:
        for wallet_tx in wallet_transactions['data']:
            wallet_tx_details = fetch_transaction_details(wallet_tx['txHash'])
            if wallet_tx_details and 'data' in wallet_tx_details:
                wallet_time = datetime.fromtimestamp(wallet_tx_details['data']['blockTime'])
                for instruction in wallet_tx_details['data']['instructions']:
                    if instruction.get('parsed') and instruction['parsed']['info'].get('lamports') == 2000000:
                        recipient_wallet = instruction['parsed']['info']['destination']
                        recipient_wallet_transactions = fetch_recent_transactions(recipient_wallet)
                        if recipient_wallet_transactions and 'data' in recipient_wallet_transactions:
                            for recipient_tx in recipient_wallet_transactions['data']:
                                recipient_tx_details = fetch_transaction_details(recipient_tx['txHash'])
                                if recipient_tx_details and 'data' in recipient_tx_details and recipient_tx_details['data']['owner'] == OWNER_ADDRESS:
                                    dev_wallets.append(wallet_address)
                                    for tx in contract_transactions['data']:
                                        tx_details = fetch_transaction_details(tx['txHash'])
                                        if tx_details and 'data' in tx_details:
                                            tx_time = datetime.fromtimestamp(tx_details['data']['blockTime'])
                                            if tx_time < wallet_time and (wallet_time - tx_time) <= timedelta(minutes=TIME_WINDOW_MINUTES):
                                                return dev_wallets, tx
    return dev_wallets, None

def main():
    # Get coin address from user input
    coin_address = input("Please enter the coin address: ")


    all_transactions = fetch_recent_transactions(coin_address, limit=1000) 
    if not all_transactions:
        print("Failed to fetch transactions. Exiting.")
        return

 
    wallets = identify_wallets_involved(all_transactions)

    # Step 3: Check wallet transactions for transfers to the owner address and flag dev wallets
    dev_wallets = []
    for wallet in wallets:
        dev_wallet, suspicious_tx = check_wallet_transactions(wallet, coin_address)
        if dev_wallet:
            dev_wallets.append(dev_wallet)
            print(f"Dev Wallet: {dev_wallet}")
            print(f"Suspicious Transaction: {suspicious_tx}")

if __name__ == "__main__":
    main()
