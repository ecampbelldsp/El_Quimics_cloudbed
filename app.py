#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on  19/8/22 14:17

@author: Edward L. Campbell Hernández & José M. Ramírez
contact: ecampbelldsp@gmail.com & ramirezsanchezjosem@gmail.com
"""

import country_converter as coco
import dateparser
from flask import Flask, render_template, jsonify, request
from src.config import request_guest_and_reservation, request_payment_and_room, property_id
from flask_cors import CORS, cross_origin
from hd.cam import take_picture
from src.config import   DATA_CLIENT_PATH
import os
import subprocess
import time
app = Flask(__name__)

# app.config['CORS_HEADERS'] = 'Content-Type'

# CORS(app)
CORS(app)


# CORS(app, resources=r'/api/*')

if not os.path.exists(DATA_CLIENT_PATH):
    os.mkdir(DATA_CLIENT_PATH)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ping')
def ping():
    return jsonify({"success": "True", "message": "pong"})


@app.route('/getReservation')
def get_reservation():
    def post_processing_reservation(json: dict):

        reservation_out = {
            "reservationID": json.get("reservationID"),
            "guestName": json.get("guestName"),
            "guestEmail": json.get("guestEmail"),
            "guestID": "",
            "guestFirstName": "",
            "guestLastName": "",
            "guestCellPhone": "",
            "guestAddress1": "",
            "guestCity": "",
            "guestCountry": "",
            "guestState": "",
            "guestZip": "",
            "guestBirthDate": "",
            "guestDocumentType": "",
            "guestDocumentNumber": "",
            "guestDocumentIssueDate": "",
            "guestDocumentIssuingCountry": "",
            "guestDocumentExpirationDate": "",
            "roomTypeID": [],
            "roomTypeName": [],
            "roomID": [],
            "startDate": [],
            "endDate": [],
            "adults": [],
            "children": [],
            "paid": "",
            "balance": "",
            "paidStatus": "",
        }

        # Guests reservation info
        guests_info = json['guestList']
        for guest_id in guests_info.keys():
            guest_data = guests_info[guest_id]

            if guest_data['guestFirstName'] in reservation_out['guestName'] and \
                    guest_data['guestLastName'] in reservation_out['guestName']:
                reservation_out['guestID'] = guest_data['guestID']
                reservation_out['guestFirstName'] = guest_data['guestFirstName']
                reservation_out['guestLastName'] = guest_data['guestLastName']
                reservation_out['guestGender'] = guest_data['guestGender']
                reservation_out['guestEmail'] = guest_data['guestEmail']
                reservation_out['guestPhone'] = guest_data['guestPhone']
                reservation_out['guestCellPhone'] = guest_data['guestCellPhone']
                reservation_out['guestCountry'] = guest_data['guestCountry']
                reservation_out['guestAddress'] = guest_data['guestAddress']
                reservation_out['guestCity'] = guest_data['guestCity']
                reservation_out['guestZip'] = guest_data['guestZip']
                reservation_out['guestState'] = guest_data['guestState']
                reservation_out['guestBirthdate'] = guest_data['guestBirthdate']
                reservation_out['guestDocumentType'] = guest_data['guestDocumentType']
                reservation_out['guestDocumentNumber'] = guest_data['guestDocumentNumber']
                reservation_out['guestDocumentIssueDate'] = guest_data['guestDocumentIssueDate']
                reservation_out['guestDocumentExpirationDate'] = guest_data['guestDocumentExpirationDate']
                reservation_out['guestDocumentIssuingCountry'] = guest_data['guestDocumentIssuingCountry']

        # Room reservation info
        for room in json['unassigned']:
            # reservation_out['roomID'].append(room.get('roomID'))
            reservation_out['roomID'].append(room.get('roomTypeID'))
            reservation_out['roomTypeName'].append(room.get('roomTypeName'))
            # reservation_out['roomID'].append(room.get('roomID'))
            reservation_out['startDate'].append(room.get('dailyRates')[0]['date'])  # room.get('startDate')
            reservation_out['endDate'].append(room.get('dailyRates')[-1]['date'])
            reservation_out['adults'].append(room.get('adults'))
            reservation_out['children'].append(room.get('children'))

        for room in json['assigned']:
            # reservation_out['roomID'].append(room.get('roomID'))
            reservation_out['roomID'].append(room.get('roomTypeID'))
            reservation_out['roomTypeName'].append(room.get('roomTypeName'))
            # reservation_out['roomID'].append(room.get('roomID'))
            reservation_out['startDate'].append(room.get('dailyRates')[0]['date'])
            reservation_out['endDate'].append(room.get('dailyRates')[-1]['date'])
            reservation_out['adults'].append(room.get('adults'))
            reservation_out['children'].append(room.get('children'))

        # Pre-processing stage for Frontend
        for key in reservation_out.keys():
            data = reservation_out[key]
            if isinstance(data, list):
                # data = ['' for d in data if d is None]
                data_set = set(data)
                reservation_out[key] = " _ ".join(data_set)

        # Reformatting date tipe from YYYY-MM-DD to DD-MM-YYYY
        for key in ['startDate', 'endDate']:
            data = reservation_out[key]
            data = data.split('_')
            data = [d.split('-')[::-1] for d in data]
            data = ['-'.join(d) for d in data]
            data = ' _ '.join(data)
            reservation_out[key] = data

        # Invoice reservation info
        total = json['balanceDetailed']['grandTotal']
        paid = json['balanceDetailed']['paid']
        balance = float(total) - float(paid)

        reservation_out["paid"] = paid
        reservation_out["total"] = total
        reservation_out["balance"] = "0" if balance < 0 else f"{balance}"

        reservation_out["paidStatus"] = "false" if balance > 0 else "true"

        return {"success": "true", "data": reservation_out}

    reservation_id = request.args.get('reservationID', None)
    response_in_json = request_guest_and_reservation.get_reservation(reservation_id)

    if response_in_json["success"] == "true":
        response_in_json = post_processing_reservation(response_in_json['data'])

    return response_in_json# jsonify(response_in_json)


@app.route('/putReservation', methods=['PUT'])
def put_reservation():
    reservation_id = request.args.get('reservationID', None)
    status = request.args.get('status', None)
    return request_guest_and_reservation.put_reservation(reservation_id, status)


@app.route('/postReservation', methods=['POST'])
def post_reservation():
    data = request.get_json()
    guest_info = data.get('guestInfo')
    room = data.get('rooms')

    # Update some reservation's values.
    guest_country_iso2 = coco.convert(names=guest_info['guestCountry'], to='ISO2')
    guest_info.update({'propertyID': property_id, 'paymentMethod': 'card', 'guestCountry': guest_country_iso2})
    # Fill the room's values.
    room_info = {'rooms': [{"roomTypeID": room.get('roomTypeID'),
                            "roomRateID": room.get('roomRateID'),
                            "quantity": 1}]}
    adults = {'adults': [{"roomTypeID": room.get('roomTypeID'),
                          "quantity": guest_info.get('adults'),
                          "roomID": ""}]}
    children = {'children': [{"roomTypeID": room.get('roomTypeID'),
                              "quantity": guest_info.get('children'),
                              "roomID": ""}]}
    # Merge all data.
    guest_info.update(room_info)
    guest_info.update(adults)
    guest_info.update(children)

    return request_guest_and_reservation.post_reservation(guest_info)


@app.route('/getReservationInvoiceInformation')
def get_reservation_invoice_information():
    """
    Get reservation invoice information.
    :return: a json with a reservation invoice information filtered.
    """
    def post_processing_reservation_invoice_information(json):
        """
        Post-processing stage for Frontend.
        :param json: a reservation's invoice information in json format.
        :return: a filtered invoice information (balance, paid, grandTotal, etc) in json format.
        """
        reservation_out = {'success': 'true', 'paid': json['paid'], 'total': json['grandTotal'],
                           'balance': str(float(json['grandTotal']) - float(json['paid']))}

        reservation_out['paidStatus'] = 'false' if float(reservation_out['balance']) > 0 else 'true'
        return reservation_out

    reservation_id = request.args.get('reservationID', None)
    full_invoce = request_guest_and_reservation.get_reservation_invoice_information(reservation_id)
    if full_invoce['success'] != 'false':
        return post_processing_reservation_invoice_information(full_invoce.get('data').get('balanceDetailed'))
    else:
        return full_invoce


@app.route('/getGuestsInformation')
def get_guests_info():
    reservation_id = request.args.get('reservationID', None)
    return request_guest_and_reservation.get_guest_info_in_reservation(reservation_id)


@app.route('/getNumberOfGuests')
def how_many_guests():
    reservation_id = request.args.get('reservationID', None)
    return request_guest_and_reservation.get_number_of_guests(reservation_id)


@app.route('/getAvailableRooms')
def get_available_rooms():
    start_date = request.args.get('startDate', None)
    end_date = request.args.get('endDate', None)

    rooms = request.args.get('rooms', 1)
    adults = int(request.args.get('adults', None))
    childrens = int(request.args.get('childrens', None))

    return request_payment_and_room.get_available_room_types(start_date, end_date, rooms, adults, childrens)


@app.route('/postGuestDocument')
def post_guest_document():
    guest_id = request.args.get('guestID', None)
    path_to_document = request.args.get('pathDocument', None)
    return request_guest_and_reservation.post_guest_document(guest_id, path_to_document)


@app.route('/postReservationDocument')
def post_reservation_document():
    reservation_id = request.args.get('reservationID', None)
    path_to_document = request.args.get('pathDocument', None)
    return request_guest_and_reservation.post_guest_document(reservation_id, path_to_document)


@app.route('/reservationIsPaid')
def reservation_is_paid():
    reservation_id = request.args.get('reservationID', None)
    return request_guest_and_reservation.reservation_is_paid(reservation_id)

@app.route('/getPaymentMethods')
def getPaymentMethods():
    propertyID = request.args.get('propertyID', None)
    return request_payment_and_room.getPaymentMethods(propertyID)


@app.route('/postPayment')
def post_payment():
    reservation_id = request.args.get('reservationID', None)
    amount = request.args.get('amount', None)
    payment_type = request.args.get('type', 'card')
    card_type: str = request.args.get('cardType', None)

    return request_payment_and_room.post_payment(reservation_id, amount, payment_type, card_type)

@app.route('/verifone')
def verifone():

    puerto = "COM4"
    cash = str(int(float(request.args.get('cash', None)) * 100))
    #cash = str(request.args.get('cash', None))

    # Define the path to the C# executable
    root = "hd/verifone/"
    csharp_executable = "Verifone_C_Sharp.exe"
    args = [puerto,cash] # El cash es en centimos
    # subprocess.Popen( ["mono"],executable=f"{root}{csharp_executable} " + "10", cwd = root)

    command = ["dotnet", "run"] + args

    csharp_process = subprocess.Popen( command,executable=f"{root}{csharp_executable}", cwd = root,stdout=subprocess.PIPE) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    # csharp_process.wait()
    time.sleep(1)
    while(True):

        out = csharp_process.stdout.readline().decode()
        if "\n" in out:
            #print(out)
            out = out.replace("\n", "")
        if "\r" in out:
            #print(out)
            out = out.replace("\r", "")


        print(out)
        #return jsonify({'success': False, 'message': 'Devolución de pago. El sistema no tiene cashBack.'})
        if "20" == out.lower():  #_on_
             print("Esperando inserción de tarjeta")
        elif "30" == out.lower():
            print("Error de lectura de tarjeta")
        elif "40" == out.lower():
            print("Tarjeta leída")
        elif "50" == out.lower():
            print("Esperando confirmación de compra por cliente")
        elif "60" == out.lower():
            print("Transacción aprobada")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "true", 'message': 'Successful payment.'})
        elif "70" == out.lower():
            print("Transcción rechazada")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "false", 'message': 'Payment rejected'})
        elif "80" == out.lower():
            print("Esperando retirada de tarjeta")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "true", 'message': 'Successful payment.'})
        elif "90" == out.lower():
            print("Operación cancelada")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "false", 'message': 'Payment cancelled'})

        elif "-1" == out.lower():
            print("Sales market down")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "false", 'message': 'Sales market down'})
        elif "-2" == out.lower():
            print("Timeout para la presentación de tarjeta")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "false", 'message': 'Timeout'})
        elif "-3" == out.lower():
            print("Volviendo a reposo luego de haber iniciado una venta. Cancelación de venta")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "false", 'message': 'Payment cancelled'})
        elif "0" == out.lower():
            print("Estado de venta desconocido")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "false", 'message': 'Unknown sales state'})
        elif "ok" == out.lower():
            print("Successful payment")
            csharp_process.terminate()
            csharp_process.wait()
            return jsonify({'success': "true", 'message': 'Successful payment.'})


# TESA API
host = "192.168.0.164"#"192.168.1.90"
operatorName = 'opencheck' #"OPEN"#'opencheck'
operatorPassword = '123456'#"123456"#'opencheck!'
agentId = "ac54a7b4ac713ae3bddf36ecf9094f"#'bacd6749e86ffb7c7d3bf0dfaad12a'

# Hotel data
roomsTable = {"102":"13","101":"12","213": "1", "214": "2", "215": "3", "216": "4", "217": "5", "218": "6", "219": "7", "220": "8",
              "221": "9", "222": "10", "223": "11", "224": "12", "225": "13", "226": "14"}


# Utils
def format_date(date, now=True):
    date_object = dateparser.parse(date)
    if date_object.time() == datetime.min.time() and now:
        now = datetime.now()
        date_object = date_object.replace(hour=now.hour, minute=now.minute, second=now.second)
    elif not now:
        date_object = date_object.replace(hour=11, minute=00, second=00)
    return date_object.strftime("%Y-%m-%dT%H:%M:%S")


def check_response(response):
    # Verifica si el resultado es exitoso (RESULT_OK)
    if response.type == 'RESULT_OK':
        result = {
            'success': True,
            'message': 'Check-in realizado correctamente'
        }
    elif response.type == 'RESULT_ERROR' and response.errorCode == '508':
        result = {
            'success': True,
            'errorCode': response.errorCode,
            'message': 'Check-in/out realizado correctamente'
        }
    # Verifica si el resultado es un error de habitación no ocupada (RESULT_ERROR_CHECKIN_ROOM_NOT_OCCUPIED)
    elif response.type == 'RESULT_ERROR' and response.errorType == 'RESULT_ERROR_CHECKIN_ROOM_NOT_OCCUPIED':
        result = {
            'success': False,
            'type': response.type,
            'errorCode': response.errorCode,
            'errorType': response.errorType
        }
    else:
        result = {
            'success': False,
            'type': response.errorType,
            'message': response.errorDetail
        }
    return result


@app.route("/tesa/v1.0/checkIn", methods=["POST"])
def checkin():
    # Extrae los datos del JSON recibido
    data = request.get_json()

    roomName = data['roomName']
    roomId = roomsTable[roomName]

    checkIn = data['checkIn']
    checkInFormatted = format_date(checkIn)

    checkOut = data['checkOut']
    checkOutFormatted = format_date(checkOut, now=False)

    # Mueve tarjeta a RF
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToRF")

    if not response:
        result = {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to RF"}
        return result

    # Crea un cliente SOAP con la URL del servidor TESA
    service = GuestsWebService(host, operatorName, operatorPassword)

    # Realiza la operación de check-in utilizando el cliente SOAP
    GuestInfoType = service.client.get_type('ns0:guestInfo')
    guest_info = GuestInfoType(roomId=roomId, openowCheckin=True, localCardCheckin=True, agentId=agentId,
                               dateActivation=checkInFormatted,
                               dateExpiration=checkOutFormatted)
    response = service.check_in(guest_info)
    result = check_response(response)

    # Entrega tarjeta
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToFrontAndHold")
    if not response:
        result = {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to front"}
        return result

    return jsonify(result)


@app.route('/tesa/v1.0/checkInCopy', methods=['POST'])
def checkinCopy():
    # Extrae los datos del JSON recibido
    data = request.get_json()

    roomName = data['roomName']
    roomId = roomsTable[roomName]

    checkIn = data['checkIn']
    checkInFormatted = format_date(checkIn)

    checkOut = data['checkOut']
    checkOutFormatted = format_date(checkOut, now=False)

    # Mueve tarjeta a RF
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToRF")
    if not response:
        result = {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to RF"}
        return result

    # Crea un cliente SOAP con la URL del servidor TESA
    service = GuestsWebService(host, operatorName, operatorPassword)

    # Realiza la operación de check-in utilizando el cliente SOAP
    GuestInfoType = service.client.get_type('ns0:guestInfo')
    guest_info = GuestInfoType(roomId=roomId, openowCheckin=True, localCardCheckin=True, agentId=agentId,
                               dateActivation=checkInFormatted,
                               dateExpiration=checkOutFormatted)

    response = service.check_in_copy(guest_info)
    result = check_response(response)

    # Entrega tarjeta
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToFrontAndHold")
    if not response:
        result = {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to front"}
        return result

    return jsonify(result)


@app.route('/tesa/v1.0/checkOut', methods=['POST'])
def checkout():
    # Extrae los datos del JSON recibido
    data = request.get_json()

    # Crea un cliente SOAP con la URL del servidor TESA
    client = GuestsWebService(host, operatorName, operatorPassword)

    # Construye el objeto `guestData`
    roomNumber = data['roomName']
    roomId = roomsTable[roomNumber]

    # Realiza la operación de check-out utilizando el cliente SOAP
    response = client.check_out(roomId)
    result = check_response(response)

    # Mueve tarjeta a RF
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToRF")
    if not response:
        result = {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to RF"}
        return result
    return jsonify(result)

@app.route("/cam")
def picture():
    flag = take_picture()
    return flag


if __name__ == '__main__':
    # Flask app
    app.run(debug=True)
