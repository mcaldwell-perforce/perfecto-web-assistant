# Perfecto AI Desktop Web Assistant

This python tool allows you to run AI commands with an open Perfecto Desktop Interactive Session

### To use:
Start by opening the desktop browser in Perfecto 

Ensure you select the checkbox "I will use this session to debug my automation script" 

If this is not present, it needs to be enabled in the cloud by support

After the browser is loaded, click the session sharing widget and copy the session id

This session id will be different everytime a device is opened in interactive mode.

If the assistant tool is quit but the interactive session hasnt been closed, you can use the same sessionId to reattach

### To install:
    pip install -r requirements.txt

### To run:
    python web_assistant.py --cloud cloudName --token perfectoToken --session perfectoSessionId
    ex: python web_assistant.py --cloud demo --token xxx-xxx-xxx --session 6aa23aef-acfa-4a9c-93df-1b0cb3c48070

### Commands
* :quit                   - quit the session and exit
* :validate prompt text   - Use the AI Validation command for the prompt
* prompt text             - Use AI User Action command for the prompt

examples:
* :validate is this a login screen    - AI Validate
* is this a login screen              - AI User Action

Each command will run and afterward print the AI thoughts and results in the console

It will also link to a viewable Perfecto report for the command itself

type :quit when you are finished with the assistant and then close the Interactive session In the browser