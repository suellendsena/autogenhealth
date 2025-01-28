# Usa uma imagem base com Python 3.8
FROM python:3.8-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o contêiner
COPY . /app

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta 8000 para acesso externo, se necessário
EXPOSE 8000

# Comando para executar o script principal
CMD ["python", "main.py"]
