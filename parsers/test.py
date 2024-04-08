import os
import csv
import json
import requests
import cfscrape
import traceback
from tqdm import tqdm
from time import sleep

PAUSE_TIME = 7  # Увеличиваем интервалы отправки запросов — борьба с капчей
CSV_NUMBER = 'test'  # Постфикс названия создаваемой таблицы
CSV_PATH = os.path.normpath(os.path.join(os.getcwd(), 'csv'))  # Создаём папку 'csv' для записи создаваемых таблиц
if not os.path.exists(CSV_PATH):  # ...если такой не существовало ранее
    os.mkdir(CSV_PATH)
    print(f'Folder {CSV_PATH} has been created!')

# Словарь некоторых городов с номерами, объявления по которым можно искать на Циан
regions = {
    'msk': 1,  # Москва
    'spb': 2,  # Санкт–Петербург
    'ekb': 4743,  # Екатеринбург
    'nsk': 4897,  # Новосибирск
    'kzn': 4777,  # Казань
    'nng': 4885,  # Нижний Новгород
}

# Названия столбцов (header) будущей таблицы,
# которые связываются с отобранными признаками в create_table()
dataset = [
    [
        'region',
        'address',
        'price',
        'total_area',
        'kitchen_area',
        'living_area',
        'rooms_count',
        'floor',
        'floors_number',
        'build_date',
        'isСomplete',
        'complitation_year',
        'house_material',
        'parking',
        'decoration',
        'balcony',
        'longitude',
        'latitude',
        'passenger_elevator',
        'cargo_elevator',
        'metro',
        'metro_distance',
        'metro_transport',
        'district',
        'is_apartments',
        'is_auction',
        'repair',
        'with_furniture',
        'windows_type'
    ]
]


# Функция для обработки пропусков и булевых значений
def add_attr(attr):
    if isinstance(attr, bool):
        return int(attr)

    return attr if attr is not None else 'empty'


