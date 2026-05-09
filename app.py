"""
Aplikasi Pembayaran Listrik Pascabayar
Backend: Flask + MariaDB
Author: Generated for db_listrik
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import mysql.connector
import hashlib
import os
import datetime
from functools import wraps

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'listrik_secret_key_2026'
CORS(app, supports_credentials=True)

# ── Database config ──────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': '',           # sesuaikan jika ada password MariaDB
    'database': 'db_listrik',
    'charset':  'utf8mb4',
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()

# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Silakan login terlebih dahulu'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Static / SPA ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = sha256(data.get('password', ''))
    role = data.get('role', 'admin')  # 'admin' or 'pelanggan'

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        if role == 'admin':
            cur.execute("""
                SELECT u.id_user, u.username, u.nama_admin, u.email,
                       l.nama_level, u.id_level
                FROM user u JOIN level l ON u.id_level = l.id_level
                WHERE u.username = %s AND u.password = %s
            """, (username, password))
            user = cur.fetchone()
            if user:
                session['user_id']   = user['id_user']
                session['username']  = user['username']
                session['nama']      = user['nama_admin']
                session['role']      = 'admin'
                session['level']     = user['nama_level']
                session['id_level']  = user['id_level']
                return jsonify({'success': True, 'user': {
                    'id': user['id_user'], 'username': user['username'],
                    'nama': user['nama_admin'], 'role': 'admin',
                    'level': user['nama_level']
                }})
        else:
            cur.execute("""
                SELECT p.id_pelanggan, p.username, p.nama_pelanggan,
                       p.nomor_kwh, p.email, t.daya, t.nama_golongan
                FROM pelanggan p JOIN tarif t ON p.id_tarif = t.id_tarif
                WHERE p.username = %s AND p.password = %s AND p.status_aktif = 1
            """, (username, password))
            user = cur.fetchone()
            if user:
                session['user_id']   = user['id_pelanggan']
                session['username']  = user['username']
                session['nama']      = user['nama_pelanggan']
                session['role']      = 'pelanggan'
                session['nomor_kwh'] = user['nomor_kwh']
                return jsonify({'success': True, 'user': {
                    'id': user['id_pelanggan'], 'username': user['username'],
                    'nama': user['nama_pelanggan'], 'role': 'pelanggan',
                    'nomor_kwh': user['nomor_kwh'], 'daya': user['daya'],
                    'golongan': user['nama_golongan']
                }})

        return jsonify({'success': False, 'message': 'Username atau password salah'}), 401
    finally:
        cur.close()
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    return jsonify({'success': True, 'user': {
        'id': session['user_id'], 'username': session['username'],
        'nama': session['nama'], 'role': session['role']
    }})

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        stats = {}
        cur.execute("SELECT COUNT(*) AS total FROM pelanggan WHERE status_aktif=1")
        stats['total_pelanggan'] = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) AS total FROM tagihan WHERE status='belum_bayar'")
        stats['tagihan_belum_bayar'] = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) AS total FROM tagihan WHERE status='sudah_bayar'")
        stats['tagihan_lunas'] = cur.fetchone()['total']

        cur.execute("SELECT COALESCE(SUM(total_bayar),0) AS total FROM pembayaran WHERE MONTH(tanggal_pembayaran)=MONTH(CURDATE()) AND YEAR(tanggal_pembayaran)=YEAR(CURDATE())")
        stats['pendapatan_bulan_ini'] = float(cur.fetchone()['total'])

        cur.execute("SELECT COUNT(*) AS total FROM penggunaan WHERE MONTH(created_at)=MONTH(CURDATE()) AND YEAR(created_at)=YEAR(CURDATE())")
        stats['pencatatan_bulan_ini'] = cur.fetchone()['total']

        # Tagihan terbaru
        cur.execute("""
            SELECT tg.id_tagihan, pl.nama_pelanggan, pl.nomor_kwh,
                   tg.bulan, tg.tahun, tg.total_tagihan, tg.status, tg.jatuh_tempo
            FROM tagihan tg JOIN pelanggan pl ON tg.id_pelanggan = pl.id_pelanggan
            ORDER BY tg.created_at DESC LIMIT 8
        """)
        stats['tagihan_terbaru'] = cur.fetchall()

        # Grafik pendapatan 6 bulan
        cur.execute("""
            SELECT DATE_FORMAT(tanggal_pembayaran,'%Y-%m') AS bulan,
                   SUM(total_bayar) AS total
            FROM pembayaran
            WHERE tanggal_pembayaran >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(tanggal_pembayaran,'%Y-%m')
            ORDER BY bulan
        """)
        stats['grafik_pendapatan'] = cur.fetchall()

        return jsonify({'success': True, 'data': stats})
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# PELANGGAN
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/pelanggan', methods=['GET'])
@login_required
def get_pelanggan():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        search = request.args.get('search', '')
        q = f"%{search}%"
        cur.execute("""
            SELECT p.*, t.daya, t.nama_golongan, t.tarifperkwh
            FROM pelanggan p JOIN tarif t ON p.id_tarif = t.id_tarif
            WHERE p.nama_pelanggan LIKE %s OR p.nomor_kwh LIKE %s OR p.username LIKE %s
            ORDER BY p.nama_pelanggan
        """, (q, q, q))
        return jsonify({'success': True, 'data': cur.fetchall()})
    finally:
        cur.close(); conn.close()

@app.route('/api/pelanggan/<int:id>', methods=['GET'])
@login_required
def get_pelanggan_by_id(id):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT p.*, t.daya, t.nama_golongan, t.tarifperkwh
            FROM pelanggan p JOIN tarif t ON p.id_tarif = t.id_tarif
            WHERE p.id_pelanggan = %s
        """, (id,))
        return jsonify({'success': True, 'data': cur.fetchone()})
    finally:
        cur.close(); conn.close()

