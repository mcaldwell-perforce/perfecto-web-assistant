import argparse
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.common.options import ArgOptions

def start_webdriver(args):
  options = ArgOptions()
  options.set_capability("perfecto:securityToken",args.token)
  options.set_capability("perfecto:deviceSessionId", args.session)
  driver = webdriver.Remote("https://" + args.cloud + ".perfectomobile.com/nexperience/perfectomobile/wd/hub", options=options)
  if not driver.capabilities:
    exit(1)
  return driver

def init():
  policy_prompt = " always take a screenshot on completion."
  parser = argparse.ArgumentParser()
  parser.add_argument("--cloud", default="", required=True,  help="Perfecto cloud name (will use https://<name>.perfectomobile.com)")
  parser.add_argument("--token", default=None, required=True, help="Perfecto Security Token")
  parser.add_argument("--session", default=None, required=True, help="Desktop Web session ID")
  args = parser.parse_args()
  driver = None
  while True:
    if not driver:
      driver = start_webdriver(args)
    user_prompt = input("\nAI Prompt:\n").strip()
    if user_prompt.startswith(":quit"):
      if driver:
        driver.quit()
      return
    if user_prompt.startswith(":help") or user_prompt == ":":
      print(":help                            - This help message")
      print(":quit                            - End chat")
      print(":validate prompt                 - AI Validation command")
      print("prompt                           - AI User Action command")
      continue
    try:
      executionId = driver.capabilities.get("executionId")
      reportUrl = driver.capabilities.get("testGridReportUrl").replace("[", "%5B").replace("]", "%5D")
      exec_script(driver, "mobile:test:start", {"name": "web assistant"})
      if user_prompt.startswith(":validate "):
        exec_script(driver, "perfecto:ai:validation", {"validation": user_prompt.replace(":validate ", "")})
      else:
        exec_script(driver, "perfecto:ai:user-action", {"action": user_prompt + policy_prompt})
      exec_script(driver, "mobile:test:end", {})
      driver.quit()
      print_report_commands(args, executionId)
      print("View Results - " + reportUrl)
    except Exception as e:
      print(str(e))
    driver = None

def exec_script(driver, script, params):
  try:
    driver.execute_script(script, params)
  except Exception as e:
    print("System - Script exception. Error=" + str(e))

def print_report_commands(args, executionId):
  try:
    reportingBaseUrl = "https://" + args.cloud + ".app.perfectomobile.com/export/api/v3/test-executions"
    headers = {"Perfecto-Authorization": args.token}
    reportDetailsUrl = reportingBaseUrl + "?externalId[0]=" + executionId
    resources = []
    count = 0
    while len(resources) == 0:
      if count > 60:
        raise TimeoutError("Reporting did not respond within 60s")
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
  except Exception as e:
    print("System - Script exception. Error=" + str(e))

# -- main --
init()
