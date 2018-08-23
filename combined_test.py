from flask import Flask, request, jsonify, render_template, Response
from flask_restful import Resource, Api
import json
import serial
from threading import Thread
import binascii
import time
import pigpio
import read_PWM

PWM_GPIO = 4
pi = pigpio.pi()
p = read_PWM.reader(pi, PWM_GPIO)
scale = 100
frequencies = []
frequencies_index = 0
port = serial.Serial("/dev/serial0", baudrate=19200, timeout=3.0)

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


def get_fuel_reading():
  global frequencies, frequencies_index
  frequencies[frequencies_index%scale] =  p.frequency()
  frequencies_index = (frequencies_index + 1)
  frequency = reduce(lambda x, y: x + y, frequencies) / len(frequencies)
  fuel_reading = round(109*(4650-frequency)/(4650-3000))
  if fuel_reading < 0:
    return 0
  else:
    return fuel_reading


def update_sbc_stream():
  filename  = time.strftime("/home/pi/Cobalt/log/%Y%m%d-%H%M%S")
  file = open(filename,"w+",0)
  time_since_last_read = 0
  global engine_data
  while True:
    time.sleep(0.1)
    engine_data['FUEL'] = get_fuel_reading()
    if port.in_waiting:
      port.read_until(b'\xfc')
      sbc_stream = port.read(3)
      if sbc_stream[0].encode("hex") == "fd" and sbc_stream[1].encode("hex") == "fe" and sbc_stream[2].encode("hex") == "ff":
        sbc_stream = sbc_stream + port.read(94)
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
        file.write(time.strftime("%Y/%m/%d-%H:%M:%S::"))
        file.write(json.dumps(engine_data))
        file.write("\n")
        file.write(binascii.hexlify(sbc_stream))
        file.write("\n")
        time_since_last_read = 0
    else:
      time_since_last_read = time_since_last_read + 1

    if time_since_last_read > 10:
      engine_data['ERROR'] = ["No data in 3 seconds"]
      file.write(time.strftime("%Y/%m/%d-%H:%M:%S::"))
      file.write(json.dumps(engine_data))
      file.write("\n")
      time_since_last_read = 0

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
  frequencies = [p.frequency()] * scale
  thread = Thread(target = update_sbc_stream)
  thread.start()
  app.run(port=5000)
