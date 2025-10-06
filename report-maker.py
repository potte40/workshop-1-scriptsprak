# Import the json library so that we can handle json
import json

# Import time so that we can handle time
from datetime import datetime

# Import defaultdict from collection so that we can handle that
from collections import defaultdict

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
    status = dev["status"].lower()
    status_text = (
        "⚠ KRITISKT" if status == "offline"
        else "⚠ VARNING" if status == "warning"
        else dev["site"]
    )
    report += f"{dev['hostname'].ljust(15)} {str(dev['uptime']).rjust(2)} dagar    {status_text}\n"


    ### Statistik per enhetstyp ###
report += "\nSTATISTIK PER ENHETSTYP\n"
report += "-"*23 + "\n"

device_count = defaultdict(int)
offline_count = defaultdict(int)

# Gå igenom alla enheter i alla sites
for location in data["locations"]:
    for device in location["devices"]:
        dtype = device.get("type", "okänd").replace("_", " ").title()
        status = device.get("status", "").lower()

        device_count[dtype] += 1
        if status == "offline":
            offline_count[dtype] += 1

# Räkna totaler
total = sum(device_count.values())
total_offline = sum(offline_count.values())
offline_percent = (total_offline / total * 100) if total > 0 else 0

# Skriv ut statistikdelen
for dtype in sorted(device_count.keys()):
    count = device_count[dtype]
    off = offline_count.get(dtype, 0)
    report += f"{dtype.ljust(15)}: {str(count).rjust(3)} st ({off} offline)\n"

report += "-"*30 + "\n"
report += f"Totalt: {str(total).rjust(12)} enheter ({total_offline} offline = {offline_percent:.1f}% offline)\n"


### Portanvändning switchar ###
report += "\nPORTANVÄNDNING SWITCHAR\n"
report += "-"*23 + "\n"
report += f"{'Site'.ljust(15)}{'Switchar'.ljust(10)}{'Använt/Totalt'.ljust(15)}{'Användning'}\n"

total_used = 0
total_ports = 0

for location in data["locations"]:
    switches = [d for d in location["devices"] if d.get("type","").lower() == "switch"]
    if not switches:
        continue

    num_switches = len(switches)
    used_ports_site = sum(d["ports"]["used"] for d in switches if "ports" in d)
    total_ports_site = sum(d["ports"]["total"] for d in switches if "ports" in d)
    usage_percent = (used_ports_site / total_ports_site * 100) if total_ports_site > 0 else 0

    # Välj symboler
    symbol = ""
    if usage_percent >= 95:
        symbol = " ⚠ KRITISKT!"
    elif usage_percent >= 80:
        symbol = " ⚠"

    # Lägg till i report
    site_name = location.get("site", "").ljust(15)
    switches_str = (str(num_switches)+' st').ljust(10)
    ports_str = (f"{used_ports_site}/{total_ports_site}").ljust(15)
    usage_str = f"{usage_percent:.1f}%".rjust(7)

    report += f"{site_name}{switches_str}{ports_str}{usage_str}{symbol}\n"

    # Lägg till i totalen
    total_used += used_ports_site
    total_ports += total_ports_site

# Totalt
total_percent = (total_used / total_ports * 100) if total_ports > 0 else 0
report += "-"*30 + f"\nTotalt:         {total_used}/{total_ports} portar används ({total_percent:.1f}%)\n"


### Switchar med hög portanvändning (>80%) ###
report += "\nSWITCHAR MED HÖG PORTANVÄNDNING (>80%)\n"
report += "-"*38 + "\n"

# Lista för switches med hög portanvändning
high_usage_switches = []

for location in data["locations"]:
    for device in location["devices"]:
        if device.get("type","").lower() != "switch":
            continue
        if "ports" not in device:
            continue

        used_ports = device["ports"]["used"]
        total_ports = device["ports"]["total"]
        usage_percent = (used_ports / total_ports * 100) if total_ports > 0 else 0

        if usage_percent > 80:
            # Symbol
            symbol = " ⚠"
            if used_ports == total_ports:
                symbol += " FULLT!"
            high_usage_switches.append({
                "hostname": device["hostname"],
                "used": used_ports,
                "total": total_ports,
                "percent": usage_percent,
                "symbol": symbol
            })

