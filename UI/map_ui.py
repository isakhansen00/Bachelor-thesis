import folium

def generate_map(flight_positions):
    last_flight_id, last_points = list(flight_positions.items())[-1]  # Get the last flight's ID and points
    last_point = last_points[-1]  # Get the last point of the last flight's path

    map = folium.Map(location=last_point, zoom_start=7)

    for flight_id, points in flight_positions.items():
        folium.PolyLine(points, color='black').add_to(map)
        last_point = points[-1]  # Get the last point of the flight path
        folium.Marker(location=last_point, 
                      tooltip=points[-1], 
                      popup = 'ICAO: {}\nLongitude: {:.4f}\nLatitude: {:.4f}'.format(flight_id, last_point[0], last_point[1]), 
                      icon=folium.Icon(color="blue", prefix="fa", icon="fa-plane")).add_to(map)
    return map