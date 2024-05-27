IF OBJECT_ID('FlightTrips', 'U') IS NOT NULL
    DROP TABLE FlightTrips;

IF OBJECT_ID('FlightTripPositions', 'U') IS NOT NULL
    DROP TABLE FlightTripPositions;

IF OBJECT_ID('FlightDataNew', 'U') IS NOT NULL
    DROP TABLE FlightDataNew;

IF OBJECT_ID('FlightData', 'U') IS NOT NULL
    DROP TABLE FlightData;
	
IF OBJECT_ID('TimestampedHexvalues', 'U') IS NOT NULL
    DROP TABLE TimestampedHexvalues;


IF OBJECT_ID('TDOAValues', 'U') IS NOT NULL
    DROP TABLE TDOAValues;

IF OBJECT_ID('TDOAAlerts', 'U') IS NOT NULL
    DROP TABLE TDOAAlerts;

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
	PositionTimestamp FLOAT,
    CONSTRAINT FK_FlightTripPositions_TripID FOREIGN KEY (TripID) REFERENCES FlightTrips(TripID)
);

CREATE TABLE FlightDataNew (
	ID INT PRIMARY KEY IDENTITY(1,1),
    ICAO NVARCHAR(255),
    Callsign NVARCHAR(255),
    NACp NVARCHAR(255),
    TripID INT FOREIGN KEY REFERENCES FlightTrips(TripID),
    CurrentDate DATE DEFAULT CONVERT(DATE, GETDATE()),
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
	
CREATE TABLE TimestampedHexvalues (
    ID INT PRIMARY KEY IDENTITY(1,1),
	HexValue VARCHAR(255),
    ICAO NVARCHAR(255),
    HexTimestamp BIGINT,
	DeviceID VARCHAR(255),
    isprocessed bit DEFAULT 0,
);


-- Creating the Delta_TDOA table
CREATE TABLE TDOAValues (
    id INT PRIMARY KEY IDENTITY(1,1),
    icao_address NVARCHAR(255),
    average_tdoa NVARCHAR(255),
    TripID INT FOREIGN KEY REFERENCES FlightTrips(TripID),
    timestamp DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_TDOAValues_TripID FOREIGN KEY (TripID) REFERENCES FlightTrips(TripID)
);

-- Creating the TDOAAlerts table
CREATE TABLE TDOAAlerts (
    id INT PRIMARY KEY IDENTITY(1,1),
    icao_address NVARCHAR(255),
    timestamp DATETIME DEFAULT GETDATE(),
);



"""
/*
Here are links to help you get started with Stream Analytics Query Language:
Common query patterns - https://go.microsoft.com/fwLink/?LinkID=619153
Query language - https://docs.microsoft.com/stream-analytics-query/query-language-elements-azure-stream-analytics
*/
SELECT
    ICAO,
    Callsign,
    NACp
INTO
    [flightDataOutput]
FROM
    [RaspberryPiHubGruppe24]
WHERE
    Type = 'FlightData';

SELECT
    Icao AS ICAO,
    Longitude,
    Latitude,
    PositionTimestamp
INTO
    [flightPositionData]
FROM
    [RaspberryPiHubGruppe24]
WHERE
    Type = 'FlightPosition';

SELECT
    hex_value as HexValue,
    icao_address as ICAO,
    hex_timestamp as HexTimestamp,
    device_id as DeviceID
INTO 
    [TimestampedHexvaluesDb]
FROM
    [RaspberryPiHubGruppe24]
"""