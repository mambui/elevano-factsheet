from flask import Flask, Response
import os
import threading
import schedule
import time

app = Flask(__name__)
FACTSHEET_PATH = '/opt/render/project/src/factsheet.html'

def run_generate():
    from generate import generate_factsheet
    generate_factsheet()

@app.route('/')
def factsheet():
    if os.path.exists(FACTSHEET_PATH):
        with open(FACTSHEET_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/html')
    return Response("Factsheet not yet generated — please wait a few minutes.", status=503)

@app.route('/health')
def health():
    return {'status': 'ok'}

@app.route('/regenerate')
def regenerate():
    run_generate()
    return {'status': 'ok', 'message': 'Factsheet regenerated'}

def run_scheduler():
    schedule.every().day.at("01:00").do(run_generate)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Generate on startup in background
t_gen = threading.Thread(target=run_generate, daemon=True)
t_gen.start()

# Start daily scheduler
t_sched = threading.Thread(target=run_scheduler, daemon=True)
t_sched.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
