class FlightDataClass():
    def __init__(self, id, icao, callsign, nacp, currentdate=None):
        self.id = id
        self.icao = icao
        self.callsign = callsign
        self.nacp = int(nacp)
        self.currentdate = currentdate