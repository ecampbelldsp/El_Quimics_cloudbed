import requests
from zeep import Client, Settings
from zeep.transports import Transport


class BaseSOAPClient:
    def __init__(self, descriptor):
        sesion = requests.Session()
        sesion.verify = False

        settings = Settings(strict=False, xml_huge_tree=True)
        transport = Transport(session=sesion, timeout=10)
        self.client = Client(descriptor, settings=settings, transport=transport)


class GuestsWebService(BaseSOAPClient):
    def __init__(self, host, operator_name, operator_password):
        self.descriptor = f"https://{host}:8181/TesaHotelPlatform/GuestsWebService?wsdl"
        #self.descriptor = "https://localhost:8181/ServerPlatform/modern/es/#/"
        self.operator_name = operator_name
        self.operator_password = operator_password
        super().__init__(self.descriptor)

    def check_in(self, guest_info):
        response = self.client.service.checkin(operatorName=self.operator_name,
                                               operatorPassword=self.operator_password,
                                               guestData=guest_info)
        return response

    def check_in_copy(self, guest_info):
        response = self.client.service.checkinCopy(operatorName=self.operator_name,
                                                   operatorPassword=self.operator_password,
                                                   guestData=guest_info)
        return response

    def check_out(self, room_id):
        response = self.client.service.checkout(operatorName=self.operator_name,
                                                operatorPassword=self.operator_password,
                                                roomId=room_id)
        return response
