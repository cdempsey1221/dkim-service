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

def split_key_by_val(key):
    # Split the record into two separate TXT records
    name = key.split()[0]
    content_1 = f"{key.split()[1]} {key.split()[2]}"
    content_2 = key.split()[3]
    content_3 = key.split()[4]

    app.logger.debug('name: %s \n content1: %s \n content2: %s\n content3 %s\n' % (name, content_1, content_2, content_3) )

    split_key_json = {'record1': f"{name} {content_1} {content_2}", 'record2': f"{name} TXT {content_3}"}
    
    app.logger.debug(split_key_json)

    # Return the two separate TXT records as a dictionary
    return split_key_json

def get_key_type(record):
    parts = record.split()
    try:
        txt_index = next(i for i, p in enumerate(parts) if p.upper() == 'TXT')
    except StopIteration:
        txt_index = -1
    tag_string = ' '.join(parts[txt_index + 1:])
    tag_parts = tag_string.rsplit(None, 1)
    if len(tag_parts) == 2 and tag_parts[1].isdigit():
        tag_string = tag_parts[0]
    for tag in tag_string.split(';'):
        tag = tag.strip()
        if tag.lower().startswith('k='):
            return tag[2:].strip().upper()
    return 'RSA'

@app.route('/split_by_value', methods=['POST'])
def split_by_value():
    # Get the DKIM record from the JSON payload
    data = request.get_json()
    dkim_record = data['dkim_record']

    result = split_key_by_val(dkim_record)

    # Return the two separate TXT records as a JSON response
    return jsonify(result)

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route('/dkim_key_type', methods=['POST'])
def dkim_key_type():
    data = request.get_json()
    if not data or 'dkim_record' not in data:
        return jsonify({"error": "missing dkim_record"}), 400
    key_type = get_key_type(data['dkim_record'])
    app.logger.debug('key_type: %s' % key_type)
    return jsonify({"key_type": key_type}), 200

if __name__ == '__main__':
    app.run(debug=True)
