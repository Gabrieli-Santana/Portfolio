# app.py
from flask import Flask, request, session, redirect, url_for, flash, jsonify
import sqlite3
import os
import json
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'mindcare_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Sistema de Conquistas
ACHIEVEMENTS = {
    'primeiro_passo': {'name': 'Primeiros Passos', 'description': 'Registre seu primeiro humor', 'icon': '🚶', 'points': 50},
    'consistencia_7': {'name': 'Consistência Semanal', 'description': 'Registre humor por 7 dias seguidos', 'icon': '📅', 'points': 100},
    'meditacao_mestre': {'name': 'Mestre da Meditação', 'description': 'Complete 10 sessões de meditação', 'icon': '🧘', 'points': 150},
    'nivel_5': {'name': 'Ascensão', 'description': 'Alcance o nível 5', 'icon': '⭐', 'points': 200},
    'estrategista': {'name': 'Estrategista', 'description': 'Complete 5 metas', 'icon': '🎯', 'points': 150},
    'atividades_mestre': {'name': 'Explorador', 'description': 'Complete 5 atividades guiadas diferentes', 'icon': '🏅', 'points': 100},
}

# Categorias de metas
GOAL_CATEGORIES = {
    'saude_mental': {'name': 'Saúde Mental', 'icon': '🧠'},
    'exercicio': {'name': 'Exercício Físico', 'icon': '💪'},
    'sono': {'name': 'Qualidade do Sono', 'icon': '🌙'},
    'geral': {'name': 'Geral', 'icon': '🎯'},
}

# Tipos de notificação
NOTIFICATION_TYPES = {
    'reminder': {'color': 'blue', 'icon': '⏰'},
    'achievement': {'color': 'yellow', 'icon': '🏆'},
    'insight': {'color': 'purple', 'icon': '💡'},
    'goal': {'color': 'green', 'icon': '🎯'},
    'system': {'color': 'gray', 'icon': '🔔'},
}

# Sistema de Atividades Guiadas
GUIDED_ACTIVITIES = {
    'respiração_profunda': {
        'name': 'Respiração Profunda',
        'description': 'Exercício de respiração para acalmar a mente e reduzir a ansiedade',
        'duration': 5,
        'points': 20,
        'icon': '🌬️',
        'category': 'relaxamento',
        'steps': [
            {'instruction': 'Encontre uma posição confortável, sentado ou deitado', 'duration': 0, 'type': 'preparation'},
            {'instruction': 'Feche os olhos e coloque uma mão sobre o abdômen', 'duration': 0, 'type': 'preparation'},
            {'instruction': 'Inspire profundamente pelo nariz por 4 segundos', 'duration': 4, 'type': 'breathing_in'},
            {'instruction': 'Segure a respiração por 4 segundos', 'duration': 4, 'type': 'holding'},
            {'instruction': 'Expire lentamente pela boca por 6 segundos', 'duration': 6, 'type': 'breathing_out'},
            {'instruction': 'Repita este ciclo por mais 2 minutos', 'duration': 120, 'type': 'repetition'},
            {'instruction': 'Abra os olhos e observe como se sente', 'duration': 0, 'type': 'completion'}
        ]
    },
    'scan_corporal': {
        'name': 'Scan Corporal',
        'description': 'Meditação de atenção plena para reconectar com o corpo',
        'duration': 10,
        'points': 30,
        'icon': '👁️',
        'category': 'mindfulness',
        'steps': [
            {'instruction': 'Deite-se em uma posição confortável com os olhos fechados', 'duration': 0, 'type': 'preparation'},
            {'instruction': 'Traga atenção para os dedos dos pés... observe qualquer sensação', 'duration': 30, 'type': 'body_scan'},
            {'instruction': 'Agora mova para os pés... tornozelos... panturrilhas', 'duration': 30, 'type': 'body_scan'},
            {'instruction': 'Perceba as coxas... quadris... região pélvica', 'duration': 30, 'type': 'body_scan'},
            {'instruction': 'Scan abdômen... tórax... costas', 'duration': 30, 'type': 'body_scan'},
            {'instruction': 'Observe mãos... braços... ombros', 'duration': 30, 'type': 'body_scan'},
            {'instruction': 'Atenção para pescoço... rosto... couro cabeludo', 'duration': 30, 'type': 'body_scan'},
            {'instruction': 'Agora sinta seu corpo como um todo por um momento', 'duration': 30, 'type': 'integration'},
            {'instruction': 'Quando estiver pronto, abra suavemente os olhos', 'duration': 0, 'type': 'completion'}
        ]
    },
    'gratidao_guia': {
        'name': 'Diário da Gratidão',
        'description': 'Prática guiada para cultivar sentimentos de gratidão',
        'duration': 8,
        'points': 25,
        'icon': '🙏',
        'category': 'positividade',
        'steps': [
            {'instruction': 'Pegue um caderno ou abra um documento digital', 'duration': 0, 'type': 'preparation'},
            {'instruction': 'Respire fundo 3 vezes para se centrar', 'duration': 10, 'type': 'centering'},
            {'instruction': 'Escreva 3 coisas pelas quais você é grato hoje', 'duration': 120, 'type': 'writing'},
            {'instruction': 'Para cada item, reflita sobre o porquê da gratidão', 'duration': 90, 'type': 'reflection'},
            {'instruction': 'Como essas coisas positivas afetaram seu dia?', 'duration': 60, 'type': 'reflection'},
            {'instruction': 'Feche os olhos e sinta a gratidão por 1 minuto', 'duration': 60, 'type': 'feeling'},
            {'instruction': 'Anote um compromisso de gratidão para amanhã', 'duration': 30, 'type': 'commitment'}
        ]
    },
    'ansiedade_5sentidos': {
        'name': 'Técnica 5-4-3-2-1',
        'description': 'Exercício para reduzir ansiedade usando os sentidos',
        'duration': 7,
        'points': 22,
        'icon': '🎯',
        'category': 'ansiedade',
        'steps': [
            {'instruction': 'Respire fundo e observe seu ambiente atual', 'duration': 0, 'type': 'preparation'},
            {'instruction': 'Identifique 5 coisas que você pode VER ao seu redor', 'duration': 30, 'type': 'sight'},
            {'instruction': 'Toque em 4 coisas que você pode SENTIR a textura', 'duration': 30, 'type': 'touch'},
            {'instruction': 'Preste atenção em 3 coisas que você pode OUVIR', 'duration': 30, 'type': 'hearing'},
            {'instruction': 'Note 2 coisas que você pode CHEIRAR', 'duration': 30, 'type': 'smell'},
            {'instruction': 'Identifique 1 coisa que você pode SABOREAR', 'duration': 30, 'type': 'taste'},
            {'instruction': 'Respire fundo e observe como se sente agora', 'duration': 0, 'type': 'completion'}
        ]
    },
    'auto_compaixtao': {
        'name': 'Auto-Compaixão',
        'description': 'Prática para desenvolver compaixão por si mesmo',
        'duration': 6,
        'points': 18,
        'icon': '💖',
        'category': 'autoestima',
        'steps': [
            {'instruction': 'Sente-se confortavelmente e coloque as mãos sobre o coração', 'duration': 0, 'type': 'preparation'},
            {'instruction': 'Lembre-se de um momento difícil que está passando', 'duration': 20, 'type': 'reflection'},
            {'instruction': 'Repita mentalmente: "Este é um momento de sofrimento"', 'duration': 15, 'type': 'phrase'},
            {'instruction': '"O sofrimento faz parte da vida humana"', 'duration': 15, 'type': 'phrase'},
            {'instruction': 'Agora: "Que eu seja gentil comigo mesmo"', 'duration': 15, 'type': 'phrase'},
            {'instruction': '"Que eu me dê a compaixão que preciso"', 'duration': 15, 'type': 'phrase'},
            {'instruction': 'Sinta o calor das mãos no peito por mais um momento', 'duration': 30, 'type': 'integration'},
            {'instruction': 'Quando pronto, abra os olhos gentilmente', 'duration': 0, 'type': 'completion'}
        ]
    }
}

