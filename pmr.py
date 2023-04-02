import time
import datetime
import os
import sys
import serial
import mysql.connector as mdb
import time
import settings as SETTINGS

# some presets
maxReadLength = 2048
continueReadingData1 = True
continueReadingData2 = True
meterData = b''
laenge = 0
outFile = "" # skip writing the data to a file. apply the path if you want to write the data to a file
currentTotal = 0
currentPower = 0
DEBUG = False;

# Establish the connection on a specific port
ser = serial.Serial('/dev/ttyUSB0', 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)

while (continueReadingData1 and continueReadingData2):
  if (DEBUG): print ("1-While\n")

  # read data from the meter
  percent = 0
  print ("Reading data from device...\n")
  while (laenge < maxReadLength):
    if (DEBUG): print ("2-While, Länge: " + str(laenge))
    laenge = len(meterData)
    percent = laenge / maxReadLength * 100
    print (str(percent) + "%")
    meterData = meterData + ser.read(256)

  meterData = meterData.lower()
  meterData = meterData.hex(' ')

  # write the raw data to a file
  if (outFile != ""):
    f = open(outFile, "w")
    f.write (str(meterData))
    f.close()

  if (DEBUG): print ("3-NachWhile2\n")
  if (DEBUG): print ("METER DATA\n")
  if (DEBUG): print (meterData)

# =============================================================================

  # Zählerstand
  searchPattern = "07 01 00 01 08 00 ff"
  startpos = meterData.find(searchPattern)
  if (DEBUG): print ("Startposition Zaehlerstand: ", startpos)

  if ((startpos > 0) and (startpos < 900)):
    if (DEBUG): print ("4-If\n")

    # extract the meter value from the following bytes
    part = meterData[startpos:startpos + 32]
    if (DEBUG): print ("PART:  " + part + "<")

    value = meterData[startpos + 32 + 1 + 18: startpos + 32 + 32 + 1]
    value = value.replace(' ', '')
    if (DEBUG): print ("VALUE: " + value + "<")

    currentTotal = round(int(value, 16) / 10000) #kWh
    print (">>>> currentTotal: " + str(currentTotal) + "<")

    continueReadingData1 = False

# =============================================================================

  # aktueller Verbrauch/Leistung
  searchPattern = "07 01 00 10 07 00 ff"
  startpos = meterData.find(searchPattern)
  if (DEBUG): print ("\n\n\nStartposition Verbrauch: ", startpos)

  if ((startpos > 0) and (startpos < 900)):
    if (DEBUG): print ("5-If\n")

    # extract the meter value from the following bytes
    part = meterData[startpos:startpos + 53]
    if (DEBUG): print ("PART:  " + part + "<")

    value = meterData[startpos + 41: startpos + 41 + 12]
    value = value.replace(' ', '')
    if (DEBUG): print ("VALUE: " + value + "<")

    currentPower = round(int(value, 16) / 10) #W
    print (">>>> currentPower: " + str(currentPower) + "<")

    continueReadingData2 = False

  if (DEBUG): print ("6-NachIf\n")

# =============================================================================
# Write data to database
# =============================================================================

try:
    if (currentTotal != 0 and currentPower != 0):
      con = mdb.connect( SETTINGS.host, SETTINGS.user, SETTINGS.passwd, SETTINGS.db )
      CURRENT_DATE = time.strftime("%Y-%m-%d")
      CURRENT_TIME = time.strftime("%H:%M:%S")
      SQL="INSERT INTO strom(date, time, currentTotal, currentPower) VALUES ('%s', '%s', %f, %f);" % (CURRENT_DATE, CURRENT_TIME, currentTotal, currentPower)
      cur = con.cursor()
      cur.execute(SQL)
      con.commit()

except mdb.Error as e:

    print ("Error %d: %s" % (e.args[0],e.args[1]) )
    sys.exit(1)

finally:
    if con:
        con.close()

print ("\n\nEND.\n")

