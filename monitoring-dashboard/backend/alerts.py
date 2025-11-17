import smtplib
import requests
from email.mime.text import MimeText
import logging

class AlertSystem:
    def __init__(self):
        self.telegram_bot_token = "YOUR_BOT_TOKEN"
        self.telegram_chat_id = "YOUR_CHAT_ID"
        
    def send_email_alert(self, subject, message, to_email):
        """Envia alerta por email"""
        try:
            # Configuração do email (usando Gmail como exemplo)
            msg = MimeText(message)
            msg['Subject'] = subject
            msg['From'] = 'your_email@gmail.com'
            msg['To'] = to_email
            
            # Usar SMTP do Gmail
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login('your_email@gmail.com', 'your_app_password')
                server.send_message(msg)
            
            logging.info(f"📧 Alerta enviado por email para {to_email}")
        except Exception as e:
            logging.error(f"Erro ao enviar email: {e}")
    
    def send_telegram_alert(self, message):
        """Envia alerta para Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": f"🚨 ALERTA DO SERVIDOR:\n{message}",
                "parse_mode": "Markdown"
            }
            requests.post(url, data=data)
            logging.info("📱 Alerta enviado para Telegram")
        except Exception as e:
            logging.error(f"Erro ao enviar para Telegram: {e}")
    
    def check_and_alert(self, metrics):
        """Verifica métricas e envia alertas se necessário"""
        alerts = []
        
        if metrics["cpu"]["percent"] > 85:
            alert_msg = f"🚨 CRÍTICO: CPU em {metrics['cpu']['percent']}%"
            alerts.append(alert_msg)
            self.send_telegram_alert(alert_msg)
            
        if metrics["memory"]["percent"] > 90:
            alert_msg = f"🚨 CRÍTICO: Memória em {metrics['memory']['percent']}%"
            alerts.append(alert_msg)
            self.send_telegram_alert(alert_msg)
            
        return alerts
