# LoRa2MQTT

Integração de dispositivos LoRa com Home Assistant via MQTT.  
Este container conecta dispositivos LoRa à rede MQTT, permitindo automações e monitoramento direto no Home Assistant ou qualquer outro cliente MQTT.

## 📦 Imagem Docker

Disponível em: [Docker Hub - leonardo/lora2mqtt](https://hub.docker.com/r/leofig/lora2mqtt)

## 🚀 Como usar

### Via linha de comando

```bash
docker run --rm \
  --privileged \
  --network host \
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
      - "/dev/ttyUSB0:/dev/ttyUSB0"
    volumes:
      - /home/user/lora2mqtt/config:/config
    network_mode: "bridge"
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
| SYNCH_WORD   | Palavra de sincronização LoRa                       | 34           |

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
- Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

