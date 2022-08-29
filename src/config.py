from src.call import RequestVersion2

# Config State
property_id = '212599'
client_id = "live1_212599_LBRQd0lhTFIkJH5GCpwPUOEg"
redirect_uri = "https://81ee-31-4-128-46.eu.ngrok.io"

client_secret = 'gwSvTrFauEbt4OkKy1sVGCnB3hpcjf7I'

scope = "write:guest read:guest write:reservation read:reservation"
code_4_scope_guest_and_reservation = "v9Kc5kU3yWb9tp0NawUiuh7eviuuqTKDSjW25FPMUIU"
state_4_scope_guest_and_reservation = "fb08f0d2ff44e959fcd83dc20e58a8c0d729cf6f630c7b2b1fb2f"
path_tokens = "data/tokens_guests_and_reservation.json"

code_4_scope_payment_and_room = "hqtyfq46xNn_E5SLz-R2tlRj6nEdwi_JyX78LkSExfg"
state_4_scope_payment_and_room = "fb08f0d2ff44e959fcd83dc20e58a8c0d729cf6f630c7b5554c79"
path_tokens_paymeent_and_room = "data/tokens_payments_and_room.json"

reservation_id = "0934955461346"
guest_id = '55949917'

date_in = "2023-01-20"
date_out = "2023-01-29"

guest_docu_path = ["data/passport.png", "data/passport.png"]
reservation_docu_path = ["data/Travel-Request-Form-Template.pdf"]

# Create the request objects
request_guest_and_reservation = RequestVersion2(client_id, client_secret, redirect_uri,
                                                code_4_scope_guest_and_reservation,
                                                path_tokens)

request_payment_and_room = RequestVersion2(client_id, client_secret, redirect_uri, code_4_scope_payment_and_room,
                                           path_tokens_paymeent_and_room)