import plaid 
import json

#cls Note: accessToken was created 27 January 2021 (see Plaid Quickstart to
# generate new token) and should be valid indefinitely

# Refer to Plaid API Quickstart Tutorialfor help with generating a new token
# or linking a new account
CREDENTIALS_FILE_PATH = "./credentials/plaid-credentials.json"

API_VERSION = '2019-05-29'


def getCreds():
    with open(CREDENTIALS_FILE_PATH) as file:
        return json.load(file)
    


def buildClient():
    creds = getCreds()
    client = plaid.Client(client_id=creds["PLAID_CLIENT_ID"],
                          secret=creds["PLAID_SECRET"],
                          environment=creds["PLAID_ENV"],
                          suppress_warnings=True,
                          api_version=API_VERSION)

    return client if client is not None else None


def getMainAccessToken():
    creds = getCreds()

    # Main access token information should be first in accessTokens array
    mainAccessTokenInfo = creds["accessTokens"][0]

    # Retrieve main item token
    mainAccessToken = mainAccessTokenInfo["itemAccessToken"]

    return mainAccessToken if mainAccessToken is not None else None


# Global constants that rely upon other functions
CREDENTIALS = getCreds()

CLIENT = buildClient()

MAIN_ACCESS_TOKEN = getMainAccessToken()

def getAccountAvailableBalance():
    availBal = None
    if (CLIENT is not None and MAIN_ACCESS_TOKEN is not None):
        resp = CLIENT.Accounts.balance.get(MAIN_ACCESS_TOKEN)

        if (resp is not None):
            mainAccountBalances = resp["accounts"][0]["balances"]
            availBal = mainAccountBalances["available"]

    return availBal


def testSanity():

    print("\nTesting buildClient()...")
    resp = "SUCCESS" if buildClient() is not None else "FAILED"
    print(resp)

    print("\nTesting getCreds()....")
    resp = "SUCCESS" if getCreds() is not None else "FAILED"
    print(resp)

    print("\nTesting getMainAccessToken()...")
    resp = "SUCCESS" if getMainAccessToken() is not None else "FAILED"
    print(resp)

    print("\nTesting getAccountAvailableBalance()...")
    resp = "SUCCESS" if getAccountAvailableBalance() is not None else "FAILED"
    print(resp)



# Main function
if __name__ == "__main__":
    testSanity()
    pass
