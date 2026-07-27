import os
print('DATABASE_URL=', repr(os.environ.get('DATABASE_URL')))
print('USE_POSTGRES=', repr(os.environ.get('USE_POSTGRES')))
print('PG_HOST=', repr(os.environ.get('PG_HOST')))
print('PG_PORT=', repr(os.environ.get('PG_PORT')))
print('PG_DATABASE=', repr(os.environ.get('PG_DATABASE')))
print('PG_USER=', repr(os.environ.get('PG_USER')))
print('PG_PASSWORD=', repr(os.environ.get('PG_PASSWORD')))
try:
    import psycopg2
    print('psycopg2 ok', psycopg2.__version__)
except Exception as e:
    print('psycopg2 failed', type(e).__name__, e)
