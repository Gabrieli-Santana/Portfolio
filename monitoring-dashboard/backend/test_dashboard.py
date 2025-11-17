# monitoring-dashboard/backend/guaranteed_server.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import psutil
import uvicorn

app = FastAPI()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoramento</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f0f0f0; }
        .card { background: white; padding: 20px; margin: 10px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric { font-size: 24px; font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <h1>✅ Dashboard</h1>
    
    <div class="card">
        <h3>⚡ CPU</h3>
        <div class="metric" id="cpu">Carregando...</div>
    </div>
    
    <div class="card">
        <h3>💾 Memória</h3>
        <div class="metric" id="memory">Carregando...</div>
    </div>
    
    <div class="card">
        <h3>🌐 Status</h3>
        <div id="status">Conectado ao servidor!</div>
    </div>

    <script>
        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                document.getElementById('cpu').textContent = data.cpu.percent + '%';
                document.getElementById('memory').textContent = data.memory.percent + '%';
                
            } catch (error) {
                document.getElementById('status').textContent = 'Erro: ' + error;
            }
        }
        
        // Atualiza a cada 3 segundos
        setInterval(updateMetrics, 3000);
        updateMetrics();
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.get("/api/metrics")
async def get_metrics():
    """Endpoint simples de métricas"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return {
        "cpu": {"percent": cpu_percent},
        "memory": {"percent": memory.percent},
        "status": "online"
    }

if __name__ == "__main__":
    print("🚀 INICIANDO SERVIDOR GARANTIDO...")
    print("📍 Acesse: http://localhost:8000")
    print("📍 Ou: http://127.0.0.1:8000")
    print("📍 API: http://localhost:8000/api/metrics")
    
    # Força o uvicorn a rodar corretamente
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )
