import argparse
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.common.options import ArgOptions

def start_webdriver(args):
  options = ArgOptions()
  options.set_capability("perfecto:securityToken",args.token)
  options.set_capability("perfecto:deviceSessionId", args.session)
  driver = None
  try:
    driver = webdriver.Remote("https://" + args.cloud + ".perfectomobile.com/nexperience/perfectomobile/wd/hub", options=options)
  except Exception as e:
    if "Tenant '" + args.cloud + "-perfectomobile-com' wasn't found" in str(e):
      print("Invalid cloud name " + args.cloud + ".perfectomobile.com")
    elif "Authorization Required" in str(e):
      print("Invalid Security token for cloud " + args.cloud + ".perfectomobile.com")
    elif "Master session " + args.session + " not found" in str(e):
      print("Invalid/Inactive session id. Check if session is still active and copy current session id")
    elif "user of slave session" in str(e) and "is different than of master session" in str(e):
      print("Token/Session mismatch. Session does not belong to user of given token.")
    elif "cloud of slave session" in str(e) and "is different than of master session" in str(e):
      print("Cloud/Session mismatch. Session does not belong to specified cloud.")
    else:
      print(str(e))
    exit(1)
  return driver

def stop_webdriver(driver):
  try:
    driver.quit()
  except Exception as e:
    print(str(e))

def init():
  policy_prompt = ""
  parser = argparse.ArgumentParser()
  parser.add_argument("--cloud", default="", required=True,  help="Perfecto cloud name (will use https://<name>.perfectomobile.com)")
  parser.add_argument("--token", default=None, required=True, help="Perfecto Security Token")
  parser.add_argument("--session", default=None, required=True, help="Desktop Web session ID")
  args = parser.parse_args()
  driver = start_webdriver(args)
  stop_webdriver(driver)
  while True:
    user_prompt = input("\nAI Prompt:\n").strip()
    if not user_prompt:
      continue
    if user_prompt.startswith(":quit"):
      return
    if user_prompt.startswith(":help") or user_prompt == ":":
      print(":help                            - This help message")
      print(":quit                            - End chat")
      print(":validate prompt                 - AI Validation command")
      print("prompt                           - AI User Action command")
      continue
    print("\nThinking...")
    driver = start_webdriver(args)
    executionId = driver.capabilities.get("executionId")
    reportUrl = driver.capabilities.get("testGridReportUrl").replace("[", "%5B").replace("]", "%5D")
    exec_script(driver, "mobile:test:start", {"name": "web assistant"}, True)
    if user_prompt.startswith(":validate "):
      result = exec_script(driver, "perfecto:ai:validation", {"validation": user_prompt.replace(":validate ", "")})
    else:
      result = exec_script(driver, "perfecto:ai:user-action", {"action": user_prompt + policy_prompt})
    exec_script(driver, "mobile:test:end", { "success": result }, True)
    try:
      driver.quit()
      print_report_commands(args, executionId)
      print("View Results - " + reportUrl)
    except Exception as e:
      print("Connection to driver interrupted... Attempting to reconnect...")
      driver = start_webdriver(args)
      stop_webdriver(driver)

def exec_script(driver, script, params, ignore=False):
  try:
    return driver.execute_script(script, params)
  except Exception as e:
    if not ignore:
      print("Error executing command: " + script) #+ " Error=" + str(e))
    return False

def print_report_commands(args, executionId):
  reportingBaseUrl = "https://" + args.cloud + ".app.perfectomobile.com/export/api/v3/test-executions"
  headers = {"Perfecto-Authorization": args.token}
  reportDetailsUrl = reportingBaseUrl + "?externalId[0]=" + executionId
  resources = []
  count = 0
  while len(resources) == 0:
    if count > 60:
      print("Assistant results not available within 60s. View report to see details.")
      return
    count+=1
    sleep(1)
    resources = requests.get(reportDetailsUrl, headers=headers).json()["resources"]
  reportId = resources[0]["id"]
  reportCommandsUrl = reportingBaseUrl + "/" + reportId + "/commands"
  entries = requests.get(reportCommandsUrl, headers=headers).json()["resources"]
  print("\nAssistant:")
  for entry in entries:
    if entry["name"] != "Test step":
      print(entry["name"])
    for command in entry["commands"]:
      print("  " + command["name"] + " - " + command["status"])
      if "message" in command and command["message"]:
        print("    " + command["message"])
      if command["name"] == "AI Validation":
        print("    Expected: " + command["expectedData"][0]["value"])
        print("    Actual:   " + command["resultData"][0]["value"])
      elif command["name"] == "type":
        for param in command["parameters"]:
          if param["name"] == "text":
            print("    Text: " + param["value"])
    print("")

# -- main --
init()
