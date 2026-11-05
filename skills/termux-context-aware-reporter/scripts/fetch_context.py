import json, subprocess, urllib.request

def get_weather(lat=35.3039, lon=136.8031):
    url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&timezone=Asia%2FTokyo'
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode('utf-8')).get('current', {})

if __name__ == '__main__':
    weather = get_weather()
    print(json.dumps({'weather': weather}, ensure_ascii=False, indent=2))
