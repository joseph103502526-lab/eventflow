from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

VERSION = "v1"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "notification-service", "version": VERSION})

@app.route('/notify', methods=['POST'])
def notify():
    data = request.get_json() or {}
    return jsonify({
        "status": "sent",
        "to": data.get("user", "anonymous"),
        "message": data.get("message", "Your booking is confirmed."),
        "version": VERSION
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
