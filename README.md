# custom-metrics-dashboard-signoz

# Setups 
% python -m venv .venv
% source .venv/bin/activate
% python -m pip install -r requirements.txt 


# server setup (this takes some time due to torch,transformer installation) 
% create docker-compose.yaml file 
% docker compose up -d llm-server 
% docker compose down -v (to close it)


# run client 
% pip install httpx opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp 
% export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
% export OTEL_RESOURCE_ATTRIBUTES="service.name=llm-client-service"
% python llm_client.py
