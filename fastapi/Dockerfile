# Multi-stage build para otimização de tamanho
FROM python:3.12-slim as builder

# Instalar dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage de produção
FROM python:3.12-slim

# Instalar dependências runtime + Chrome para Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copiar ambiente virtual do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs && \
    chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Expor porta da aplicação
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log", "--no-server-header"]
