from flask import Flask, render_template, make_response
import os
import time

app = Flask(__name__)

def format_server_time():
  server_time = time.localtime()
  return time.strftime("%I:%M:%S %p", server_time)

@app.route('/')
def index():
    context = { 'server_time': format_server_time() }
    return render_template('index.html', context=context)

@app.route('/rqst', methods=['GET'])
def hello_world_GET():
    return "GET request sent"

@app.route('/rqst', methods=['POST'])
def hello_world_POST():
    return "POST request sent"

@app.route('/rqst', methods=['PUT'])
def hello_world_PUT():
    return "PUT request sent"

@app.route('/rqst', methods=['DELETE'])
def hello_world_DELETE():
    return "DELETE request sent"

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))