import paho.mqtt.client as mqtt
import serial
import logging
import json
import time
import re
import os

import lflora
import msgs
import devs
import funcs
import globals

# Para MQTT
from consts import ADDON_NAME, ADDON_SLUG, VERSION, UNIQUE, OWNER, HA_PREFIX, LWT_MSG, LWT_QOS, \
    LWT_REATAIN, MQTT_KEEP_ALIVE, MQTT_CLIENT_ID, CMD_GET_USB_MODEL, NET_ID_DEF, SYNC_WORD_DEF, \
    FREQUENCY_DEF, CMD_SET_SYNCH_WORD

########### MAIN ############
def main(broker, port, broker_user, broker_pass):

    # Configuro segundo variáveis de ambiente
    net_id = os.getenv("NET_ID", NET_ID_DEF)
    logging.info(f"net_id: {net_id}")
    frequency = os.getenv("FREQUENCY", FREQUENCY_DEF)
    logging.info(f"frequency: {frequency}")
    synch_word = os.getenv("SYNCH_WORD", SYNC_WORD_DEF)
    logging.debug(f"synch_word: {synch_word}")

    # Dados do sistema não são configuráveis por variáveis de ambiente
    # Mas serão referenciado no docker-compose.yml
    # devices:
    #  - /dev/ttyUSB0:/dev/ttyUSB0
    # volumes:
    #  - /home/usr/lora2mqtt/config:/config
    serial_obj = "/dev/ttyUSB0"
    logging.debug(f"serial_obj: {serial_obj}")
    data_path = "/config"
    logging.debug(f"data_path: {data_path}")

    hex_format = r"^0x[0-9A-Fa-f]{2}$"
    if re.match(hex_format, net_id) is None:
        logging.error(f"net_id: {net_id}, incorrect format! Used {NET_ID_DEF}.")
        net_id = NET_ID_DEF
    if re.match(hex_format, synch_word) is None:
        logging.error(f"synch_word: {synch_word}, incorrect format! Used {SYNC_WORD_DEF}.")
        synch_word = SYNC_WORD_DEF

    # Configurando conexão serial
    try:
        ser = serial.Serial(serial_obj["port"], 115200)
        ser.flush()

    except serial.SerialException as e:
        ser = None  # Define como None para evitar problemas futuros
        logging.error(f"Erro {e} na configuração serial...")

    # LFLoraClass precisa de net_id inteiro
    net_id_int = int(net_id, 16)

    # Inicializando variáveis globais
    globals.g_data_path = data_path             # Tornando o data_path global, tem que ser antes de g_devices...
    globals.g_devices = devs.DeviceManager()    # Criando a instância de dispositivos global
    globals.g_devices.load_devices_to_ram()     # Carregando os dispositivos cadastrados para a RAM
    globals.g_serial = ser                      # Tornando o serial global
    globals.g_lf_lora = lflora.LFLoraClass(net_id_int, 1)  # Criando instância LFLoraClass global, com net_id_int e endereço       
    globals.g_cli_mqtt = LoRa2MQTTClient(broker, port, broker_user, broker_pass) # Criando o cliente MQTT global
            
    # Deixando o cliente vizível localmente
    client = globals.g_cli_mqtt                   

    try:
        
        # Iniciando o Loop geral se serial OK
        if ser:
            # Enviando comando de solicitação de estado da dongue
            cmdUsb = CMD_GET_USB_MODEL
            ser.write(cmdUsb.encode('utf-8'))    # Enviando uma string (precisa ser em bytes)
            logging.debug("Enviado comando solicita estado do adaptador")
            time.sleep(2)  # Aguarda 2 segundos
            # Verificando se tem dado na serial
            if ser.in_waiting > 0:
                # Pegandando o dado e deixando como string
                serial_data = ser.readline().decode('utf-8').strip()
                # Tratando o dado
                if serial_data[0] == '!':
                    # Guardando o usb_id no cliente
                    client.usb_id = serial_data[1:]
                    logging.debug(f"Recebeu do adaptador: {client.usb_id}")

            # Definindo a synch_word e a frequência no adaptador usb
            synch_word_int = int(synch_word, 16)
            cmdUsb = CMD_SET_SYNCH_WORD + f"{synch_word_int:03}{frequency}"
            ser.write(cmdUsb.encode('utf-8'))    # Enviando uma string (precisa ser em bytes)

            # Iniciando a comunicação MQTT
            client.mqtt_connection()
            client.loop_start()  # Inicia o loop MQTT em uma thread separada

            # Loop Geral
            while True:
                # Loop Serial
                msgs.loop_serial()
                # Loop MQTT
                msgs.loop_mqtt()
                # Loop LoRa
                msgs.loop_lora()

    except Exception as e:
        logging.error(f"Erro: {e}")
    finally:
        logging.error("Encerrando aplicação LoRa2MQTT...")
        ser.close()
        client.loop_stop()
        client.disconnect()