def get_db_connection():
    conn = sqlite3.connect('mindcare.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                streak INTEGER DEFAULT 0,
                last_login DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mood TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT NOT NULL,
                points_earned INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id TEXT NOT NULL,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                goal_type TEXT DEFAULT 'geral',
                target_date DATE,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # TABELA DE NOTIFICAÇÕES
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'system',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # TABELA DE CONFIGURAÇÕES DE NOTIFICAÇÃO
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                daily_reminder BOOLEAN DEFAULT TRUE,
                reminder_time TIME DEFAULT '20:00',
                achievement_notifications BOOLEAN DEFAULT TRUE,
                goal_reminders BOOLEAN DEFAULT TRUE,
                weekly_insights BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # TABELA DE ATIVIDADES COMPLETADAS
        conn.execute('''
            CREATE TABLE IF NOT EXISTS completed_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_id TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, activity_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados criado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def check_achievements(user_id, achievement_type):
    conn = get_db_connection()
    try:
        existing = conn.execute(
            'SELECT * FROM achievements WHERE user_id = ? AND achievement_id = ?',
            (user_id, achievement_type)
        ).fetchone()
        
        if not existing:
            achievement = ACHIEVEMENTS.get(achievement_type)
            if achievement:
                conn.execute(
                    'INSERT INTO achievements (user_id, achievement_id) VALUES (?, ?)',
                    (user_id, achievement_type)
                )
                conn.execute(
                    'UPDATE users SET points = points + ? WHERE id = ?',
                    (achievement['points'], user_id)
                )
                # Criar notificação de conquista
                create_notification(
                    user_id, 
                    '🏆 Conquista Desbloqueada!', 
                    f'Você desbloqueou "{achievement["name"]}" e ganhou {achievement["points"]} pontos!',
                    'achievement'
                )
                conn.commit()
                flash(f'🏆 {achievement["name"]} desbloqueada! +{achievement["points"]} pontos', 'success')
    except Exception as e:
        print(f"Erro ao verificar conquista: {e}")
    finally:
        conn.close()

# SISTEMA DE NOTIFICAÇÕES
def create_notification(user_id, title, message, notification_type='system'):
    """Cria uma nova notificação para o usuário"""
    conn = get_db_connection()
    try:
        # Verificar configurações do usuário
        settings = conn.execute(
            'SELECT * FROM notification_settings WHERE user_id = ?', (user_id,)
        ).fetchone()
        
        # Se não existem configurações, criar padrão
        if not settings:
            conn.execute(
                'INSERT INTO notification_settings (user_id) VALUES (?)', (user_id,)
            )
            conn.commit()
        
        # Inserir notificação
        conn.execute(
            'INSERT INTO notifications (user_id, title, message, notification_type) VALUES (?, ?, ?, ?)',
            (user_id, title, message, notification_type)
        )
        conn.commit()
        
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")
    finally:
        conn.close()

def get_unread_notifications_count(user_id):
    """Retorna a quantidade de notificações não lidas"""
    conn = get_db_connection()
    try:
        count = conn.execute(
            'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = FALSE',
            (user_id,)
        ).fetchone()
        return count['count'] if count else 0
    except Exception as e:
        print(f"Erro ao contar notificações: {e}")
        return 0
    finally:
        conn.close()

def generate_intelligent_insights(user_id):
    """Gera insights inteligentes baseados no comportamento do usuário"""
    conn = get_db_connection()
    try:
        # Insight 1: Consistência
        consistency = conn.execute('''
            SELECT COUNT(DISTINCT DATE(created_at)) as active_days 
            FROM mood_entries 
            WHERE user_id = ? AND created_at >= date('now', '-7 days')
        ''', (user_id,)).fetchone()
        
        if consistency and consistency['active_days'] >= 5:
            create_notification(
                user_id,
                '📊 Excelente Consistência!',
                'Você registrou seu humor em 5 dos últimos 7 dias! Continue assim! 🎉',
                'insight'
            )
        
        # Insight 2: Metas em andamento
        pending_goals = conn.execute('''
            SELECT COUNT(*) as count FROM goals 
            WHERE user_id = ? AND completed = FALSE AND target_date < date('now')
        ''', (user_id,)).fetchone()
        
        if pending_goals and pending_goals['count'] > 0:
            create_notification(
                user_id,
                '🎯 Metas Atrasadas',
                f'Você tem {pending_goals["count"]} meta(s) com prazo vencido. Que tal revisá-las?',
                'goal'
            )
        
        # Insight 3: Progresso de nível
        user = conn.execute('SELECT level FROM users WHERE id = ?', (user_id,)).fetchone()
        if user and user['level'] >= 3:
            next_level_points = user['level'] * 50
            current_points = conn.execute('SELECT points FROM users WHERE id = ?', (user_id,)).fetchone()
            
            if current_points and current_points['points'] >= next_level_points - 10:
                create_notification(
                    user_id,
                    '⭐ Quase lá!',
                    'Você está muito perto de subir de nível! Continue se dedicando! 🚀',
                    'insight'
                )
        
        # Insight 4: Padrão de humor
        mood_pattern = conn.execute('''
            SELECT mood, COUNT(*) as count 
            FROM mood_entries 
            WHERE user_id = ? AND created_at >= date('now', '-7 days')
            GROUP BY mood ORDER BY count DESC LIMIT 1
        ''', (user_id,)).fetchone()
        
        if mood_pattern:
            mood_emojis = {'😢': 'triste', '😕': 'preocupado', '😐': 'neutro', '😊': 'feliz', '😄': 'muito feliz'}
            dominant_mood = mood_emojis.get(mood_pattern['mood'], 'neutro')
            
            if mood_pattern['count'] >= 3:
                create_notification(
                    user_id,
                    '💡 Padrão Identificado',
                    f'Na última semana, você esteve principalmente {dominant_mood}. Que tal refletir sobre isso?',
                    'insight'
                )
        
    except Exception as e:
        print(f"Erro ao gerar insights: {e}")
    finally:
        conn.close()

def check_daily_reminder(user_id):
    """Verifica se o usuário precisa de lembrete diário"""
    conn = get_db_connection()
    try:
        # Verificar se já registrou humor hoje
        today_entry = conn.execute('''
            SELECT COUNT(*) as count FROM mood_entries 
            WHERE user_id = ? AND DATE(created_at) = DATE('now')
        ''', (user_id,)).fetchone()
        
        # Verificar configurações
        settings = conn.execute(
            'SELECT daily_reminder FROM notification_settings WHERE user_id = ?', (user_id,)
        ).fetchone()
        
        if settings and settings['daily_reminder'] and today_entry['count'] == 0:
            # Verificar se já enviou lembrete hoje
            today_reminder = conn.execute('''
                SELECT COUNT(*) as count FROM notifications 
                WHERE user_id = ? AND notification_type = 'reminder' 
                AND DATE(created_at) = DATE('now')
            ''', (user_id,)).fetchone()
            
            if today_reminder['count'] == 0:
                create_notification(
                    user_id,
                    '⏰ Lembrete Diário',
                    'Como você está se sentindo hoje? Registre seu humor para manter sua sequência! 😊',
                    'reminder'
                )
        
    except Exception as e:
        print(f"Erro ao verificar lembrete: {e}")
    finally:
        conn.close()

# Sistema de Estatísticas
def get_user_statistics(user_id):
    """Retorna estatísticas detalhadas do usuário"""
    conn = get_db_connection()
    try:
        # Estatísticas básicas
        stats = conn.execute('''
            SELECT 
                COUNT(*) as total_entries,
                COUNT(DISTINCT DATE(created_at)) as active_days,
                AVG(CASE 
                    WHEN mood = '😢' THEN 1
                    WHEN mood = '😕' THEN 2
                    WHEN mood = '😐' THEN 3
                    WHEN mood = '😊' THEN 4
                    WHEN mood = '😄' THEN 5
                END) as avg_mood_score
            FROM mood_entries 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        # Distribuição de humor
        mood_distribution = conn.execute('''
            SELECT mood, COUNT(*) as count 
            FROM mood_entries 
            WHERE user_id = ? 
            GROUP BY mood 
            ORDER BY count DESC
        ''', (user_id,)).fetchall()
        
        # Metas e conquistas
        goals_stats = conn.execute('''
            SELECT 
                COUNT(*) as total_goals,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_goals
            FROM goals 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        # Atividade recente
        recent_activity = conn.execute('''
            SELECT 
                COUNT(*) as entries_last_7_days
            FROM mood_entries 
            WHERE user_id = ? AND created_at >= date('now', '-7 days')
        ''', (user_id,)).fetchone()
        
        # Atividades completadas
        completed_activities = conn.execute('''
            SELECT COUNT(DISTINCT activity_id) as unique_activities
            FROM completed_activities 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        return {
            'total_entries': stats['total_entries'] or 0,
            'active_days': stats['active_days'] or 0,
            'avg_mood_score': round(stats['avg_mood_score'] or 0, 2),
            'mood_distribution': dict(mood_distribution),
            'total_goals': goals_stats['total_goals'] or 0,
            'completed_goals': goals_stats['completed_goals'] or 0,
            'entries_last_7_days': recent_activity['entries_last_7_days'] or 0,
            'unique_activities': completed_activities['unique_activities'] or 0
        }
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return {}
    finally:
        conn.close()

def generate_personalized_insights(stats, user_id):
    """Gera insights personalizados baseados nas estatísticas do usuário"""
    insights = []
    
    # Insight sobre consistência
    if stats['entries_last_7_days'] >= 5:
        insights.append('''
        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">🔥</span>
                <div>
                    <div class="font-bold text-green-800">Excelente Consistência!</div>
                    <div class="text-green-600">Você tem mantido uma rotina sólida de registros. Continue assim!</div>
                </div>
            </div>
        </div>
        ''')
    elif stats['entries_last_7_days'] <= 2:
        insights.append('''
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">💡</span>
                <div>
                    <div class="font-bold text-yellow-800">Que tal retomar?</div>
                    <div class="text-yellow-600">Você registrou pouco nos últimos dias. Que tal voltar à rotina?</div>
                </div>
            </div>
        </div>
        ''')
    
    # Insight sobre humor médio
    if stats['avg_mood_score'] >= 4:
        insights.append('''
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">😊</span>
                <div>
                    <div class="font-bold text-blue-800">Humor Positivo!</div>
                    <div class="text-blue-600">Seu humor médio está muito bom! Ótimo trabalho no autocuidado.</div>
                </div>
            </div>
        </div>
        ''')
    elif stats['avg_mood_score'] <= 2.5:
        insights.append('''
        <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">🤗</span>
                <div>
                    <div class="font-bold text-purple-800">Cuidado com Você</div>
                    <div class="text-purple-600">Seu humor está mais baixo. Que tal tentar uma atividade guiada?</div>
                </div>
            </div>
        </div>
        ''')
    
    # Insight sobre metas
    if stats['total_goals'] > 0 and stats['completed_goals'] == stats['total_goals']:
        insights.append('''
        <div class="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">🎯</span>
                <div>
                    <div class="font-bold text-indigo-800">Metastratego!</div>
                    <div class="text-indigo-600">Você concluiu todas as suas metas! Incrível foco e determinação.</div>
                </div>
            </div>
        </div>
        ''')
    
    # Insight sobre atividades
    if stats['unique_activities'] >= 3:
        insights.append(f'''
        <div class="bg-pink-50 border border-pink-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">🏅</span>
                <div>
                    <div class="font-bold text-pink-800">Explorador Ativo!</div>
                    <div class="text-pink-600">Você já experimentou {stats["unique_activities"]} atividades diferentes! Continue explorando.</div>
                </div>
            </div>
        </div>
        ''')
    
    if not insights:
        insights.append('''
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div class="flex items-center">
                <span class="text-2xl mr-3">📝</span>
                <div>
                    <div class="font-bold text-gray-800">Continue Registrando</div>
                    <div class="text-gray-600">Quanto mais você usar o MindCare, mais insights personalizados receberá!</div>
                </div>
            </div>
        </div>
        ''')
    
    return '\n'.join(insights)

# Sistema de Lembretes Inteligentes
def check_and_send_reminders():
    """Verifica e envia lembretes inteligentes para todos os usuários"""
    conn = get_db_connection()
    try:
        # Buscar todos os usuários ativos
        users = conn.execute('SELECT id FROM users').fetchall()
        
        for user in users:
            user_id = user['id']
            
            # Verificar lembretes diários
            check_daily_reminder(user_id)
            
            # Verificar metas próximas do prazo
            upcoming_goals = conn.execute('''
                SELECT * FROM goals 
                WHERE user_id = ? AND completed = FALSE 
                AND target_date BETWEEN date('now') AND date('now', '+2 days')
            ''', (user_id,)).fetchall()
            
            for goal in upcoming_goals:
                create_notification(
                    user_id,
                    '⏰ Meta Próxima do Prazo',
                    f'Sua meta "{goal["title"]}" está próxima do prazo!',
                    'goal'
                )
            
            # Insights semanais (aos domingos)
            if datetime.now().weekday() == 6:  # Domingo
                generate_intelligent_insights(user_id)
                
    except Exception as e:
        print(f"Erro ao verificar lembretes: {e}")
    finally:
        conn.close()

# ROTAS PRINCIPAIS
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MindCare Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-500 to-purple-600 min-h-screen flex items-center justify-center">
        <div class="bg-white rounded-2xl shadow-2xl p-8 max-w-4xl w-full mx-4">
            <div class="text-center">
                <div class="text-6xl mb-4">🧠</div>
                <h1 class="text-5xl font-bold text-gray-800 mb-4">MindCare Pro</h1>
                <p class="text-gray-600 mb-6 text-xl">Sua plataforma inteligente para bem-estar mental</p>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="bg-blue-50 p-6 rounded-xl">
                        <div class="text-3xl text-blue-500 mb-3">😊</div>
                        <h3 class="font-bold text-lg mb-2">Acompanhamento</h3>
                        <p class="text-gray-600">Registre seus sentimentos</p>
                    </div>
                    
                    <div class="bg-green-50 p-6 rounded-xl">
                        <div class="text-3xl text-green-500 mb-3">🔔</div>
                        <h3 class="font-bold text-lg mb-2">Notificações</h3>
                        <p class="text-gray-600">Insights inteligentes</p>
                    </div>
                    
                    <div class="bg-purple-50 p-6 rounded-xl">
                        <div class="text-3xl text-purple-500 mb-3">🎯</div>
                        <h3 class="font-bold text-lg mb-2">Atividades Guiadas</h3>
                        <p class="text-gray-600">Exercícios práticos</p>
                    </div>
                </div>
                
                <a href="/login" class="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-4 px-8 rounded-lg transition duration-300 inline-block text-lg">
                    🚀 Começar Jornada
                </a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        
        if not username:
            flash('Por favor, digite um nome.', 'error')
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        try:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()
            
            today = datetime.now().date()
            
            if not user:
                conn.execute(
                    'INSERT INTO users (username, points, level, streak, last_login) VALUES (?, ?, ?, ?, ?)',
                    (username, 0, 1, 1, today)
                )
                conn.commit()
                user = conn.execute(
                    'SELECT * FROM users WHERE username = ?', (username,)
                ).fetchone()
                
                # Notificação de boas-vindas
                create_notification(
                    user['id'],
                    '👋 Bem-vindo ao MindCare!',
                    'Estamos felizes em tê-lo conosco! Comece registrando como você está se sentindo hoje. 😊',
                    'system'
                )
                
                flash('🎉 Conta criada! Bem-vindo!', 'success')
                check_achievements(user['id'], 'primeiro_passo')
            else:
                conn.execute(
                    'UPDATE users SET last_login = ? WHERE id = ?',
                    (today, user['id'])
                )
                conn.commit()
                
                # Gerar insights ao fazer login
                generate_intelligent_insights(user['id'])
                check_daily_reminder(user['id'])
                
                flash(f'👋 Bem-vindo de volta, {username}!', 'success')
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'❌ Erro: {str(e)}', 'error')
            return redirect(url_for('login'))
        finally:
            conn.close()
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-500 to-purple-600 min-h-screen flex items-center justify-center">
        <div class="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
            <div class="text-center mb-6">
                <div class="text-4xl mb-2">🔐</div>
                <h2 class="text-3xl font-bold text-gray-800">Entrar</h2>
                <p class="text-gray-600 mt-2">Sua jornada começa aqui</p>
            </div>
            
            <form method="POST">
                <div class="mb-6">
                    <label class="block text-gray-700 mb-2 font-bold">Nome</label>
                    <input type="text" name="username" placeholder="Digite seu nome" 
                           class="w-full px-4 py-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                           required>
                </div>
                
                <button type="submit" class="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-4 px-4 rounded-lg transition duration-300 text-lg">
                    🚀 Entrar
                </button>
            </form>
            
            <div class="mt-6 text-center">
                <a href="/" class="text-blue-500 hover:text-blue-600 text-lg">← Voltar</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        
        stats = conn.execute('''
            SELECT COUNT(*) as total_entries FROM mood_entries WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
        recent_moods = conn.execute('''
            SELECT mood, notes, created_at FROM mood_entries 
            WHERE user_id = ? ORDER BY created_at DESC LIMIT 5
        ''', (session['user_id'],)).fetchall()
        
        recent_goals = conn.execute('''
            SELECT * FROM goals WHERE user_id = ? AND completed = FALSE ORDER BY created_at DESC LIMIT 3
        ''', (session['user_id'],)).fetchall()
        
        # Notificações não lidas
        unread_count = get_unread_notifications_count(session['user_id'])
        
        # Notificações recentes
        recent_notifications = conn.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (session['user_id'],)).fetchall()
        
        moods_html = ""
        for mood in recent_moods:
            try:
                date_obj = datetime.strptime(mood['created_at'], '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d/%m')
            except:
                formatted_date = mood['created_at'][:10]
            
            moods_html += f'''
            <div class="bg-white p-3 rounded-lg border-l-4 border-blue-500 shadow-sm">
                <div class="flex items-center justify-between">
                    <span class="text-2xl">{mood["mood"]}</span>
                    <span class="text-sm text-gray-500">{formatted_date}</span>
                </div>
                {f'<p class="text-gray-600 mt-1 text-sm">{mood["notes"]}</p>' if mood["notes"] else ''}
            </div>
            '''
        
        if not moods_html:
            moods_html = '<p class="text-gray-500 text-center py-4">Nenhum registro ainda.</p>'

        goals_html = ""
        for goal in recent_goals:
            goals_html += f'''
            <div class="bg-white p-4 rounded-lg border-l-4 border-green-500 shadow-sm">
                <h4 class="font-bold text-gray-800">{goal["title"]}</h4>
                <p class="text-sm text-gray-600">{goal["goal_type"]}</p>
            </div>
            '''
        
        if not goals_html:
            goals_html = '<p class="text-gray-500 text-center py-4">Nenhuma meta ativa.</p>'

        notifications_html = ""
        for notification in recent_notifications:
            notification_type = NOTIFICATION_TYPES.get(notification['notification_type'], NOTIFICATION_TYPES['system'])
            try:
                date_obj = datetime.strptime(notification['created_at'], '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%H:%M')
            except:
                formatted_date = notification['created_at'][11:16]
            
            read_class = "bg-gray-50" if notification['is_read'] else "bg-white border-l-4 border-blue-500"
            
            notifications_html += f'''
            <div class="{read_class} p-3 rounded-lg shadow-sm mb-2">
                <div class="flex items-start space-x-3">
                    <span class="text-lg">{notification_type['icon']}</span>
                    <div class="flex-1">
                        <div class="font-semibold text-gray-800">{notification["title"]}</div>
                        <div class="text-sm text-gray-600">{notification["message"]}</div>
                        <div class="text-xs text-gray-400 mt-1">{formatted_date}</div>
                    </div>
                </div>
            </div>
            '''
        
        if not notifications_html:
            notifications_html = '<p class="text-gray-500 text-center py-4">Nenhuma notificação.</p>'

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - MindCare</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50 min-h-screen">
            <nav class="bg-white shadow-lg">
                <div class="max-w-7xl mx-auto px-4">
                    <div class="flex justify-between items-center py-4">
                        <div class="flex items-center">
                            <span class="text-3xl mr-3">🧠</span>
                            <span class="font-bold text-2xl">MindCare</span>
                        </div>
                        <div class="flex items-center space-x-6">
                            <a href="/notificacoes" class="relative">
                                <span class="text-2xl">🔔</span>
                                {f'<span class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center">{unread_count}</span>' if unread_count > 0 else ''}
                            </a>
                            <span class="text-gray-700">Olá, <strong>{session["username"]}</strong>!</span>
                            <a href="/logout" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg">Sair</a>
                        </div>
                    </div>
                </div>
            </nav>

            <div class="max-w-7xl mx-auto px-4 py-8">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="bg-blue-500 text-white rounded-2xl p-6 text-center">
                        <div class="text-3xl mb-3">🎯</div>
                        <div class="text-3xl font-bold">{user["points"] or 0}</div>
                        <div>Pontos</div>
                    </div>
                    
                    <div class="bg-green-500 text-white rounded-2xl p-6 text-center">
                        <div class="text-3xl mb-3">📈</div>
                        <div class="text-3xl font-bold">{user["level"] or 1}</div>
                        <div>Nível</div>
                    </div>
                    
                    <div class="bg-purple-500 text-white rounded-2xl p-6 text-center">
                        <div class="text-3xl mb-3">🔔</div>
                        <div class="text-3xl font-bold">{unread_count}</div>
                        <div>Notificações</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div class="lg:col-span-2">
                        <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
                            <h3 class="text-xl font-bold mb-4">😊 Registrar Humor</h3>
                            <form action="/registrar_humor" method="POST" class="space-y-4">
                                <div class="flex justify-between">
                                    <button type="submit" name="mood" value="😢" class="text-4xl hover:scale-125 transition">😢</button>
                                    <button type="submit" name="mood" value="😕" class="text-4xl hover:scale-125 transition">😕</button>
                                    <button type="submit" name="mood" value="😐" class="text-4xl hover:scale-125 transition">😐</button>
                                    <button type="submit" name="mood" value="😊" class="text-4xl hover:scale-125 transition">😊</button>
                                    <button type="submit" name="mood" value="😄" class="text-4xl hover:scale-125 transition">😄</button>
                                </div>
                                <textarea name="notes" placeholder="Observações..." class="w-full p-3 border rounded-lg"></textarea>
                                <button type="submit" class="w-full bg-green-500 text-white py-3 rounded-lg">Salvar (+10 pontos)</button>
                            </form>
                        </div>

                        <div class="bg-white rounded-2xl shadow-lg p-6">
                            <h3 class="text-xl font-bold mb-4">📝 Histórico Recente</h3>
                            <div class="space-y-3">
                                {moods_html}
                            </div>
                        </div>
                    </div>

                    <div class="space-y-6">
                        <div class="bg-white rounded-2xl shadow-lg p-6">
                            <h3 class="text-xl font-bold mb-4">🔔 Notificações Recentes</h3>
                            <div class="space-y-3 max-h-80 overflow-y-auto">
                                {notifications_html}
                            </div>
                            <a href="/notificacoes" class="block text-center bg-blue-500 text-white py-2 rounded-lg mt-4">Ver Todas</a>
                        </div>

                        <div class="bg-white rounded-2xl shadow-lg p-6">
                            <h3 class="text-xl font-bold mb-4">🎯 Metas Recentes</h3>
                            <div class="space-y-3">
                                {goals_html}
                            </div>
                            <a href="/metas" class="block text-center bg-green-500 text-white py-2 rounded-lg mt-4">Ver Todas</a>
                        </div>

                        <div class="bg-white rounded-2xl shadow-lg p-6">
                            <h3 class="text-xl font-bold mb-4">🚀 Ações Rápidas</h3>
                            <div class="space-y-3">
                                <a href="/atividades" class="block bg-purple-500 text-white text-center py-3 rounded-lg hover:bg-purple-600">
                                    🧘 Atividades Guiadas
                                </a>
                                <a href="/estatisticas" class="block bg-blue-500 text-white text-center py-3 rounded-lg hover:bg-blue-600">
                                    📊 Ver Estatísticas
                                </a>
                                <a href="/configuracoes/notificacoes" class="block bg-gray-500 text-white text-center py-3 rounded-lg hover:bg-gray-600">
                                    ⚙️ Configurações
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        conn.close()

@app.route('/registrar_humor', methods=['POST'])
@login_required
def registrar_humor():
    mood = request.form.get('mood')
    notes = request.form.get('notes', '')
    
    if not mood:
        flash('Selecione um humor.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO mood_entries (user_id, mood, notes) VALUES (?, ?, ?)',
            (session['user_id'], mood, notes)
        )
        conn.execute(
            'UPDATE users SET points = points + 10 WHERE id = ?',
            (session['user_id'],)
        )
        
        # Verificar conquistas
        check_achievements(session['user_id'], 'consistencia_7')
        
        # Gerar insights após registrar humor
        generate_intelligent_insights(session['user_id'])
        
        conn.commit()
        flash('✅ Humor registrado! +10 pontos', 'success')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

# SISTEMA DE ATIVIDADES GUIADAS
@app.route('/atividades')
@login_required
def atividades():
    """Página principal de atividades guiadas"""
    
    # Agrupar atividades por categoria
    activities_by_category = {}
    for activity_id, activity in GUIDED_ACTIVITIES.items():
        category = activity['category']
        if category not in activities_by_category:
            activities_by_category[category] = []
        activities_by_category[category].append((activity_id, activity))
    
    categories_html = ""
    for category, activities in activities_by_category.items():
        category_display = category.capitalize()
        activities_html = ""
        
        for activity_id, activity in activities:
            activities_html += f'''
            <div class="bg-white rounded-xl shadow-lg p-6 mb-4 hover:shadow-xl transition-shadow">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-start space-x-4">
                        <span class="text-4xl">{activity['icon']}</span>
                        <div>
                            <h3 class="text-xl font-bold text-gray-800">{activity['name']}</h3>
                            <p class="text-gray-600 mt-1">{activity['description']}</p>
                            <div class="flex items-center space-x-4 mt-2">
                                <span class="text-sm text-blue-600">⏱️ {activity['duration']} min</span>
                                <span class="text-sm text-green-600">⭐ {activity['points']} pontos</span>
                                <span class="text-sm text-purple-600">📝 {len(activity['steps'])} passos</span>
                            </div>
                        </div>
                    </div>
                </div>
                <a href="/atividade/{activity_id}" class="block w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-center py-3 rounded-lg font-semibold transition duration-300">
                    🚀 Iniciar Atividade Guiada
                </a>
            </div>
            '''
        
        categories_html += f'''
        <div class="mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">🎯 {category_display}</h2>
            {activities_html}
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Atividades Guiadas - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="text-blue-500 font-bold">← Voltar</a>
                    <div class="font-bold text-xl">🧘 Atividades Guiadas</div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-4xl mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-800 mb-4">Atividades Práticas</h1>
                <p class="text-xl text-gray-600">Exercícios guiados para seu bem-estar mental</p>
            </div>
            
            {categories_html}
        </div>
    </body>
    </html>
    '''

@app.route('/atividade/<activity_id>')
@login_required
def atividade_detalhes(activity_id):
    """Página de detalhes da atividade com guia passo a passo"""
    
    if activity_id not in GUIDED_ACTIVITIES:
        flash('Atividade não encontrada.', 'error')
        return redirect(url_for('atividades'))
    
    activity = GUIDED_ACTIVITIES[activity_id]
    
    # Preparar os passos para o JavaScript
    steps_json = json.dumps(activity['steps'])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{activity['name']} - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-purple-100 to-pink-100 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/atividades" class="text-blue-500 font-bold">← Voltar</a>
                    <div class="font-bold text-xl">🧘 {activity['name']}</div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-2xl mx-auto px-4 py-8">
            <div class="bg-white rounded-2xl shadow-xl p-8 mb-6 text-center">
                <div class="text-6xl mb-4">{activity['icon']}</div>
                <h1 class="text-3xl font-bold text-gray-800 mb-2">{activity['name']}</h1>
                <p class="text-gray-600 text-lg mb-4">{activity['description']}</p>
                <div class="flex justify-center space-x-6 text-sm text-gray-500">
                    <span>⏱️ {activity['duration']} min</span>
                    <span>⭐ {activity['points']} pontos</span>
                    <span>📝 {len(activity['steps'])} passos</span>
                </div>
            </div>

            <div id="activity-container" class="bg-white rounded-2xl shadow-xl p-8">
                <div id="step-container" class="text-center">
                    <div id="current-step" class="mb-6">
                        <h2 id="step-title" class="text-2xl font-bold text-gray-800 mb-4">Preparação</h2>
                        <p id="step-instruction" class="text-xl text-gray-600 mb-6">Encontre um local tranquilo e prepare-se para começar</p>
                        <div id="timer-container" class="hidden">
                            <div id="timer-circle" class="w-32 h-32 mx-auto mb-4 rounded-full border-4 border-purple-500 flex items-center justify-center">
                                <span id="timer-display" class="text-2xl font-bold text-purple-600">00:00</span>
                            </div>
                            <p id="timer-message" class="text-gray-500">Mantenha-se focado</p>
                        </div>
                    </div>
                    
                    <div id="progress-container" class="mb-6">
                        <div class="w-full bg-gray-200 rounded-full h-3">
                            <div id="progress-bar" class="bg-purple-500 h-3 rounded-full transition-all duration-500" style="width: 0%"></div>
                        </div>
                        <p id="progress-text" class="text-sm text-gray-500 mt-2">Passo 0 de {len(activity['steps'])}</p>
                    </div>
                    
                    <button id="start-button" onclick="startActivity()" class="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-4 px-8 rounded-lg text-lg transition duration-300">
                        🚀 Começar Atividade
                    </button>
                    
                    <button id="next-button" onclick="nextStep()" class="hidden bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-8 rounded-lg text-lg transition duration-300">
                        ▶️ Próximo Passo
                    </button>
                    
                    <button id="complete-button" onclick="completeActivity()" class="hidden bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-8 rounded-lg text-lg transition duration-300">
                        ✅ Concluir Atividade
                    </button>
                </div>
            </div>
        </div>

        <script>
            const activitySteps = {steps_json};
            let currentStep = -1;
            let timerInterval = null;
            let remainingTime = 0;

            function startActivity() {{
                currentStep = 0;
                document.getElementById('start-button').classList.add('hidden');
                document.getElementById('next-button').classList.remove('hidden');
                showStep(currentStep);
            }}

            function showStep(stepIndex) {{
                const step = activitySteps[stepIndex];
                const progress = ((stepIndex + 1) / activitySteps.length) * 100;
                
                document.getElementById('step-title').textContent = 'Passo ' + (stepIndex + 1);
                document.getElementById('step-instruction').textContent = step.instruction;
                document.getElementById('progress-bar').style.width = progress + '%';
                document.getElementById('progress-text').textContent = 'Passo ' + (stepIndex + 1) + ' de ' + activitySteps.length;
                
                // Configurar timer se necessário
                if (step.duration > 0) {{
                    startTimer(step.duration);
                }} else {{
                    document.getElementById('timer-container').classList.add('hidden');
                }}
                
                // Mostrar botão de conclusão no último passo
                if (stepIndex === activitySteps.length - 1) {{
                    document.getElementById('next-button').classList.add('hidden');
                    document.getElementById('complete-button').classList.remove('hidden');
                }}
            }}

            function startTimer(duration) {{
                if (timerInterval) {{
                    clearInterval(timerInterval);
                }}
                
                document.getElementById('timer-container').classList.remove('hidden');
                remainingTime = duration;
                updateTimerDisplay();
                
                timerInterval = setInterval(function() {{
                    remainingTime--;
                    updateTimerDisplay();
                    
                    if (remainingTime <= 0) {{
                        clearInterval(timerInterval);
                        document.getElementById('timer-message').textContent = 'Tempo esgotado!';
                    }}
                }}, 1000);
            }}

            function updateTimerDisplay() {{
                const minutes = Math.floor(remainingTime / 60);
                const seconds = remainingTime % 60;
                document.getElementById('timer-display').textContent = 
                    minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
            }}

            function nextStep() {{
                if (timerInterval) {{
                    clearInterval(timerInterval);
                }}
                
                currentStep++;
                if (currentStep < activitySteps.length) {{
                    showStep(currentStep);
                }}
            }}

            function completeActivity() {{
                // Enviar requisição para marcar atividade como concluída
                fetch('/completar_atividade', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        activity_id: '{activity_id}',
                        points: {activity['points']}
                    }})
                }})
                .then(function(response) {{
                    return response.json();
                }})
                .then(function(data) {{
                    if (data.success) {{
                        window.location.href = '/atividades';
                    }} else {{
                        alert('Erro ao completar atividade: ' + data.error);
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/completar_atividade', methods=['POST'])
@login_required
def completar_atividade():
    """Marca uma atividade como concluída e concede pontos"""
    data = request.json
    activity_id = data.get('activity_id')
    points = data.get('points', 0)
    
    if activity_id not in GUIDED_ACTIVITIES:
        return jsonify({'success': False, 'error': 'Atividade não encontrada'})
    
    conn = get_db_connection()
    try:
        # Verificar se já completou esta atividade
        existing = conn.execute(
            'SELECT * FROM completed_activities WHERE user_id = ? AND activity_id = ?',
            (session['user_id'], activity_id)
        ).fetchone()
        
        if not existing:
            # Registrar atividade completada
            conn.execute(
                'INSERT INTO completed_activities (user_id, activity_id) VALUES (?, ?)',
                (session['user_id'], activity_id)
            )
            
            # Adicionar pontos
            conn.execute(
                'INSERT INTO activities (user_id, activity_type, points_earned) VALUES (?, ?, ?)',
                (session['user_id'], f'atividade_{activity_id}', points)
            )
            
            conn.execute(
                'UPDATE users SET points = points + ? WHERE id = ?',
                (points, session['user_id'])
            )
            
            # Verificar conquista de atividades
            completed_count = conn.execute('''
                SELECT COUNT(DISTINCT activity_id) as count 
                FROM completed_activities 
                WHERE user_id = ?
            ''', (session['user_id'],)).fetchone()
            
            if completed_count and completed_count['count'] >= 5:
                check_achievements(session['user_id'], 'atividades_mestre')
            
            # Notificação de conclusão
            activity_name = GUIDED_ACTIVITIES[activity_id]['name']
            create_notification(
                session['user_id'],
                '🎉 Atividade Concluída!',
                f'Você completou "{activity_name}" e ganhou {points} pontos!',
                'achievement'
            )
            
            conn.commit()
            flash(f'🎉 {activity_name} concluída! +{points} pontos', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Atividade já concluída'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# ROTAS EXISTENTES (metas, estatisticas, notificacoes, etc.)
@app.route('/metas', methods=['GET', 'POST'])
@login_required
def metas():
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        goal_type = request.form.get('goal_type', 'geral')
        
        if not title:
            flash('Digite um título.', 'error')
            return redirect(url_for('metas'))
        
        try:
            conn.execute('''
                INSERT INTO goals (user_id, title, goal_type) VALUES (?, ?, ?)
            ''', (session['user_id'], title, goal_type))
            
            # Notificação de nova meta
            create_notification(
                session['user_id'],
                '🎯 Nova Meta Criada',
                f'Sua meta "{title}" foi criada com sucesso!',
                'goal'
            )
            
            conn.commit()
            flash('🎯 Meta criada!', 'success')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('metas'))
    
    try:
        goals = conn.execute('''
            SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC
        ''', (session['user_id'],)).fetchall()
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()
    
    categories_html = ""
    for category_id, category in GOAL_CATEGORIES.items():
        categories_html += f'<option value="{category_id}">{category["icon"]} {category["name"]}</option>'
    
    goals_html = ""
    for goal in goals:
        status = "✅ Concluída" if goal['completed'] else "🟡 Em andamento"
        goals_html += f'''
        <div class="bg-white p-4 rounded-lg border shadow-sm">
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="font-bold text-lg">{goal["title"]}</h4>
                    <p class="text-gray-600">{status}</p>
                </div>
                <div class="space-x-2">
                    {f'''
                    <form action="/completar_meta" method="POST" class="inline">
                        <input type="hidden" name="goal_id" value="{goal["id"]}">
                        <button type="submit" class="bg-green-500 text-white px-3 py-1 rounded">Concluir</button>
                    </form>
                    ''' if not goal['completed'] else ''}
                    <form action="/excluir_meta" method="POST" class="inline">
                        <input type="hidden" name="goal_id" value="{goal["id"]}">
                        <button type="submit" class="bg-red-500 text-white px-3 py-1 rounded">Excluir</button>
                    </form>
                </div>
            </div>
        </div>
        '''
    
    if not goals_html:
        goals_html = '<p class="text-gray-500 text-center py-8">Nenhuma meta criada.</p>'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metas - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="text-blue-500 font-bold">← Voltar</a>
                    <div class="font-bold text-xl">🎯 Metas</div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-4xl mx-auto px-4 py-8">
            <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
                <h3 class="text-xl font-bold mb-4">➕ Nova Meta</h3>
                <form method="POST" class="space-y-4">
                    <div>
                        <label class="block font-bold mb-2">Título</label>
                        <input type="text" name="title" class="w-full p-3 border rounded-lg" required>
                    </div>
                    <div>
                        <label class="block font-bold mb-2">Categoria</label>
                        <select name="goal_type" class="w-full p-3 border rounded-lg">
                            {categories_html}
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-green-500 text-white py-3 rounded-lg">Criar Meta</button>
                </form>
            </div>

            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-xl font-bold mb-4">📋 Minhas Metas</h3>
                <div class="space-y-4">
                    {goals_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/completar_meta', methods=['POST'])
@login_required
def completar_meta():
    goal_id = request.form.get('goal_id')
    
    conn = get_db_connection()
    try:
        # Buscar dados da meta antes de completar
        goal = conn.execute('SELECT title FROM goals WHERE id = ?', (goal_id,)).fetchone()
        
        conn.execute('''
            UPDATE goals SET completed = TRUE, completed_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (goal_id, session['user_id']))
        conn.execute('UPDATE users SET points = points + 25 WHERE id = ?', (session['user_id'],))
        
        # Notificação de meta concluída
        if goal:
            create_notification(
                session['user_id'],
                '✅ Meta Concluída!',
                f'Parabéns! Você concluiu a meta "{goal["title"]}" e ganhou 25 pontos! 🎉',
                'achievement'
            )
        
        # Verificar conquista de metas
        completed_goals = conn.execute('''
            SELECT COUNT(*) as count FROM goals 
            WHERE user_id = ? AND completed = TRUE
        ''', (session['user_id'],)).fetchone()
        
        if completed_goals and completed_goals['count'] >= 5:
            check_achievements(session['user_id'], 'estrategista')
        
        conn.commit()
        flash('🎉 Meta concluída! +25 pontos', 'success')
        
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('metas'))

@app.route('/excluir_meta', methods=['POST'])
@login_required
def excluir_meta():
    goal_id = request.form.get('goal_id')
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM goals WHERE id = ? AND user_id = ?', (goal_id, session['user_id']))
        conn.commit()
        flash('🗑️ Meta excluída', 'success')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('metas'))

