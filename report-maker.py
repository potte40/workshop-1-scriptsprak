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

### Executive Summary ###
# Fixa countsvariablar
offline_count = 0
warning_count = 0
low_uptime_count = 0
high_port_usage_count = 0
# Göra loopar och ifsatser för det jag vill veta
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
report += f"⚠ {low_uptime_count} enheter med låg uptime (mindre än 30 dagar) - kan indikera instabilitet\n"
report += f"⚠ {high_port_usage_count} switchar har hög portanvändning (mer än 80%)\n"

### Enheter med problem ###
# Samla problem per status
report += "\n""ENHETER MED PROBLEM\n" + "-"*19

statuses = ["offline", "warning"]

for status in statuses:
    report += f"\nStatus: {status.upper()}\n"
    
    for location in data["locations"]:
        for device in location["devices"]:
            device_status = device.get("status", "").lower()
            if device_status == status:
                hostname = device.get("hostname", "")
                ip = device.get("ip_address", "")
                device_type = device.get("type", "").replace("_", " ").title()
                site = location.get("site", "")
                
                # Extra info
                extra_info = ""
                
                # Uptime om warning
                if device_status == "warning":
                    uptime_days = device.get("uptime_days")
                    if uptime_days is not None:
                        extra_info += f"(uptime: {uptime_days} dagar)"
                
                # Anslutna klienter om access point
                if device_type.lower() == "access point":
                    clients = device.get("connected_clients") or 0
                    if clients > 0:
                        if extra_info:
                            extra_info += " "
                        extra_info += f"\n({clients} anslutna klienter!)"
                
                # Lägg till extra_info om det finns
                if extra_info:
                    extra_info = " " + extra_info

                report += f"{hostname.ljust(15)} {ip.ljust(15)} {device_type.ljust(12)} {site}{extra_info}\n"


### Enheter med låg uptime ###
# Samla uptime_days
report += "\nENHETER MED LÅG UPTIME (<30 dagar)\n"
report += "-"*34 + "\n"

# Samla alla låg-uptime-enheter i en lista
low_uptime_devices = [
    {
        "hostname": device.get("hostname", ""),
        "uptime": device.get("uptime_days", 0),
        "site": location.get("site", ""),
        "status": device.get("status", "").lower()
    }
    for location in data["locations"]
    for device in location["devices"]
    if device.get("uptime_days", 0) < 30
]

# Sortera på uptime_days (lägst först)
low_uptime_devices.sort(key=lambda d: d["uptime"])

# Skriv ut
for dev in low_uptime_devices:
    status_text = "⚠ KRITISKT" if dev["status"] in ["offline", "warning"] else dev["site"]
    report += f"{dev['hostname'].ljust(15)} {str(dev['uptime']).rjust(2)} dagar    {status_text}\n"



# loop through the location list
for location in data["locations"]:
    report += f"\n{location["site"]} - {location["city"]}\n" + f"Kontakt: {location["contact"]}\n" + "-"*30 + "\n"
    report += "hostname".ljust(16) + "vendor".ljust(12) + "uptime_days".ljust(20) + "status".ljust(16) + "ipaddress".ljust(15) + "\n"

    # Dictionaries för att räkna antal per typ och offline per typ
    type_counts = {}
    status_counts = {}
    total_devices = 0
    site_status_counts = {"online": 0, "offline": 0, "warning": 0}

    # Loopa igenom alla enheter
    for device in location["devices"]:
        report += ("" 
                   + device["hostname"].ljust(15) + " "
                   + device["vendor"].ljust(15) + " "
                   + str(device["uptime_days"]).ljust(15) + " " 
                   + str(device["status"]).ljust(15) + " "
                   + str(device["ip_address"]).ljust(15) + "\n"
                   )
        total_devices += 1

        device_type = device["type"].lower()
        status = device["status"].lower()

        # Initiera räknare om det inte finns
        if device_type not in type_counts:
            type_counts[device_type] = 0
            status_counts[device_type] = {"online": 0, "offline": 0, "warning": 0}

        # Räkna Status
        type_counts[device_type] += 1
        if status in status_counts[device_type]:
            status_counts[device_type][status] += 1

        if status in site_status_counts:
            site_status_counts[status] += 1


    # Sektion för summering
    report += "-"*30 + "\n"
    report += "Totalt per enhetstyp:\n"
    for dev_type, count in type_counts.items():
        online = status_counts[dev_type].get("online", 0)
        offline = status_counts[dev_type].get("offline", 0)
        warning = status_counts[dev_type].get("warning", 0)
        report += f"{dev_type.ljust(15)}: {count} st (online: {online}, offline: {offline}, warning: {warning})\n"
    
    report += "-"*30 + "\n"

    # Skriv totalen för hela site
    report += f"Totalt antal enheter : {total_devices} st (online: {site_status_counts['online']}, offline: {site_status_counts['offline']}, warning: {site_status_counts['warning']})\n"
    report += "-"*80 + "\n"
        
# write the report to text file
with open('network_report.txt', 'w', encoding='utf-8') as f:
    f.write(report)