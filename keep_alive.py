from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    try:
        with open("version", "r") as f:
            version = f.read().strip()
    except:
        version = "unknown"
    return f'Discord bot ok - version: {version}'

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
