#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on  19/8/22 14:17

@author: Edward L. Campbell Hernández & José M. Ramírez
contact: ecampbelldsp@gmail.com & ramirezsanchezjosem@gmail.com
"""
import base64
import json
import os
import shutil
import subprocess
import threading
import time
import zipfile
from datetime import datetime
from os.path import basename
from time import sleep

import country_converter as coco
import cv2
import dateparser
import qrcode
import requests as rq
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from email_server.send import gmail_send_message
from hd.cam import take_picture
from src.config import DATA_CLIENT_PATH
from src.config import request_guest_and_reservation, request_payment_and_room, property_id
from src.tesa import GuestsWebService

app = Flask(__name__)

# app.config['CORS_HEADERS'] = 'Content-Type'

# CORS(app)
CORS(app)

# CORS(app, resources=r'/api/*')

if not os.path.exists(DATA_CLIENT_PATH):
    os.mkdir(DATA_CLIENT_PATH)
if not os.path.exists("C:/Opencheck/parte.txt"):
    with open("C:/Opencheck/parte.txt", "w") as file:
        file.write("0")


@app.route('/')
def index():
    return {"success": True, "message": "WELCOME! Backend-Kiosko-Cloudbeds"}


@app.route('/ping')
def ping():
    return jsonify({"success": "True", "message": "pong"})


@app.route('/getReservation')
def get_reservation():
    def post_processing_reservation(reservation_json: dict):

        reservation_out = {
            "reservationID": reservation_json.get("reservationID"),
            "guestName": reservation_json.get("guestName"),
            "guestEmail": reservation_json.get("guestEmail"),
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
            "roomName": [],
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
        guests_info = reservation_json['guestList']
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
        for room in reservation_json['unassigned']:
            reservation_out['roomID'].append(room.get('roomTypeID'))
            reservation_out['roomName'].append(room.get('roomName'))
            reservation_out['roomTypeName'].append(room.get('roomTypeName'))
            reservation_out['startDate'].append(room.get('dailyRates')[0]['date'])  # room.get('startDate')
            reservation_out['endDate'].append(room.get('dailyRates')[-1]['date'])
            reservation_out['adults'].append(room.get('adults'))
            reservation_out['children'].append(room.get('children'))

        for room in reservation_json['assigned']:
            reservation_out['roomID'].append(room.get('roomTypeID'))
            reservation_out['roomName'].append(room.get('roomName'))
            reservation_out['roomTypeName'].append(room.get('roomTypeName'))
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
        total = reservation_json['balanceDetailed']['grandTotal']
        paid = reservation_json['balanceDetailed']['paid']
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

    return response_in_json


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

    def post_processing_reservation_invoice_information(invoice_json):
        """
        Post-processing stage for Frontend.
        :param invoice_json: a reservation's invoice information in json format.
        :return: a filtered invoice information (balance, paid, grandTotal, etc) in json format.
        """
        reservation_out = {'success': 'true', 'paid': invoice_json['paid'], 'total': invoice_json['grandTotal'],
                           'balance': str(float(invoice_json['grandTotal']) - float(invoice_json['paid']))}

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
def get_payment_methods():
    property_id_ = request.args.get('propertyID', None)
    return request_payment_and_room.getPaymentMethods(property_id_)


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
    # cash = str(request.args.get('cash', None))

    # Define the path to the C# executable
    root = "hd/verifone/"
    csharp_executable = "Verifone_C_Sharp.exe"
    args = [puerto, cash]  # El cash es en centimos
    # subprocess.Popen( ["mono"],executable=f"{root}{csharp_executable} " + "10", cwd = root)

    command = ["dotnet", "run"] + args

    csharp_process = subprocess.Popen(command, executable=f"{root}{csharp_executable}", cwd=root,
                                      stdout=subprocess.PIPE)  # , stdout=subprocess.PIPE, stderr=subprocess.PIPE
    # csharp_process.wait()
    time.sleep(1)
    while True:

        out = csharp_process.stdout.readline().decode()
        if "\n" in out:
            # print(out)
            out = out.replace("\n", "")
        if "\r" in out:
            # print(out)
            out = out.replace("\r", "")

        print(out)
        # return jsonify({'success': False, 'message': 'Devolución de pago. El sistema no tiene cashBack.'})
        if "20" == out.lower():  # _on_
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
host = "192.168.1.10"
operatorName = "direc"
operatorPassword = "clave1"
agentId = "c4097353db0354d419ca229064c98b"  # Kiosko AgentID

# Hotel data
roomsTable = {"101": "3", "102": "4", "103": "5", "104": "6", "105": "7", "106": "8",
              "201": "9", "202": "10", "203": "11", "204": "12", "205": "13", "206": "14",
              "301": "15", "302": "16", "303": "17", "304": "18", "305": "19", "306": "20",
              "401": "21", "402": "22", "403": "23", "404": "24", "405": "25", "406": "26",
              "501": "27", "502": "28", "503": "29", "504": "30", "505": "31", "506": "32",
              "601": "33", "602": "34", "603": "35", "604": "36", "605": "37", "606": "38",
              "607": "59", "608": "60", "609": "61"}


# Utils
def format_date(date, now=True):
    date_object = dateparser.parse(date)
    if date_object.time() == datetime.min.time() and now:
        now = datetime.now()
        date_object = date_object.replace(hour=now.hour, minute=now.minute, second=now.second)
    elif not now:
        date_object = date_object.replace(hour=13, minute=00, second=00)
    return date_object.strftime("%Y-%m-%dT%H:%M:%S")


def check_response(response):
    # Verifica si el resultado es exitoso (RESULT_OK)
    if response.type == 'RESULT_OK':
        result = {
            'success': True,
            'message': 'Check-in/out success'
        }
    elif response.type == 'RESULT_ERROR' and response.errorCode == '508':
        result = {
            'success': True,
            'message': 'Check-in/out successfully completed',
            'errorCode': response.errorCode
        }
    # Verifica si el resultado es un error de habitación no ocupada (RESULT_ERROR_CHECKIN_ROOM_NOT_OCCUPIED)
    elif response.type == 'RESULT_ERROR' and response.errorType == 'RESULT_ERROR_CHECKIN_ROOM_NOT_OCCUPIED':
        result = {
            'success': False,
            'message': 'Room not occupied.',
            'type': response.type,
            'errorCode': response.errorCode,
            'errorType': response.errorType
        }
    elif response.type == 'RESULT_ERROR' and response.errorType == 'RESULT_ERROR_CHECKIN_ROOM_OCCUPIED':
        result = {
            'success': False,
            'message': 'Check-in done! Please, make a key duplication instead. / Ya ha hecho el check-in! Por favor haga un duplicado de llaves',
            'type': response.type,
            'errorCode': response.errorCode,
            'errorType': response.errorType
        }
    else:
        result = {
            'success': False,
            'message': response.errorDetail,
            'type': response.errorType
        }
    return result


def move_card_rfid():
    # Mueve tarjeta a RF
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToRF")
    if not response:
        return {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to RF"}
    else:
        return {'success': True, 'message': "Card on RF"}


def move_card_front_and_hold():
    # Move card to front and hold it
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToFrontAndHold")
    if not response:
        return {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "error moving card to front"}
    else:
        return {'success': True, 'message': "Card on front"}


def move_car_error_card_bin():
    # Move card to front and hold it
    response = rq.get("http://localhost:3200/api-hardware/v1/cardDispenser/moveCardToErrorCardBin")
    if not response:
        return {'success': False, 'type': "CARD_DISPENSER_ERROR", 'message': "Error moving card to error card bin"}
    else:
        return {'success': True, 'message': "Card on error card bin"}


# TESA
@app.route("/tesa/findAllRooms")
def tesa_find_all_rooms():
    # Crea un cliente SOAP con la URL del servidor TESA
    try:
        service = GuestsWebService(host, operatorName, operatorPassword)
        response = service.find_all_rooms()
        print(response)
        return {"success": True}
    except:
        return {"success": False}


@app.route("/tesa/checkIn", methods=["POST"])
def tesa_checkin():
    # Extrae los datos del JSON recibido
    data = request.get_json()

    room_id = roomsTable.get(data.get('roomName'))

    check_in_formatted = format_date(data.get('checkIn'))
    check_out_formatted = format_date(data.get('checkOut'), now=False)

    # Crea un cliente SOAP con la URL del servidor TESA
    service = GuestsWebService(host, operatorName, operatorPassword)

    # Realiza la operación de check-in utilizando el cliente SOAP
    guest_info_type = service.client.get_type('ns0:guestInfo')
    guest_info = guest_info_type(roomId=room_id, openowCheckin=True, localCardCheckin=True, agentId=agentId,
                                 dateActivation=check_in_formatted,
                                 dateExpiration=check_out_formatted)
    response = service.check_in(guest_info)
    result = check_response(response)

    return jsonify(result)


@app.route("/tesa/v1.0/checkIn", methods=["POST"])
def checkin():
    # Extrae los datos del JSON recibido
    data = request.get_json()

    room_id = roomsTable.get(data.get('roomName'))

    check_in_formatted = format_date(data.get('checkIn'))
    check_out_formatted = format_date(data.get('checkOut'), now=False)

    # Mueve tarjeta a RF
    card_response = move_card_rfid()
    if not card_response.get("success"):
        return card_response

    # Crea un cliente SOAP con la URL del servidor TESA
    service = GuestsWebService(host, operatorName, operatorPassword)

    # Realiza la operación de check-in utilizando el cliente SOAP
    guest_info_type = service.client.get_type('ns0:guestInfo')
    guest_info = guest_info_type(roomId=room_id, openowCheckin=True, localCardCheckin=True, agentId=agentId,
                                 dateActivation=check_in_formatted,
                                 dateExpiration=check_out_formatted)
    response = service.check_in(guest_info)
    result = check_response(response)

    if result.get("success"):
        # Entrega tarjeta
        card_response = move_card_front_and_hold()
        if not card_response.get("success"):
            return card_response

        # Espera y entrega segunda copia
        time.sleep(15)

        # Mueve tarjeta a RF
        card_response = move_card_rfid()
        if not card_response.get("success"):
            return card_response

        # Grabar duplicado
        response = service.check_in_copy(guest_info)
        result = check_response(response)
        if not result.get("success"):
            result = move_car_error_card_bin()

        # Entrega tarjeta
        card_response = move_card_front_and_hold()
        if not card_response.get("success"):
            return card_response
    else:
        # Mover a ErrorCardBin
        move_car_error_card_bin()

    return jsonify(result)


@app.route('/tesa/v1.0/checkInCopy')
def check_in_copy():
    def post_processing_reservation(reservation_json: dict):

        reservation_out = {
            "reservationID": reservation_json.get("reservationID"),
            "roomName": "",
            "startDate": reservation_json.get("startDate"),
            "endDate": reservation_json.get("endDate"),
            "paidStatus": ""
        }

        for room in reservation_json['assigned']:
            reservation_out['roomName'] = room.get('roomName')

        # Pre-processing stage for Frontend
        for key in reservation_out.keys():
            data = reservation_out[key]
            if isinstance(data, list):
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
        total = reservation_json['balanceDetailed']['grandTotal']
        paid = reservation_json['balanceDetailed']['paid']
        balance = float(total) - float(paid)

        reservation_out["paidStatus"] = "false" if balance > 0 else "true"
        return reservation_out

    # Get reservationID info
    reservation_id = request.args.get('reservationID', None)
    response_in_json = request_guest_and_reservation.get_reservation(reservation_id)
    result = response_in_json

    if response_in_json["success"] == "true":
        response_data = response_in_json.get("data")
        response_data = post_processing_reservation(response_data)

        if response_data.get('paidStatus'):
            room_name = response_data.get('roomName')
            room_id = roomsTable.get(room_name)

            check_in_formatted = format_date(response_data.get("startDate"))
            check_out_formatted = format_date(response_data.get("endDate"), now=False)

            # # Mueve tarjeta a RF
            card_response = move_card_rfid()
            if not card_response.get("success"):
                return card_response

            # Crea un cliente SOAP con la URL del servidor TESA
            service = GuestsWebService(host, operatorName, operatorPassword)

            # Realiza la operación de check-in utilizando el cliente SOAP
            guest_info_type = service.client.get_type('ns0:guestInfo')
            guest_info = guest_info_type(roomId=room_id, localCardCheckin=True, agentId=agentId,
                                         dateActivation=check_in_formatted,
                                         dateExpiration=check_out_formatted)

            response = service.check_in_copy(guest_info)
            result = check_response(response)

            if result:
                # Entrega tarjeta
                card_response = move_card_front_and_hold()
                if not card_response.get("success"):
                    return card_response
            else:
                result = {"success": False,
                          "message": "Check your reservation dates."}

        else:
            result = {"success": False, "message": "Please make the Check-In first, and then get a second key. Thanks!"}

    return jsonify(result)


@app.route('/tesa/v1.0/checkOut', methods=['POST'])
def check_out():
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


# Video and Camera
@app.route("/cam")
def picture():
    flag = take_picture()
    return flag


@app.route('/guardar-imagen', methods=['POST'])
def guardar_imagen():
    imagen_base64 = request.form['imagen']
    # Decodificar la imagen base64 en una matriz de bytes
    imagen_bytes = base64.b64decode(imagen_base64.split(',')[1])

    # Definir la ruta y el nombre de archivo para guardar la imagen
    date_str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    reservationID = request.form['reservationID']
    guest_i = request.form['guest_i']
    name = f"{reservationID}_{guest_i}_{date_str}"
    print(name)
    ruta_guardado = os.path.join(DATA_CLIENT_PATH, name + '.png')

    # Guardar la imagen en el servidor
    with open(ruta_guardado, 'wb') as archivo:
        archivo.write(imagen_bytes)

    sleep(1)
    return "Imagen: " + name + " recibida y guardada exitosamente"


@app.route('/picture')
def webcam():
    cam = cv2.VideoCapture(0)

    date_str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    reservationID = request.args.get('reservationID', None)
    guest_i = request.args.get('guest_i', None)
    name = f"{reservationID}_{guest_i}_{date_str}"
    sleep(1)

    ret, image = cam.read()
    cv2.imwrite(f"{DATA_CLIENT_PATH}{name}.png", image)
    print("{DATA_CLIENT_PATH}/{name}.png")

    cam.release()
    cv2.destroyAllWindows()

    return json.dumps({'success': ret})


socketio = SocketIO(app, cors_allowed_origins="*")


# Manejador de evento para la conexión del cliente
@socketio.on('connect')
def handle_connect():
    # Iniciar el proceso de captura de video en un hilo separado
    video_thread = VideoThread()
    video_thread.start()


# Clase para el hilo de captura de video
class VideoThread(threading.Thread):
    def run(self):
        # Iniciar la captura de video desde la cámara web
        capture = cv2.VideoCapture(0)

        while True:
            ret, frame = capture.read()
            if not ret:
                break

            # Codificar el frame en formato JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)

            # Enviar el frame codificado al navegador a través de Socket.IO
            socketio.emit('video_stream', jpeg.tobytes())

        # Liberar los recursos de la cámara y detener la captura
        capture.release()


@app.route('/sendEmail')
def call_send_gmail_function():
    reservationID = request.args.get('reservationID', None)
    guest_email = request.args.get('TO', None)

    if reservationID is None or len(reservationID) == 0:
        return json.dumps({"data": "", "success": False})


    with zipfile.ZipFile(f"{DATA_CLIENT_PATH}{reservationID}.zip", "w") as zf:
        tmp = f"{DATA_CLIENT_PATH}"
        for file_name in os.listdir(tmp):
            if file_name[-4:] == ".pdf" or file_name[-4:] == ".png" or file_name[-4:] == ".jpg":
                zf.write(tmp + file_name, basename(tmp + file_name))
    attachment = f"{DATA_CLIENT_PATH}{reservationID}.zip"

    message = "Thank you for booking with us. Find attached your reservation information."
    send_message_status = gmail_send_message(message_text=message,
                                             FROM='apartamentoselsquimics@gmail.com',
                                             TO=f"{guest_email}",
                                             attachment_filename=attachment,
                                             subject=f"Clients info - APARTAMENTOS ELS QUIMICS (Girona)  - Reservation ID {reservationID}")

    send_message_status = gmail_send_message(message_text=message,
                                             FROM='apartamentoselsquimics@gmail.com',
                                             TO=f"info@quimics.com",
                                             attachment_filename=attachment,
                                             subject=f"Clients info - APARTAMENTOS ELS QUIMICS (Girona)  - Reservation ID {reservationID}")
    if not os.path.exists("C:/Clients/"):
        os.mkdir("C:/Clients/")
    shutil.copy(attachment, f"C:/Clients/{attachment.split('/')[-1]}")

    # time.sleep(3)
    if send_message_status.get('labelIds')[0] == 'SENT':
        for file_name in os.listdir(tmp):
            os.remove(f"{tmp}{file_name}")

    return send_message_status


@app.route("/parteDeViajero", methods=["GET"])
def parteDeViajero():
    try:
        # Test

        with open("C:/Opencheck/parte.txt", "r") as file:
            parte = file.read()
            newParte = str(int(parte) + 1)
        with open("C:/Opencheck/parte.txt", "w") as file:
            file.write(newParte)
        return jsonify({'success': "true", 'data': parte})
    except:
        return jsonify({'success': "false", 'data': "_"})


@app.route("/qr")
def create_qr():
    try:
        reservationID = request.args.get('reservationID', None)
        qr_img = qrcode.make(reservationID)
        qr_img.save(f"{DATA_CLIENT_PATH}QR_localizador_{reservationID}.jpg")

        return {'success': 'true', 'message': "OK"}
    except:

        return {'success': 'false', 'message': ""}


if __name__ == '__main__':
    # Flask app
    app.run(host="localhost", port=5050, debug=True)
