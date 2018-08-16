from flask import Flask, request, jsonify, render_template, Response
from flask_restful import Resource, Api
import json
import serial
from threading import Thread
import binascii


def convert(number, sign, len, fp_index):
  try:
    number = int(number.encode('hex'), 16)
  except ValueError:
        print 'Invalid value!'
        return 0
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


sbc_stream = "\0" * 100

port = serial.Serial("/dev/serial0", baudrate=19200, timeout=3.0)

# TODO:add 100ms delay
# TODO:create json here
# TODO:save to file
# TODO:Check for additional sync bytes
def update_sbc_stream():
  global sbc_stream
  while True:
    if port.in_waiting:
      sbc_stream = port.read_until(b'\xfc')


app = Flask(__name__)
api = Api(app)

num = 0.0
class Engine(Resource):
    def get(self):
        global sbc_stream
        global num 
        engine_data = {}
        engine_data['FUEL'] = 0
        engine_data['PWR'] = convert(sbc_stream[3:5], False, 16, 9)
        engine_data['RPM'] = convert(sbc_stream[7:9], False, 16, 4)
        engine_data['MANP'] = convert(sbc_stream[9:11], False, 16, 8)
        engine_data['FUELP'] = convert(sbc_stream[11:13], False, 16, 9)
        engine_data['OILP'] = convert(sbc_stream[47:49], False, 16, 9)
        engine_data['OILT'] = convert(sbc_stream[49:51], False, 16, 9)
        engine_data['CHT1'] = convert(sbc_stream[15:17], False, 16, 6)
        engine_data['CHT2'] = convert(sbc_stream[17:19], False, 16, 6)
        engine_data['CHT3'] = convert(sbc_stream[19:21], False, 16, 6)
        engine_data['CHT4'] = convert(sbc_stream[21:23], False, 16, 6)
        engine_data['CHT5'] = convert(sbc_stream[23:25], False, 16, 6)
        engine_data['CHT6'] = convert(sbc_stream[25:27], False, 16, 6)
        engine_data['EGT1'] = convert(sbc_stream[31:33], False, 16, 4)
        engine_data['EGT2'] = convert(sbc_stream[33:35], False, 16, 4)
        engine_data['EGT3'] = convert(sbc_stream[35:37], False, 16, 4)
        engine_data['EGT4'] = convert(sbc_stream[37:39], False, 16, 4)
        engine_data['EGT5'] = convert(sbc_stream[39:41], False, 16, 4)
        engine_data['EGT6'] = convert(sbc_stream[41:43], False, 16, 4)

        # steps = 100
        # engine_data['FUEL'] = num/steps * 100
        # engine_data['PWR'] = num/steps * 100
        # engine_data['RPM'] = num/steps * 2700
        # engine_data['MANP'] = num/steps * 45
        # engine_data['FUELP'] = num/steps * 120
        # engine_data['OILP'] = num/steps * 110
        # engine_data['OILT'] = num/steps * 250
        # engine_data['CHT1'] = num/steps * 500
        # engine_data['CHT2'] = num/steps * 500
        # engine_data['CHT3'] = num/steps * 500
        # engine_data['CHT4'] = num/steps * 500
        # engine_data['CHT5'] = num/steps * 500
        # engine_data['CHT6'] = num/steps * 500
        # engine_data['EGT1'] = num/steps * 1800
        # engine_data['EGT2'] = num/steps * 1800
        # engine_data['EGT3'] = num/steps * 1800
        # engine_data['EGT4'] = num/steps * 1800
        # engine_data['EGT5'] = num/steps * 1800
        # engine_data['EGT6'] = num/steps * 1800
        # if num < steps:
        #   num = num + 1
        return Response(json.dumps(engine_data), status=200, mimetype='application/json')

@app.route("/")
def index():  
    return render_template('index.html')


api.add_resource(Engine, '/engine')

if __name__ == "__main__":
  thread = Thread(target = update_sbc_stream)
  thread.start()
  app.run()
