# ФІНАЛЬНИЙ ПРОЄКТ з дисципліни PYTHON Core
# Телеграм-бот "РАДІАЦІЯ В СВІТІ" within the framework AsyncIOTelegram

# Виконав студент гр. СПР411
# Комп'ютерної Академії IT STEP
# Качуровський Р.Р.

# Одеса 2025


import logging
import json
import os
import requests
import asyncio  # https://docs.python.org/uk/3.13/library/asyncio.html
# https://docs.aiogram.dev/en/dev-3.x/
from aiogram import Bot, Dispatcher, types
# https://docs.aiogram.dev/uk-ua/latest/
from aiogram.filters import Command
from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter
from math import radians, sin, cos, sqrt, asin
from datetime import datetime
from dotenv import load_dotenv


# Заводимо журнал
logging.basicConfig(level=logging.INFO)  # а було DEBUG !
# https://docs.python.org/3/library/logging.html#logging.basicConfig

# Операції з токеном телеграм-бота "РАДІАЦІЯ В СВІТІ"
# https://pypi.org/project/python-dotenv/
load_dotenv()
# https://docs.python.org/3/library/os.html#os.getenv
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    # https://docs.python.org/3/library/logging.html#logging.error
    logging.error("\tТокен не знайдено! Перевірте файл .env")
    exit(1)  # Завершуємо програму, якщо токен відсутній
else:
    # https://docs.python.org/3/library/logging.html#logging.info
    logging.info("\tТокен переписано з файлу .env")


def load_coordinates_from_json(filepath="data/coordinates.json"):
    """
    Завантажує в пам'ять з файлу JSON список координат, де вимірювали
    радіаційне випромінювання, – результат програми data processing.py

    :param filepath: відносний шлях до JSON файлу
    :return: список списків координат у форматі [широта, довгота]:
        [
            [latitude1, longitude1],
            [latitude2, longitude2],
            ...
        ]
    :return: порожній список у разі помилки завантаження даних.
    """
    # Вирішуємо проблему з відносним шляхом:
    current_directory = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_directory, filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            coordinates = json.load(f)
        logging.info("\tУспішне завантаження координат!")
        return coordinates  # [0] – широта, [1] – довгота
    except Exception as e:
        logging.error(f"\tПомилка завантаження координат з файлу: {e}")
        return []


# Відразу завантажуємо дані в пам'ять для швидшої роботи телеграм-бота
stations = load_coordinates_from_json()  # станції радіаційного контролю


# https://geopy.readthedocs.io/en/stable/
# geopy makes it easy for Python developers to locate the coordinates
# of addresses, cities, countries, and landmarks across the globe
# using third-party geocoders and other data sources.


async def get_coordinates(location_name):
    """
    Отримує координати для заданого місця, використовуючи сервіс geopy.
    Функція здійснює асинхронний запит до геокодера Nominatim та
    повертає широту і довготу місця, назву якого можна ввести довільно.

    :param: location_name (str)
    Назва місця або адреса, для якої необхідно отримати координати.
    :return: lat, lon (tuple)
    Кортеж, що містить широту та довготу місця. Якщо координати не
    знайдено або якщо під час запиту до геокодера виникає помилка,
    повертається (None, None).
    """
    logging.info(f"\tОтримуємо координати для місця: {location_name}")
    # https://geopy.readthedocs.io/en/stable/#geopy.geocoders.Nominatim.geocode
    try:
        # Синтаксис асинхронного запиту згідно з документацією geopy:
        # https://geopy.readthedocs.io/en/stable/#async-mode
        async with Nominatim(user_agent="radiazioni_ionizzanti_bot",
                             adapter_factory=AioHTTPAdapter) as geolocator:
            # Мови для геокодування у порядку зменшення пріоритету:
            languages = ["uk", "en", "de", "ro", "it"]
            location = await geolocator.geocode(location_name,
                                                language=languages)
        if location:
            # https://geopy.readthedocs.io/en/stable/#geopy.location.Location
            lat = round(location.latitude, 2)
            lon = round(location.longitude, 2)
            logging.info(
                f"\tЗнайдено координати для {location_name}: ({lat}, {lon})")
            return lat, lon
        else:
            # https://docs.python.org/3/library/logging.html#logging.warning
            logging.warning(f"\tНе знайдено координат місця: {location_name}")
            return None, None
    except Exception as e:
        logging.error(f"\tПомилка під час запиту до geopy: {e}")
        return None, None


