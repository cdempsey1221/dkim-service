"""
DKIM Record Splitter REST Service

This Flask application defines a single endpoint '/split_by_value' that accepts a POST request
with a JSON payload containing a DKIM record. The application then splits the DKIM record
into two separate TXT records, and returns the two separate TXT records as a JSON response.

Expected Input:
    A JSON payload containing a DKIM record:
    {
        "dkim_record": "big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F709EF665853333EEC3F5ADE69A2362BECE40658267AB2FC3CB6CBE 6000"
    }

Output:
    A JSON response containing the two separate TXT records:
    {
        "record1": "big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F709EF665853333EEC3F5ADE69A2362BECE40658267AB2FC3CB6CBE",
        "record2": "big-email._domainkey.example.com TXT 6000"
    }

author: dempsey
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

def _parse_dkim_record(record):
    tokens = record.split()
    tags = []
    for token in tokens:
        for part in token.split(';'):
            part = part.strip()
            if '=' in part:
                k, _, v = part.partition('=')
                tags.append((k.strip().lower(), v.strip()))
    return tokens, tags

def split_key_by_val(key):
    tokens, _ = _parse_dkim_record(key)
    name = tokens[0]
    content_1 = f"{tokens[1]} {tokens[2]}"
    content_2 = tokens[3]
    content_3 = tokens[4]

    app.logger.debug('name: %s \n content1: %s \n content2: %s\n content3 %s\n' % (name, content_1, content_2, content_3) )

    split_key_json = {'record1': f"{name} {content_1} {content_2}", 'record2': f"{name} TXT {content_3}"}

    app.logger.debug(split_key_json)

    # Return the two separate TXT records as a dictionary
    return split_key_json

def parse_key_type(record):
    _, tags = _parse_dkim_record(record)
    for key, value in tags:
        if key == 'k':
            return value.upper()
    return 'RSA'  # RFC 6376 §3.3 default

def is_valid_dkim(record):
    _, tags = _parse_dkim_record(record)
    tag_map = {}
    for key, value in tags:
        tag_map[key] = value
    return tag_map.get('v', '').upper() == 'DKIM1' and 'p' in tag_map

@app.route('/split_by_value', methods=['POST'])
def split_by_value():
    # Get the DKIM record from the JSON payload
    data = request.get_json()
    dkim_record = data['dkim_record']

    result = split_key_by_val(dkim_record)

    # Return the two separate TXT records as a JSON response
    return jsonify(result)

@app.route('/dkim_key_type', methods=['POST'])
def dkim_key_type():
    data = request.get_json()
    if not data or 'dkim_record' not in data:
        return jsonify({'error': 'missing dkim_record'}), 400
    key_type = parse_key_type(data['dkim_record'])
    return jsonify({'key_type': key_type}), 200

@app.route('/validate_dkim', methods=['POST'])
def validate_dkim():
    data = request.get_json()
    if not data or 'dkim_record' not in data:
        return jsonify({'error': 'missing dkim_record'}), 400
    valid = is_valid_dkim(data['dkim_record'])
    return jsonify({'valid': valid}), 200

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route('/readyz', methods=['GET'])
def readyz():
    return jsonify({"status": "ready"}), 200

if __name__ == '__main__':
    app.run(debug=True)
