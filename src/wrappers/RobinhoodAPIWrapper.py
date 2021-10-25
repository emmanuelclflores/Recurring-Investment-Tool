import robin_stocks as rs
import json
import requests
import copy

CREDENTIALS_FILE_PATH = "./credentials/rh-credentials.json"

MAIN_BANK_ACCOUNT_URL = "https://api.robinhood.com/ach/relationships/ad0d5b2c-ef75-47e9-9771-7ee7dacffcee/"


def login():
    with open(CREDENTIALS_FILE_PATH) as file:
        creds = json.load(file)

    

    rs.login(username=creds["username"],
             password=creds["password"],
             expiresIn=86400,
             by_sms=True)


def logout():

    rs.logout()

def getSymbolFromInstrumentURL(instrumentURL):
    resp = requests.get(instrumentURL)
    symbol = (resp.json())["symbol"]

    return symbol


def getQuoteOfSymbol(symbol):
    quote = None
    
    if (isCrypto(symbol)):
        quote =  rs.crypto.get_crypto_quote(symbol)
        quote = quote['mark_price']
    elif (isStock(symbol)):
        quote =  rs.stocks.get_stock_quote_by_symbol(symbol)
        # Determine most recent stock quote (extended hours or last trade in 
        # day)
        if (quote['last_extended_hours_trade_price'] is not None):
            quote = quote['last_extended_hours_trade_price']
        elif (quote['last_trade_price'] is not None):
            quote = quote['last_trade_price']

    return float(quote)

def isCrypto(symbol):
    return (rs.crypto.get_crypto_quote(symbol) is not None)

def isStock(symbol):
    return (rs.stocks.get_stock_quote_by_symbol(symbol) is not None)

def getAccountInfo():
    generalAccountInfo = rs.account.load_phoenix_account()

    return generalAccountInfo


def getAccountEquityValue():
    accountValue = 0
    openPositionSummary = getAllOpenPositions()

    # Get all open positions
    return round(openPositionSummary['totalEquityValue'], 2)


def getAllOpenPositions():
    openPositionsSummary = {"totalEquityValue": 0, "positions": [] }

    openPositions = openPositionsSummary["positions"]
    openPosition = {"symbol": None, "quantity": 0,
                    "price": 0, "equity": 0}

    # Append all open stock positions
    stockPositions = rs.account.get_open_stock_positions()
    for stockPosition in stockPositions:

        # Create deep copy of openPosition template
        postionToBeAdded = copy.deepcopy(openPosition)

        # Get all stock position details
        postionToBeAdded["symbol"] = getSymbolFromInstrumentURL(
            stockPosition["instrument"])
        postionToBeAdded["quantity"] = float(stockPosition["quantity"])
        postionToBeAdded["price"] = getQuoteOfSymbol(
            postionToBeAdded["symbol"])
        if postionToBeAdded["price"] is not None:
            # Update equity value in positions array
            postionToBeAdded["equity"] = postionToBeAdded["price"] * postionToBeAdded["quantity"]

            # Update total equity value
            openPositionsSummary["totalEquityValue"] += postionToBeAdded["equity"]
        else:
            postionToBeAdded["equity"] = None

        openPositions.append(postionToBeAdded)

    # Append all open crypto positions
    cryptoPositions = rs.crypto.get_crypto_positions()

    for cryptoPosition in cryptoPositions:
        # Create deep copy of openPosition template
        postionToBeAdded = copy.deepcopy(openPosition)

        # Get all crypto position details
        postionToBeAdded["symbol"] = cryptoPosition["currency"]["code"]
        postionToBeAdded["quantity"] = float(cryptoPosition["quantity"])
        postionToBeAdded["price"] = getQuoteOfSymbol(
            postionToBeAdded["symbol"])
        if postionToBeAdded["price"] is not None:
            # Update equity value in positions array
            postionToBeAdded["equity"] = postionToBeAdded["price"] * postionToBeAdded["quantity"]

            # Update total equity value
            openPositionsSummary["totalEquityValue"] += postionToBeAdded["equity"]
        else:
            postionToBeAdded["equity"] = None
        
        openPositions.append(postionToBeAdded)
    
    return openPositionsSummary


