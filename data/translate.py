import requests


# функция для получения актуального курса валют
def latest():
    app_id = '085ee583e286490db6abbdd3dfbb57a7'
    request_url = 'https://openexchangerates.org/api/latest.json'
    req = f"{request_url}?app_id={app_id}"
    response = requests.get(req)

    if response.status_code == 200:
        return {
            'USD': 1,
            **response.json()['rates']
        }
    return {}