# Функция для создания экземпляра класса запросов
def get_session():
    # Передаваемые параметры для экземпляра (как получить — туториал ниже)

    headers = {
        'authority': 'api.cian.ru',
        'accept': '*/*',
        'accept-language': 'ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        # 'cookie': '_CIAN_GK=441c9cc0-20d7-402e-b6f1-9f5b4e163dc3; __cf_bm=ZMUzypkDtpWXjX1xKpH_a8I99QowM1i.kYoELZDGkvw-1710764995-1.0.1.1-EHC0dvRYumKXpEzVYSBLHJbLA1k6CgKWDgRe.CFtulUMKNRBdvR6_nuVtCGSS_dcvz9n8wZ.53yGn4NHdtH3cQ; login_mro_popup=1; session_region_id=1; session_region_name=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0; forever_region_id=1; forever_region_name=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0; session_main_town_region_id=1',
        'origin': 'https://www.cian.ru',
        'referer': 'https://www.cian.ru/',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    session = requests.Session()
    session.headers = headers
    return cfscrape.create_scraper(sess=session)  # cfscrape — обход защиты от ботов Cloudflare


# Записываем всё в файл формата .csv
def recording_table():
    try:
        with open(os.path.join(CSV_PATH, f'data_{CSV_NUMBER}.csv'), mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for row in dataset:
                writer.writerow(row)

        print(f'The dataset is written in file "data_{CSV_NUMBER}.csv"')
        return

    except Exception as error:
        print('Recording error!\n', traceback.format_exc())
        sleep(PAUSE_TIME)
        return


# Получаем формат json (питоновский dict) из нашего запроса Response
def get_json(session, region_name, cur_page):
    # Параметры, которые отображаются в URL-запросе
    # https://www.cian.ru/cat.php/?deal_type=sale&engine_version=2&offer_type=flat&region=1&
    # room1=1&room2=1&room3=1&room4=1&room5=1&room6=1
    json_data = {
        'jsonQuery': {
            '_type': 'flatsale',
            'engine_version': {
                'type': 'term',
                'value': 2,
            },
            'region': {
                'type': 'terms',
                'value': [
                    regions[region_name],
                ],
            },
            'room': {
                'type': 'terms',
                'value': [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                ],
            },
            'page': {
                'type': 'term',
                'value': cur_page,
            },
            # Можно задавать дополнительные атрибуты фильтрации объявлений

            # 'price': {
            #     'type': 'range',
            #     'value': {
            #         'gte': min_price,
            #         'lte': max_price,
            #     },
            # },
        },
    }

    # Получаем запрос с заданными параметрами
    # Возвращаемое значение — bytes
    try:
        response = session.post('https://api.cian.ru/search-offers/v2/search-offers-desktop/',
                                json=json_data)

    except:
        return f'oops! Error {response.status_code}'

    # Получаем формат .json
    if (
            response.status_code != 204 and
            response.headers["content-type"].strip().startswith("application/json")
    ):
        try:
            return response.json()
        except ValueError:
            return f'oops! ValueError!'


def create_table(region_name='spb', start_page=1, end_page=55, number_of_samples=10000):
    # В Циан выдаются страницы в диапазоне [1, 54]

    if start_page < 1:
        start_page = 1
    if end_page > 55:
        end_page = 55

    session = get_session()

    cnt_samples = 0
    for cur_page in tqdm(range(start_page, end_page)):  # tqdm — выводим прогресс выполнения цикла
        if cnt_samples >= number_of_samples:
            break

        data = get_json(session, region_name, cur_page)
        if data is None:
            print('oops! Captcha!')
            return
        if isinstance(data, str):
            print(data)
            continue

        # Отбираем из большого словаря то, что нам нужно (можно и больше — смотри data)
        for item in data['data']['offersSerialized']:
            cur_item = [
                region_name,
                add_attr(item["geo"]["userInput"]),
                add_attr(item['bargainTerms']['priceRur']),
                add_attr(item.get('totalArea')),
                add_attr(item.get('kitchenArea')),
                add_attr(item.get('livingArea')),
                add_attr(item.get('roomsCount')),
                add_attr(item.get('floorNumber')),
                add_attr(item['building'].get('floorsCount')),
                add_attr(item['building'].get('buildYear')),
                add_attr(item['building']['deadline']['isComplete'] if item['building'].get(
                    'deadline') is not None else None),
                add_attr(
                    item['building']['deadline']['year'] if item['building'].get('deadline') is not None else None),
                add_attr(item['building'].get('materialType')),
                add_attr(item['building']['parking']['type'] if item['building'].get('parking') is not None else None),
                add_attr(item.get('decoration')),
                add_attr(item.get('balconiesCount')),
                add_attr(item['geo']['coordinates']['lng']),
                add_attr(item['geo']['coordinates']['lat']),
                add_attr(item['building'].get('passengerLiftsCount')),
                add_attr(item['building'].get('cargoLiftsCount')),
                add_attr(','.join([str(x['name']) for x in item['geo']['undergrounds'] if x is not None])),
                add_attr(','.join([str(x['time']) for x in item['geo']['undergrounds'] if x is not None])),
                add_attr(','.join([str(x['transportType']) for x in item['geo']['undergrounds'] if x is not None])),
                add_attr(','.join([str(x['name']) for x in item['geo']['districts'] if x is not None])),
                add_attr(item.get('isApartments')),
                add_attr(item.get('isAuction')),
                add_attr(item.get('repair')),
                add_attr(item.get('with_furniture')),
                add_attr(item.get('windows_type'))
            ]

            if cur_item not in dataset:
                dataset.append(cur_item)
                cnt_samples += 1
            else:
                continue

            if cnt_samples >= number_of_samples:
                break

        print(f'{cnt_samples} / {number_of_samples} | page: {cur_page}')
        sleep(PAUSE_TIME)

    recording_table()
    return


create_table()