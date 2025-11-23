# ... (código anterior permanece igual até a função metas())

# SISTEMA DE METAS COMPLETO
@app.route('/metas', methods=['GET', 'POST'])
@login_required
def metas():
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        goal_type = request.form.get('goal_type', 'geral')
        target_date = request.form.get('target_date')
        priority = request.form.get('priority', 'medium')
        difficulty = request.form.get('difficulty', 'medium')
        
        if not title:
            flash('Por favor, digite um título para sua meta.', 'error')
            return redirect(url_for('metas'))
        
        try:
            conn.execute('''
                INSERT INTO goals (user_id, title, description, goal_type, target_date, priority, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], title, description, goal_type, target_date, priority, difficulty))
            conn.commit()
            
            flash('🎯 Meta criada com sucesso!', 'success')
            return redirect(url_for('metas'))
            
        except Exception as e:
            flash(f'❌ Erro ao criar meta: {str(e)}', 'error')
            return redirect(url_for('metas'))
    
    try:
        # Buscar todas as metas do usuário
        goals = conn.execute('''
            SELECT * FROM goals 
            WHERE user_id = ? 
            ORDER BY 
                completed ASC,
                priority DESC,
                target_date ASC,
                created_at DESC
        ''', (session['user_id'],)).fetchall()
        
        # Estatísticas de metas
        goals_stats = conn.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN completed = TRUE THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN completed = FALSE AND target_date < date('now') THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN completed = FALSE AND priority = 'high' THEN 1 ELSE 0 END) as high_priority
            FROM goals 
            WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
    except Exception as e:
        flash(f'❌ Erro ao carregar metas: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()
    
    # HTML para categorias de metas
    categories_html = ""
    for category_id, category in GOAL_CATEGORIES.items():
        categories_html += f'''
        <option value="{category_id}">{category['icon']} {category['name']}</option>
        '''
    
    # HTML para lista de metas
    goals_html = ""
    for goal in goals:
        status_color = "bg-green-100 border-green-400" if goal['completed'] else "bg-white border-gray-300"
        status_text = "✅ Concluída" if goal['completed'] else "🟡 Em andamento"
        
        days_left = ""
        if goal['target_date'] and not goal['completed']:
            try:
                target_date = datetime.strptime(goal['target_date'], '%Y-%m-%d').date()
                today = datetime.now().date()
                days = (target_date - today).days
                if days < 0:
                    days_left = f"<span class='text-red-500 font-bold'>(Atrasada {-days} dias)</span>"
                elif days == 0:
                    days_left = "<span class='text-orange-500 font-bold'>(Vence hoje!)</span>"
                else:
                    days_left = f"<span class='text-gray-500'>({days} dias restantes)</span>"
            except:
                days_left = ""
        
        completed_at = ""
        if goal['completed_at']:
            try:
                completed_date = datetime.strptime(goal['completed_at'], '%Y-%m-%d %H:%M:%S')
                completed_at = f"<div class='text-green-600 text-sm'>Concluída em {completed_date.strftime('%d/%m/%Y')}</div>"
            except:
                completed_at = ""
        
        category = GOAL_CATEGORIES.get(goal['goal_type'], GOAL_CATEGORIES['geral'])
        priority_color = {
            'high': 'bg-red-100 text-red-800 border-red-300',
            'medium': 'bg-yellow-100 text-yellow-800 border-yellow-300', 
            'low': 'bg-green-100 text-green-800 border-green-300'
        }.get(goal['priority'] or 'medium', 'bg-gray-100 text-gray-800 border-gray-300')
        
        difficulty_color = {
            'hard': 'bg-purple-100 text-purple-800',
            'medium': 'bg-blue-100 text-blue-800',
            'easy': 'bg-green-100 text-green-800'
        }.get(goal['difficulty'] or 'medium', 'bg-gray-100 text-gray-800')
        
        goals_html += f'''
        <div class="{status_color} border-2 rounded-xl p-6 mb-4 shadow-sm hover:shadow-md transition duration-300">
            <div class="flex justify-between items-start mb-3">
                <div class="flex-1">
                    <h4 class="text-xl font-bold text-gray-800">{goal["title"]}</h4>
                    {f'<p class="text-gray-600 mt-1">{goal["description"]}</p>' if goal["description"] else ''}
                </div>
                <div class="flex space-x-2 ml-4">
                    <span class="{priority_color} px-3 py-1 rounded-full text-sm font-bold border">{goal['priority'] or 'medium'}</span>
                    <span class="{difficulty_color} px-3 py-1 rounded-full text-sm font-bold">{goal['difficulty'] or 'medium'}</span>
                </div>
            </div>
            
            <div class="flex justify-between items-center mt-4">
                <div class="flex items-center space-x-4">
                    <span class="flex items-center text-sm text-gray-600">
                        {category['icon']} {category['name']}
                    </span>
                    <span class="font-semibold text-sm { 'text-green-600' if goal['completed'] else 'text-blue-600' }">
                        {status_text}
                    </span>
                    {days_left}
                    {completed_at}
                </div>
                
                <div class="flex space-x-2">
                    {f'''
                    <form action="/completar_meta" method="POST" class="inline">
                        <input type="hidden" name="goal_id" value="{goal["id"]}">
                        <button type="submit" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition duration-300 font-bold">
                            ✅ Concluir
                        </button>
                    </form>
                    ''' if not goal['completed'] else ''}
                    
                    <form action="/excluir_meta" method="POST" class="inline" onsubmit="return confirm('Tem certeza que deseja excluir esta meta?');">
                        <input type="hidden" name="goal_id" value="{goal["id"]}">
                        <button type="submit" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition duration-300 font-bold">
                            🗑️ Excluir
                        </button>
                    </form>
                </div>
            </div>
        </div>
        '''
    
    if not goals_html:
        goals_html = '''
        <div class="text-center py-12">
            <div class="text-6xl mb-4">🎯</div>
            <p class="text-gray-500 text-xl mb-4">Nenhuma meta criada ainda</p>
            <p class="text-gray-400">Crie sua primeira meta para começar a acompanhar seus objetivos!</p>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metas - MindCare Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="flex items-center text-blue-500 hover:text-blue-600 font-bold">
                        <i class="fas fa-arrow-left mr-2"></i>
                        <span>Voltar ao Dashboard</span>
                    </a>
                    <div class="flex items-center">
                        <span class="text-2xl mr-2">🎯</span>
                        <span class="font-bold text-xl">Minhas Metas</span>
                    </div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-6xl mx-auto px-4 py-8">
            <!-- Estatísticas Rápidas -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-2xl shadow-lg p-6 text-center">
                    <div class="text-3xl text-blue-500 mb-2">🎯</div>
                    <div class="text-2xl font-bold text-gray-800">{goals_stats["total"] or 0}</div>
                    <div class="text-gray-600">Total de Metas</div>
                </div>
                <div class="bg-white rounded-2xl shadow-lg p-6 text-center">
                    <div class="text-3xl text-green-500 mb-2">✅</div>
                    <div class="text-2xl font-bold text-gray-800">{goals_stats["completed"] or 0}</div>
                    <div class="text-gray-600">Concluídas</div>
                </div>
                <div class="bg-white rounded-2xl shadow-lg p-6 text-center">
                    <div class="text-3xl text-red-500 mb-2">⏰</div>
                    <div class="text-2xl font-bold text-gray-800">{goals_stats["overdue"] or 0}</div>
                    <div class="text-gray-600">Atrasadas</div>
                </div>
                <div class="bg-white rounded-2xl shadow-lg p-6 text-center">
                    <div class="text-3xl text-orange-500 mb-2">🔥</div>
                    <div class="text-2xl font-bold text-gray-800">{goals_stats["high_priority"] or 0}</div>
                    <div class="text-gray-600">Alta Prioridade</div>
                </div>
            </div>

            <!-- Formulário de Nova Meta -->
            <div class="bg-white rounded-2xl shadow-lg p-8 mb-8">
                <h3 class="text-2xl font-bold text-gray-800 mb-6">➕ Criar Nova Meta</h3>
                
                <form method="POST" class="space-y-6">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-gray-700 mb-2 font-bold">Título da Meta *</label>
                            <input type="text" name="title" placeholder="Ex: Praticar meditação diária" 
                                   class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                                   required>
                        </div>
                        
                        <div>
                            <label class="block text-gray-700 mb-2 font-bold">Categoria</label>
                            <select name="goal_type" class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg">
                                {categories_html}
                            </select>
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-gray-700 mb-2 font-bold">Descrição (opcional)</label>
                        <textarea name="description" placeholder="Descreva sua meta com mais detalhes..." 
                                  class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg h-24"></textarea>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <label class="block text-gray-700 mb-2 font-bold">Data Alvo (opcional)</label>
                            <input type="date" name="target_date" 
                                   class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg">
                        </div>
                        
                        <div>
                            <label class="block text-gray-700 mb-2 font-bold">Prioridade</label>
                            <select name="priority" class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg">
                                <option value="low">🟢 Baixa</option>
                                <option value="medium" selected>🟡 Média</option>
                                <option value="high">🔴 Alta</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-gray-700 mb-2 font-bold">Dificuldade</label>
                            <select name="difficulty" class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg">
                                <option value="easy">🟢 Fácil</option>
                                <option value="medium" selected>🟡 Médio</option>
                                <option value="hard">🔴 Difícil</option>
                            </select>
                        </div>
                    </div>
                    
                    <button type="submit" class="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold py-4 px-4 rounded-xl transition duration-300 text-lg transform hover:scale-105">
                        🎯 Criar Meta
                    </button>
                </form>
            </div>

            <!-- Lista de Metas -->
            <div class="bg-white rounded-2xl shadow-lg p-8">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-2xl font-bold text-gray-800">📋 Minhas Metas</h3>
                    <div class="text-sm text-gray-600">
                        {goals_stats["completed"] or 0} de {goals_stats["total"] or 0} concluídas
                    </div>
                </div>
                <div class="space-y-4">
                    {goals_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# Completar meta
@app.route('/completar_meta', methods=['POST'])
@login_required
def completar_meta():
    goal_id = request.form.get('goal_id')
    
    conn = get_db_connection()
    try:
        # Marcar meta como concluída
        conn.execute('''
            UPDATE goals SET completed = TRUE, completed_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (goal_id, session['user_id']))
        
        # Adicionar pontos por completar meta
        conn.execute(
            'UPDATE users SET points = points + 25 WHERE id = ?',
            (session['user_id'],)
        )
        
        # Verificar conquista de metas
        completed_goals = conn.execute('''
            SELECT COUNT(*) as count FROM goals 
            WHERE user_id = ? AND completed = TRUE
        ''', (session['user_id'],)).fetchone()
        
        if completed_goals and completed_goals['count'] >= 10:
            check_achievements(session['user_id'], 'estrategista')
        
        conn.commit()
        flash('🎉 Meta concluída com sucesso! +25 pontos!', 'success')
        
    except Exception as e:
        flash(f'❌ Erro ao completar meta: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('metas'))

# Excluir meta
@app.route('/excluir_meta', methods=['POST'])
@login_required
def excluir_meta():
    goal_id = request.form.get('goal_id')
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM goals WHERE id = ? AND user_id = ?', (goal_id, session['user_id']))
        conn.commit()
        flash('🗑️ Meta excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'❌ Erro ao excluir meta: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('metas'))

# Atividades
@app.route('/atividades')
@login_required
def atividades():
    activities_data = [
        {'nome': 'Meditação Guiada', 'duracao': 10, 'pontos': 15, 'icon': '🧘', 'descricao': 'Relaxe e acalme a mente', 'tipo': 'mindfulness'},
        {'nome': 'Respiração 4-7-8', 'duracao': 5, 'pontos': 10, 'icon': '🌬️', 'descricao': 'Técnica calmante', 'tipo': 'mindfulness'},
        {'nome': 'Caminhada Mindful', 'duracao': 20, 'pontos': 25, 'icon': '🚶', 'descricao': 'Caminhada consciente', 'tipo': 'exercicio'},
        {'nome': 'Yoga Básico', 'duracao': 15, 'pontos': 20, 'icon': '🧘‍♀️', 'descricao': 'Posturas simples', 'tipo': 'exercicio'},
        {'nome': 'Journaling Diário', 'duracao': 10, 'pontos': 15, 'icon': '📝', 'descricao': 'Reflita sobre seu dia', 'tipo': 'reflexao'},
        {'nome': '3 Coisas Boas', 'duracao': 5, 'pontos': 10, 'icon': '🙏', 'descricao': 'Pratique gratidão', 'tipo': 'reflexao'}
    ]
    
    activities_html = ""
    for activity in activities_data:
        activities_html += f'''
        <div class="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition duration-300 border-2 border-gray-200">
            <div class="text-4xl text-center mb-4">{activity['icon']}</div>
            <h4 class="text-xl font-bold text-gray-800 mb-2 text-center">{activity['nome']}</h4>
            <p class="text-gray-600 mb-4 text-center">{activity['descricao']}</p>
            <div class="flex justify-between items-center mb-4">
                <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-bold">⏱️ {activity['duracao']} min</span>
                <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-bold">🎯 {activity['pontos']} pts</span>
            </div>
            <form action="/completar_atividade" method="POST">
                <input type="hidden" name="activity_type" value="{activity['nome']}">
                <input type="hidden" name="points" value="{activity['pontos']}">
                <button type="submit" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-lg transition duration-300">
                    ✅ Completar Atividade
                </button>
            </form>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Atividades - MindCare Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <a href="/dashboard" class="flex items-center text-blue-500 hover:text-blue-600 font-bold">
                        <i class="fas fa-arrow-left mr-2"></i>
                        <span>Voltar ao Dashboard</span>
                    </a>
                    <div class="flex items-center">
                        <span class="text-2xl mr-2">💪</span>
                        <span class="font-bold text-xl">Atividades</span>
                    </div>
                    <div></div>
                </div>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <h2 class="text-3xl font-bold text-gray-800 mb-4">💪 Atividades para seu Bem-Estar</h2>
                <p class="text-gray-600 text-lg">Pratique estas atividades diariamente para melhorar sua saúde mental</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {activities_html}
            </div>
        </div>
    </body>
    </html>
    '''

# Completar atividade
@app.route('/completar_atividade', methods=['POST'])
@login_required
def completar_atividade():
    activity_type = request.form.get('activity_type')
    points = request.form.get('points')
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO activities (user_id, activity_type, points_earned) VALUES (?, ?, ?)',
            (session['user_id'], activity_type, points)
        )
        
        conn.execute(
            'UPDATE users SET points = points + ? WHERE id = ?',
            (points, session['user_id'])
        )
        
        user = conn.execute(
            'SELECT points, level FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        
        if user:
            new_level = (user['points'] or 0) // 50 + 1
            current_level = user['level'] or 1
            
            if new_level > current_level:
                conn.execute(
                    'UPDATE users SET level = ? WHERE id = ?',
                    (new_level, session['user_id'])
                )
                flash(f'🎉 Nível up! Você agora é nível {new_level}!', 'success')
            else:
                flash(f'✅ Atividade "{activity_type}" completada! +{points} pontos 🎯', 'success')
        
        if "Meditação" in activity_type:
            meditation_count = conn.execute(
                'SELECT COUNT(*) as count FROM activities WHERE user_id = ? AND activity_type LIKE "%Meditação%"',
                (session['user_id'],)
            ).fetchone()['count']
            
            if meditation_count >= 10:
                check_achievements(session['user_id'], 'meditacao_mestre')
        
        conn.commit()
        return redirect(url_for('atividades'))
    
    except Exception as e:
        flash(f'❌ Erro ao completar atividade: {str(e)}', 'error')
        return redirect(url_for('atividades'))
    finally:
        conn.close()

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta. Até logo! 👋', 'info')
    return redirect(url_for('index'))

# API Routes
@app.route('/api/user/profile')
@login_required
def api_user_profile():
    conn = get_db_connection()
    try:
        user = conn.execute('''
            SELECT id, username, points, level, streak, created_at 
            FROM users WHERE id = ?
        ''', (session['user_id'],)).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = conn.execute('''
            SELECT 
                COUNT(*) as total_moods,
                COUNT(DISTINCT DATE(created_at)) as active_days,
                AVG(mood_score) as avg_mood
            FROM mood_entries WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
        return jsonify({
            'user': dict(user),
            'stats': dict(stats) if stats else {}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/achievements')
@login_required
def api_achievements():
    conn = get_db_connection()
    try:
        achievements = conn.execute('''
            SELECT achievement_id FROM achievements WHERE user_id = ?
        ''', (session['user_id'],)).fetchall()
        
        return jsonify({
            'achievements': [ach['achievement_id'] for ach in achievements]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/goals')
@login_required
def api_goals():
    conn = get_db_connection()
    try:
        goals = conn.execute('''
            SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC
        ''', (session['user_id'],)).fetchall()
        
        return jsonify({
            'goals': [dict(goal) for goal in goals]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔄 Inicializando banco de dados...")
    init_db()
    print("🚀 MindCare Pro iniciado com sucesso!")
    print("📍 Acesse: http://localhost:5000")
    print("💡 Dica: Digite qualquer nome para fazer login")
    print("")
    print("✨ Rotas disponíveis:")
    print("   📍 / - Página inicial")
    print("   📍 /login - Login")
    print("   📍 /dashboard - Dashboard principal")
    print("   📍 /progresso - Gráficos de progresso")
    print("   📍 /atividades - Atividades")
    print("   📍 /metas - Sistema completo de metas")
    print("   📍 /api/* - APIs para integração")
    print("")
    print("🎯 Sistema de Metas Inclui:")
    print("   ✅ Criar metas com categorias")
    print("   ✅ Prioridade e dificuldade")
    print("   ✅ Prazos e datas alvo")
    print("   ✅ Marcar como concluído")
    print("   ✅ Excluir metas")
    print("   ✅ Estatísticas de progresso")
    print("   ✅ Pontos por metas concluídas")
    app.run(debug=True, port=5000)