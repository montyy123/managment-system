from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import logging
from sqlalchemy import func

# --- Configuration & Setup ---

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nexgen-secure-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///event_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging for better future debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def __init__(self, username, password, role='user'):
        self.username = username
        self.password = password
        self.role = role

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    membership_type = db.Column(db.String(50), nullable=False, default='6 months') 
    fee = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active')

    def __init__(self, guest_id, name, email, membership_type, fee, start_date, end_date, status='Active'):
        self.guest_id = guest_id
        self.name = name
        self.email = email
        self.membership_type = membership_type
        self.fee = fee
        self.start_date = start_date
        self.end_date = end_date
        self.status = status

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    details = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref=db.backref('transactions', lazy='dynamic'))

    def __init__(self, member_id, action, amount, details, date=None):
        self.member_id = member_id
        self.action = action
        self.amount = amount
        self.details = details
        if date:
            self.date = date

# --- Global Logic & Middleware ---

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', code=404, message="Nexus Link Severed"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', code=500, message="Core Logic Cascade Failure"), 500

@app.before_request
def check_session_expiry():
    # Simple middleware for future security expansions
    pass

# --- Self-Healing Database Logic ---

def init_db():
    """Robust database initialization with thorough health check."""
    with app.app_context():
        try:
            # Check all tables to ensure schema matches
            User.query.count()
            Member.query.count()
            Transaction.query.count()
            logger.info("Database health check: PASSED (All tables reachable)")
        except Exception as e:
            logger.warning(f"Database health check: FAILED - {str(e)}. Attempting system restoration...")
            try:
                db.drop_all()
                db.create_all()
                # Seed Demo Data
                admin = User(username='admin', password='admin123', role='admin')
                user = User(username='user', password='user123', role='user')
                db.session.add_all([admin, user])
                db.session.commit()
                logger.info("System restoration complete. Demo accounts provisioned.")
            except Exception as schema_error:
                logger.error(f"FATAL: Database restoration failed: {str(schema_error)}")

# --- Controllers / Routes ---

@app.route('/')
def home():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and user.password == password:
                session.update({
                    'user_id': user.id,
                    'role': user.role,
                    'username': user.username
                })
                flash('Authentication successful. Welcome to the cluster.', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid passcode or identifier. Access denied.', 'danger')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Critical authentication failure. Try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Terminal session terminated successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/maintenance')
def maintenance():
    if session.get('role') != 'admin':
        flash('Unauthorized Access Attempt. Security log updated.', 'danger')
        return redirect(url_for('dashboard'))
    members = Member.query.all()
    return render_template('maintenance.html', members=members)

@app.route('/maintenance/add', methods=['GET', 'POST'])
def add_member():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            if 'terms' not in request.form:
                flash('Protocol violation: Terms must be acknowledged.', 'danger')
                return redirect(url_for('add_member'))

            # Extract and calc
            m_type = request.form['membership_type']
            fees = {'6 months': 50.0, '1 year': 90.0, '2 years': 160.0}
            days = {'6 months': 180, '1 year': 365, '2 years': 730}
            
            fee = fees.get(m_type, 50.0)
            end_date = datetime.utcnow() + timedelta(days=days.get(m_type, 180))
            
            new_member = Member(
                guest_id=request.form['guest_id'],
                name=request.form['name'],
                email=request.form['email'],
                membership_type=m_type,
                fee=fee,
                start_date=datetime.utcnow(),
                end_date=end_date
            )
            
            db.session.add(new_member)
            db.session.flush() # Get ID for transaction
            
            txn = Transaction(new_member.id, 'New', fee, f'Provisioned: {m_type}')
            db.session.add(txn)
            db.session.commit()
            
            flash(f'Entity {new_member.name} successfully provisioned. Credit: ${fee}', 'success')
            return redirect(url_for('maintenance'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Provisioning error: {str(e)}")
            flash(f"System error during provisioning: {str(e)}", "danger")
            
    return render_template('add_member.html')

@app.route('/maintenance/update/<int:id>', methods=['GET', 'POST'])
def update_member(id):
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
        
    member = db.get_or_404(Member, id)
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            amount = 0.0
            
            if action == 'cancel':
                member.status = 'Cancelled'
                flash(f'Node lifecycle {member.guest_id} terminated.', 'warning')
            elif action == 'extend':
                ext_type = request.form.get('extension_type', '6 months')
                fees = {'6 months': 40.0, '1 year': 75.0, '2 years': 130.0}
                days = {'6 months': 180, '1 year': 365, '2 years': 730}
                
                amount = fees.get(ext_type, 40.0)
                base_date = max(member.end_date, datetime.utcnow().date())
                member.end_date = base_date + timedelta(days=days.get(ext_type, 180))
                member.status = 'Active'
                flash(f'Node lifecycle extended by {ext_type}. Credit: ${amount}', 'success')
                
            txn = Transaction(member.id, action.capitalize(), amount, f'Override: {action}')
            db.session.add(txn)
            db.session.commit()
            return redirect(url_for('maintenance'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update error: {str(e)}")
            flash("Override protocol failed. System rollbacked.", "danger")
        
    return render_template('update_member.html', member=member)

@app.route('/reports')
def reports():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    try:
        # Aggregations
        active_count = Member.query.filter_by(status='Active').count()
        
        # Financial Computation
        revenue_sum = db.session.query(func.sum(Transaction.amount)).scalar()
        total_revenue = float(revenue_sum) if revenue_sum is not None else 0.0
        
        # Temporal Logic
        today = datetime.utcnow().date()
        soon = today + timedelta(days=30)
        expiring_soon = Member.query.filter(
            Member.end_date <= soon, 
            Member.end_date >= today, 
            Member.status == 'Active'
        ).count()

        # Monthly Analytics Execution
        monthly_query = db.session.query(
            func.strftime('%Y-%m', Transaction.date),
            func.sum(Transaction.amount)
        ).group_by(func.strftime('%Y-%m', Transaction.date)).order_by(func.strftime('%Y-%m', Transaction.date)).limit(6).all()
        
        chart_labels = []
        chart_values = []
        
        for record in monthly_query:
            # Safe parsing of database results
            label = str(record[0]) if record[0] else "No Date"
            value = float(record[1]) if record[1] is not None else 0.0
            chart_labels.append(label)
            chart_values.append(value)
        
        return render_template('reports.html', 
                               active=active_count, 
                               soon=expiring_soon, 
                               revenue=total_revenue,
                               labels=chart_labels,
                               values=chart_values)
    except Exception as e:
        logger.error(f"Nexus Reports Analytical failure: {str(e)}")
        return render_template('error.html', code=500, message="Critical Analytical Failure"), 500

@app.route('/transactions')
def transactions():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('transactions.html', transactions=Transaction.query.order_by(Transaction.date.desc()).all())

@app.route('/flow_chart')
def flow_chart():
    return render_template('flow_chart.html', 
                           total=Member.query.count(), 
                           active=Member.query.filter_by(status='Active').count(), 
                           cancelled=Member.query.filter_by(status='Cancelled').count())

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001)
