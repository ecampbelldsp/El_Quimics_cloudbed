from src.call import requestVersion2

import sys
import os

DATA_CLIENT_PATH = "C:/Opencheck/tmp/"

if not os.path.exists(DATA_CLIENT_PATH):
    os.mkdir(DATA_CLIENT_PATH)


# Config State
property_id = '295501'
client_id = "live1_295501_g6aBYH9oejmTdGLsbFO8uDtR"
redirect_uri = "https://opencheck.es"

client_secret = '3Xki5vVmtIuCYHhGdTMJU4fjgF0ewbO2'

scope = "write:guest read:guest write:reservation read:reservation"
code_4_scope_guest_and_reservation = "8AubJP-rnMiMJ7YshudHlNfgd0kIoSuv7_EBH-3F1EQ"
state_4_scope_guest_and_reservation = "2b25900784b1f315fd71f16d19992c7e02773e5864be50422e1a4"
path_tokens = "data/tokens_guests_and_reservation.json"

code_4_scope_payment_and_room = "V7SAw3ev9pHKE2ha8kayeBBQcpxGPYRMNRXkTUK4YSA"
state_4_scope_payment_and_room = "2b25900784b1f315fd71f16d19992c7e02773e5864be50729fdb3"
path_tokens_payment_and_room = "data/tokens_payments_and_room.json"

reservation_id = "0934955461346"
guest_id = '55949917'

date_in = "2023-01-20"
date_out = "2023-01-29"

guest_docu_path = ["data/passport.png", "data/passport.png"]
reservation_docu_path = ["data/Travel-Request-Form-Template.pdf"]

# Create the request objects
request_guest_and_reservation = requestVersion2(client_id, client_secret, redirect_uri,
                                                code_4_scope_guest_and_reservation,
                                                path_tokens)

request_payment_and_room = requestVersion2(client_id, client_secret, redirect_uri, code_4_scope_payment_and_room,
                                           path_tokens_payment_and_room)
