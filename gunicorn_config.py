import multiprocessing

# The address and port where Gunicorn should listen for requests
bind = "0.0.0.0:5000"

# The number of worker processes to spawn
workers = multiprocessing.cpu_count() * 2 + 1

# The maximum number of requests a worker will process before restarting
max_requests = 1000

# The number of seconds a worker will wait for a new request
timeout = 30

# The file to write the Gunicorn process ID to
pidfile = "/var/run/gunicorn.pid"

# The file to write Gunicorn's access log to
accesslog = "/var/log/gunicorn/access.log"

# The file to write Gunicorn's error log to
errorlog = "/var/log/gunicorn/error.log"

# The log level for Gunicorn's error log
loglevel = "info"
