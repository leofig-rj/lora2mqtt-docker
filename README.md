# LoRa2MQTT

Integração de dispositivos LoRa com Home Assistant via MQTT.  
Este container conecta dispositivos LoRa à rede MQTT, permitindo automações e monitoramento direto no Home Assistant ou qualquer outro cliente MQTT.



Integrating your LoRa devices with Home Assistant over MQTT.

Useful for making your own local LoRa infrastructure, without the need for complex structures like LoRaWan.

![Project Stage][project-stage-shield]![Maintenance][maintenance-shield]

<img src="https://raw.githubusercontent.com/leofig-rj/leofig-hass-addons/main/lora2mqtt/pictures/LoRa2MQTT logo.png"/>



## 📦 Imagem Docker

Disponível em: [Docker Hub - leonardo/lora2mqtt](https://hub.docker.com/r/leofig/lora2mqtt)

## 🚀 Como usar

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
| MQTT_HOST    | Endereço do broker MQTT                             | —            |
| MQTT_PORT    | Porta do broker MQTT                                | 1883         |
| MQTT_USER    | Usuário MQTT                                        | —            |
| MQTT_PASS    | Senha MQTT                                          | —            |
| NET_ID       | ID da rede LoRa                                     | 0x00         |
| FREQUENCY    | Frequência LoRa (433E6, 868E6, 915E6)               | 915E6        |
| LOG_LEVEL    | Nível de log (DEBUG, INFO, WARNING, ERROR)          | INFO         |

📁 Volumes
- /config: pasta para persistência de dados e configurações, em /home/user/lora2mqtt/config

🔌 Dispositivos
- /dev/ttyUSB0: acesso à porta serial LoRa

🛠️ Requisitos
- Docker instalado
- Acesso à porta serial (/dev/ttyUSB0)
- Broker MQTT acessível

🤝 Contribuições
- Pull requests são bem-vindos! Para sugestões, melhorias ou correções, abra uma issue ou entre em contato.

📄 Licença
- Este projeto está sob a licença [MIT][mit]. Veja o arquivo [LICENSE][license] para mais detalhes.

## License

This libary is [licensed][license] under the [MIT Licence][mit].

<!-- Markdown link -->
[project-stage-shield]: https://img.shields.io/badge/project%20stage-development%20beta-red.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[github_LF_LoRa]: https://github.com/leofig-rj/Arduino-LF_LoRa
[docs_link]: https://github.com/leofig-rj/leofig-hass-addons/blob/master/lora2mqtt/DOCS.md
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
[license]:https://github.com/leofig-rj/leofig-hass-addons/blob/main/LICENSE
[mit]:https://en.wikipedia.org/wiki/MIT_License