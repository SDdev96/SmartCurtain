import machine
from machine import Pin, ADC, I2C
import dht
from ssd1306 import SSD1306_I2C
import time

# Riga 24 da testare
class LED:
    '''Classe che rappresenta un LED

    Attributi:
        led (Pin): Il led in utilizzo
    '''

    def __init__(self, pin):
        '''Costruttore della classe LED

        Args:
            pin (int): il pin a cui è connesso
        '''
        self.led = Pin(pin, Pin.OUT)

        # Da testare
        self.off()

    def on(self):
        '''Richiamo al metodo on di Pin.
        Accende il LED
        '''
        self.led.on()

    def off(self):
        '''Richiamo al metodo off di Pin
        Spegne il LED
        '''
        self.led.off()

    def value(self, value=None):
        return self.led.value() if value is None else self.led.value(value)

    def bool_state(self):
        '''Legge lo stato del sensore
        Ritorna True se il led è acceso, False se spento.
        '''
        return True if self.led.value() == 1 else False

    def state(self):
        '''Legge lo stato del sensore
        Stampa "Acceso" se True, "Spento" altrimenti.
        '''
        return "Acceso" if self.bool_state() else "Spento"


class LDR:
    '''Classe che rappresenta un LDR (light dependent resistor)

    Attributi:
        min_value (int): valore minimo
        max_value (int): valore massimo
        ldr (ADC): LDR in utilizzo 
    '''

    def __init__(self, pin, min_value=0, max_value=100):
        '''Costruttore della classe LDR

        Args:
            pin (int): il pin a cui è connesso
            min_value (int): il valore minimo
            max_value (int): il valore massimo
        '''
        if min_value >= max_value:
            raise Exception('Min value is greater or equal to max value')
        self.ldr = ADC(Pin(pin))
        self.min_value = min_value
        self.max_value = max_value

    def read(self):
        '''Metodo che legge il valore analogico dell'adc
        Ritorna il valore analogico
        '''
        return self.ldr.read()

    def value(self):
        '''Metodo che converte il valore analogico in digitale
        Ritorna il valore digitale
        '''
        return (self.max_value - self.min_value) * self.read() / 4095


class Button:
    '''Classe che rappresenta un Pulsante

    Attributi:
        button (Pin): il pulsante in utilizzo
    '''

    def __init__(self, pin, mode=Pin.PULL_DOWN):
        '''Costruttore della classe LDR

        Args:
            pin (int): il pin a cui è connesso
            [mode] (str): indica 
        '''
        self.button = Pin(pin, Pin.IN, mode)

    def irq(self, trigger=Pin.IRQ_FALLING or Pin.IRQ_RISING, handler=None):
        '''Metodo per la gestione della pressione del pulsante.

        Args:
            [trigger] (str): Definisce quando viene generato l'evento.
                Valori ammessi: Pin.IRQ_FALLING | Pin.IRQ_RISING
            [handler] (str): Funzione opzionale che viene eseguita quando
                si verifica l'evento. L'handler deve avere esattamente un
                argomento che è esattamente un'istanza di Pin
        '''
        self.button.irq(trigger=trigger, handler=handler)


class DHT22:
    '''Classe che rappresenta un LDR (light dependent resistor).
    Per ottenere i risultati più accurati, può essere chiamato solo una volta ogni due secondi almeno.
    Inoltre, la sua precisione degrada col passare del tempo.

    Attributi:
        dht (DHT22): il sensore in utilizzo
    '''

    def __init__(self, pin):
        '''Costruttore della classe LDR

        Args:
            pin (int): il pin a cui è connesso
        '''
        self.dht22 = dht.DHT22(Pin(pin))

    def measure(self):
        '''Metodo utilizzato per ricevere le misurazioni'''
        self.dht22.measure()

    def temperature(self):
        '''Metodo per stampare il valore della temperatura.
        Ritorna la temperatura in °C
        '''
        return self.dht22.temperature()

    def humidity(self):
        '''Metodo utilizzato per stampare l'umidità.
        Ritorna l'umidità in %'''
        return self.dht22.humidity()


