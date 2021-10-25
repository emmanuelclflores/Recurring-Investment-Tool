from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

"""
*Module description*
"""

# Declare instance variables and constants here
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1ZKgiY01HxvmRCREcWGUaAkocXzzuMYhEZk9SKjVGkQo'

CREDENTIALS_FILE_PATH = './credentials/google-credentials.json'
PICKLE_FILE_PATH = './credentials/token.pickle'

ASSET_FIELDS_ROW = 4

INDEX_TO_COLUMN_LETTER_BUFFER = 65


def buildAuthorizedService():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(PICKLE_FILE_PATH):
        with open(PICKLE_FILE_PATH, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(PICKLE_FILE_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    return service


def getFullSpreadsheet():
    authorizedService = buildAuthorizedService()
    spreadsheet = authorizedService.spreadsheets()
    spreadsheet = spreadsheet.get(
        spreadsheetId=SPREADSHEET_ID, includeGridData=True).execute()

    return spreadsheet


# Since only one spreadsheet is used for this application, the script has a
# global spreadsheet constant
SPREADSHEET = getFullSpreadsheet()


def getAllSheetNames():

    # Call the Sheets API
    result = SPREADSHEET["sheets"]

    sheetNames = []
    for i in range(len(result)):
        sheetName = result[i]["properties"]["title"]
        # print(sheetName)
        sheetNames.append(sheetName)

    return sheetNames


def getSheetAssetFields(sheetName):

    # Obtain sheet by name
    sheet = getSheetByName(sheetName=sheetName)

    # Obtain asset fields
    sheetAssetFields = getAllCellValuesInRow(
        sheetRow=ASSET_FIELDS_ROW, sheetName=sheetName)

    return sheetAssetFields


def indexToColumnLetter(index):
    return chr(index + INDEX_TO_COLUMN_LETTER_BUFFER)


def columnLetterToIndex(columnLetter):
    return ord(columnLetter) - INDEX_TO_COLUMN_LETTER_BUFFER


def getAllRecurringInvestments():

    fullSpreadsheet = SPREADSHEET

    # Retrieve all sheet names
    assetCategories = getAllSheetNames()
    assetCategories.remove("Main")

    # print(assetCategories)

    recurringInvestments = {}
    for assetCategory in assetCategories:

        sheet = getSheetByName(sheetName=assetCategory)

        # Identify fields for the asset category
        assetCategoryFields = getAllCellValuesInRow(
            sheetRow=ASSET_FIELDS_ROW, sheetName=assetCategory)
        # print(assetCategoryFields)

        # Determine column letter corresponding with the Symbols in the asset
        # category
        symbolsColumnIndex = assetCategoryFields.index("Symbol")
        symbolsColumnLetter = indexToColumnLetter(symbolsColumnIndex)
        # print(symbolsColumnLetter)

        # Determine column letter corresponding with the Weekly Investment
        # values in the asset category
        weeklyInvestmentColumnIndex = assetCategoryFields.index(
            "Weekly Investment")
        weeklyInvestmentColumnLetter = indexToColumnLetter(
            weeklyInvestmentColumnIndex)
        # print(weeklyInvestmentColumnLetter)

        # Determine rows that contain viable values

        # Identify ALL values in Symbols column
        symbolsColumnValues = getAllCellValuesInColumn(
            sheetColumn=symbolsColumnLetter, sheetName=assetCategory)
        # print(symbolsColumnValues)

        # Identify ALL values in Weekly Investment column
        weeklyInvestmentColumnValues = getAllCellValuesInColumn(
            sheetColumn=weeklyInvestmentColumnLetter, sheetName=assetCategory)
        # print(weeklyInvestmentColumnValues)

        # Iterate through all symbolsColumnValues to determine range of rows
        # that contain viable values
        viableRowRange = {"start": None, "end": None}
        for i in range(len(symbolsColumnValues)):
            # Determine start of viable row range
            if (symbolsColumnValues[i]) == "Symbol":
                viableRowRange["start"] = i + 1
            # Determine end of viable row range (first instance of None AFTER # "Symbol")
            # Executes only if START HAS BEEN ESTABLISHED AND END INDEX HAS  #
            # NOT YET BEEN ESTABLISHED
            elif viableRowRange["start"] is not None and viableRowRange["end"] is None and (symbolsColumnValues[i]) is None:
                viableRowRange["end"] = i

        # Match Symbol to Weekly Investment Amount
        startRange = viableRowRange["start"]
        endRange = viableRowRange["end"]
        viableSymbols = symbolsColumnValues[startRange:endRange]
        viableInvestmentAmounts = weeklyInvestmentColumnValues[startRange:endRange]

        # Convert matches to Key-Values paris in dictionary
        recurringInvestmentsForCategory = dict(
            zip(viableSymbols, viableInvestmentAmounts))

        # Merge with existing recurringInvestments dictionary
        recurringInvestments.update(recurringInvestmentsForCategory)

    return recurringInvestments


def getTotalRecurringInvestmentsValue():

    totalRecurringInvestmentsValue = None

    # Get main portfolio fields from Main sheet
    mainPortfolioFields = getAllCellValuesInRow(
        sheetRow=ASSET_FIELDS_ROW, sheetName='Main')

    # Get total value of weekly investments
    weeklyInvestmentColumnIndex = mainPortfolioFields.index(
        "Weekly Investment")
    weeklyInvestmentColumnLetter = indexToColumnLetter(
        weeklyInvestmentColumnIndex)

    weeklyInvestmentValues = getAllCellValuesInColumn(
        sheetColumn=weeklyInvestmentColumnLetter, sheetName='Main')

    # Reverse weeklyInvestmentValues and traverse it
    weeklyInvestmentValues.reverse()

    # Determine first non-None value in weeklyInvestmentValues
    # This first value will be the TOTAL VALUE OF ALL WEEKLY INVESTMENTS
    totalWeeklyInvestmentsValue = next(
        value for value in weeklyInvestmentValues if value is not None)

    if totalRecurringInvestmentsValue is None:
        totalRecurringInvestmentsValue = totalWeeklyInvestmentsValue
    else:
        totalRecurringInvestmentsValue += totalWeeklyInvestmentsValue

    return totalRecurringInvestmentsValue

    # Iterate backwards through weekly investment column until you arrive
    # at the TOTAL VALUE CELL


def getCellValue(sheetCoord, sheetName):

    sheet = getSheetByName(sheetName)

    if (sheet != None):

        # Sheet coord should be of the form 'A1'
        colVal = columnLetterToIndex(sheetCoord[0])
        rowVal = int(sheetCoord[1:]) - 1

        rawData = sheet["data"][0]["rowData"]

        cell = rawData[rowVal]["values"][colVal]
        cellValue = None

        if "effectiveValue" in cell:
            # Obtain first value in effectiveValue dictionary
            cellValue = list(cell["effectiveValue"].values())[0]

        # print(f"{sheetCoord} --> {rowVal}, {colVal} --> {cellValue}")
        return cellValue

    else:

        return None


def getAllCellValuesInColumn(sheetColumn, sheetName):
    sheet = getSheetByName(sheetName)

    totRows = len(sheet["data"][0]["rowData"])

    values = []
    for rowVal in range(totRows):

        # rowVal + 1 ensured that getCellValue receives the correct coordinates
        # (rows start at 1 rather than 0)
        cellCoord = f"{sheetColumn}{rowVal + 1}"

        cellValue = getCellValue(sheetCoord=cellCoord, sheetName=sheetName)
        values.append(cellValue)

    return values


def getAllCellValuesInRow(sheetRow, sheetName):
    sheet = getSheetByName(sheetName)

    totCols = len(sheet["data"][0]["rowData"][0]["values"])

    values = []
    for colVal in range(totCols):
        cellCoord = f"{indexToColumnLetter(colVal)}{sheetRow}"

        cellValue = getCellValue(sheetCoord=cellCoord, sheetName=sheetName)
        values.append(cellValue)

    return values


def getSheetByName(sheetName):

    for sheet in SPREADSHEET["sheets"]:
        if (sheet["properties"]["title"] == sheetName):
            return sheet
    print(f"No sheet found with name \"{sheetName}\"")
    return None


def testSanity():

    # TODO: Validation for tests! (Use basic portfolio sample)

    print("\nTesting buildAuthorizedService")
    service = buildAuthorizedService()
    resp = "SUCCESS" if service is not None else "FAILED"
    print(resp)

    print("\nTesting getFullSpreadsheet")
    output = getFullSpreadsheet()
    resp = "SUCCESS" if output is not None else "FAILED"
    print(resp)

    print("\nTest basic getCellValue")
    # TODO: Complete this test

    # TODO: Implement more tests for methods

    print("\nTest basic retrieve all recurring investments")
    output = getAllRecurringInvestments()
    resp = "SUCCESS" if isinstance(output, dict) else "FAILED"
    print(resp)
    prettifiedOutput = json.dumps(output, indent=2)
    print(prettifiedOutput)


# Main function
if __name__ == "__main__":
    pass