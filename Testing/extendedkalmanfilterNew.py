import numpy as np

# Constants
c = 299792458  # Speed of light in m/s
T = 1  # Time interval between updates (1 second for example)

threshold1 = 100
threshold2 = 20
threshold3 = 0.5

# Initial aircraft state vector (position and velocity)
state_vector_tn = np.array([3828371.0, 323486.0, 5047278.0, 100.0, 200.0, -50.0])

# Initial state covariance matrix (large uncertainties)
state_cov_tn = np.eye(6) * 1e6

station_positions = np.array([
    [3828371.0, 323486.0, 5047178.0],  # Station 1 position (ECEF)
    [3828471.0, 323586.0, 5047278.0],  # Station 2 position (ECEF)
    [3828571.0, 323686.0, 5047378.0],  # Station 3 position (ECEF)
])

# Transition matrix G for constant velocity model
G = np.array([
    [1, 0, 0, T, 0, 0],
    [0, 1, 0, 0, T, 0],
    [0, 0, 1, 0, 0, T],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1]
])

# Process noise covariance matrix W
W = np.diag([0.01, 0.01, 0.01, 0.001, 0.001, 0.001])

# ADS-B observation matrix F_ADSB (selects the position states)
F_ADSB = np.array([
    [1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0]
])

# Function to calculate TDOAs
def f(station_positions, aircraft_position):
    distances = np.linalg.norm(station_positions - aircraft_position, axis=1)
    toas = distances / c
    tdoas = toas[1:] - toas[0]
    return tdoas

# Function to calculate Jacobian F_TDOA
def jacobian_f_tdoa(station_positions, aircraft_position):
    jacobian = []
    for i in range(1, len(station_positions)):
        d1 = np.linalg.norm(aircraft_position - station_positions[0])
        d2 = np.linalg.norm(aircraft_position - station_positions[i])
        partials = (aircraft_position - station_positions[i]) / d2 - (aircraft_position - station_positions[0]) / d1
        jacobian.append(partials / c)
    return np.array(jacobian)

# Sample measurement noise (assumed standard deviations)
sigma_adsb_position = 40  # Standard deviation of ADS-B position measurements in meters
sigma_tdoa = c * 0.7 * 0.5e-6  # Standard deviation of TDOA measurements in seconds

# Covariance matrices for measurement noise
Q_ADSB = np.diag([sigma_adsb_position**2] * 3)
Q_TDOA = np.diag([sigma_tdoa**2] * (len(station_positions) - 1))

# Kalman filter prediction step

# Define synthetic ADS-B measurement vector based on initial state
# Assuming some measurement error/noise in ADS-B data
x_adsb_tn = state_vector_tn[:3] + np.random.normal(0, sigma_adsb_position, 3)

# Update the F_TDOA matrix using the function we defined earlier
F_TDOA = jacobian_f_tdoa(station_positions, state_vector_tn[:3])

# Define synthetic TDOA measurement vector based on the function f
# This should calculate the TDOA based on the true positions of the aircraft and the stations
# Here we are adding some synthetic noise to simulate measurement error
actual_tdoas = f(station_positions, state_vector_tn[:3])
measurement_noise = np.random.normal(0, sigma_tdoa, len(actual_tdoas))
z_tdoa_tn = actual_tdoas + measurement_noise

# Kalman filter update with TDOA data (measurement update)
z_tdoa_tn1 = np.array([1e-6, 1.5e-6])  # Synthetic TDOA measurements


# Kalman filter process
# 1. Prediction
state_vector_tn1_hat = G @ state_vector_tn  # Predicted state vector
state_cov_tn1_hat = G @ state_cov_tn @ G.T + W  # Predicted state covariance matrix

#print(state_cov_tn1_hat)

# 2. ADS-B Innovation test
y_adsb_tn1 = x_adsb_tn - F_ADSB @ state_vector_tn1_hat  # ADS-B innovation
R_adsb_tn1 = F_ADSB @ state_cov_tn1_hat @ F_ADSB.T + Q_ADSB  # Innovation covariance matrix
test_adsb = y_adsb_tn1.T @ np.linalg.inv(R_adsb_tn1) @ y_adsb_tn1  # Innovation test statistic
if test_adsb > threshold1:
    print("Alarm T1: ADS-B data inconsistent")

# 3. Updating with ADS-B data
K_adsb_tn1 = state_cov_tn1_hat @ F_ADSB.T @ np.linalg.inv(R_adsb_tn1)  # Kalman gain for ADS-B
state_vector_tn1 = state_vector_tn1_hat + K_adsb_tn1 @ y_adsb_tn1  # Updated state vector
state_cov_tn1 = (np.eye(6) - K_adsb_tn1 @ F_ADSB) @ state_cov_tn1_hat  # Updated state covariance matrix


#print(f"FTDOA: {F_TDOA} \n\n state_cov: {state_cov_tn1}")

# 4. TDOA Innovation test
y_tdoa_tn1 = z_tdoa_tn - f(station_positions, state_vector_tn1[:3])  # TDOA innovation (define f() accordingly)
R_tdoa_tn1 = F_TDOA @ state_cov_tn1 @ F_TDOA.T + Q_TDOA  # Innovation covariance matrix for TDOA
test_tdoa = y_tdoa_tn1.T @ np.linalg.inv(R_tdoa_tn1) @ y_tdoa_tn1  # Innovation test statistic for TDOA
if test_tdoa > threshold2:
    print("Alarm T2: TDOA data inconsistent")

# 5. Updating with TDOA measurements
if test_tdoa < threshold3:
    K_tdoa_tn1 = state_cov_tn1 @ F_TDOA.T @ np.linalg.inv(R_tdoa_tn1)  # Kalman gain for TDOA
    state_vector_tn1 = state_vector_tn1 + K_tdoa_tn1 @ y_tdoa_tn1  # Update state vector with TDOA data
    state_cov_tn1 = (np.eye(6) - K_tdoa_tn1 @ F_TDOA) @ state_cov_tn1  # Update state covariance matrix with TDOA data

# Print the updated state vector and covariance matrix
print("Updated state vector:\n", state_vector_tn1)
print("\nUpdated state covariance matrix:\n", state_cov_tn1)