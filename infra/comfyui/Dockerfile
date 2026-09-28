# Etapa 1: clonar ComfyUI (imagen con git, sin depender de apt)
FROM alpine/git:latest AS source
ARG COMFYUI_REF=master
RUN git clone --depth 1 --branch ${COMFYUI_REF} https://github.com/comfyanonymous/ComfyUI.git /src

# Etapa 2: runtime Python
FROM python:3.11-slim
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
WORKDIR /app
COPY --from=source /src /app
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url ${TORCH_INDEX_URL} \
 && pip install --no-cache-dir -r requirements.txt
EXPOSE 8188
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