class HC_SR04:
    '''Classe che rappresenta il sensore ad ultrasuoni HC-SR04. 
    Il sensore ha un range che va da 2cm a 4m.

    Attributi:
        echo_timeouut_us (int): Timeout per il ricevimento dell'impulso
        trigger (Pin): Pin che invia l'impulso
        echo (Pin): Pin che riceve l'impulso
        TIMEOUT_us (int): Timeout in microsecondi
    '''

    TIMEOUT_US = 500*2*30

    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=TIMEOUT_US):
        '''Costruttore della classe HC_SR04

        Args:
            trigger_pin: Pin utilizzato per inviare l'impulso.
                Il timeout è impostato per un range di 400cm
            echo_pin: Pin per la lettura della distanza
            echo_timeout_us: Timeout in microsencodi dall'ascolto di echo_pin. 
        '''
        self.echo_timeout_us = echo_timeout_us
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

        self.trigger.value(0)

    def _send_pulse_and_wait(self):
        '''Metodo che invia l'impulso che attiva e mettere in ascolto echo_pin'''
        self.trigger.value(0)
        time.sleep_us(5)
        self.trigger.value(1)
        # Invia un impulso di 10us
        time.sleep_us(10)
        self.trigger.value(0)
        try:
            # time_pulse_us(pin, pulse_level, timeout_us) è una funzione del modulo machine
            # usata per cronometrare il tempo di un impulso.
            # pulse_level = 0 per cronometrare un impulso basso
            # pulse_level = 1 per cronometrare un impulso alto
            # Ritorna la durata dell'impulso in microsecondi
            pulse_time = machine.time_pulse_us(
                self.echo, 1, self.echo_timeout_us)
            return pulse_time
        except OSError as ex:
            if ex.args[0] == 110:  # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):
        '''Metodo che ritorna la distanza in mm che percorre l'impulso senza operazioni in floating point'''
        pulse_time = self._send_pulse_and_wait()

        # Per calcolare la distanza si ricava prima il pulse_time e lo si divide per 2
        # (perchè l'impulso percorre la distanza due volte) e poi per 29.1 per la velocità
        # del suono nell'aria (343.2 m/s), che equivale a 0.34320 mm/us, cioè 1mm ogno 2.91 us.
        # pulse_time // (2 * 2.91) -> pulse_time // 5.82 -> pulse_time * 100 // 582
        mm = pulse_time * 100 // 582
        return mm

    def distance_cm(self):
        '''Metodo che ritorna la distanza in cm che percorre l'impulso con operazione in floating point. Ritorna la distanza in cm (float)'''
        pulse_time = self._send_pulse_and_wait()

        # Per calcolare la distanza si ricava prima il pulse_time e lo si divide per 2
        # (perchè l'impulso percorre la distanza due volte) e poi per 29.1 per la velocità
        # del suono nell'aria (343.2 m/s), che equivale a 0.34320 mm/us, cioè 1cm ogno 29.1 us.
        cm = (pulse_time / 2) / 29.1
        return cm


class HW_511:
    '''Classe che rappresenta il sensore ad infrarossi HW_511

    Attributi:
        hw511 (pin): il sensore in utilizzo    
    '''

    def __init__(self, pin):
        '''Costruttore della classe HW_511

        Args:
            pin (int): Il pin a cui è connesso 
        '''
        self.hw511 = Pin(pin, Pin.IN, Pin.PULL_UP)

    def on(self):
        '''Richiamo al metodo on di Pin
        Accende il led del sensore
        '''
        self.hw511.on()

    def off(self):
        '''Richiamo al metodo off di Pin
        Spegne il led del sensore
        '''
        self.hw511.off()

    def value(self, value=None):
        '''Metodo che legge o modifica il value del pin associato all'oggetto.

        Args:
            [value] (int): 0 | 1
        Restituisce 0 quando attivo, 1 viceversa
        '''
        return self.hw511.value() if (value is None) else self.hw511.value(value)

    def pull(self, pull=None or Pin.PULL_UP or Pin.PULL_DOWN):
        '''Metodo che legge o modifica il pull del sensore.

        Args:
            [pull] (str): Pin.PULL_UP | Pin.PULL_DOWN | None
        '''
        if pull == Pin.PULL_UP:
            self.hw511.pull(pull)
            return "pull=PULL_UP"
        elif pull == Pin.PULL_DOWN:
            self.hw511.pull(pull)
            return "pull=PULL_UP"
        else:
            if pull is not None:
                return "Errore configurazione, modifica il pull."
            else:
                self.hw511.pull()
            # self.hw511.pull(pull)

    # def pull(self, pull=None or Pin.PULL_UP or Pin.PULL_DOWN):
    #     return self.hw511.pull() if pull is None else self.hw511.pull(pull)

    def bool_state(self):
        '''Legge lo stato del sensore
        Ritorna True se il led è acceso, False se spento.
        '''
        return True if self.led.value() == 1 else False

    def state(self):
        #     '''Legge lo stato del sensore'''
        #     return False if self.hw511.value() == 1 else True
        '''Legge lo stato del sensore
        Stampa "Acceso" se True, "Spento" altrimenti.
        '''
        return "Acceso" if self.bool_state() else "Spento"


