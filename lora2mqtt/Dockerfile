FROM python:3.11-alpine

WORKDIR /app

# Copia os arquivos principais
COPY requirements.txt ./
COPY run.sh ./
COPY bridge.py ./

# Copia os módulos que estão na raiz
COPY consts.py ./
COPY devs.py ./
COPY funcs.py ./
COPY globals.py ./
COPY lflora.py ./
COPY msgs.py ./
COPY utils.py ./

# Copia os diretórios de apoio
COPY config/ ./config/
COPY models/ ./models/
COPY models_import/ ./models_import/

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Permissão de execução
RUN chmod +x run.sh

ENTRYPOINT ["./run.sh"]
