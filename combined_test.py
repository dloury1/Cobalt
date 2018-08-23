from flask import Flask, request, jsonify, render_template, Response
from flask_restful import Resource, Api
import json
# import serial
from threading import Thread
import binascii
import time



engine_data = {'FUEL': 0, 'PWR': 0, 'RPM': 0, 'MANP': 0, 'FUELP': 0, 
      'OILP': 0, 'OILT': 0, 'CHT1': 0, 'CHT2': 0,  'CHT3': 0, 
      'CHT4': 0, 'CHT5': 0, 'CHT6': 0, 'EGT1': 0, 'EGT2': 0, 
      'EGT3': 0, 'EGT4': 0, 'EGT5': 0, 'EGT6': 0, 'ERROR':[] }


def convert(number, sign, len, fp_index):
  try:
    number = int(number.encode('hex'), 16)
  except ValueError:
        print 'Invalid value!'
        return -0.1
  ret = 0;
  mask_index = len - 1;
  if (sign):
    mask_index = mask_index - 1;
  while(mask_index >= 0):
    mask = 1 << mask_index;
    if(number & mask):
      ret += pow(2, mask_index - fp_index);
    mask_index = mask_index - 1;
  if (sign and (number & 1 << (len - 1))):
    ret = ret * -1;
  return ret;


def update_sbc_stream():
  global engine_data
  while True:
    time.sleep(0.1)
    sbc_stream = "\0" * 98
    engine_data['FUEL'] = 50
    engine_data['PWR'] = 70
    engine_data['RPM'] = 1500
    engine_data['MANP'] = 28
    engine_data['FUELP'] = 75
    engine_data['OILP'] = 50
    engine_data['OILT'] = 150
    engine_data['CHT1'] = 300
    engine_data['CHT2'] = 425
    engine_data['CHT3'] = 225
    engine_data['CHT4'] = 330
    engine_data['CHT5'] = 250
    engine_data['CHT6'] = 200
    engine_data['EGT1'] = 1500
    engine_data['EGT2'] = 1500
    engine_data['EGT3'] = 1500
    engine_data['EGT4'] = 1500
    engine_data['EGT5'] = 1500
    engine_data['EGT6'] = 1500
    engine_data['ERROR'] = ["No data in 3 seconds"]


class Engine(Resource):
    def get(self):
        global engine_data
        return Response(json.dumps(engine_data), status=200, mimetype='application/json')

app = Flask(__name__)
api = Api(app)
api.add_resource(Engine, '/engine')
@app.route("/")
def index():  
    return render_template('index.html')

if __name__ == "__main__":
  time.sleep(0.2)
  thread = Thread(target = update_sbc_stream)
  thread.start()
  app.run(port=5000)
