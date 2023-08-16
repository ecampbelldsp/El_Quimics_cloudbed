import bs4


class RedfortsBasic:
    """
    Basic class to parse the XML response from Redforts
    """
    def check_and_cast(self) -> str:
        """
        Check if all the attributes of the class are a bs4.Tag, if it is, then cast it to string, otherwise set it to None
        :return:
        """
        for attributes in self.__dict__.keys():
            if isinstance(self.__dict__[attributes], bs4.Tag):
                self.__dict__[attributes] = self.__dict__[attributes].text
            elif isinstance(self.__dict__[attributes], list) and len(self.__dict__[attributes]) != 0:

                aux = self.__dict__[attributes][0].find_all('string')
                self.__dict__[attributes] = [item.text for item in aux]
            else:
                self.__dict__[attributes] = 'None'


class ReservationRedforts(RedfortsBasic):
    """
    Class to parse the XML response with a Reservation from Redforts
    The attributes are:
        InternalReservationNumber: int
        PublicReservationNumber: int
        NumberOfAdults: int
        NumberOfChildren: int
        Customer: CustomerRedforts
        Rooms: list[RoomRedforts]
    """
    def __init__(self, reservation):
        self.InternalReservationNumber = reservation.find('InternalReservationNumber')
        self.PublicReservationNumber = reservation.find('PublicReservationNumber')
        self.NumberOfAdults = reservation.find('Adults')
        self.NumberOfChildren = reservation.find('NumberOfChildren')
        self.TotalAmountIT = reservation.find('TotalAmountIT')
        self.TotalBalanceIT = reservation.find('TotalBalanceIT')
        self.TotalPaidIT = reservation.find('TotalPaidIT')
        self.TotalVAT = reservation.find('TotalVAT')

        self.check_and_cast()

        self.Customer = CustomerRedforts(reservation.find('Customer')).__dict__
        self.Rooms = [RoomRedforts(room).__dict__ for room in reservation.find_all('Room')]


class GuestRedforts(RedfortsBasic):
    """
    Class to parse the XML response with a Guest from Redforts
    The attributes are:
        LastName: str
        SecondName: str
        FirstName: str
        PassportNumber: str
        BirthDate: str
        BirthPlace: str
        Gender: str
        DocumentCountryOfIssue: str
        PassportExpirationDay: datetime
        DocumentIssueDate: datetime
        DocumentType: str
        Nationality: str
        Occupation: str
        Email: str
        Phone: str
        SignedRegister: str
    """
    def __init__(self, guest):
        self.LastName = guest.find('LastName')
        self.SecondName = guest.find('SecondName')
        self.FirstName = guest.find('FirstName')
        self.PassportNumber = guest.find('PassportNumber')
        self.BirthDate = guest.find('BirthDate')
        self.BirthPlace = guest.find('BirthPlace')
        self.Gender = guest.find('Gender')
        self.DocumentCountryOfIssue = guest.find('DocumentCountryOfIssue')
        self.PassportExpirationDay = guest.find('PassportExpirationDay')
        self.DocumentIssueDate = guest.find('DocumentIssueDate')
        self.DocumentType = guest.find('DocumentType')
        self.Nationality = guest.find('Nationality')
        self.Occupation = guest.find('Occupation')
        self.Email = guest.find_all('Email')
        self.Phone = guest.find_all('Phone')
        self.SignedRegister = guest.find('SignedRegister')
        self.check_and_cast()


class CustomerRedforts(RedfortsBasic):
    """
    Class to parse the XML response with a Customer from Redforts
    The attributes are:
        LastName: str
        SecondName: str
        FirstName: str
        PassportNumber: str
    """
    def __init__(self, customer):
        self.LastName = customer.find('LastName')
        self.SecondName = customer.find('SecondName')
        self.FirstName = customer.find('FirstName')
        self.PassportNumber = customer.find('PassportNumber')
        self.check_and_cast()


class RoomRedforts(RedfortsBasic):
    """
    Class to parse the XML response with a Room from Redforts
    The atrributes are:
        RoomNumber: int
        RoomID: int
        RoomStatus: str
        BlockNumber: int
        Adults: int
        Children: int
        ShortDescription: str
        StartDate: datetime
        EndDate: datetime
        Guests: list[GuestRedforts]
    """
    def __init__(self, room):
        self.RoomNumber = room.find('RoomNumber')
        self.RoomID = room.find('RoomID')
        self.RoomStatus = room.find('RoomStatus')
        self.BlockNumber = room.find('BlockNumber')
        self.Adults = room.find('Adults')
        self.Children = room.find('Children')
        self.ShortDescription = room.find('ShortDescription')
        self.StartDate = room.find('StartDate')
        self.EndDate = room.find('EndDate')
        self.check_and_cast()

        self.Guests = [GuestRedforts(guest).__dict__ for guest in room.find_all('Guest')]


patter_dict = {'InternalReservationNumber': '',
               'PublicReservationNumber': '',
               'NumberOfAdults': '',
               'NumberOfChildren': '',
               'Customer': {'LastName': '',
                            'SecondName': '',
                            'FirstName': '',
                            'PassportNumber': ''},
               'Rooms': [
                   {'RoomNumber': '',
                    'RoomID': '',
                    'RoomStatus': '',
                    'RoomRate': '',
                    'BlockNumber': '',
                    'Adults': '',
                    'Children': '',
                    'ShortDescription': '',
                    'StartDate': '',
                    'EndDate': '',
                    'Guest': [
                        {'BirthDate': '',
                         'BirthPlace': '',
                         'Gender': '',
                         'DocumentCountryOfIssue': '',
                         'PassportExpirationDay': '',
                         'DocumentIssueDate': '',
                         'PassportNumber': '',
                         'DocumentType': '',
                         'Nationality': '',
                         'Occupation': '',
                         'Email': '',
                         'Phone': '',
                         'SignedRegister': '',
                         'LastName': '',
                         'SecondName': '',
                         'FirstName': '',
                         }]
                    }
               ],
               'Folio': {'FolioId': '',
                         'DepositIT': '',
                         'TotalAmountET': '',
                         'TotalAmountIT': '',
                         'TotalBalanceIT': '',
                         'TotalPaidIT': '',
                         'TotalVAT': ''}
               }

data_cloudbed_format_getReservation = {
    "adults": "",
    "balance": "",
    "children": "",
    "endDate": "",
    "guestAddress": "",
    "guestAddress1": "",
    "guestBirthDate": "",
    "guestBirthdate": "",
    "guestCellPhone": "",
    "guestCity": "",
    "guestCountry": "",
    "guestDocumentExpirationDate": "",
    "guestDocumentIssueDate": "",
    "guestDocumentIssuingCountry": "",
    "guestDocumentNumber": "",
    "guestDocumentType": "",
    "guestEmail": "",
    "guestFirstName": "",
    "guestGender": "",
    "guestID": "",
    "guestLastName": "",
    "guestName": "",
    "guestPhone": "",
    "guestState": "",
    "guestZip": "",
    "paid": "",
    "paidStatus": "",
    "reservationID": "",
    "roomID": "",
    "roomTypeID": "",
    "roomTypeName": "",
    "startDate": "",
    "total": ""
}