async def haversine(lat1, lon1, lat2, lon2):
    """
    Обчислює відстань між двома точками на поверхні Землі за допомогою
    формули гаверсинуса – однієї з рідкісних тригонометричних функцій.
    https://en.wikipedia.org/wiki/Haversine_formula
    https://www.themathdoctors.org/distances-on-earth-2-the-haversine-formula/

    :param: lat1 (float) широта першої точки (в градусах)
    :param: lon1 (float) довгота першої точки (в градусах)
    :param: lat2 (float) широта другої точки (в градусах)
    :param: lon2 (float) довгота другої точки (в градусах)
    :return: distance (float)
    Відстань між двома точками на поверхні Землі в кілометрах.
    """
    # https://docs.python.org/3/library/logging.html#logging.debug
    logging.debug(f"\tОбчислюємо відстань між точками: "
                  f"({lat1}, {lon1}) та ({lat2}, {lon2})")

    R = 6371  # середній радіус планети Земля в кілометрах
    lat1 = radians(lat1)  # перетворення градусів у радіани
    lat2 = radians(lat2)
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)

    # Обчислення гаверсинуса – квадрата півсинуса великої дуги:
    havTheta = sin(dLat / 2)**2 + cos(lat1) * cos(lat2) * sin(dLon / 2)**2
    # Кутова відстань по великому колу
    c = 2 * asin(sqrt(havTheta))
    # Відстань між двома точками земної поверхні в кілометрах
    distance = round(R * c, 1)

    logging.debug(f"\tОбчислена відстань: {distance} км")
    return distance


async def get_latest_measurement(latitude, longitude, distance=10_000):
    """
    Отримує найсвіжіше вимірювання радіації з сервісу Safecast API
    поблизу заданих координат на відстані, що не перевищує 10 км.
    Функція повертає значення та одиницю останнього вимірювання, час
    його захоплення, а також точні координати станції радіаційного
    моніторингу для подальшого визначення адреси вимірювання. Вибране
    значення distance = 10 000 м враховує похибку округлення координат
    з файлу coordinates.json до першого знака після коми та, власне,
    дозволяє отримати масив даних про радіацію після запиту GET до API.

    :param latitude (float) широта для запиту до Safecast API
    :param longitude (float) довгота для запиту до Safecast API
    :param distance (float) радіус вибірки даних про радіацію в метрах
    :return: tuple (value, unit, captured_at, latitude, longitude), де:
        – "value": останнє значення вимірювання
        – "unit": "cpm" (кількість імпульсів за хвилину) або "usv"
        (мікрозіверт на годину) – одиниці вимірювання радіаційного
        випромінювання, коефіцієнт перетворення залежить від типу
        застосовуваного лічильника Гейгера
        – "captured_at": час, коли було зроблено це вимірювання, у
        форматі ISO 8601
        – "latitude", "longitude": точні координати станції
        Див. форму відповіді на запит до Safecast API
        https://api.safecast.org/measurements.json?distance=100&latitude=34.5&longitude=135.5
        Якщо дані не знайдено, поверне (None, None, None, None, None).
    """
    logging.info(f"\tОтримання вимірів за координатами "
                 f"({latitude}, {longitude})")

    # Формування адреси для запиту api.safecast.org/en-US
    url = f"https://api.safecast.org/measurements.json?distance={distance}&latitude={latitude}&longitude={longitude}"

    try:
        # https://requests.readthedocs.io/en/latest/api/#requests.request
        response = requests.get(url)
        # https://requests.readthedocs.io/en/latest/api/#requests.Response.status_code
        if response.status_code == 200:
            # https://requests.readthedocs.io/en/latest/api/#status-code-lookup

            measurements = response.json()

            # Знайдемо найсвіжіше вимірювання за датою
            if measurements:
                # https://docs.python.org/3/library/functions.html#max
                latest_measurement = max(
                    measurements,
                    key=lambda x: datetime.fromisoformat(x["captured_at"])
                )  # https://docs.python.org/3/library/datetime.html#datetime.date.fromisoformat

                logging.info(
                    f"""\tОтримано вимір радіаційного випромінювання:
                    {latest_measurement["value"]} {latest_measurement["unit"]}
                    мітка часу {latest_measurement["captured_at"]}
                    широта {latest_measurement["latitude"]}
                    довгота {latest_measurement["longitude"]}"""
                )
                return (latest_measurement["value"],
                        latest_measurement["unit"],
                        latest_measurement["captured_at"],
                        latest_measurement["latitude"],
                        latest_measurement["longitude"]
                        )
                # думав про переведення імпульсів у мікрозіверти
            else:
                logging.warning(
                    f"\tНемає даних для координат ({latitude}, {longitude})")
                return None, None, None, None, None
        else:
            logging.error(
                f"\tПомилка в разі запиту до API: {response.status_code}")
            return None, None, None, None, None
    except Exception as e:
        logging.error(f"\tЗагальна помилка під час запиту до API: {e}")
        return None, None, None, None, None


