import folium

def generate_map(flight_positions):
    map = folium.Map(location=[65, 10], zoom_start=5)
    for flight_id, points in flight_positions.items():
        folium.PolyLine(points[1:], color='black', tooltip=flight_id).add_to(map)
        last_point = points[-1]  # Get the last point of the flight path
        folium.Marker(location=last_point, tooltip=points[0], icon=folium.Icon(color="blue", prefix="fa", icon="fa-plane")).add_to(map)
    map.save("map.html")