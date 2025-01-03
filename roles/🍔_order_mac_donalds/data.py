# load mc_do_data.json file as "menu" variable
import json

with open("roles/🍔_order_mac_donalds/mc_do_data.json") as f:
    menu = json.load(f)
    f.close()