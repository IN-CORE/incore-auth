"""Gunicorn configuration."""

bind = '0.0.0.0:5000'

workers = 1
worker_class = 'gevent'
worker_connections = 100
