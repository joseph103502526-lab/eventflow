from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import uuid

app = Flask(__name__)
metrics = PrometheusMetrics(app)

VERSION = "v1"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "booking-service", "version": VERSION})

@app.route('/bookings', methods=['GET'])
def get_bookings():
    return jsonify({"version": VERSION, "bookings": []})

@app.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json() or {}
    return jsonify({
        "booking_id": str(uuid.uuid4()),
        "event_id": data.get("event_id", "e1"),
        "user": data.get("user", "anonymous"),
        "status": "confirmed",
        "version": VERSION
    }), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
