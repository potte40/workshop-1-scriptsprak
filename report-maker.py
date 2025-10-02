# Import the json library so that we can handle json
import json

# Import time so that we can handle time
from datetime import datetime

# Read json from products.json to the variable products
# open(filePath, "r" for read, encoding = character encoding)

data = json.load(open("network_devices.json","r",encoding = "utf-8"))


# Create a variable that holds our whole text report
report = ""

# Rapportens namn + företag
company = data["company"]
report += ("="*80 + "\n" + f"NÄTVERKSRAPPORT - {company}".center(80) 
+ "\n" + "="*80 + "\n")

# Rapportdatum + datauppdatering
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #Formaterat till sträng
last_updated = data["last_updated"]
report += "Rapportdatum: " + now + "\n" + "Datauppdatering: " + last_updated + "\n" + "="*80

# Executive Summary
# Göra loopar och ifsatser för det jag vill veta
offline_count = 0
warning_count = 0
low_uptime_count = 0
high_port_usage_count = 0

for location in data["locations"]:
    for device in location["devices"]:
        status = device["status"].lower()
        uptime = int(device["uptime_days"])

        if status == "offline":
            offline_count += 1
        elif status == "warning":
            warning_count += 1

        if uptime < 30:
            low_uptime_count += 1
        
        if device["type"] == "switch":
            total_ports = device["ports"]["total"]
            used_ports = device["ports"]["used"]
            port_usage = (used_ports / total_ports) * 100

            if port_usage > 80:
                high_port_usage_count += 1

report += "\nEXECUTIVE SUMMARY\n"
report += "-----------------\n"
report += f"⚠ KRITISKT: {offline_count} enheter offline\n"
report += f"⚠ VARNING: {warning_count} enheter med varningsstatus\n"
report += f"⚠ {low_uptime_count} enheter med låg uptime (<30 dagar) - kan indikera instabilitet\n"
report += f"⚠ {high_port_usage_count} switchar har hög portanvändning (>80%)\n"

# loop through the location list
for location in data["locations"]:
    # add the site/"name" of the location to the report
    report += "\n" + location["site"] + " - " + location["city"] + "\n" + " " + "hostname".ljust(15) + " " + "vendor".ljust(11) + " " + "uptime_days".ljust(20) + "status".ljust(16) + "ipaddress".ljust(15) + "\n"
    # add a list of the host names of the devices
    # on the location to the report
    for device in location["devices"]:
        report += (" " 
                   + device["hostname"].ljust(15) + " "
                   + device["vendor"].ljust(15) + " "
                   + str(device["uptime_days"]).ljust(15) + " " 
                   + str(device["status"]).ljust(15) + " "
                   + str(device["ip_address"]).ljust(15) + " "
                   + "\n")

# Create an empty summary
summary = ""

# Somewhere later in our report add something to summary
summary += "Summary:\n"
summary += "This is our basic report:"

# Add summary before main report
#report = summary + report

# write the report to text file
with open('network_report.txt', 'w', encoding='utf-8') as f:
    f.write(report)