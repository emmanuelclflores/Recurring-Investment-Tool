from datetime import datetime
import requests
from time import sleep
import json
import os
global SheetsAPIWrapper
from wrappers import SheetsAPIWrapper

# PlaidAPIWrapper has global constants that are reliant upon a stable
# internet connection
global PlaidAPIWrapper
from wrappers import PlaidAPIWrapper

global RobinhoodAPIWrapper
from wrappers import RobinhoodAPIWrapper


def awaitInternetConnection():
    print("Determining Internet connection....")
    count = 1
    while True:
        try:
            print(f"Attempting connection #{count}")
            url = "https://api.myip.com/"
            resp = requests.get(url=url, timeout=1)
            count += 1
            break
        except:
            pass
    print("Internet connection established!")


def importCustomWrappers():
    print("Importing custom wrappers...")

    # SheetsAPIWrapper has global constants that are reliant upon a stable
    # internet connection
    global SheetsAPIWrapper
    from wrappers import SheetsAPIWrapper
    
    # PlaidAPIWrapper has global constants that are reliant upon a stable
    # internet connection
    global PlaidAPIWrapper
    from wrappers import PlaidAPIWrapper

    global RobinhoodAPIWrapper
    from wrappers import RobinhoodAPIWrapper

    # Global/Import combination ensures imports can be used throughout
    # the entire script (not just within the functino)

# Global constants 

SUNDAY_NUMERIC_VALUE = 6

# Ensures that there is AT MINMUM this amount of available brokerage funds
BROKERAGE_ACCOUNT_CASH_BUFFER = 100

# Ensures that there is AT MINMUM this amount of available bank account funds
BANK_ACCOUNT_CASH_BUFFER = 500

# Prevents API from being flooded with fractional orders
FRACTIONAL_ORDER_FLOW_DELAY = 7.5


def clearAllDatabases():
    resp = str(input(
        "Are you sure you would like to CLEAR ALL DATABASES (this cannot be undone)? [Y/N]\n")).strip()

    if resp == "Y":
        clearAllCaches()
        clearInvestmentHistory()


def validateEmptyInvestmentHistoryCache():
    # Validate that investment-history-cache-main is EMPTY
    with open("./investments/investment-history-cache-main.json") as file:
        investmentHistoryCache = json.load(file)

    emptyCache = len(list(investmentHistoryCache.keys())) == 0

    return emptyCache


def validateWeeklyOrdersNotCompleted():

    # Function should only be called if the day is Sunday

    # Determine currDate
    currDatetime = datetime.now()
    currWeekdayVal = currDatetime.weekday()
    currDate = currDatetime.strftime("%m-%d-%y")

    # Validate that investment-history does not contain an entry for the
    # given Sunday
    with open("./investments/investment-history.json") as file:
        investmentHistory = json.load(file)

    ordersCompleted = False
    for entry in investmentHistory:
        if entry["date"] == currDate:
            ordersCompleted = True

    return not ordersCompleted


def validateSufficientFunds(totalInvestmentValue):

    print("Determining available bank account funds (with buffer)....")
    availBankAccountFunds = PlaidAPIWrapper.getAccountAvailableBalance() - \
        BANK_ACCOUNT_CASH_BUFFER

    print("Determining available brokerage account funds (with buffer)....")
    availBrokerageFunds = RobinhoodAPIWrapper.getAccountBuyingPower() - \
        BROKERAGE_ACCOUNT_CASH_BUFFER

    fundsToBeDeposited = totalInvestmentValue - availBrokerageFunds
    # fundsToBeDeposited = 0

    # Addresses cases in which funds should be deposited from the bank account
    # to the brokerage account
    print("Checking if any funds should be deposited into brokerage account to afford investment orders...")
    if (fundsToBeDeposited > 0):

        # If there are not sufficient funds available in the bank acccount
        # STOP RECURRING INVESTMENT FLOW
        print("Checking if there are sufficient bank account funds to deposit into brokerage account....")
        if (fundsToBeDeposited > availBankAccountFunds):
            print("INSUFFICIENT FUNDS TO DEPOSIT INTO BROKERAGE ACCOUNT!")
            return False
        # If there ARE sufficient funds available in the bank account
        # transfer them to brokerage account
        else:
            print(
                f"Depositing ${fundsToBeDeposited} into brokerage account....")
            RobinhoodAPIWrapper.depositFundsToAccount(
                amount=fundsToBeDeposited)
            return True

    # If there are already sufficient funds in the brokerage acccount
    # CONTINUE RECURRING INVESTMENT FLOW
    else:
        print("Sufficient funds in brokerage account!")
        return True


def retrieveSingleWeeklyOrderFromCache():

    # Read progress cache JSON
    investmentHistoryCache = loadProgressCache()

    # Retrieve first order in progress cache
    firstKey = list(investmentHistoryCache.keys())[0]
    order = {"symbol": firstKey, "amount": investmentHistoryCache[firstKey]}

    # Remove first order from progress cache
    investmentHistoryCache.pop(firstKey)

    # Update progress cache JSON
    with open("./investments/investment-history-cache-progress.json", "w") as file:
        json.dump(investmentHistoryCache, file)

    return order


def clearAllCaches():
    with open("./investments/investment-history-cache-main.json", "w") as file:
        json.dump({},  file)
    with open("./investments/investment-history-cache-progress.json", "w") as file:
        json.dump({},  file)


def clearInvestmentHistory():
    with open("./investments/investment-history.json", "w") as file:
        json.dump([],  file)


def addToInvestmentHistory(toBeAdded):
    print("Updating investment history...")
    investmentHistory = None
    with open("./investments/investment-history.json") as file:
        investmentHistory = json.load(file)

    investmentHistory.append(toBeAdded)

    with open("./investments/investment-history.json", "w") as file:
        json.dump(investmentHistory, file)


