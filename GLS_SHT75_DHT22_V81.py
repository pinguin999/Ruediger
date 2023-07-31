# -*- encoding: utf-8 -*-

# Importieren der zusätzlich benötigten Module
# import Adafruit_DHT #fuer DHT22-Sensoren
import time
# import sys
import math
# import vcgencmd
import lcddriver  # Sainsmart LCD 4x20
import RPi.GPIO as GPIO  # Import GPIO library
from sht_sensor import Sht, ShtCommFailure, ShtCRCCheckError
from time import sleep

GPIO.setmode(GPIO.BOARD)  # Use board pin numbering
# tells Python not to print GPIO warning messages to the screen
GPIO.setwarnings(False)
GPIO.setup(36, GPIO.OUT)  # Setup GPIO Pin 36 (GPIO16) to OUT; LED grün
GPIO.setup(40, GPIO.OUT)  # Setup GPIO Pin 40 (GPIO21) to OUT; LED gelb
GPIO.setup(32, GPIO.OUT)  # Setup GPIO Pin 32 (GPIO12) to OUT; LED rot
GPIO.setup(38, GPIO.OUT)  # Setup GPIO Pin 38 (GPIO20) to OUT; LED blau
GPIO.setup(35, GPIO.OUT)  # Setup GPIO Pin 35 (GPIO19) to OUT; LED grün2
# Setup GPIO Pin 12 (GPIO18) to OUT; Taste 2 (Pin4) FS20 Ein
GPIO.setup(12, GPIO.OUT)
GPIO.output(12, True)   # setzt den Pin12 auf High = 3,3V
# Setup GPIO Pin 13 (GPIO27) to OUT; Taste 1 (Pin2) FS20 Aus
GPIO.setup(13, GPIO.OUT)
GPIO.output(13, True)   # setzt den Pin13 auf High = 3,3V

# Definition der Variablen (Parameter)
cd = 20.0  # [min] Countdown-Wert
krFi = 70.0  # [%] kritische rel. Feuchte innen Schimmelgefahr
kT = 10.0  # [°C] kritsche Temperatur Schimmelgefahr
mTo = 5.0  # [°C] min. Temperatur out (Regelungsgrenze)
mxTi = 26.0  # [°C] max. Temperatur in (wenn zu warm doch lüften)
mTTr = 8.0  # [°C] min. Temperatur Trockner einschalten
ukrFi = 55.0  # [%] unkritische rel. Feuchte innen (keine Regelung nötig)
Ld = 15.0  # [min] Lüftungsdauer
Wz = 30.0  # [min] Wartezeit
a = 7.5      # Berechnungswert
b = 237.3    # Berechnungswert
mw = 18.016  # [kg/kmol] Molekulargewicht des Wasserdampfes
R = 8314.3   # [J/(kmol*K)] universelle Gaskonstante
c = ':'

# nur zur Simulation
# Ti = 10.1
# rFi = 69.0
# To = 10.2
# rFo = 80.0


# SENSORTYP UND GPIO bzw. PIN FESTLEGEN

# DHT22
# sensor1 = Adafruit_DHT.DHT22
# gpio1 = 4  # GPIO 04 , hier nicht PIN7 ?!? ,Innensensor, Klinkenanschluss links

# sensor2 = Adafruit_DHT.DHT22
# gpio2 = 17 # GPIO 017 , hier nicht PIN11 ?!? ,Außensensor, Klinkenanschluss rechts

# SHT75
# sht1 = Sht(11, 5, voltage='3,3V')
sht1 = Sht(11, 5)  # Innensensor SCK GPIO11/Pin23, Data GPIO5/Pin29
# sht2 = Sht(4, 17, voltage='5V')
sht2 = Sht(4, 17)  # Aussensensor SCK GPIO4/Pin7, Data GPIO17/Pin11

lcd = lcddriver.lcd()

