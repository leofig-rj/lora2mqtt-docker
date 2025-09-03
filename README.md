# LoRa2MQTT

![Project Stage][project-stage-shield]![Maintenance][maintenance-shield]

<img src="https://raw.githubusercontent.com/leofig-rj/lora2mqtt-docker/main/pictures/LoRa2MQTT logo.png"/>


<img src="https://raw.githubusercontent.com/leofig-rj/leofig-hass-addons/main/lora2mqtt/pictures/LoRa2MQTT logo.png"/>

Integração de dispositivos LoRa com Home Assistant via MQTT.  
Este container conecta dispositivos LoRa à rede MQTT, permitindo automações e monitoramento direto no Home Assistant ou qualquer outro cliente MQTT.
Útil para fazer sua própria infraestrutura LoRa, sem a necessidade de complexas struturas como LoRaWan.


## 📦 Imagem Docker

Disponível em: [Docker Hub - leonardo/lora2mqtt](https://hub.docker.com/r/leofig/lora2mqtt)

## 🚀 Como instalar

### Via linha de comando

```bash
docker run --rm \
  --privileged \
  --network bridge \
  -v $(pwd)/config:/config \
  -e MQTT_HOST=192.168.1.100 \
  -e MQTT_PORT=1883 \
  -e MQTT_USER=usuario \
  -e MQTT_PASS=senha \
  -e NET_ID=0x00 \
  -e FREQUENCY=915E6 \
  -e LOG_LEVEL=INFO \
  -v /dev/ttyUSB0:/dev/ttyUSB0 \
  leofig/lora2mqtt
```

### Via Docker Compose

```bash
version: '3.8'

services:
  lora2mqtt:
    image: leonardo/lora2mqtt
    container_name: lora2mqtt
    restart: unless-stopped
    privileged: true
    environment:
      MQTT_HOST: "192.168.1.100"
      MQTT_PORT: "1883"
      MQTT_USER: "usuario"
      MQTT_PASS: "senha"
      NET_ID: "0x00"
      FREQUENCY: "915E6"
      LOG_LEVEL: "INFO"
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    volumes:
      - /home/user/lora2mqtt/config:/config
    network_mode: bridge
```

⚙️ Variáveis de ambiente

| Variável     | Descrição                                           | Valor padrão |
|--------------|-----------------------------------------------------|--------------|
| MQTT_HOST    | Endereço do broker MQTT (do Home Assistant)         | —            |
| MQTT_PORT    | Porta do broker MQTT                                | 1883         |
| MQTT_USER    | Usuário MQTT                                        | —            |
| MQTT_PASS    | Senha MQTT                                          | —            |
| NET_ID       | ID da rede LoRa                                     | 0x00         |
| FREQUENCY    | Frequência LoRa (433E6, 868E6, 915E6)               | 915E6        |
| LOG_LEVEL    | Nível de log (DEBUG, INFO, WARNING, ERROR)          | INFO         |

📁 Volumes
- /config: pasta para persistência de dados e configurações, em /home/user/lora2mqtt/config

🔌 Dispositivos
- /dev/ttyUSB0: acesso à porta serial com o adaptador USB LoRa.

🛠️ Requisitos
- Docker instalado.
- Acesso à porta serial (/dev/ttyUSB0).
- Broker MQTT acessível.

## 🏠 Acesso no Home Assistant

Uma vez iniciado o container, sem erros, aparecerá dentro da integração MQTT o dispositivo "LoRa2MQTT Bridge", por onde você poderá configurar e manter os dispositivos.

## 🔧 Exemplos de dispositivos

Existem exemplos para uma primeira experiência com o par dispositivo / LoRa2MQTT. Eles usam a bilioteca [LF_Lora][github_LF_LoRa].

O Exemplo [LF_LoRa_USB_Adapter_01][ex_usb] é para criar um adaptador USB LoRa, para ser conectado ao hospedeiro do container e permitir a conexão via LoRa com os dispositivos.

Cada exemplo em Arduino (.ino) contém um arquivo de configuração LoRa2MQTT correspondente (.py). O par .ino / .py de cada exemplo serve de base para desenvolvimento de novos dispositivos.

Os exemplos:

- [LF_LoRa_Model_TEST01.ino][ex_01_ino] / [test01.py][ex_01_py]

- [LF_LoRa_Model_TEST02.ino][ex_02_ino] / [test02.py][ex_02_py]

- [LF_LoRa_Model_TEST03.ino][ex_03_ino] / [test03.py][ex_03_py]

## 🧪 Novos dispositivos

Novos dispositivos podem ser desenvolvidos baseados nos exemplos acima.
O arquivo de configuração .py para LoRa2MQTT deve ser colocado na pasta "/home/user/lora2mqtt/config/models" ou outra que tenha sido utilizada no Docker Compose, para que sejam importados. Note que "/models" é criada automaticamente dentro de "/home/user/lora2mqtt/config", pelo container se não existir.

Para parear o dispositivo no LoRa2MQTT:

- A primeira vez que ligar o dispositivo, ele ficará com o LED piscando indicando que está no modo pareamento (ou indicará pareamento no display se tiver).
- Para colocar o dispositivo no modo pareamento (se ele já não estiver), pressione o botão 5 vezes ou mais.
- No Home Assistant, vá emm "Configuração/Dispositivos & Serviços/MQTT/LoRa2MQTT Bridge" e acione o "Modo Pareamento".
- Depois de algum tempo o LED deve parar de piscar e sensor "info" de "LoRa2MQTT Bridge" deve indicar o MAC do dispositivo conectado.
- Desative o "Modo Pareamento" no "LoRa2MQTT Bridge".
- Um novo dispositivo deve aparecer na tela do "LoRa2MQTT Bridge" dentro de "Dispositivos Conectados".

Nota:

Os arquivos de configuração dos exemplos já estão incluidos no LoRa2MQTT. Novos arquivos deverão ser colocados em "/home/user/lora2mqtt/config/models" ou outra pasta que tenha sido utilizada no Docker Compose.

## 🛠️ Criar nova imagem

Caso queira criar sua própria imagem:

- Copiar a pasta "lora2mqtt" para sua máquina e dela comandar:

```bash
docker build -t leofig/lora2mqtt .

```


🤝 Contribuições
- Pull requests são bem-vindos! Para sugestões, melhorias ou correções, abra uma issue ou entre em contato.

📄 Licença
- Este projeto está sob a licença [MIT][mit]. Veja o arquivo [LICENSE][license] para mais detalhes.

<!-- Markdown link -->
[project-stage-shield]: https://img.shields.io/badge/project%20stage-development%20beta-red.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[github_LF_LoRa]: https://github.com/leofig-rj/Arduino-LF_LoRa
[github_leofig-rj]: https://github.com/leofig-rj
[arduino]:https://arduino.cc/
[lora]:https://www.lora-alliance.org/
[ex_usb]:https://github.com/leofig-rj/Arduino-LF_LoRa/tree/main/examples/LF_LoRa_USB_Adapter_01
[ex_01_ino]:https://github.com/leofig-rj/Arduino-LF_LoRa/tree/main/examples/LF_LoRa_Model_TEST01
[ex_01_py]:https://github.com/leofig-rj/leofig-hass-addons/blob/main/lora2mqtt/rootfs/usr/bin/models/test01.py
[ex_02_ino]:https://github.com/leofig-rj/Arduino-LF_LoRa/tree/main/examples/LF_LoRa_Model_TEST02
[ex_02_py]:https://github.com/leofig-rj/leofig-hass-addons/blob/main/lora2mqtt/rootfs/usr/bin/models/test02.py
[ex_03_ino]:https://github.com/leofig-rj/Arduino-LF_LoRa/tree/main/examples/LF_LoRa_Model_TEST03
[ex_03_py]:https://github.com/leofig-rj/leofig-hass-addons/blob/main/lora2mqtt/rootfs/usr/bin/models/test03.py
[license]:https://github.com/leofig-rj/lora2mqtt-docker/blob/main/LICENSE
[mit]:https://en.wikipedia.org/wiki/MIT_License