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

@app.route('/split_by_value', methods=['POST'])
def split_by_value():
    # Get the DKIM record from the JSON payload
    data = request.get_json()
    dkim_record = data['dkim_record']

    result = split_key_by_val(dkim_record)

    # Return the two separate TXT records as a JSON response
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