@app.route('/api/pelanggan', methods=['POST'])
@login_required
def add_pelanggan():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO pelanggan (username,password,nomor_kwh,nama_pelanggan,alamat,id_tarif,no_hp,email)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (d['username'], sha256(d['password']), d['nomor_kwh'], d['nama_pelanggan'],
              d.get('alamat',''), d['id_tarif'], d.get('no_hp',''), d.get('email','')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Pelanggan berhasil ditambahkan', 'id': cur.lastrowid})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cur.close(); conn.close()

@app.route('/api/pelanggan/<int:id>', methods=['PUT'])
@login_required
def update_pelanggan(id):
    d = request.json
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE pelanggan SET nama_pelanggan=%s, alamat=%s, id_tarif=%s,
            no_hp=%s, email=%s, status_aktif=%s WHERE id_pelanggan=%s
        """, (d['nama_pelanggan'], d.get('alamat',''), d['id_tarif'],
              d.get('no_hp',''), d.get('email',''), d.get('status_aktif',1), id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Data pelanggan diperbarui'})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cur.close(); conn.close()

@app.route('/api/pelanggan/<int:id>', methods=['DELETE'])
@login_required
def delete_pelanggan(id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM pelanggan WHERE id_pelanggan=%s", (id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Pelanggan dihapus'})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cur.close(); conn.close()

# SP: Pelanggan 900 watt
@app.route('/api/pelanggan/daya900', methods=['GET'])
@login_required
def pelanggan_900():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.callproc('sp_pelanggan_900watt')
        for result in cur.stored_results():
            data = result.fetchall()
        return jsonify({'success': True, 'data': data})
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# TARIF
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/tarif', methods=['GET'])
@login_required
def get_tarif():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM tarif ORDER BY daya")
        return jsonify({'success': True, 'data': cur.fetchall()})
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# PENGGUNAAN
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/penggunaan', methods=['GET'])
@login_required
def get_penggunaan():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        bulan = request.args.get('bulan', '')
        tahun = request.args.get('tahun', '')
        search = request.args.get('search', '')

        base_q = "SELECT * FROM v_info_penggunaan WHERE 1=1"
        params = []
        if bulan:
            base_q += " AND bulan=%s"; params.append(bulan)
        if tahun:
            base_q += " AND tahun=%s"; params.append(tahun)
        if search:
            base_q += " AND (nama_pelanggan LIKE %s OR nomor_kwh LIKE %s)"
            params += [f"%{search}%", f"%{search}%"]
        base_q += " LIMIT 200"

        cur.execute(base_q, params)
        rows = cur.fetchall()
        # Convert Decimal to float for JSON
        for r in rows:
            for k, v in r.items():
                if hasattr(v, '__float__'):
                    r[k] = float(v)
                elif isinstance(v, datetime.date):
                    r[k] = v.isoformat()
        return jsonify({'success': True, 'data': rows})
    finally:
        cur.close(); conn.close()

@app.route('/api/penggunaan', methods=['POST'])
@login_required
def add_penggunaan():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO penggunaan (id_pelanggan,bulan,tahun,meter_awal,meter_ahir,tanggal_catat,petugas)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (d['id_pelanggan'], d['bulan'], d['tahun'], d['meter_awal'],
              d['meter_ahir'], d.get('tanggal_catat', datetime.date.today()), d.get('petugas','')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Data penggunaan berhasil dicatat (tagihan auto-dibuat)', 'id': cur.lastrowid})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cur.close(); conn.close()

# Function: total kwh per bulan
@app.route('/api/penggunaan/total', methods=['GET'])
@login_required
def total_penggunaan():
    id_plg = request.args.get('id_pelanggan')
    bulan  = request.args.get('bulan')
    tahun  = request.args.get('tahun')
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT fn_total_penggunaan_perbulan(%s,%s,%s) AS total_kwh", (id_plg, bulan, tahun))
        result = cur.fetchone()
        return jsonify({'success': True, 'total_kwh': float(result[0]) if result[0] else 0})
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# TAGIHAN
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/tagihan', methods=['GET'])
@login_required
def get_tagihan():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        role   = session.get('role')
        user_id = session.get('user_id')

        q = """
            SELECT tg.*, pl.nama_pelanggan, pl.nomor_kwh, t.daya, t.nama_golongan
            FROM tagihan tg
            JOIN pelanggan pl ON tg.id_pelanggan = pl.id_pelanggan
            JOIN tarif t ON pl.id_tarif = t.id_tarif
            WHERE 1=1
        """
        params = []
        if role == 'pelanggan':
            q += " AND tg.id_pelanggan=%s"; params.append(user_id)
        if status:
            q += " AND tg.status=%s"; params.append(status)
        if search:
            q += " AND (pl.nama_pelanggan LIKE %s OR pl.nomor_kwh LIKE %s)"
            params += [f"%{search}%", f"%{search}%"]
        q += " ORDER BY tg.created_at DESC LIMIT 200"

        cur.execute(q, params)
        rows = cur.fetchall()
        for r in rows:
            for k, v in r.items():
                if hasattr(v, '__float__'):
                    r[k] = float(v)
                elif isinstance(v, (datetime.date, datetime.datetime)):
                    r[k] = v.isoformat()
        return jsonify({'success': True, 'data': rows})
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# PEMBAYARAN
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/pembayaran', methods=['GET'])
@login_required
def get_pembayaran():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        role = session.get('role')
        user_id = session.get('user_id')
        search = request.args.get('search', '')

        q = """
            SELECT pb.*, pl.nama_pelanggan, pl.nomor_kwh,
                   tg.bulan, tg.tahun, tg.jumlah_meter, tg.total_tagihan,
                   u.nama_admin AS nama_kasir
            FROM pembayaran pb
            JOIN tagihan tg ON pb.id_tagihan = tg.id_tagihan
            JOIN pelanggan pl ON pb.id_pelanggan = pl.id_pelanggan
            JOIN user u ON pb.id_user = u.id_user
            WHERE 1=1
        """
        params = []
        if role == 'pelanggan':
            q += " AND pb.id_pelanggan=%s"; params.append(user_id)
        if search:
            q += " AND (pl.nama_pelanggan LIKE %s OR pl.nomor_kwh LIKE %s)"
            params += [f"%{search}%", f"%{search}%"]
        q += " ORDER BY pb.tanggal_pembayaran DESC LIMIT 200"

        cur.execute(q, params)
        rows = cur.fetchall()
        for r in rows:
            for k, v in r.items():
                if hasattr(v, '__float__'):
                    r[k] = float(v)
                elif isinstance(v, (datetime.date, datetime.datetime)):
                    r[k] = v.isoformat()
        return jsonify({'success': True, 'data': rows})
    finally:
        cur.close(); conn.close()

@app.route('/api/pembayaran', methods=['POST'])
@login_required
def bayar():
    d = request.json
    id_tagihan = d['id_tagihan']
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        # Ambil info tagihan
        cur.execute("SELECT * FROM tagihan WHERE id_tagihan=%s AND status='belum_bayar'", (id_tagihan,))
        tg = cur.fetchone()
        if not tg:
            return jsonify({'success': False, 'message': 'Tagihan tidak ditemukan atau sudah dibayar'}), 400

        biaya_admin = float(d.get('biaya_admin', 2500))
        total_bayar = float(tg['total_tagihan']) + biaya_admin
        no_ref = f"PLN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{id_tagihan}"

        cur2 = conn.cursor()
        cur2.execute("""
            INSERT INTO pembayaran (id_tagihan, id_pelanggan, tanggal_pembayaran,
                bulan_bayar, tahun_bayar, biaya_admin, total_bayar, id_user,
                metode_bayar, no_referensi, keterangan)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (id_tagihan, tg['id_pelanggan'], datetime.date.today(),
              tg['bulan'], tg['tahun'], biaya_admin, total_bayar,
              session['user_id'], d.get('metode_bayar','tunai'), no_ref, d.get('keterangan','')))

        cur2.execute("UPDATE tagihan SET status='sudah_bayar' WHERE id_tagihan=%s", (id_tagihan,))
        conn.commit()

        return jsonify({'success': True, 'message': 'Pembayaran berhasil', 'no_referensi': no_ref, 'total_bayar': total_bayar})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT u.id_user, u.username, u.nama_admin, u.email, u.hp,
                   l.nama_level, u.id_level, u.created_at
            FROM user u JOIN level l ON u.id_level = l.id_level
            ORDER BY u.nama_admin
        """)
        rows = cur.fetchall()
        for r in rows:
            if isinstance(r.get('created_at'), datetime.datetime):
                r['created_at'] = r['created_at'].isoformat()
        return jsonify({'success': True, 'data': rows})
    finally:
        cur.close(); conn.close()

@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO user (username,password,nama_admin,id_level,email,hp)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (d['username'], sha256(d['password']), d['nama_admin'],
              d['id_level'], d.get('email',''), d.get('hp','')))
        conn.commit()
        return jsonify({'success': True, 'message': 'User berhasil ditambahkan'})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cur.close(); conn.close()

@app.route('/api/level', methods=['GET'])
@login_required
def get_level():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM level")
        return jsonify({'success': True, 'data': cur.fetchall()})
    finally:
        cur.close(); conn.close()

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("  APLIKASI LISTRIK PASCABAYAR")
    print("  Buka browser: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')
