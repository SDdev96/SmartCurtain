from Project_Classes import LED, LDR, Button, DHT22, HC_SR04, HW_511, OLED, StepperMotor
import time
import ujson
import network
from umqtt.simple import MQTTClient
import machine


'''INIZIALIZZAZIONI'''
# Sensori
ultrasonicSensor = HC_SR04(18, 19)
infraredSensor = HW_511(16)
photoresistor = LDR(34)
led = LED(4)
stepper = StepperMotor(26, 25, 33, 32)
temperatureSensor = DHT22(15)
display = OLED(22, 21)
button = Button(14)
buttonWiFi = Button(12)

# Connessione alla rete
sta_if = network.WLAN(network.STA_IF)
# led.off()
# Variabili globali
presenzaPersona = False
modalitaAutomatica = True
prev_conditions = ""
last = 0

# Parametri MQTT
MQTT_CLIENT_ID = ""
MQTT_BROKER = "test.mosquitto.org"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_TOPIC = "unisa/iot/group16/smartCurtain"
MQTT_CURTAIN = b'unisa/iot/group16/lightIntensity'
MQTT_MODE = b'unisa/iot/group16/modality'
MQTT_MANUAL_MODE = b'unisa/iot/group16/manualmodality'

# Creazione cient
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER,
                    user=MQTT_USER, password=MQTT_PASSWORD)


def connectWiFi(id, password=""):
    '''Funzione per la connessione al WiFi.
    Mostra sia sullo stato sia attraverso il LED lo stato della connessione.
    Quando il LED lampeggia si sta connettendo.
    Quando il LED ha luce fissa è connesso.

    Args:
        id (str): id del WiFi
        password (str): Passwor del WiFi
    '''
    global sta_if
    global display, led

    print("Connecting to WiFi", end="")
    display.clear()
    display.text("Connecting to", 5, 10)
    display.text("WiFi...", 5, 20)
    display.show()
    sta_if.active(True)
    sta_if.connect(id, password)
    while not sta_if.isconnected():
        print(".", end="")
        led.value(not led.value())
        time.sleep(0.1)
    print(" Connected!")
    display.clear()
    display.text("Connected!", 5, 30)
    display.show()
    led.on()


def subCallback(topic, msg):
    '''Funzione di callback per la gestione dei messaggi MQTT.

    Args:
        topic (str): Il topic sotto il quale inviare il messaggio
        msg (str): Il messaggio da gestire
    '''
    global modalitaAutomatica

    if topic == MQTT_MODE:
        if msg == b'0':
            modalitaAutomatica = True
            display.clear()
            display.text("Attivata Modalita Automatica", 5, 10)
            display.show()
        elif msg == b'1':
            modalitaAutomatica = False
            display.clear()
            display.text(" Attivata Modalita Manuale", 5, 10)
            display.show()

    if topic == MQTT_CURTAIN and modalitaAutomatica == True:  # apre e chiude le tende in base alla luminosità
        # b'1' equivale a luminosità >= 40
        if msg == b'1' and infraredSensor.value() == 1 and rilevazioneInterna() == True:
            display.clear()
            display.text("La tenda si sta", 5, 10)
            display.text("chiudendo...", 5, 20)
            display.show()
            for x in range(4200):
                stepper.step(1)
            # statoTenda = True
            display.clear()
            display.text("Tenda chiusa", 5, 10)
            display.show()
        # b'0' equivale a luminosità < 40
        elif msg == b'0' and infraredSensor.value() == 0 and rilevazioneInterna() == True:
            display.clear()
            display.text("La tenda si sta", 5, 10)
            display.text("aprendo...", 5, 20)
            display.show()
            for x in range(4200):
                stepper.step(-1)
            # statoTenda = False
            display.clear()
            display.text("Tenda aperta", 5, 10)
            display.show()

    if topic == MQTT_MANUAL_MODE and modalitaAutomatica == False:  # Comportamento tenda in modalità manuale
        # b'0' corrisponde al messaggio di chiusura inviato tramite dashboard di Node-Red
        if msg == b'0' and infraredSensor.value() == 1:
            display.clear()
            display.text("La tenda si sta", 5, 10)
            display.text("chiudendo...", 5, 20)
            display.show()
            for x in range(4200):
                stepper.step(1)
            # statoTenda = True
            display.clear()
            display.text("Tenda chiusa", 5, 10)
            display.show()

        # b'1' corrisponde al messaggio di apertura inviato tramite dashboard di Node-Red
        elif msg == b'1' and infraredSensor.value() == 0:
            display.clear()
            display.text("La tenda si sta", 5, 10)
            display.text("aprendo...", 5, 20)
            display.show()
            for x in range(4200):
                stepper.step(-1)
            # statoTenda = False
            display.clear()
            display.text("Tenda aperta", 5, 10)
            display.show()


