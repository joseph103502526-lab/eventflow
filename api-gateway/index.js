const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

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
