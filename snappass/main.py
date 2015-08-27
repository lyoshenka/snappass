import os
import uuid
import sys  

import redis

from flask import abort, Flask, render_template, request

reload(sys)  
sys.setdefaultencoding('utf8')

NO_SSL = os.environ.get('NO_SSL', False)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'Secret Key')

id_ = lambda: uuid.uuid4().hex

#redis_host = os.environ.get('REDIS_HOST', 'localhost')
#redis_client = redis.StrictRedis(host=redis_host, port=6379, db=0)

redis_url = os.getenv('REDISTOGO_URL', os.getenv('REDIS_URL', 'redis://localhost:6379'))
redis_client = redis.from_url(redis_url)

def set_password(password, ttl):
    key = id_()
    redis_client.set('snappass:'+key, password)
    redis_client.expire('snappass:'+key, ttl)
    return key


def get_password(key):
    password = redis_client.get('snappass:'+key)
    redis_client.delete('snappass:'+key)
    return password


def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if not 'data' in request.form:
        abort(400)

    if not 'ttl' in request.form:
        abort(400)

    ttl = max(int(request.form['ttl']), 604800)
    return ttl, request.form['data']


@app.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')


@app.route('/', methods=['POST'])
def handle_password():
    ttl, password = clean_input()
    key = set_password(password, ttl)

    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")
    link = base_url + key
    return render_template('confirm.html', password_link=link)


@app.route('/<password_key>', methods=['GET'])
def show_password(password_key):
    password = get_password(password_key)
    if not password:
        abort(404)

    return render_template('password.html', password=password)


def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()