class OLED:
    '''Classe che rappresenta il display OLED

    Attributi:
        OLED_WIDTH (int): Larghezza in pixel
        OLED_HEIGHT (int): Altezza in pixel
        i2c (I2C): protocollo seriale utilizzato
        oled (SSD1306_I2C): display OLED in utilizzo
    '''

    def __init__(self, scl_pin, sda_pin, width=128, height=64):
        '''Costruttore della classe OLED

        Args:
            scl_pin (Pin): Pin associato per il bus del clock
            sda_pin (Pin): Pin associato per il bus dei dati
            width (int): Larghezza del display
            height (int): Altezza del display
        '''
        self.OLED_WIDTH = width
        self.OLED_HEIGHT = height

        self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.oled = SSD1306_I2C(width, height, self.i2c)

    def text(self, string, x, y):
        '''Metodo utilizzato per scrivere sul display

        Args:
            string (str): La frase che si vuole mostrare
            x (int): La posizione orizzontale (a partire dall'angolo in alto a sinistra)
            y (int): La posizione verticale (a partire dall'angolo in alto a sinistra)
        '''
        self.oled.text(string, x, y)

    def scroll(self, dx, dy):
        '''Metodo utilizzato per "scrollare" i pixel nel display

        Args:
            dx (int): Spostamento orizzontale
            dy (int): Spostamento verticale
        '''
        self.oled.scroll(dx, dy)

    def fill(self, col):
        '''Metodo che "riempie" i pixel del display.

        Args:
            col (int): 1 per colorarlo di nero, 0 per colorarlo di bianco
        '''
        self.oled.fill(col)

    def show(self):
        '''Metodo per mostrare sullo schermo i valori scritti'''
        self.oled.show()

    def clear(self):
        '''Metodo per pulire il display'''
        self.fill(0)
        self.show()


class StepperMotor:
    '''Classe che rappresenta un motore stepper

    Args:
        stepper_pins (list): Lista dei pin usata per il motore
        step_index (int): Idice degli step del motore
        delay_time (float): Tempo di delay tra uno step e l'altro
        step_sequence (list): Array multidimensionale per la sequenza degli step
    '''

    def __init__(self, pin1, pin2, pin3, pin4, delay=0.002):
        '''Costruttore dello StepperMotor

        Args:
            pin1 (int): Pin1 a cui è collegato il motore
            pin2 (int): Pin2 a cui è collegato il motore
            pin3 (int): Pin3 a cui è collegato il motore
            pin4 (int): Pin4 a cui è collegato il motore
            delay (float): Tempo di delay tra uno step e l'altro

        '''
        self.stepper_pins = [Pin(pin1, Pin.OUT), Pin(
            pin2, Pin.OUT), Pin(pin3, Pin.OUT), Pin(pin4, Pin.OUT)]

        # Inizializza l'indice di step
        self.step_index = 0

        # Imposta il tempo di delay tra uno step e l'altro
        self.delay_time = delay

        # Definisce la seguenza degli step completi del motore
        self.step_sequence = [
            [1, 0, 0, 1],
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
        ]

    def delay(self, time=None):
        '''Metodo che legge o modifica il delay tra uno step e l'altro

        Args:
            time (float): tempo di delay degli step
        '''
        if time is None:
            return self.delay_time
        else:
            self.delay_time = time

    def step(self, direction):
        '''Metodo che esegue un singolo step in una determinata direzione

        Args:
            direction (int): Indica il verso di rotazione del motore.
                1 per il senso antiorario | 2 per il senso orario
        '''
        self.step_index = (self.step_index +
                           direction) % len(self.step_sequence)
        for pin_index in range(len(self.stepper_pins)):
            self.stepper_pins[pin_index].value(
                self.step_sequence[self.step_index][pin_index])
        time.sleep(self.delay_time)
