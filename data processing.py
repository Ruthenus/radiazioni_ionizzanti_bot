# ФІНАЛЬНИЙ ПРОЄКТ з дисципліни PYTHON Core
# Пре-процесинг великих даних для телеграм-бота "РАДІАЦІЯ В СВІТІ"

# Виконав студент гр. СПР411
# Комп'ютерної Академії IT STEP
# Качуровський Р.Р.

# Одеса 2025

import pandas  # Python Data Analysis Library
import json
import math
import time
import sys
import os
import threading  # https://docs.python.org/uk/3.13/library/threading.html

# Повний набір радіаційних даних Safecast, оновлюється щодня,
# можна завантажити негайно (обережно, великий архів!) звідси:
# https://api.safecast.org/system/measurements.tar.gz

# Нижче РЕФАКТОРИНГ Week 9 Homework.py

"""
Раніше було визначено індекси та назви колонок CSV набору:
https://docs.python.org/3/library/functions.html#enumerate
https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.columns.html

        0 Captured Time
        1 Latitude
        2 Longitude
        3 Value
        4 Unit
        5 Location Name
        6 Device ID
        7 MD5Sum
        8 Height
        9 Surface
        10 Radiation
        11 Uploaded Time
        12 Loader ID
"""


def process_coordinates(filepath, chunk_size=1_000_000):
    """
    Функція для попередньої обробки (пре-процесингу) великого CSV файлу
    замірів радіаційного фону по всьому світові (історичний зріз)
    з метою отримання координат станцій радіаційного моніторингу.

    :param filepath: шлях до CSV файлу
    :param chunk_size: розмір шматка CSV файлу, який обробляємо за раз
    :return: список координат у вигляді кортежів (широта, довгота)

    Щоб зменшити обсяг результату та виявити саме унікальні координати
    (без похибок GPS), виконано округлення до першого знаку після коми.
    ШІ знає, що 0,1 градус довготи (на екваторі) та 0,1 градус широти 
    (у будь-якій точці земної кулі) дорівнюють приблизно 11,1 км.
    """

    # Установимо тип даних для стовпців, де під час першого проходу
    # програми (див. домашню роботу) виявлено змішані типи:
    dtype = {
        5: str,
        9: str,
        10: str,
    }

    # Щоб автоматично видалити дублікати, ініціалізуємо множину Set:
    coord_tuples = set()

    try:  # успішно зчитати CSV з рекомендованими параметрами
        df = pandas.read_csv(filepath, header=0, chunksize=chunk_size,
                             dtype=dtype, low_memory=False)
        for chunk in df:  # DataFrame
            chunk["Latitude"] = chunk["Latitude"].round(1)
            chunk["Longitude"] = chunk["Longitude"].round(1)
            # Множина кортежів (широта, довгота) для поточного шматка:
            unique_chunk = set(zip(chunk["Latitude"], chunk["Longitude"]))
            # Шматок за шматком додаємо до загальної множини
            coord_tuples.update(unique_chunk)
        return list(coord_tuples)

    except FileNotFoundError:
        print("\nERROR1: вихідний файл CSV не знайдено за вказаним шляхом!")
    # https://pandas.pydata.org/docs/reference/testing.html
    except pandas.errors.ParserError as e:
        print("\nERROR2: НЕ ВДАЛОСЯ ОБРОБИТИ НАБІР РАДІАЦІЙНИХ ДАНИХ")
        print(f"Деталі помилки: {e}")
    except pandas.errors.EmptyDataError as e:
        print("\nERROR3: зустрічаються порожні дані або заголовок!")
        print(f"Деталі помилки: {e}")
    except Exception as e:
        print("\nERROR4: сталася непередбачена помилка.")
        print(f"Детально: {e}")


def save_to_json(data, output_file):
    """
    Функція для збереження результату обробки CSV файлу в JSON файл.

    :param data: дані, які потрібно зберегти
    :param output_file: шлях до файлу для збереження
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print("\nERROR5: не вдалося відкрити JSON файл для запису!")
        print(f"Деталі помилки: {e}")
    except Exception as e:
        print("\nERROR6: сталася непередбачена помилка.")
        print(f"Детально: {e}")


def remove_nan_from_json(input_file, output_file):
    """
    Функція для очищення JSON файлу від нечислових значень.

    :param input_file: шлях до вхідного JSON файлу
    :param output_file: шлях до вихідного очищеного JSON файлу
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Функція для перевірки, чи є в списку "Not a number"
        def is_valid_coordinates(coord):
            return all(not math.isnan(x) for x in coord)

        # Фільтруємо дані: залишаємо тільки валідні координати
        filtered_data = [coord for coord in data if
                         is_valid_coordinates(coord)]

        # Зберігаємо очищені дані в новий файл
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, indent=4)
        print(f"\nРезультат збережено у файл {output_file}")

    except FileNotFoundError:
        print("\nERROR7: файл JSON не знайдено за вказаним шляхом!")
    except json.JSONDecodeError as e:
        print("\nERROR8: не вдалося прочитати JSON файл '{input_file}'.")
        print(f"Деталі помилки: {e}")
    except Exception as e:
        print("\nERROR9: сталася непередбачена помилка.")
        print(f"Детально: {e}")


def timer():
    """Вирішення проблеми відображення часу екзекуції."""
    start_time = time.time()
    while not stop_event.is_set():
        execution_time = time.time() - start_time
        minutes, seconds = divmod(execution_time, 60)
        # sys.stdout.write записує рядок безпосередньо в термінал без
        # символу нового рядка – для повторного оновлення рядка
        sys.stdout.write(
            f"\rМинуло часу: {int(minutes)} хв {seconds:.1f} с...")
        sys.stdout.flush()  # примусово записує в термінал негайно
        time.sleep(0.2)  # створення паузи між оновленнями


# Ініціалізація події для зупинки таймера
stop_event = threading.Event()


def main():
    """
    Головна функція програми пре-процесингу радіаційних даних
    """
    try:
        # Запускаємо функцію "таймер" у окремому потоці
        timer_thread = threading.Thread(target=timer)  # це ООП...
        timer_thread.start()

        # Відносний шлях, де збережено розархівований для обробки архів:
        filepath = "data/measurements-out.csv"
        # Куди зберегти координати станцій радіаційного моніторингу:
        output_file = "data/coordinates.json"
        # шляхи відносно розташування програми data processing.py

        # Встановлюємо поточний робочий каталог як теку, де знаходиться
        # програма data processing.py, щоб запрацювали відносні шляхи:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_directory, filepath)
        output_file = os.path.join(current_directory, output_file)
        # https://docs.python.org/3/library/os.path.html

        # Основні операції
        unique_coords = process_coordinates(filepath)
        save_to_json(unique_coords, output_file)
        remove_nan_from_json(output_file, output_file)

        # Зупинка таймера
        stop_event.set()
        timer_thread.join()

    except KeyboardInterrupt:  # якщо що натиснути в терміналі Ctrl + C
        stop_event.set()
        timer_thread.join()
        print("\nПрограму завершено!")
        sys.stdout.flush()


if __name__ == '__main__':
    main()