@app.route('/estatisticas')
@login_required
def estatisticas():
    stats = get_user_statistics(session['user_id'])
    
    # Calcular porcentagem de metas concluídas
    goals_percentage = 0
    if stats['total_goals'] > 0:
        goals_percentage = (stats['completed_goals'] / stats['total_goals']) * 100
    
    # Gerar insights baseados nas estatísticas
    insights = generate_personalized_insights(stats, session['user_id'])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Estatísticas - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="text-blue-500 font-bold">← Voltar</a>
                    <div class="font-bold text-xl">📊 Estatísticas</div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-6xl mx-auto px-4 py-8">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-blue-500 text-white rounded-2xl p-6 text-center">
                    <div class="text-3xl mb-3">📝</div>
                    <div class="text-3xl font-bold">{stats['total_entries']}</div>
                    <div>Registros Totais</div>
                </div>
                
                <div class="bg-green-500 text-white rounded-2xl p-6 text-center">
                    <div class="text-3xl mb-3">🎯</div>
                    <div class="text-3xl font-bold">{stats['completed_goals']}/{stats['total_goals']}</div>
                    <div>Metas Concluídas</div>
                </div>
                
                <div class="bg-purple-500 text-white rounded-2xl p-6 text-center">
                    <div class="text-3xl mb-3">⭐</div>
                    <div class="text-3xl font-bold">{stats['avg_mood_score']}/5</div>
                    <div>Humor Médio</div>
                </div>
                
                <div class="bg-orange-500 text-white rounded-2xl p-6 text-center">
                    <div class="text-3xl mb-3">🏅</div>
                    <div class="text-3xl font-bold">{stats['unique_activities']}</div>
                    <div>Atividades Únicas</div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="bg-white rounded-2xl shadow-lg p-6">
                    <h3 class="text-xl font-bold mb-4">📈 Distribuição de Humor</h3>
                    <div class="h-64">
                        <canvas id="moodChart"></canvas>
                    </div>
                </div>

                <div class="bg-white rounded-2xl shadow-lg p-6">
                    <h3 class="text-xl font-bold mb-4">🎯 Progresso de Metas</h3>
                    <div class="h-64">
                        <canvas id="goalsChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-lg p-6 mt-8">
                <h3 class="text-xl font-bold mb-4">💡 Insights Personalizados</h3>
                <div class="space-y-4">
                    {insights}
                </div>
            </div>
        </div>

        <script>
            // Gráfico de Distribuição de Humor
            const moodCtx = document.getElementById('moodChart').getContext('2d');
            const moodDistribution = {json.dumps(stats['mood_distribution'])};
            
            const moodLabels = ['😢', '😕', '😐', '😊', '😄'];
            const moodData = moodLabels.map(emoji => moodDistribution[emoji] || 0);
            
            new Chart(moodCtx, {{
                type: 'doughnut',
                data: {{
                    labels: moodLabels,
                    datasets: [{{
                        data: moodData,
                        backgroundColor: [
                            '#EF4444', '#F59E0B', '#6B7280', '#10B981', '#3B82F6'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});

            // Gráfico de Metas
            const goalsCtx = document.getElementById('goalsChart').getContext('2d');
            new Chart(goalsCtx, {{
                type: 'bar',
                data: {{
                    labels: ['Concluídas', 'Pendentes'],
                    datasets: [{{
                        label: 'Metas',
                        data: [
                            {stats['completed_goals']},
                            {stats['total_goals'] - stats['completed_goals']}
                        ],
                        backgroundColor: ['#10B981', '#6B7280']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    '''

@app.route('/notificacoes')
@login_required
def notificacoes():
    conn = get_db_connection()
    try:
        # Marcar todas como lidas ao abrir a página
        conn.execute(
            'UPDATE notifications SET is_read = TRUE WHERE user_id = ?',
            (session['user_id'],)
        )
        
        # Buscar todas as notificações
        notifications = conn.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (session['user_id'],)).fetchall()
        
        conn.commit()
        
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()
    
    notifications_html = ""
    for notification in notifications:
        notification_type = NOTIFICATION_TYPES.get(notification['notification_type'], NOTIFICATION_TYPES['system'])
        try:
            date_obj = datetime.strptime(notification['created_at'], '%Y-%m-%d %H:%M:%S')
            formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
        except:
            formatted_date = notification['created_at']
        
        read_class = "bg-gray-50" if notification['is_read'] else "bg-white border-l-4 border-blue-500"
        
        notifications_html += f'''
        <div class="{read_class} p-4 rounded-lg shadow-sm mb-4">
            <div class="flex items-start space-x-3">
                <span class="text-2xl">{notification_type['icon']}</span>
                <div class="flex-1">
                    <div class="font-bold text-gray-800 text-lg">{notification["title"]}</div>
                    <div class="text-gray-600 mt-1">{notification["message"]}</div>
                    <div class="text-sm text-gray-400 mt-2">{formatted_date}</div>
                </div>
            </div>
        </div>
        '''
    
    if not notifications_html:
        notifications_html = '''
        <div class="text-center py-12">
            <div class="text-6xl mb-4">🔔</div>
            <p class="text-gray-500 text-xl mb-4">Nenhuma notificação</p>
            <p class="text-gray-400">Suas notificações aparecerão aqui</p>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Notificações - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="text-blue-500 font-bold">← Voltar</a>
                    <div class="font-bold text-xl">🔔 Notificações</div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-4xl mx-auto px-4 py-8">
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-xl font-bold mb-6">Todas as Notificações</h3>
                <div class="space-y-4">
                    {notifications_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/configuracoes/notificacoes', methods=['GET', 'POST'])
@login_required
def configuracoes_notificacoes():
    conn = get_db_connection()
    
    if request.method == 'POST':
        daily_reminder = 'daily_reminder' in request.form
        achievement_notifications = 'achievement_notifications' in request.form
        goal_reminders = 'goal_reminders' in request.form
        weekly_insights = 'weekly_insights' in request.form
        reminder_time = request.form.get('reminder_time', '20:00')
        
        try:
            # Verificar se já existe configuração
            existing = conn.execute(
                'SELECT * FROM notification_settings WHERE user_id = ?', (session['user_id'],)
            ).fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE notification_settings 
                    SET daily_reminder = ?, reminder_time = ?, achievement_notifications = ?, 
                        goal_reminders = ?, weekly_insights = ?
                    WHERE user_id = ?
                ''', (daily_reminder, reminder_time, achievement_notifications, goal_reminders, weekly_insights, session['user_id']))
            else:
                conn.execute('''
                    INSERT INTO notification_settings 
                    (user_id, daily_reminder, reminder_time, achievement_notifications, goal_reminders, weekly_insights)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (session['user_id'], daily_reminder, reminder_time, achievement_notifications, goal_reminders, weekly_insights))
            
            conn.commit()
            flash('✅ Configurações salvas!', 'success')
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('configuracoes_notificacoes'))
    
    try:
        settings = conn.execute(
            'SELECT * FROM notification_settings WHERE user_id = ?', (session['user_id'],)
        ).fetchone()
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()
    
    # Valores padrão se não existirem configurações
    if not settings:
        settings = {
            'daily_reminder': True,
            'reminder_time': '20:00',
            'achievement_notifications': True,
            'goal_reminders': True,
            'weekly_insights': True
        }
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configurações - MindCare</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="text-blue-500 font-bold">← Voltar</a>
                    <div class="font-bold text-xl">⚙️ Configurações</div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-2xl mx-auto px-4 py-8">
            <div class="bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-xl font-bold mb-6">🔔 Configurações de Notificações</h3>
                
                <form method="POST" class="space-y-6">
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-semibold">Lembrete Diário</div>
                                <div class="text-sm text-gray-600">Receber lembrete para registrar humor</div>
                            </div>
                            <input type="checkbox" name="daily_reminder" {'checked' if settings['daily_reminder'] else ''} class="w-5 h-5">
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-semibold">Notificações de Conquistas</div>
                                <div class="text-sm text-gray-600">Receber notificações quando desbloquear conquistas</div>
                            </div>
                            <input type="checkbox" name="achievement_notifications" {'checked' if settings['achievement_notifications'] else ''} class="w-5 h-5">
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-semibold">Lembretes de Metas</div>
                                <div class="text-sm text-gray-600">Receber lembretes sobre metas pendentes</div>
                            </div>
                            <input type="checkbox" name="goal_reminders" {'checked' if settings['goal_reminders'] else ''} class="w-5 h-5">
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-semibold">Insights Semanais</div>
                                <div class="text-sm text-gray-600">Receber insights sobre seu progresso</div>
                            </div>
                            <input type="checkbox" name="weekly_insights" {'checked' if settings['weekly_insights'] else ''} class="w-5 h-5">
                        </div>
                    </div>
                    
                    <div>
                        <label class="block font-semibold mb-2">Horário do Lembrete Diário</label>
                        <input type="time" name="reminder_time" value="{settings['reminder_time']}" class="w-full p-3 border rounded-lg">
                    </div>
                    
                    <button type="submit" class="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold">
                        💾 Salvar Configurações
                    </button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    flash('Até logo! 👋', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🔄 Inicializando...")
    init_db()
    print("🚀 MindCare Pro - Sistema Completo com Atividades Guiadas!")
    print("📍 Acesse: http://localhost:5000")
    print("\n🎯 Funcionalidades Disponíveis:")
    print("   🧘 5 Atividades Guiadas Interativas")
    print("   📊 Sistema de Estatísticas Detalhadas")
    print("   💡 Insights Personalizados Avançados")
    print("   📈 Gráficos Interativos")
    print("   🔔 Lembretes Inteligentes Automáticos")
    print("   🏅 Sistema de Conquistas Expandido")
    app.run(debug=True, port=5000)