async def reverse_geocode(lat, lon):
    """
    Виконує зворотне геокодування: отримує адресу для заданих координат.
    Функція здійснює асинхронний запит до геокодера Nominatim та повертає
    адресу для заданих широти та довготи.

    :param lat: (float) широта локації
    :param lon: (float) довгота локації
    :return: address (str)
    Адреса, що відповідає заданим координатам. Якщо адреса не знайдена,
    або сталася помилка, повертається None.
    """
    logging.info(f"\tВиконуємо зворотне геокодування для координат: "
                 f"({lat}, {lon})")

    try:
        # Асинхронний запит до геокодера на зворотне геокодування:
        async with Nominatim(user_agent="radiazioni_ionizzanti_bot",
                             adapter_factory=AioHTTPAdapter) as geolocator:
            # https://geopy.readthedocs.io/en/stable/#geopy.geocoders.Nominatim.reverse
            location = await geolocator.reverse((lat, lon), language="uk")

        if location:
            # https://geopy.readthedocs.io/en/stable/index.html?highlight=address#geopy.location.Location.address
            address = location.address
            logging.info(f"\tЗнайдено адресу для координат ({lat}, {lon}): "
                         f"{address}")
            return address
        else:
            logging.warning(
                f"\tНе знайдено адреси для координат ({lat}, {lon})")
            return None
    except Exception as e:
        logging.error(f"\tПомилка під час запиту до geopy: {e}")
        return None


# Створення об'єктів для бота та диспетчера
bot = Bot(token=TOKEN)  # https://docs.aiogram.dev/en/stable/api/bot.html
dp = Dispatcher()  # https://docs.aiogram.dev/en/stable/dispatcher/dispatcher.html

# Обробник команди /start


async def start(message: types.Message):
    """
    Обробляє команду /start, яка була надіслана користувачем.
    Коли користувач надсилає команду /start, бот реагує, надсилаючи
    привітальне повідомлення, яке містить інструкцію для подальших дій.
    Також записується інформація в лог про отриману команду
    з ідентифікатором користувача.

    Аргумент:
        message (types.Message): Повідомлення, яке надіслав користувач,
        що містить команду /start.
    """

    logging.info(
        f"Отримано команду /start від користувача {message.from_user.id}")
    # https://docs.aiogram.dev/en/latest/api/types/message.html#aiogram.types.message.Message.from_user
    welcome_message = (
        "Напиши найточніше локацію, щоб дізнатися про радіацію! "
        "Раджу OpenStreetMap Nominatim"
    )
    # https://docs.aiogram.dev/en/latest/api/types/message.html#aiogram.types.message.Message.answer
    await message.answer(welcome_message)