while True:
    while True:
        while True:
            # DATEN AUSLESEN
            # Ti => Temperatur innen
            # rFi => rel. Feuchte innen
            # To => Temperatur außen
            # rFo => rel. Feuchte außen
            # rFi, Ti = Adafruit_DHT.read_retry(sensor1, gpio1) # DHT22 ausklammern, wenn simulieren
            # rFo, To = Adafruit_DHT.read_retry(sensor2, gpio2) # DHT22 ausklammern, wenn simulieren

            # Vermeidung Programmstop aufgrund aufgetretener Exception-Fehler
            try:
                rFi = sht1.read_rh()
                Ti = sht1.read_t()
                rFo = sht2.read_rh()
                To = sht2.read_t()

                # bei Nicht-Zahl-Ergebnis (text statt float) erneut auslesen lassen
                if isinstance(Ti, float) and isinstance(rFi, float) and isinstance(To, float) and isinstance(rFo, float):
                    break
                else:
                    # bei fehlerhaften Messwerten nach kl. Pause erneut auslesen lassen
                    print("Fehlerhafter Datensatz (keine Zahl), erneutes Auslesen")
                    sleep(10)

            except (ShtCommFailure) as err:
                print("Fehler: {0}".format(err))
                sleep(10)
            except (ShtCRCCheckError) as err:
                print("Fehler: {0}".format(err))
                sleep(10)

        if (-20.0 < To < 50.0 and -10.0 < Ti < 50.0 and 0.0 < rFi < 99.99 and 0.0 < rFo < 99.99):  # neu V71: 99.99
            break
        else:
            print(time.strftime('%d/%m/%y %H:%M'))  # dd/mm/yyyy hh:mm
            print("Fehlerhafte Messwerte")
            print('Ti: {0:>+5.1f}*C rFi: {1:>2.1f}%' .format(Ti, rFi))
            print('To: {0:>+5.1f}*C rFo: {1:>2.1f}%' .format(To, rFo))
            print("erneutes Auslesen")
            sleep(10)

    # aFi => errechneter Wert abs. Feuchte innen
    SDDi = 6.1078*10**((a*Ti)/(b+Ti))
    DDi = rFi/100*SDDi
    v = math.log10(DDi/6.1078)
    TDi = (b*v)/(a-v)
    aFi = 10**5*mw/R*DDi/(Ti+273.0)

    # aFo => errechneter Wert abs. Feuchte außen
    SDDo = 6.1078*10**((a*To)/(b+To))
    DDo = rFo/100*SDDo
    v = math.log10(DDo/6.1078)
    TDo = (b*v)/(a-v)
    aFo = 10**5*mw/R*DDo/(To+273.0)

    # CPU-Temperatur auslesen
    # CPU = vcgencmd measure_temp()  #funktioniert nicht

    # Ausgabe Konsole/ Python-2-Shell
    print(time.strftime('%d/%m/%y %H:%M'))  # dd/mm/yyyy hh:mm
    print(
        'Ti: {0:>+5.1f}*C rFi: {1:>2.1f}% aFi: {2:>4.1f}g/m3' .format(Ti, rFi, aFi))
    print(
        'To: {0:>+5.1f}*C rFo: {1:>2.1f}% aFo: {2:>4.1f}g/m3' .format(To, rFo, aFo))
    # print str(CPU)  #funktioniert nicht

    # Ausgabe LCD 2004
    lcd.lcd_clear()

    # lcd.lcd_display_string("{0}".format(Empfehlung), 1)
    lcd.lcd_display_string(" Temp rel.F. abs.F. ", 2)
    lcd.lcd_display_string(
        "{0:>5.1f} {1:>3.0f}% {2:>5.1f}g/m3".format(Ti, rFi, aFi), 3)
    lcd.lcd_display_string(
        "{0:>5.1f} {1:>3.0f}% {2:>5.1f}g/m3".format(To, rFo, aFo), 4)

    # grüne oder gelbe .LED (Empfehlung Lüften/ NICHT Lüften)
    if (aFo <= aFi) and (To > mTo) or (Ti > To) and (Ti > mxTi) and (rFi < ukrFi):
        # print ("LED grün an")
        GPIO.output(36, True)
        GPIO.output(40, False)
        # print ("Display: Lüften OK")
        Empfehlung = "Lueften OK    "  # 14 Zeichen lang
    else:
        # print ("LED gelb an")
        GPIO.output(36, False)
        GPIO.output(40, True)
        # print ("Display: NICHT Lüften")
        Empfehlung = "NICHT Lueften "  # 14 Zeichen lang

    # rote LED an (Schimmelgefahr)
    if (rFi > krFi) and (Ti > kT):
        # print ("LED rot an")
        GPIO.output(32, True)
    else:
        # print ("LED rot aus")
        GPIO.output(32, False)

    # blau LED an (Trockner an)
    if (aFo > aFi) and (Ti > mTTr) and (rFi > krFi):
        # print ("LED blau an")
        GPIO.output(38, True)
    else:
        # print ("LED blau aus")
        GPIO.output(38, False)

    # grün2 LED an (Lüfter an, Bedingungen:1 außen besser als innen/2 innen zu warm)
    if (aFo < aFi) and (rFi > ukrFi) and (To > mTo):
        # print ("LED grün2 an")
        GPIO.output(35, True)
        print("Lüfter AN-Befehl1...Countdown Lüftungsdauer...")
        GPIO.output(12, False)  # Einschalten FS20 Taste2/ Pin4:
        # AN-Befehl senden: low (GND) durchschalten (Schaltimpuls Anfang)
        sleep(0.3)
        GPIO.output(12, True)  # Ausschalten FS20 Taste2/ Pin4:
        # AN-Befehl Ende: high schalten (Schaltimpuls Ende)

    elif (Ti > To) and (Ti > mxTi) and (rFi < ukrFi):
        # print ("LED grün2 an")
        GPIO.output(35, True)
        print("Lüfter AN-Befehl2...Countdown Lüftungsdauer...")
        GPIO.output(12, False)  # Einschalten FS20 Taste2/ Pin4:
        # AN-Befehl senden: low (GND) durchschalten (Schaltimpuls Anfang)
        sleep(0.3)
        GPIO.output(12, True)  # Ausschalten FS20 Taste2/ Pin4:
        # AN-Befehl Ende: high schalten (Schaltimpuls Ende)

    else:
        # print ("LED grün2 aus")
        GPIO.output(35, False)

    # Countdown-Zeit = Lüftungsdauer
    # soll nur laufen, wenn Bedingung erfüllt und Lüfter angeschaltet ist
    if (aFo < aFi) and (rFi > ukrFi) and (To > mTo) or (Ti > To) and (Ti > mxTi) and (rFi < ukrFi):
        minz = Ld
        secz = 0.0  # Zeitvorgabe in Sekunden nicht benötigt

        min = int(minz)
        sec = int(secz)

        while min > -1:
            while sec > 0:
                sec = sec-1
                sleep(0.895)
                sec1 = ('%02.f' % sec)  # format
                min1 = ('%02.f' % min)
                lcd.lcd_display_string("{0} {1:>2}:{2:1}".format(
                    Empfehlung, str(min1), str(sec1)), 1)
                # sys.stdout.write('\r'),
                # sys.stdout.write(str(min1) + c + str(sec1)),     #Var1K: Zeile funktioniert
                # sys.stdout.flush()                             #Var1K: Zeile2 funktioniert

            min = min-1
            sec = 60

            sleep(0.01)

        GPIO.output(13, False)  # Einschalten FS20 Taste1/ Pin2:
        # AUS-Befehl senden: low (GND) durchschalten (Schaltimpuls Anfang)
        sleep(0.3)
        GPIO.output(13, True)  # Ausschalten FS20 Taste1/ Pin2:
        # AUS-Befehl Ende: high schalten (Schaltimpuls Ende)
        # print ("Lüfter AUS-Befehl")
        GPIO.output(35, False)
        # print ("LED grün2 aus")

#    else:
#        sleep(0.01)

    # Countdown-Zeit = Wartezeit
    # damit die Lüfter nicht dauerhaft laufen, solange Bedingung erfüllt
    minz = Wz
    secz = 0.0  # Zeitvorgabe in Sekunden nicht benötigt

    min = int(minz)
    sec = int(secz)
    Wartezeit = "Next check in "  # 14 Zeichen lang
    # print ("Lüfter AUS-Befehl...Countdown Wartezeit...")

    while min > -1:
        while sec > 0:
            sec = sec-1
            sleep(0.895)
            sec2 = ('%02.f' % sec)  # format
            min2 = ('%02.f' % min)
            lcd.lcd_display_string("{0} {1:>2}:{2:1}".format(
                Wartezeit, str(min2), str(sec2)), 1)
            # sys.stdout.write('\r'),
            # sys.stdout.write(str(min1) + c + str(sec1)),     #Var1K: Zeile funktioniert
            # sys.stdout.flush()                             #Var1K: Zeile2 funktioniert

        min = min-1
        sec = 60

        sleep(0.01)

# except KeyboardInterrupt:
#  GPIO.cleanup()
# lcd.lcd_clear()
