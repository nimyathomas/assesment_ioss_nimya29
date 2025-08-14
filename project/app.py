from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import string, random
import qrcode
from io import BytesIO
from flask import send_file

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_super_secret_key'  # session safety

db = SQLAlchemy(app)

# Models
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)

# Generate short code
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Home / Index route
@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    if request.method == 'POST':
        long_url = request.form['long_url']
        url = URL.query.filter_by(long_url=long_url).first()
        if not url:
            code = generate_short_code()
            url = URL(long_url=long_url, short_code=code)
            db.session.add(url)
            db.session.commit()
        short_url = request.host_url + url.short_code
        flash('Short URL generated successfully!', 'success')

    recent_urls = URL.query.order_by(URL.id.desc()).limit(5).all()
    total_clicks = sum([u.clicks for u in URL.query.all()])
    total_urls = URL.query.count()

    return render_template('index.html', short_url=short_url, recent_urls=recent_urls,
                           total_clicks=total_clicks, total_urls=total_urls)

# Redirect short URL
@app.route('/<short_code>')
def redirect_short_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first_or_404()
    url.clicks += 1
    db.session.commit()
    return redirect(url.long_url)

# Generate QR code on demand
@app.route('/qr/<short_code>')
def generate_qr(short_code):
    url = URL.query.filter_by(short_code=short_code).first_or_404()
    qr_img = qrcode.make(request.host_url + url.short_code)
    buf = BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png', download_name=f'{short_code}.png')

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
