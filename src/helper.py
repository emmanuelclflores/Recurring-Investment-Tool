import json

INVESTMENT_HISTORY_PATH = "investments/investment-history.json"

with open(INVESTMENT_HISTORY_PATH, "r") as file:
    data = json.load(file)
    orderCount = 0
    weekCount = 0
    for weeklyOrdersObj in data:
        weekCount += 1
        for order in weeklyOrdersObj["orders"]:
            orderCount += 1
    print(f"orderCount:{orderCount}")
    print(f"weekCount:{weekCount}")