# Обробник текстових повідомлень (адреса локації)

async def location_address(message: types.Message):
    # https://docs.aiogram.dev/en/dev-3.x/api/types/message.html#aiogram.types.message.Message.text
    location_address = message.text.strip()
    logging.info(f"Отримано адресу локації від користувача "
                 f"{message.from_user.id}: {location_address}")

    # Отримуємо координати для локації
    lat, lon = await get_coordinates(location_address)

    if lat is None or lon is None:
        await message.answer(f"Не вдалося знайти координати для локації "
                             f"{location_address}. Спробуйте ще раз.")
        return

    nearest_stations = []

    # Знайдемо 4 найближчі до локації станції радіаційного контролю
    for station in stations:
        distance = await haversine(lat, lon, station[0], station[1])
        nearest_stations.append((station, distance))

    # Сортуємо всі станції за відстанню та вибираємо 4 найближчі
    nearest_stations.sort(key=lambda x: x[1])  # [0] координати
    # https://docs.python.org/3.13/library/stdtypes.html#list.sort
    nearest_stations = nearest_stations[:4]

    all_measurements = []

    # Перевірка для кожної з 4 найближчих станцій
    for station, _ in nearest_stations:  # ігноруємо distance, тому _
        lat_station, lon_station = station[0], station[1]
        latest = await get_latest_measurement(lat_station, lon_station)
        value, unit, captured_at, lat_station, lon_station = latest

        if value is not None:
            # Перетворюємо captured_at з ISO формату на об'єкт
            # datetime для кращої роботи з часом.
            captured_at_dt = datetime.fromisoformat(captured_at)
            all_measurements.append((station, value, unit, captured_at_dt))

    # Сортуємо вимірювання за часом (найновіші зверху)
    # all_measurements.sort(key=lambda x: x[3], reverse=True)

    # Формуємо 4 повідомлення для найближчих станцій
    # Перебираємо перші 4 елементи з колекції all_measurements,
    # де кожен елемент є кортежем з даними для станції
    # (координати, значення, одиниця вимірювання та час вимірювання)
    few_measurements = enumerate(all_measurements[:4])  # задовгий рядок
    for i, (station, value, unit, captured_at) in few_measurements:
        station_name = await reverse_geocode(station[0], station[1])
        # lat_station, lon_station = station[0], station[1]
        response = f"З архіву станції радіаційного контролю №{i + 1}:\n"
        response += f"Адреса: {station_name}\n"
        response += f"Найсвіжіший запис: {value} {unit}\n"
        response += f"Час реєстрації: " + \
            f"{captured_at.strftime('%Y-%m-%d %H:%M:%S')}"

        # Відправляємо повідомлення для кожної станції
        await message.answer(response)


# Основна функція для запуску бота

async def main():
    # Реєструємо обробник для команди "/start".
    # Коли користувач відправить /start, буде викликано функцію start.
    dp.message.register(start, Command("start"))
    # Реєструємо обробник для повідомлень з адресою локації.
    # Коли користувач напише адресу, буде викликано location_address.
    dp.message.register(location_address)

    # Запускаємо бота та починаємо отримувати повідомлення
    # від користувачів. Функція start_polling відповідає за запуск бота
    # та обробку вхідних повідомлень.
    await dp.start_polling(bot)

# Основна точка входу в програму.
# Це перевірка, чи є цей файл головним (не імпортованим)
if __name__ == '__main__':
    # Для запуску асинхронної функції main використовуємо asyncio.run().
    # Це необхідно, оскільки в Python асинхронні функції потрібно
    # запускати через asyncio.
    asyncio.run(main())