########## Classe para MQTT ############
class LoRa2MQTTClient(mqtt.Client):
    def __init__(self, broker, port, broker_user=None, broker_pass=None):
        super().__init__(MQTT_CLIENT_ID, clean_session=True)
        self.connected_flag = False
        self.broker_host = broker
        self.broker_port = port
        self.addon_slug = ADDON_SLUG
        self.addon_name = ADDON_NAME
        self.usb_id = ""
        self.ram_devs = globals.g_devices.get_ram_devs()
        self.num_slaves = None            # Definido em _setup_mqtt_topics
        self.bridge_topic = None          # Definido em _setup_mqtt_topics
        self.bridge_set_topic = None      # Definido em _setup_mqtt_topics
        self.bridge_status_topic = None   # Definido em _setup_mqtt_topics
        self.todos_topic = None           # Definido em _setup_mqtt_topics
        self.work_topics = []             # Definido em _setup_mqtt_topics
        self.set_topics = []              # Definido em _setup_mqtt_topics
        self.masc_uniq_topics = []        # Definido em _setup_mqtt_topics
        self.masc_disc_topics = []        # Definido em _setup_mqtt_topics
        self.lwt_topic = None             # Definido em _setup_mqtt_topics
        self.setup_mqtt_topics()

        # Configurações de autenticação MQTT (se fornecidas)
        if broker_user and broker_pass:
            self.username_pw_set(broker_user, password=broker_pass)
        logging.debug(f"MQTT Usr {broker_user}")
        logging.debug(f"MQTT Psw {broker_pass}")

        # Configura o LWT
        self.will_set(self.lwt_topic, LWT_MSG, qos=LWT_QOS, retain=LWT_REATAIN)

        # Callback para eventos MQTT
        self.on_connect = LoRa2MQTTClient.cb_on_connect
        self.on_disconnect = LoRa2MQTTClient.cb_on_disconnect
        self.on_message = LoRa2MQTTClient.cb_on_message

        # Logging informativo
        logging.info(f"Client {MQTT_CLIENT_ID} Created")

    def setup_mqtt_topics(self):
        """Configura os tópicos MQTT."""
        self.num_slaves = len(self.ram_devs)
        self.bridge_topic = f"{self.addon_slug}/bridge"
        self.bridge_set_topic = f"{self.bridge_topic}/+/set"
        self.bridge_status_topic = f"{self.bridge_topic}/status"
        self.todos_topic = f"{self.addon_slug}/*/+/set"
        self.lwt_topic = self.bridge_status_topic

        # Configura os tópicos para cada slave
        self.work_topics.clear()
        self.set_topics.clear()
        self.masc_uniq_topics.clear()
        self.masc_disc_topics.clear()
        for i in range(self.num_slaves):
            work_topic = f"{self.addon_slug}/{self.ram_devs[i].slaveName}"
            set_topic = f"{work_topic}/+/set"
            masc_uniq_topic = f"{self.addon_slug}_{self.ram_devs[i].slaveMac}_%s"
            masc_disc_topic = f"{HA_PREFIX}/%s/{self.addon_slug}_{self.ram_devs[i].slaveMac}/%s/config"

            self.work_topics.append(work_topic)
            self.set_topics.append(set_topic)
            self.masc_uniq_topics.append(masc_uniq_topic)
            self.masc_disc_topics.append(masc_disc_topic)

        # Logging para verificar se os tópicos foram configurados
        logging.debug("Topicos MQTT configurado com sucesso.")
        logging.debug(f"Bridge Topic: {self.bridge_topic}")
        logging.debug(f"Set Topics: {self.set_topics}")
        logging.debug(f"Masc Disc Topics: {self.masc_disc_topics}")

    def mqtt_connection(self):
        """Tenta conectar ao broker MQTT."""
        try:
            logging.debug(f"Connecting to MQTT broker {self.broker_host}:{self.broker_port}")
            self.connect(self.broker_host, self.broker_port, MQTT_KEEP_ALIVE)
        except Exception as e:
            logging.error(f"Falha ao conectar ao MQTT broker: {e}")

    @classmethod
    def cb_on_message(cls, client, userdata, message):
        """Callback para mensagens recebidas."""
        try:
            # Processa a mensagem no cliente
            client.handle_message(message)
        except Exception as e:
            logging.error(f"Erro processando msg recebida: {e}")

    @classmethod
    def cb_on_disconnect(cls, client, userdata, rc):
        """Callback para desconexões."""
        client.connected_flag = False
        logging.error(f"Client {client._client_id.decode('utf-8')} disconnected!")

    @classmethod
    def cb_on_connect(cls, client, userdata, flags, rc):
        """Callback para conexões."""
        if rc == 0:
            client.connected_flag = True
            logging.info(f"Client {client._client_id.decode('utf-8')} connected successfully!")
            # Publica mensagem de "online" ao conectar
            client.publish(client.lwt_topic, "online", qos=0, retain=True)
            client.on_mqtt_connect()
        else:
            logging.error(f"Failed to connect with code {rc}")

    def handle_message(self, message):
        """Processa mensagens recebidas do MQTT)."""
        logging.debug(f"Processando msg do topico {message.topic}: {message.payload.decode('utf-8')}")
        msgs.on_mqtt_message(message.topic, message.payload.decode('utf-8'))
    
    def on_mqtt_connect(self):
        """Assina os tópicos MQTT necessários ao conectar."""
        try:
            # Subscrever aos tópicos principais
            self.subscribe(self.todos_topic, qos=1)
            self.subscribe(self.bridge_set_topic, qos=1)

            # Subscrever aos tópicos dos slaves
            for i in range(self.num_slaves):
                self.subscribe(self.set_topics[i-1], qos=1)

            # Atualiza status online
            self.online = False
            logging.debug("Assinanados com sucesso a todos os topicos relevantes.")

        except Exception as e:
            logging.error(f"Error subscribing to MQTT topic: {e}")

    def common_discovery(self):
        """
        Realiza a descoberta comum para o dispositivo principal.
        """
        payload = {
            "dev": {
                "ids": [f"{self.addon_slug}_{UNIQUE}"],
                "name": f"{self.addon_name} Bridge",
                "sw": VERSION,
                "hw": self.usb_id,
                "mf": OWNER,
                "mdl": "Bridge"
            }
        }
        return payload

    def common_discovery_ind(self, index):
        """
        Realiza a descoberta individual para um slave LoRa. 
        """
        payload = {
            "dev": {
                "ids": [f"{self.addon_slug}_{self.ram_devs[index].slaveMac}"],
                "cns": [["mac", self.ram_devs[index].slaveMac]],
#                "name": f"{self.ram_devs[index].slaveName} {funcs.last4(self.ram_devs[index].slaveMac)}",
                "name": f"{self.ram_devs[index].slaveName}",
                "sw": self.ram_devs[index].slaveVer,
                "mf": self.ram_devs[index].slaveMan,
                "mdl": self.ram_devs[index].slaveModel,
                "via_device" : f"{self.addon_slug}_{UNIQUE}"
            }
        }
        return payload

    def send_connectivity_discovery(self):
        """
        Envia a descoberta de conectividade para o dispositivo principal.
        """
        payload = self.common_discovery()
        payload.update({
            "~": self.bridge_topic,
            "name": "Conectividade",
            "uniq_id": f"{self.addon_slug}_{UNIQUE}_conectividade",
            "json_attr_t": "~/telemetry",
            "stat_t": "~/status",
            "dev_cla": "connectivity",
            "pl_on": "online",
            "pl_off": "offline"
        })

        topic = f"{HA_PREFIX}/binary_sensor/{self.addon_slug}_{UNIQUE}/conectividade/config"
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_aux_connectivity_discovery(self, index):
        """
        Envia a descoberta auxiliar de conectividade para um slave LoRa.
        """
        name = "Com Lora"
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "json_attr_t": "~/telemetry",
            "stat_t": f"~/{slug}",
            "dev_cla": "connectivity",
            "pl_on": "online",
            "pl_off": "offline"
        })

        topic = self.masc_disc_topics[index] % ("binary_sensor", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_tele_binary_sensor_discovery(self, index, name, entity_category, value_template, device_class):
        """
        Envia a descoberta de um sensor binário de telemetria via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": "~/telemetry",
            "value_template": value_template,
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class

        topic = self.masc_disc_topics[index] % ("binary_sensor", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_tele_sensor_discovery(self, index, name, entity_category, value_template, device_class, units):
        """
        Envia a descoberta de um sensor de telemetria via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": "~/telemetry",
            "value_template": value_template,
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class
        if units:
            payload["unit_of_meas"] = units

        topic = self.masc_disc_topics[index] % ("sensor", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_sensor_discovery(self, index, name, entity_category, device_class, units, state_class, force_update):
        """
        Envia a descoberta de um sensor via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": f"~/{slug}",
            "frc_upd": force_update,
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class
        if units:
            payload["unit_of_meas"] = units
        if state_class:
            payload["stat_cla"] = state_class

        topic = self.masc_disc_topics[index] % ("sensor", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_binary_sensor_discovery(self, index, name, entity_category, device_class):
        """
        Envia a descoberta de um sensor binário via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": f"~/{slug}",
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class

        topic = self.masc_disc_topics[index] % ("binary_sensor", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_button_discovery(self, index, name, entity_category, device_class):
        """
        Envia a descoberta de um botão via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class

        topic = self.masc_disc_topics[index] % ("button", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_switch_discovery(self, index, name, entity_category):
        """
        Envia a descoberta de um interruptor via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
        })
        if entity_category:
            payload["entity_category"] = entity_category

        topic = self.masc_disc_topics[index] % ("switch", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_number_discovery(self, index, name, entity_category, min, max, step):
        """
        Envia a descoberta de um número via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
        })
        if min:
            payload["step"] = min
        if max:
            payload["step"] = max
        if step:
            payload["step"] = step
        if entity_category:
            payload["entity_category"] = entity_category

        topic = self.masc_disc_topics[index] % ("number", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_light_discovery(self, index, name, entity_category, brightness=False, rgb=False):
        """
        Envia a descoberta de uma luz via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery_ind(index)
        payload.update({
            "~": self.work_topics[index],
            "name": name,
            "uniq_id": self.masc_uniq_topics[index] % slug,
            "avty_t": "~/com_lora",
            "schema": "json",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
            "brightness": brightness,
        })
        if rgb:
            payload["supported_color_modes"] = "rgb"
        if entity_category:
            payload["entity_category"] = entity_category

        topic = self.masc_disc_topics[index] % ("light", slug)
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_bridge_sensor_discovery(self, name, entity_category="", device_class="", units="", state_class="", icon="", force_update=True):
        """
        Envia a descoberta de um sensor via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery()
        payload.update({
            "~": self.bridge_topic,
            "name": name,
            "uniq_id": f"{self.addon_slug}_{UNIQUE}_{slug}",
            "avty_t": "~/status",
            "stat_t": f"~/{slug}",
            "frc_upd": force_update,
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class
        if units:
            payload["unit_of_meas"] = units
        if state_class:
            payload["stat_cla"] = state_class
        if icon:
            payload["icon"] = icon

        topic = f"{HA_PREFIX}/sensor/{self.addon_slug}_{UNIQUE}/{slug}/config"
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_bridge_select_discovery(self, name, entity_category, options):
        """
        Envia a descoberta de um select para a ponte via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery()
        payload.update({
            "~": self.bridge_topic,
            "name": name,
            "uniq_id": f"{self.addon_slug}_{UNIQUE}_{slug}",
            "avty_t": "~/status",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
            "options": options,
        })
        if entity_category:
            payload["entity_category"] = entity_category

        topic = f"{HA_PREFIX}/select/{self.addon_slug}_{UNIQUE}/{slug}/config"
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_bridge_text_discovery(self, name, entity_category):
        """
        Envia a descoberta de um select para a ponte via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery()
        payload.update({
            "~": self.bridge_topic,
            "name": name,
            "uniq_id": f"{self.addon_slug}_{UNIQUE}_{slug}",
            "avty_t": "~/status",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
            "min": 2,
        })
        if entity_category:
            payload["entity_category"] = entity_category

        topic = f"{HA_PREFIX}/text/{self.addon_slug}_{UNIQUE}/{slug}/config"
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_bridge_button_discovery(self, name, entity_category, device_class, icon=""):
        """
        Envia a descoberta de um botão para a ponte via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery()
        payload.update({
            "~": self.bridge_topic,
            "name": name,
            "uniq_id": f"{self.addon_slug}_{UNIQUE}_{slug}",
            "avty_t": "~/status",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if device_class:
            payload["dev_cla"] = device_class
        if icon:
            payload["icon"] = icon

        topic = f"{HA_PREFIX}/button/{self.addon_slug}_{UNIQUE}/{slug}/config"
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_bridge_switch_discovery(self, name, entity_category, icon=""):
        """
        Envia a descoberta de um interruptor para a ponte via MQTT.
        """
        slug = funcs.slugify(name)
        payload = self.common_discovery()
        payload.update({
            "~": self.bridge_topic,
            "name": name,
            "uniq_id": f"{self.addon_slug}_{UNIQUE}_{slug}",
            "avty_t": "~/status",
            "stat_t": f"~/{slug}",
            "cmd_t": f"~/{slug}/set",
        })
        if entity_category:
            payload["entity_category"] = entity_category
        if icon:
            payload["icon"] = icon

        topic = f"{HA_PREFIX}/switch/{self.addon_slug}_{UNIQUE}/{slug}/config"
        payload_json = json.dumps(payload)
        return self.pub(topic, 0, True, payload_json)

    def send_delete_discovery(self, domain, name):
        """
        Envia uma mensagem para deletar descoberta da ponte .
        """
        slug = funcs.slugify(name)
        topic = f"{HA_PREFIX}/{domain}/{self.addon_slug}_{UNIQUE}/{slug}/config"
        return self.pub(topic, 0, False, "")

    def send_delete_discovery_x(self, index, domain, name):
        """
        Envia uma mensagem para deletar descoberta de um slave LoRa.
        """
        slug = funcs.slugify(name)
        topic = self.masc_disc_topics[index] % (domain, slug)
        return self.pub(topic, 0, False, "")

    def send_online(self):
        """
        Envia o status online da ponte via MQTT.
        """
        if self.pub(self.bridge_status_topic, 0, True, "online"):
            self.online = True
        else:
            logging.error("Erro enviando status=online")

    def send_com_lora(self):
        """
        Envia o status de conectividade dos dispositivos LoRa.
        """
        for i in range(self.num_slaves):
            if self.last_lora_com[i] != self.lora_com[i]:
                self.last_lora_com[i] = self.lora_com[i]
                status = "online" if self.lora_com[i] else "offline"
                self.pub(f"{self.work_topics[i]}/com_lora", 0, True, status)

    def pub(self, topic, qos, retain, payload):
        """
        Publica uma mensagem no MQTT com tentativas de repetição.

        Args:
            topic (str): O tópico MQTT onde a mensagem será publicada.
            qos (int): Nível de Qualidade de Serviço (QoS).
            retain (bool): Define se a mensagem deve ser retida.
            payload (str): O conteúdo da mensagem.

        Returns:
            bool: True se a mensagem for publicada com sucesso, False caso contrário.
        """
        for attempt in range(10):  # Tenta publicar a mensagem até 10 vezes
            result = self.publish(topic, payload, qos=qos, retain=retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            time.sleep(0.025)  # Espera 25ms entre as tentativas
        return False


########## Inicaialização do AddOn ############
if __name__ == '__main__':
    broker = 'localhost'
    port = 1883
    broker_user = None
    broker_pass = None
    loglevel = 'INFO'

    # Carregar as opções de mqtt
    broker = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    broker_user = os.getenv("MQTT_USER", "mqtt_usr")
    broker_pass = os.getenv("MQTT_PASS", "mqtt_psw")

    # Carregar a opção de log
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configurar o logger
    logging.basicConfig(level=getattr(logging, log_level), datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)-15s - [%(levelname)s] LoRa2MQTT: %(message)s', )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging level: %s", log_level)  
    logger.debug(f"Options: {broker}, {port}, {broker_user}, {broker_pass}")
    
    main(broker, port, broker_user, broker_pass)
