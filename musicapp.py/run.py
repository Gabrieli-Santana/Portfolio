from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from mutagen import File
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spotify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg'}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Tabela de associação para playlists e músicas
playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

# Modelos atualizados
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    songs = db.relationship('Song', backref='uploader', lazy=True)
    playlists = db.relationship('Playlist', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    album = db.Column(db.String(100), default='Unknown Album')
    duration = db.Column(db.Integer)
    filename = db.Column(db.String(200))
    file_path = db.Column(db.String(200))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    play_count = db.Column(db.Integer, default=0)
    playlists = db.relationship('Playlist', secondary=playlist_songs, back_populates='songs')

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    songs = db.relationship('Song', secondary=playlist_songs, back_populates='playlists')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Funções auxiliares (mantidas as mesmas)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_audio_metadata(file_path):
    """Extrai metadados do arquivo de áudio"""
    try:
        audio = File(file_path)
        if audio is not None:
            metadata = {
                'title': 'Unknown Title',
                'artist': 'Unknown Artist', 
                'album': 'Unknown Album',
                'duration': int(audio.info.length) if hasattr(audio.info, 'length') else 0
            }
            
            if hasattr(audio, 'tags') and audio.tags is not None:
                if 'TIT2' in audio.tags:
                    metadata['title'] = str(audio.tags['TIT2'])
                if 'TPE1' in audio.tags:
                    metadata['artist'] = str(audio.tags['TPE1'])
                if 'TALB' in audio.tags:
                    metadata['album'] = str(audio.tags['TALB'])
            
            return metadata
    except Exception as e:
        print(f"Erro ao extrair metadados: {e}")
    
    return None

# Inicialização (mantida igual)
with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    if not User.query.filter_by(username='testuser').first():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        print("✅ Usuário de teste criado: testuser / password123")

# Rotas principais (mantidas)
@app.route('/')
def index():
    if current_user.is_authenticated:
        songs = Song.query.order_by(Song.id.desc()).limit(6).all()
        playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).limit(3).all()
        return render_template('index.html', recent_songs=songs, recent_playlists=playlists)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

@app.route('/library')
@login_required
def library():
    user_songs = Song.query.filter_by(uploader_id=current_user.id).all()
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template('library.html', songs=user_songs, playlists=user_playlists)

# Rotas de Upload (mantidas)
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        file = request.files['audio_file']
        
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(file_path)
                
                metadata = extract_audio_metadata(file_path)
                
                title = request.form.get('title') or (metadata['title'] if metadata else 'Unknown Title')
                artist = request.form.get('artist') or (metadata['artist'] if metadata else 'Unknown Artist')
                album = request.form.get('album') or (metadata['album'] if metadata else 'Unknown Album')
                duration = metadata['duration'] if metadata else 0
                
                song = Song(
                    title=title,
                    artist=artist,
                    album=album,
                    duration=duration,
                    filename=filename,
                    file_path=unique_filename,
                    uploader_id=current_user.id
                )
                
                db.session.add(song)
                db.session.commit()
                
                flash(f'Música "{title}" uploadada com sucesso!', 'success')
                return redirect(url_for('library'))
                
            except Exception as e:
                flash(f'Erro no upload: {str(e)}', 'danger')
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('Tipo de arquivo não permitido. Use MP3, WAV ou OGG.', 'danger')
    
    return render_template('upload.html')

@app.route('/stream/<int:song_id>')
@login_required
def stream_song(song_id):
    song = Song.query.get_or_404(song_id)
    song.play_count += 1
    db.session.commit()
    
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], song.file_path),
        as_attachment=False,
        mimetype='audio/mpeg'
    )

# 🎵 NOVAS ROTAS DE PLAYLIST
@app.route('/playlists')
@login_required
def playlists():
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template('playlists.html', playlists=user_playlists)

@app.route('/playlist/create', methods=['GET', 'POST'])
@login_required
def create_playlist():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_public = request.form.get('is_public') == 'on'
        
        if not name:
            flash('Nome da playlist é obrigatório', 'danger')
            return redirect(request.url)
        
        playlist = Playlist(
            name=name,
            description=description,
            is_public=is_public,
            user_id=current_user.id
        )
        
        db.session.add(playlist)
        db.session.commit()
        
        flash(f'Playlist "{name}" criada com sucesso!', 'success')
        return redirect(url_for('view_playlist', playlist_id=playlist.id))
    
    return render_template('create_playlist.html')

@app.route('/playlist/<int:playlist_id>')
@login_required
def view_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Verifica se o usuário tem acesso à playlist
    if not playlist.is_public and playlist.user_id != current_user.id:
        flash('Você não tem permissão para acessar esta playlist', 'danger')
        return redirect(url_for('playlists'))
    
    user_songs = Song.query.filter_by(uploader_id=current_user.id).all()
    return render_template('playlist.html', playlist=playlist, user_songs=user_songs)

@app.route('/playlist/<int:playlist_id>/add_song', methods=['POST'])
@login_required
def add_song_to_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Verifica se o usuário é o dono
    if playlist.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permissão negada'})
    
    song_id = request.form.get('song_id')
    song = Song.query.get_or_404(song_id)
    
    # Verifica se a música já está na playlist
    if song in playlist.songs:
        return jsonify({'success': False, 'error': 'Música já está na playlist'})
    
    playlist.songs.append(song)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Música "{song.title}" adicionada à playlist'})

@app.route('/playlist/<int:playlist_id>/remove_song/<int:song_id>', methods=['POST'])
@login_required
def remove_song_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    if playlist.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permissão negada'})
    
    song = Song.query.get_or_404(song_id)
    
    if song in playlist.songs:
        playlist.songs.remove(song)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Música removida da playlist'})
    else:
        return jsonify({'success': False, 'error': 'Música não encontrada na playlist'})

@app.route('/playlist/<int:playlist_id>/delete', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    if playlist.user_id != current_user.id:
        flash('Permissão negada', 'danger')
        return redirect(url_for('playlists'))
    
    db.session.delete(playlist)
    db.session.commit()
    
    flash(f'Playlist "{playlist.name}" deletada com sucesso!', 'success')
    return redirect(url_for('playlists'))

@app.route('/add_sample_songs')
@login_required
def add_sample_songs():
    sample_songs = [
        Song(title="Bohemian Rhapsody", artist="Queen", duration=354, uploader_id=current_user.id, filename="sample1.mp3", file_path="sample1.mp3"),
        Song(title="Imagine", artist="John Lennon", duration=183, uploader_id=current_user.id, filename="sample2.mp3", file_path="sample2.mp3"),
        Song(title="Blinding Lights", artist="The Weeknd", duration=200, uploader_id=current_user.id, filename="sample3.mp3", file_path="sample3.mp3"),
    ]
    
    for song in sample_songs:
        existing_song = Song.query.filter_by(title=song.title, artist=song.artist).first()
        if not existing_song:
            db.session.add(song)
    
    db.session.commit()
    flash('Músicas de exemplo adicionadas!', 'success')
    return redirect(url_for('library'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)