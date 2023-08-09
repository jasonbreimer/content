import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


SUCCESS_COLOR = "color:rgb(29,184,70)"  # Green
FAILURE_COLOR = "color:rgb(209,60,60)"  # Red
PROGRESS_COLOR = "color:rgb(0,116,223)"  # Light Blue
SKIPPED_COLOR = "color:rgb(64,65,66)" # Black

# Getting incident context:
incident_id = demisto.incidents()[0].get('id', {})
context = demisto.executeCommand("getContext", {'id': incident_id})


# Variable initialization:
html = ""
brand_name = ""
instance_name = ""
is_success = ""
error_code = ""
error_message = ""
action = ""
runstatus = ""


# Getting context fields:
brand_name = str(context[0]['Contents'].get('context', {}).get('IAM', {}).get('Vendor', {}).get('brand', ""))
instance_name = str(context[0]['Contents'].get('context', {}).get('IAM', {}).get('Vendor', {}).get('instanceName', ""))
is_success = context[0]['Contents'].get('context', {}).get('IAM', {}).get('Vendor', {}).get('success', "")
error_code = str(context[0]['Contents'].get('context', {}).get('IAM', {}).get('Vendor', {}).get('errorCode', ""))
error_message = str(context[0]['Contents'].get('context', {}).get('IAM', {}).get('Vendor', {}).get('errorMessage', ""))
action = str(context[0]['Contents'].get('context', {}).get('IAM', {}).get('Vendor', {}).get('action', ""))

# Getting incident fields:
incident = demisto.incidents()
runstatus = str(incident[0].get('runStatus', {}))  # Whether there is an error
status = str(incident[0].get('status', {}))  # Whether incident is open or closed

if action:
    action = action[0].upper() + action[1:]  # First letter will be upper case

if is_success is True:
    html = "<div style='text-align:center; font-size:32px; padding: 6px; " + SUCCESS_COLOR + ";'>" + action + "d  Successfully" + "</div> <div style='text-align:center;'> <p style='font-size:12px; padding: 7px;'> in </p><div style='font-size:32px; padding: 16px;'>" + brand_name + "</div><div style='font-size:17px;'> Instance: " + instance_name + "</div></div>"

elif is_success is False:
    html = "<div style='text-align:center; font-size:32px; padding: 6px; " + FAILURE_COLOR + ";'>" + action + " Failed" + "</div> <div style='text-align:center;'> <p style='font-size:12px; padding: 7px;'> in </p><div style='font-size:32px; padding: 16px;'>" + brand_name + "</div><div style='font-size:17px;'> Instance: " + instance_name + "</div></div>"

elif is_success == "":  # Did not sync
    if runstatus != "error" and runstatus != "idle":  # Did not sync because playbook is still running:
        html = "<div style='text-align:center; font-size:32px; padding: 6px; " + PROGRESS_COLOR + ";'> Sync In Progress </div>"
    elif runstatus == "error":  # Did not sync because of error before the sync, incident still running:
        html = "<div style='text-align:center; font-size:32px; padding: 6px; " + FAILURE_COLOR + ";'> Error Before Sync </div> <div style='font-size:17px; text-align:center; padding: 12px;'> See 'Event Work Plan' section for details </div>"
    else:
        html = "<div style='text-align:center; font-size:32px; padding: 6px; " + SKIPPED_COLOR + ";'> Sync Skipped </div> <div style='font-size:17px; text-align:center; padding: 12px;'> No further action is needed </div>"

# Return the data to the layout:
demisto.results({
'ContentsFormat': EntryFormat.HTML,
'Type': EntryType.NOTE,
'Contents': html
})
