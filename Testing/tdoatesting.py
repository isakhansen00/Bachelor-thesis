import numpy as np

# Constants
c = 299792458  # Speed of light in m/s

# Given time variance factor for TOA (converted from microseconds to seconds)
time_variance_factor = 0.7 * 0.5e-6  # 0.5 microseconds

# Compute the TOA measurement standard deviation
sigma_toa = c * time_variance_factor

# Number of stations (sensors)
M = 3  # Number of stations

# Define the Q_TDOA covariance matrix for TDOA measurements
Q_TDOA = np.full((M - 1, M - 1), sigma_toa**2)
for i in range(M - 1):
    Q_TDOA[i, i] += sigma_toa**2

# ADS-B position error standard deviation (given as 40 meters for x, y, z)
sigma_adsb_position = 40  # in meters

# Define the covariance matrix for ADS-B position error
Q_ADSB = np.diag([sigma_adsb_position**2, sigma_adsb_position**2, sigma_adsb_position**2])

# Sample station positions (ECEF coordinates) and aircraft position
# These are synthetic and should be replaced with real data
station_positions = np.array([
    [3828371.0, 323486.0, 5047178.0],  # Station 1 position (ECEF)
    [3828471.0, 323586.0, 5047278.0],  # Station 2 position (ECEF)
    [3828571.0, 323686.0, 5047378.0],  # Station 3 position (ECEF)
])
aircraft_position = np.array([3828371.0, 323486.0, 5047278.0])  # Aircraft position (ECEF)

# TDOA measurement error vector with standard deviation sigma_toa
eta_tdoa = np.random.normal(0, sigma_toa, M - 1)

# Function to calculate TDOAs
def f(station_positions, aircraft_position):
    distances = np.linalg.norm(station_positions - aircraft_position, axis=1)
    toas = distances / c
    tdoas = toas[1:] - toas[0]  # Using the first station as the reference
    return tdoas

# Calculate TDOA vector with measurement noise
tdoa_vector = f(station_positions, aircraft_position) + eta_tdoa

# ADS-B observation matrix
F_ADSB = np.array([
    [1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0]
])

# Sample state vector for the aircraft at time t_n (position and velocity in ECEF)
state_vector_tn = np.array([3828371.0, 323486.0, 5047278.0, 100.0, 200.0, -50.0])  # Replace with actual state vector

# ADS-B measurement error vector with standard deviation sigma_adsb_position
eta_adsb = np.random.normal(0, sigma_adsb_position, 3)

# ADS-B encoded position with noise
x_adsb_tn = F_ADSB @ state_vector_tn + eta_adsb  # Only use the first three elements corresponding to position

# Function to calculate Jacobian F_TDOA
def jacobian_f_tdoa(station_positions, aircraft_position):
    jacobian = []
    for i in range(1, M):
        d1 = np.linalg.norm(aircraft_position - station_positions[0])
        d2 = np.linalg.norm(aircraft_position - station_positions[i])
        partials = (aircraft_position - station_positions[i]) / d2 - (aircraft_position - station_positions[0]) / d1
        jacobian.append(partials / c)
    return np.array(jacobian)

# Calculate Jacobian matrix
F_TDOA = jacobian_f_tdoa(station_positions, aircraft_position)

# Example of printing out the sample data and matrices
print("Sample station positions (ECEF):\n", station_positions)
print("\nSample aircraft position (ECEF):\n", aircraft_position)
print("\nSample state vector at time t_n:\n", state_vector_tn)
print("\nSample TDOA vector with noise:\n", tdoa_vector)
print("\nSample ADS-B encoded position with noise:\n", x_adsb_tn)
print("\nJacobian matrix F_TDOA:\n", F_TDOA)

