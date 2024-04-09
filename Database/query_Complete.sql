IF OBJECT_ID('FlightTrips', 'U') IS NOT NULL
    DROP TABLE FlightTrips;

IF OBJECT_ID('FlightTripPositions', 'U') IS NOT NULL
    DROP TABLE FlightTripPositions;

IF OBJECT_ID('FlightDataNew', 'U') IS NOT NULL
    DROP TABLE FlightDataNew;

IF OBJECT_ID('FlightData', 'U') IS NOT NULL
    DROP TABLE FlightData;
	
CREATE TABLE FlightTrips (
    TripID INT PRIMARY KEY IDENTITY(1,1),
    ICAO NVARCHAR(255),
    TripTimestamp INT,
);

CREATE TABLE FlightTripPositions (
    PositionID INT PRIMARY KEY IDENTITY(1,1),
    TripID INT FOREIGN KEY REFERENCES FlightTrips(TripID),
    ICAO NVARCHAR(255),
	Longitude DECIMAL(15, 12),
    Latitude DECIMAL(15, 12),
    CONSTRAINT FK_FlightTripPositions_TripID FOREIGN KEY (TripID) REFERENCES FlightTrips(TripID)
);

CREATE TABLE FlightDataNew (
	ID INT PRIMARY KEY IDENTITY(1,1),
    ICAO NVARCHAR(255),
    Callsign NVARCHAR(255),
    NACp NVARCHAR(255),
    TripID INT FOREIGN KEY REFERENCES FlightTrips(TripID),
	isprocessed bit DEFAULT 0,
	CONSTRAINT FK_FlightData_TripID FOREIGN KEY (TripID) REFERENCES FlightTrips(TripID)
);

CREATE TABLE FlightData (
	ID INT PRIMARY KEY IDENTITY(1,1),
    ICAO NVARCHAR(255),
    Callsign NVARCHAR(255),
    NACp NVARCHAR(255),
	EventProcessedUtcTime datetime NULL,
 	EventEnqueuedUtcTime datetime NULL,
 	IoTHub nvarchar(200) NULL,
	PartitionId nvarchar (3) NULL,
	isprocessed bit DEFAULT 0,
);