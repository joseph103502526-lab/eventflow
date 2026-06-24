const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const client = require('prom-client');

const app = express();

// 建立 metrics registry 並啟用預設的 Node.js metrics
const register = new client.Registry();
client.collectDefaultMetrics({ register });

// 自訂 HTTP request counter
const httpRequestCounter = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'path', 'status'],
  registers: [register],
});

// middleware：每個 request 完成後記錄一次
app.use((req, res, next) => {
  res.on('finish', () => {
    httpRequestCounter.inc({
      method: req.method,
      path: req.path,
      status: res.statusCode,
    });
  });
  next();
});

// /metrics endpoint 給 Prometheus 抓
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

const EVENT_SERVICE_URL = process.env.EVENT_SERVICE_URL || 'http://event-service:5001';
const BOOKING_SERVICE_URL = process.env.BOOKING_SERVICE_URL || 'http://booking-service:5002';
const NOTIFICATION_SERVICE_URL = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:5003';

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'api-gateway', version: 'v1' });
});

app.use('/events', createProxyMiddleware({ target: EVENT_SERVICE_URL, changeOrigin: true }));
app.use('/bookings', createProxyMiddleware({ target: BOOKING_SERVICE_URL, changeOrigin: true }));
app.use('/notify', createProxyMiddleware({ target: NOTIFICATION_SERVICE_URL, changeOrigin: true }));

app.listen(3000, () => console.log('Gateway running on port 3000'));
