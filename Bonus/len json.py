import json

def count_elements_in_json(input_filepath):
    try:
        with open(input_filepath, 'r') as json_file:
            data_list = json.load(json_file)
        
        # Отримати кількість елементів у списку
        element_count = len(data_list)
        print(f"Кількість елементів у списку: {element_count}")
        return element_count
    except Exception as e:
        print(f"Помилка при обробці файлу JSON: {e}")
        return None

# Шлях до вхідного файлу JSON, який містить весь список
input_filepath = 'D:/PYTHON/@radiazioni_ionizzanti_bot/data/coordinates.json'

# Виклик функції для підрахунку кількості елементів у файлі JSON
count_elements_in_json(input_filepath)