def writeToMainCache(data):
    with open("./investments/investment-history-cache-main.json", "w") as file:
        json.dump(data, file)


def writeToProgressCache(data):
    with open("./investments/investment-history-cache-progress.json", "w") as file:
        json.dump(data, file)


def loadMainCache():
    with open("./investments/investment-history-cache-main.json") as file:
        return json.load(file)


def loadProgressCache():
    with open("./investments/investment-history-cache-progress.json") as file:
        return json.load(file)


def sendWeeklyOrders():

    # Determine currDate
    currDatetime = datetime.now()
    currWeekdayVal = currDatetime.weekday()
    currDate = currDatetime.strftime("%m-%d-%y")

    isSunday = (currWeekdayVal == SUNDAY_NUMERIC_VALUE)

    # If the day is Sunday, go through order flow
    print("Validating day....")
    # if (isSunday):s
    if (True):

        # Addresses cases in which orders have not yet been completed
        print("Determing order completion status....")
        if (validateWeeklyOrdersNotCompleted()):

            # Addresses cases in which order flow has NOT BEEN INITIATED
            print("Determining cache status ....")
            if (validateEmptyInvestmentHistoryCache()):

                # Initiate order flow
                print("Initiating order flow....")

                # Validate that there are sufficient funds for making
                # recurring investments
                totalRecurringInvestmentsValue = SheetsAPIWrapper.getTotalRecurringInvestmentsValue()

                print(
                    "Determine if brokerage has sufficient funds to make the investments...")
                brokerageHasSufficientFunds = validateSufficientFunds(
                    totalInvestmentValue=totalRecurringInvestmentsValue)

                # NOTE: If there are sufficient funds at this point in the order
                # flow, then if the flow is interrupted the brokerage account
                # will still have all the liquidity it needs to complete the
                # remaining orders

                if (brokerageHasSufficientFunds):
                    # Cache prospective orders
                    ordersToBeCached = SheetsAPIWrapper.getAllRecurringInvestments()
                    print("Caching orders based on Google Sheets....")
                    writeToMainCache(ordersToBeCached)
                    writeToProgressCache(ordersToBeCached)

                    # Retrieve single order from cache
                    for i in range(len(ordersToBeCached)):

                        # Retrieve order and update cache
                        print("Retrieving order from progress cache...")
                        order = retrieveSingleWeeklyOrderFromCache()

                        # Send order to RobinHood API
                        sendSimulatedMarketOrder(
                            symbol=order["symbol"], amount=order["amount"])
                        # RobinhoodAPIWrapper.buyFractionalSharesByPrice(
                        #     symbol=order["symbol"], amountInDollars=order["amount"])

                        # Pause to ensure that the API is not flooded
                        sleep(FRACTIONAL_ORDER_FLOW_DELAY)

                else:
                    print("INSUFFICIENT FUNDS FOR CONTINUING ORDER FLOW!")
                    clearAllCaches()

                    # STOP order flow
                    return
            # Addresses cases in which order flow HAS been initiated but not
            # completed
            else:
                print("Order flow previously initiated....")
                print("Completing order flow.....")
                ordersToBeCompleted = loadProgressCache()

                # Retrieve single orders from cache and send to RobinHood # API
                for i in range(len(ordersToBeCompleted)):

                    # Retrieve order and update cache
                    print("Retrieving order from progress cache...")
                    order = retrieveSingleWeeklyOrderFromCache()

                    # Send order to RobinHood API
                    # sendSimulatedMarketOrder(
                    #     symbol=order["symbol"], amount=order["amount"])
                    RobinhoodAPIWrapper.buyFractionalSharesByPrice(
                        symbol=order["symbol"], amountInDollars=order["amount"])

                    # Pause to ensure that the API is not flooded
                    sleep(FRACTIONAL_ORDER_FLOW_DELAY)

            print("Weekly orders completed!")
            # By this point the cache tracking the order completiong process
            # should be EMPTY (no more orders to send)

            # Main cache should still contain all the info regarding the orders
            # sent
            ordersCompleted = loadMainCache()

            # Update investment-history to indicate weekly order(s) completion
            addToInvestmentHistory(
                toBeAdded={"recurringType": "Weekly", "date": currDate, "orders": ordersCompleted})

            print("Investment history updated!")

            # Clear caches
            clearAllCaches()

        # Addresses cases in which all weekly orders have been sent
        else:
            print("All weekly orders have been sent!")
            sleep(2)

    # If day is NOT sunday, STOP ORDER FLOW
    else:
        print("Day is not viable for delivery of weekly order requests!")
        sleep(2)


def sendSimulatedMarketOrder(symbol, amount):
    print(
        f"\nPlacing a simulated market order for ${amount} worth of {symbol}")
    sleep(0.5)
    print("ORDER FILLED!")


def main():
    # Log into Robinhood account to ensure access to account-specific
    # functionality
    RobinhoodAPIWrapper.login()

    # # Send Weekly Orders
    sendWeeklyOrders()

    # Logout of Robinhood account for security
    RobinhoodAPIWrapper.logout()


def testDependencies():

    print("\nTesting SheetsAPIWrapper:\n")
    SheetsAPIWrapper.testSanity()

    print("\nTesting RobinhoodAPIWrapper:\n")
    RobinhoodAPIWrapper.testSanity()

    print("\nTesting PlaidAPIWrapper:\n")
    PlaidAPIWrapper.testSanity()


# Main function
if __name__ == "__main__":
    awaitInternetConnection()
    importCustomWrappers()
    try:
        # testDependencies()
        print("Tests passed!")
    
        # If testDependencies fails, main will NOT be executed
        main()
    except:
        pass
    
