from flask import Flask, render_template, jsonify, request

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from werkzeug.middleware.proxy_fix import ProxyFix

from charset_normalizer import from_bytes
from chardet import detect as chardet_detect
from cchardet import detect as cchardet_detect

from base64 import b64encode

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1 per second"]
)


@app.route('/', methods=['GET'])
def hello_world():
    return render_template('index.html')


@app.route('/detect', methods=['POST'])
@limiter.limit("1 per second")
def detect():
    if 'file' not in request.files:
        return jsonify({'message': 'No file has been sent'}), 400

    my_file = request.files['file']  # type: FileStorage

    byte_str = my_file.stream.read()

    r_ = from_bytes(byte_str).best()

    k_ = chardet_detect(byte_str)
    k_['confidence'] = str(round(k_['confidence'] * 100., ndigits=3)) + ' %' if k_['confidence'] is not None else None

    z_ = cchardet_detect(byte_str)
    z_['confidence'] = str(round(z_['confidence'] * 100., ndigits=3)) + ' %' if z_['confidence'] is not None else None

    return jsonify(
        {
            'charset-normalizer': {
                'encoding': r_.encoding,
                'aliases': r_.encoding_aliases,
                'alphabets': r_.alphabets,
                'language': r_.language,
                'chaos': str(r_.percent_chaos) + ' %',
                'coherence': str(r_.percent_coherence) + ' %',
                'could_be': r_.could_be_from_charset
            } if r_ is not None else None,
            'chardet': k_,
            'cchardet': z_,
            'filename': my_file.filename,
            'b64_content': b64encode(r_.output()).decode('ascii') if r_ is not None else ''
        }
    )


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
