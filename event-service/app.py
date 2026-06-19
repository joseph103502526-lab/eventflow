from flask import Flask, jsonify

app = Flask(__name__)

VERSION = "v3-broken"

@app.route('/health')
def health():
    # 故意回傳 500，讓 readinessProbe 失敗
    return jsonify({"status": "error", "service": "event-service"}), 500

@app.route('/events')
def get_events():
    return jsonify({
        "version": VERSION,
        "events": [
            {"id": "e1", "name": "Taipei Tech Summit", "date": "2026-07-01", "seats": 200},
            {"id": "e2", "name": "GKE Workshop", "date": "2026-07-15", "seats": 50}
        ]
    })

@app.route('/events/<event_id>')
def get_event(event_id):
    return jsonify({"id": event_id, "name": "Taipei Tech Summit", "version": VERSION})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