def subscribe(*topics):
    '''Funzione per il subscribe ai topic

    Args:
        topics (list): lista dei topic a cui fare la sottoscrizione
    '''
    global client
    for topic in topics:
        client.subscribe(topic)


def rilevazioneInterna():
    '''Funzione per rilevare la presenza di persone all'interno di una stanza
    attraverso il sensore ad ultrasioni. Gestisce la tenda in base al valore
    del sensore ad infrarossi
    '''
    global presenzaPersona

    if ultrasonicSensor.distance_cm() < 20:
        presenzaPersona = True
        return True
    else:
        presenzaPersona = False
        if infraredSensor.value() == 1:
            display.clear()
            display.text("La tenda si sta", 5, 10)
            display.text("chiudendo...", 5, 20)
            display.show()
            for x in range(4200):
                stepper.step(1)
            return False


def reset(button):
    '''Funzione per il reset del sistema'''
    global last
    current = time.ticks_ms()
    delta = time.ticks_diff(current, last)
    if delta < 200:
        return
    last = current

    machine.reset()


def resetConnection(buttonWiFi):
    '''Funzione per il riavvio della connessione'''
    global last
    current = time.ticks_ms()
    delta = time.ticks_diff(current, last)
    if delta < 200:
        return
    last = current

    connectWiFi()


# Connessione al WiFi - METTERE NEL BOOT
connectWiFi('TIM-25978669', password='1eS6VpLuCdRbHxmyp7ww1MwD')

# Connessione al broker e creazione callback
client.set_callback(subCallback)
print("Connecting to MQTT server... ", end="")
client.connect()
# client.subscribe(MQTT_TOPIC)
# client.subscribe(MQTT_CURTAIN)
# client.subscribe(MQTT_MODE)
# client.subscribe(MQTT_MANUAL_MODE)

# Subscribe ai topic - DA TESTARE
subscribe(MQTT_TOPIC, MQTT_CURTAIN, MQTT_MODE, MQTT_MANUAL_MODE)

# Gestione degli eventi dei pulsanti
button.irq(trigger=machine.Pin.IRQ_RISING, handler=reset)
buttonWiFi.irq(trigger=machine.Pin.IRQ_RISING, handler=resetConnection)


'''CICLO DEL PROGRAMMA PRINCIPALE'''
while True:
    # check_msg controlla l'arrivo di messaggi mqtt
    client.check_msg()

    # Leggere il valore analogico del fotoresistore
    photoresistor.read()

    # Misura i valori di temperatura e umidità
    temperatureSensor.measure()

    # Invio valori di temperatura e luminosità al topic
    message = ujson.dumps({
        "temp": int(temperatureSensor.temperature()),
        "light": int(photoresistor.value()),
    })
    if message != prev_conditions:
        print("Reporting to MQTT topic {}: {}".format(MQTT_TOPIC, message))
        client.publish(MQTT_TOPIC, message)
        prev_conditions = message
        print("Updated!")
    else:
        print("No change")

    # Controlla se la connessione al WiFi è ancora attiva
    if not sta_if.isconnected():
        led.off()

    time.sleep(1)

    # Mostra i valori di temperatura e luminosità sullo schermo
    display.clear()
    display.text("Luminosità (perc):", 10, 10)
    display.text(str(photoresistor.value()), 10, 20)
    display.text("Temperatura (C):", 10, 30)
    display.text(str(temperatureSensor.temperature()), 10, 40)
    display.show()

    # Effettua la rilevazione della stanza
    rilevazioneInterna()
