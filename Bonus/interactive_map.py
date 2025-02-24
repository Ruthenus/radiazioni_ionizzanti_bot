import folium
from folium.plugins import Search

# Створюємо карту
m = folium.Map(location=[20, 0], zoom_start=2)  # Центр світу

# Приклад міток з даними
locations = [
    {"name": "Київ", "lat": 50.4501, "lon": 30.5247, "info": "Столиця України"},
    {"name": "Лондон", "lat": 51.5074, "lon": -0.1278, "info": "Столиця Великої Британії"},
    {"name": "Нью-Йорк", "lat": 40.7128, "lon": -74.0060, "info": "Місто в США"},
    {"name": "Токіо", "lat": 35.6762, "lon": 139.6503, "info": "Столиця Японії"}
]

# Додаємо мітки на карту
for location in locations:
    folium.Marker(
        [location["lat"], location["lon"]],
        popup=folium.Popup(f"{location['name']}: {location['info']}", max_width=300),
    ).add_to(m)

# Збереження карти в HTML файл
m.save("interactive_map.html")