def getAccountBuyingPower():
    generalAccountInfo = rs.account.load_phoenix_account()

    accountBuyingPower = generalAccountInfo['account_buying_power']['amount']

    if accountBuyingPower is not None:
        cash = round(float(accountBuyingPower), 2)
    return cash

def depositFundsToAccount(amount):

    
    # Ensure amount goes to 2 decimal places
    amount = round(amount, 2)
    print("WARNING: DEPOSIT AMOUNT NOT LIMITED!")

    # print("DEPOSIT CURRENTLY LIMITED TO $0.50")
    # amount = 0.50

    resp = rs.deposit_funds_to_robinhood_account(
        ach_relationship=MAIN_BANK_ACCOUNT_URL, amount=amount)
    print(resp)

    if resp is not None:
        print(f"Desposit of {amount} from main bank account SUCCESSFUL!")
    else:
        print(f"Desposit of {amount} from main bank account UNSUCCESSFUL!")

def buyFractionalSharesByPrice(symbol, amountInDollars):
    resp = None
    if (isCrypto(symbol)):
        resp = rs.orders.order_buy_crypto_by_price(symbol=symbol, amountInDollars=amountInDollars)
    elif(isStock(symbol)):
        resp = rs.orders.order_buy_fractional_by_price(symbol=symbol, amountInDollars=amountInDollars)

    print(resp)
    if resp is not None:
        print(f"SUCESSFULLY BOUGHT ${amountInDollars} of {symbol}!")
        resp = json.dumps(resp, indent = 3)
    else:
        print(f"FAILED TO BUY ${amountInDollars} of {symbol}!")

    

    return resp

def sellFractionalSharesByQuantity(symbol, quantity):
    resp = None
    if (isCrypto(symbol)):
        resp = rs.orders.order_sell_crypto_by_quantity(symbol=symbol, quantity=quantity)
    elif(isStock(symbol)):
        resp = rs.orders.order_sell_fractional_by_quantity(symbol=symbol, quantity=quantity)

    print(resp)
    if resp is not None:
        print(f"SUCESSFULLY SOLD ${amountInDollars} SHARES OF {symbol}!")
        resp = json.dumps(resp, indent = 3)
    else:
        print(f"FAILED TO BUY ${amountInDollars} OF {symbol}!")

    return resp

def sellAllOpenPositions():
    openPositionsSummary = getAllOpenPositions()
    openPositions = openPositionsSummary["positions"]

    for openPosition in openPositions:
        quantityToBeSold = openPosition['quantity']
        symbol = openPosition['symbol']
        print(f"Selling {quantityToBeSold} shares or {symbol}")
        sellFractionalSharesByQuantity(symbol=symbol, quantity=quantityToBeSold)

    print("All open positions liquidated!")


def testSanity():
    print("\nTesting basic login and logout...")
    login()
    print("Log in successful")
    logout()


    # Login is necessary for the following functions
    login()
    print("\nTesting getAccountBuyingPower()... ")
    output = getAccountBuyingPower()
    resp = "SUCCESS" if isinstance(output, float) else "FAILED"
    print(resp)


    print("\nTesting getAllOpenPositions()...")
    output = getAllOpenPositions()
    resp = "SUCCESS" if isinstance(output, dict) else "FAILED"
    prettifiedOutput = json.dumps(output, indent=3)
    print(prettifiedOutput)
    print(resp)

    print("\nTesting getAccountEquityValue()...")
    output = getAccountEquityValue()
    resp = "SUCCESS" if isinstance(output, float) else "FAILED"
    print(resp)


    # Must logout after method tests
    logout()


# Main function
if __name__ == "__main__":
    login()
    # resp = getAllOpenPositions()
    # resp = json.dumps(resp, indent=3)
    # print(resp)

    resp = getAccountInfo()
    resp = json.dumps(resp, indent=3)
    print(resp)
    logout()
    pass
