

class FlightDataClass():
    def __init__(self, id, icao, callsign, nacp):
        self.id = id
        self.icao = icao
        self.callsign = callsign
        self.nacp = int(nacp)