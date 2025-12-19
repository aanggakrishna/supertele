import re
from models import SessionLocal, Token, TokenMention
from datetime import datetime

# Regex for CA (Solana: 32-44 alphanumeric, EVM: 0x...)
SOLANA_CA_REGEX = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
EVM_CA_REGEX = r'0x[a-fA-F0-9]{40}'

def extract_ca(text):
    sol_match = re.search(SOLANA_CA_REGEX, text)
    if sol_match:
        return sol_match.group(0), "solana"
    
    evm_match = re.search(EVM_CA_REGEX, text)
    if evm_match:
        return evm_match.group(0), "evm"
    
    return None, None

def parse_rick_bot_response(text):
    """
    Parses emojis and metrics from Rick Bot's response.
    Example input: 💊 Chinese Communist Dr.. [3.5K/7%] $FENTANYL ... 💎 FDV: $3.5K ...
    """
    # This is a complex parser that needs to be robust against message changes.
    data = {}
    
    # Extract FDV
    fdv_match = re.search(r'FDV:\s*\$([\d\.MK]+)', text)
    if fdv_match:
        val = fdv_match.group(1)
        if 'K' in val: data['fdv'] = float(val.replace('K', '')) * 1000
        elif 'M' in val: data['fdv'] = float(val.replace('M', '')) * 1000000
        else: data['fdv'] = float(val)

    # Extract Liquidity
    liq_match = re.search(r'Liq:\s*\$([\d\.MK]+)', text)
    if liq_match:
        val = liq_match.group(1)
        if 'K' in val: data['liquidity'] = float(val.replace('K', '')) * 1000
        elif 'M' in val: data['liquidity'] = float(val.replace('M', '')) * 1000000
        else: data['liquidity'] = float(val)

    # Extract Symbol/Name
    symbol_match = re.search(r'\s\$([A-Z0-9]+)', text)
    if symbol_match:
        data['symbol'] = symbol_match.group(1)

    # Extract Top Holders Wallet Links (dummy example)
    # Rick bot usually provides a link or a summary of TH. 
    # For now, we extract the CA at the bottom of the response if provided.
    ca_match = re.search(SOLANA_CA_REGEX, text)
    if ca_match:
        data['contract_address'] = ca_match.group(0)

    return data