# Sortera efter procent (högst först)
high_usage_switches.sort(key=lambda x: x["percent"], reverse=True)

# Skriv till rapporten
for sw in high_usage_switches:
    report += f"{sw['hostname'].ljust(15)}{str(sw['used'])+'/'+str(sw['total']).ljust(7)}{sw['percent']:7.1f}%{sw['symbol']}\n"


### VLAN-ÖVERSIKT ###
report += "\nVLAN-ÖVERSIKT\n"
report += "-"*13 + "\n"

# Samla alla VLANs
vlan_set = set()

for location in data["locations"]:
    for device in location["devices"]:
        if device.get("type","").lower() == "switch" and "vlans" in device:
            vlan_set.update(device["vlans"])

# Sortera VLANs numeriskt
vlan_list = sorted(vlan_set)

# Skriv total antal och VLANs
report += f"Totalt antal unika VLANs i nätverket: {len(vlan_list)} st\n"

# Dela upp i rader om många VLANs
vlans_per_line = 12
vlan_lines = [vlan_list[i:i+vlans_per_line] for i in range(0, len(vlan_list), vlans_per_line)]

report += "VLANs: "
for i, line in enumerate(vlan_lines):
    vlan_str = ", ".join(str(v) for v in line)
    if i == 0:
        report += vlan_str + ",\n"
    else:
        report += "       " + vlan_str + ("," if i < len(vlan_lines)-1 else "") + "\n"



report += "\nSTATISTIK PER SITE\n" + "-"*30
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

    ### REKOMMENDATIONER ###
report += "\nREKOMMENDATIONER\n"
report += "-"*20 + "\n"

# 1. AKUT: offline-enheter
offline_devices = [
    device["hostname"]
    for location in data["locations"]
    for device in location["devices"]
    if device.get("status","").lower() == "offline"
]
num_offline = len(offline_devices)
if num_offline > 0:
    report += f". AKUT: Undersök offline-enheter omgående ({num_offline} st)\n"

# 2. KRITISKT: hög portanvändning (>95%) per site
for location in data["locations"]:
    switches = [d for d in location["devices"] if d.get("type","").lower() == "switch" and "ports" in d]
    if not switches:
        continue
    used_ports_site = sum(d["ports"]["used"] for d in switches)
    total_ports_site = sum(d["ports"]["total"] for d in switches)
    usage_percent = (used_ports_site / total_ports_site * 100) if total_ports_site > 0 else 0
    if usage_percent >= 95:
        report += f". KRITISKT: {location.get('site')} har extremt hög portanvändning - planera expansion\n"

# 3. Kontrollera låg uptime (<30 dagar), särskilt <5 dagar
low_uptime_devices = [
    device for location in data["locations"]
    for device in location["devices"]
    if device.get("uptime_days", 0) < 30
]
if low_uptime_devices:
    short_uptime_devices = [d for d in low_uptime_devices if d.get("uptime_days",0) < 5]
    if short_uptime_devices:
        report += ". Kontrollera enheter med låg uptime - särskilt de med <5 dagar\n"
    else:
        report += ". Kontrollera enheter med låg uptime (<30 dagar)\n"

# 4. Access points med många klienter (>30 t.ex.) och warning status
for location in data["locations"]:
    for device in location["devices"]:
        if device.get("type","").lower() == "access_point":
            clients = device.get("connected_clients",0)
            status = device.get("status","").lower()
            if clients > 30 or status == "warning":
                report += f". {device['hostname']} har {clients} anslutna klienter ({status}) - överväg lastbalansering\n"

# 5. Standardisering av vendor per site (exempel)
report += ". Överväg standardisering av vendorer per site för enklare underhåll\n"

report += ("\n" + "="*80 + "\n" + f"RAPPORT SLUT".center(80) 
+ "\n" + "="*80 + "\n")
        
# write the report to text file
with open('network_report.txt', 'w', encoding='utf-8') as f:
    f.write(report)