import os
import multiprocessing

# The socket to bind to
bind = "127.0.0.1:8000"

# Number of worker processes (Recommended: 2 * CPUs + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class (sync is standard, gevent/eventlet can be used for async)
worker_class = "sync"

# Log files
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process name
proc_name = "django_newsapp"

# Clean up memory by restarting workers after a certain number of requests
max_requests = 1000
max_requests_jitter = 50
