import aiohttp
from datetime import timedelta
import hashlib
import json
import redis
from flask import Flask, request, jsonify


redis_cache_time = timedelta(hours=1)
special_characters = '"!@#$%^&*()-+?_=,<>/'
target_domain = "local-qa.staples.com"
application_path = "/services/printing"
cookie_name = "SPLUS.Phoenix.Site.Auth"
app = Flask(__name__)
redis_cache_db = redis.Redis(host="myredis.pnistaging.com", port=6379, db=7)
cookies = None


def get_cookies():
    cookie_b_string = redis_cache_db.get("Site.TestCookies")
    if cookie_b_string is None:
        return None

    cookie_string = str(cookie_b_string, 'utf-8')
    global cookies
    cookies = {}
    cookies["from_proxy"] = "true"
    items = cookie_string.split("; ")
    for itm in items:
        entry = itm.split("=")
        if len(entry) >= 2 and not any(c in special_characters for c in entry[0]):
            cookies[entry[0]] = entry[1]
    return None


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
async def catch_all(path):
    forward_path = request.full_path if len(request.args) else request.path
    get_cookies()

    if request.method == "POST":
        body = request.get_json()
        async with aiohttp.ClientSession(cookies=cookies) as session:
                try:
                    async with session.post(f"https://{target_domain}/{forward_path}",
                                            json=body, ssl=False, timeout=None) as response:
                        if response.status == 200:
                            data = await response.json()
                            return jsonify(data)
                        else:
                            return str(response.status), response.status
                except aiohttp.ClientError as ce:
                    return str(ce)
                except:
                    return "Server Error", 500
    else:
        async with aiohttp.ClientSession(cookies=cookies) as session:
                try:
                    async with session.get(f"https://{target_domain}/{forward_path}",
                                           ssl=False, timeout=None) as response:
                        if response.status == 200:
                            data = await response.json()
                            return jsonify(data)
                        else:
                            return str(response.status), response.status
                except aiohttp.ClientError as ce:
                    return str(ce)
                except:
                    return "Server Error", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=6500, threaded=True)
