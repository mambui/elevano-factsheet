from flask import Flask, send_file, Response
import os

app = Flask(__name__)

FACTSHEET_PATH = '/opt/render/project/src/factsheet.html'

@app.route('/')
def factsheet():
    if os.path.exists(FACTSHEET_PATH):
        with open(FACTSHEET_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/html')
    return Response("Factsheet not yet generated", status=404)

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
