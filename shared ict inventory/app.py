from flask import Flask, render_template_string, request, jsonify, send_file, session, redirect, url_for, flash
import os
import warnings
import requests
import tempfile
from openpyxl import __version__ as openpyxl_version
from pymongo import MongoClient
from bson import ObjectId
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "afrahkoum")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "ict_inventory")

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
mongo_collection = mongo_db[MONGO_COLLECTION_NAME]

# Simple user credentials (in production, use a proper database)
USERS = {
    "admin": {"password": "admin123", "role": "admin", "hidden": True},
    "user": {"password": "user123", "role": "user", "hidden": True}
}

# User management collection
users_collection = mongo_db["users"]

# Check connection to MongoDB
try:
    # Test the connection and print collection info
    doc_count = mongo_collection.count_documents({})
    print(f"Connected to MongoDB database '{MONGO_DB_NAME}', collection '{MONGO_COLLECTION_NAME}'")
    print(f"Total documents in collection: {doc_count}")
    
    # Print first few documents for debugging
    if doc_count > 0:
        sample_docs = list(mongo_collection.find({}, {"_id": 0}).limit(3))
        print("Sample documents:")
        for i, doc in enumerate(sample_docs, 1):
            print(f"  Document {i}: {doc}")
    else:
        print("No documents found in the collection")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check hardcoded users first (admin/user)
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            session['role'] = USERS[username]['role']
            session['location_permissions'] = {}  # No restrictions for hardcoded users
            session['column_permissions'] = []  # No column restrictions for hardcoded users
            
            if USERS[username]['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            # Check MongoDB users
            user = users_collection.find_one({"username": username, "password": password})
            if user:
                session['username'] = username
                session['role'] = user['role']
                session['location_permissions'] = user.get('location_permissions', {})
                session['column_permissions'] = user.get('column_permissions', [])
                
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid username or password')
    
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>ICT Inventory - Login</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .login-card {
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                    padding: 40px;
                    width: 100%;
                    max-width: 400px;
                }
                .login-header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .login-header h2 {
                    color: #333;
                    font-weight: 700;
                    margin-bottom: 10px;
                }
                .login-header p {
                    color: #666;
                    margin-bottom: 0;
                }
                .form-group label {
                    font-weight: 600;
                    color: #333;
                }
                .form-control {
                    border-radius: 8px;
                    border: 2px solid #e9ecef;
                    padding: 12px 15px;
                    font-size: 16px;
                }
                .form-control:focus {
                    border-color: #667eea;
                    box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
                }
                .btn-login {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    width: 100%;
                    color: white;
                }
                .btn-login:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                    color: white;
                }
                .demo-credentials {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin-top: 20px;
                    font-size: 14px;
                }
                .demo-credentials h6 {
                    color: #495057;
                    font-weight: 600;
                    margin-bottom: 10px;
                }
                .credential-item {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 5px;
                }
            </style>
        </head>
        <body>
            <div class="login-card">
                <div class="login-header">
                    <h2><i class="fas fa-database mr-2"></i>ICT Inventory</h2>
                    <p>Please sign in to continue</p>
                </div>
                
                {% with messages = get_flashed_messages() %}
                    {% if messages %}
                        <div class="alert alert-danger" role="alert">
                            {{ messages[0] }}
                        </div>
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-login">
                        <i class="fas fa-sign-in-alt mr-2"></i>Sign In
                    </button>
                </form>
                
                <div class="demo-credentials">
                    <h6><i class="fas fa-info-circle mr-2"></i>Demo Credentials</h6>
                    <div class="credential-item">
                        <strong>Admin:</strong> <span>admin / admin123</span>
                    </div>
                    <div class="credential-item">
                        <strong>User:</strong> <span>user / user123</span>
                    </div>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    try:
        # Fetch all documents from MongoDB
        data = list(mongo_collection.find({}, {"_id": 0}))
        if not data:
            raise Exception("No data found in MongoDB collection 'ict_inventory'.")
        # Create a mapping of display names to safe names
        original_columns = [str(col).strip() for col in data[0].keys()]
        safe_columns = [f"col_{i}" for i in range(len(original_columns))]
        column_mapping = dict(zip(original_columns, safe_columns))
        reverse_mapping = dict(zip(safe_columns, original_columns))
        # Convert data to safe columns
        for row in data:
            for orig, safe in column_mapping.items():
                row[safe] = row.pop(orig)
        # Create DataFrame for shape
        import pandas as pd
        df = pd.DataFrame(data)
    except Exception as e:
        import traceback
        error_message = str(e)
        tb = traceback.format_exc()
        return render_template_string('''
            <html>
            <head>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
            </head>
            <body>
                <div class="container mt-4">
                    <h2>Error loading MongoDB data</h2>
                    <div class="alert alert-danger">
                        Could not load the MongoDB data.<br>
                        <br>Error details: {{ error_message }}
                        <pre>{{ tb }}</pre>
                    </div>
                </div>
            </body>
            </html>
        ''', error_message=error_message, tb=tb)
    # Create enumerated columns for the template
    columns_list = original_columns  # Use original column names for display
    enumerated_columns = list(enumerate(columns_list))
    shape = df.shape
    username = session.get('username', 'Admin')
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>ICT Inventory - Admin Dashboard</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/fixedheader/3.4.0/css/fixedHeader.dataTables.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body { background: #f8f9fa; }
                .navbar { background: #343a40; }
                .navbar-brand, .navbar-nav .nav-link { color: #fff !important; }
                .dashboard-title { font-size: 2.2rem; font-weight: 700; color: #343a40; }
                .dashboard-subtitle { font-size: 1.1rem; color: #6c757d; }
                .card { box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-radius: 1rem; position: relative; }
                .footer { background: #343a40; color: #fff; padding: 1rem 0; text-align: center; margin-top: 2rem; }
                
                /* Excel-like table styling */
                .table-container { 
                    position: relative; 
                    overflow: hidden;
                }
                
                /* DataTables scroll container styling */
                .dataTables_wrapper .dataTables_scroll {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    background: white;
                }
                
                .dataTables_wrapper .dataTables_scrollBody {
                    max-height: 60vh;
                }
                
                /* Sticky header styling - target DataTables elements */
                .dataTables_wrapper .dataTable thead th {
                    position: sticky !important;
                    top: 0 !important;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
                    z-index: 10 !important;
                    border: 1px solid #dee2e6 !important;
                    padding: 12px 8px !important;
                    font-weight: 600 !important;
                    font-size: 14px !important;
                    text-align: center !important;
                    vertical-align: middle !important;
                    min-width: 120px !important;
                }
                
                .dataTables_wrapper .dataTable thead th:hover {
                    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
                }
                
                /* Filter row styling */
                .filter-row th {
                    position: sticky !important;
                    top: 50px !important;
                    background: #e9ecef !important;
                    padding: 4px 8px !important;
                    border-bottom: 2px solid #dee2e6 !important;
                    z-index: 9 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
                
                /* Data table styling */
                .table-body-wrapper table {
                    margin-bottom: 0 !important;
                    width: 100%;
                    min-width: 100%;
                }
                
                .table-body-wrapper th {
                    display: none !important; /* Hide headers in body */
                }
                
                /* Allow natural column expansion */
                .table-body-wrapper td {
                    padding: 8px 12px !important;
                    border: 1px solid #dee2e6 !important;
                    min-width: 120px !important;
                }
                
                /* Excel-like cell styling */
                .excel-cell {
                    cursor: pointer;
                    padding: 8px 12px !important;
                    border: 1px solid #dee2e6 !important;
                    position: relative;
                    background: white;
                    min-width: 120px;
                }
                
                .excel-cell:hover {
                    background-color: #e3f2fd !important;
                    border-color: #2196f3 !important;
                }
                
                .excel-cell.editing {
                    background-color: #fff3e0 !important;
                    border-color: #ff9800 !important;
                    border-width: 2px !important;
                }
                
                .excel-cell input {
                    border: none;
                    background: transparent;
                    width: 100%;
                    padding: 0;
                    margin: 0;
                    outline: none;
                    font-size: inherit;
                    font-family: inherit;
                }
                
                /* Row selection */
                .row-selected {
                    background-color: #e8f5e8 !important;
                }
                
                .row-checkbox {
                    width: 20px;
                    text-align: center;
                }
                
                /* Action buttons */
                .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
                .action-buttons { white-space: nowrap; min-width: 120px; }
                
                /* Fixed header with filters */
                .dataTables_wrapper .dataTable thead th {
                    position: sticky !important;
                    top: 0 !important;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
                    z-index: 10 !important;
                    border: 1px solid #dee2e6 !important;
                    padding: 8px 12px !important;
                    font-weight: 600 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    transition: all 0.3s ease !important;
                }
                
                .dataTables_wrapper .dataTable thead th:hover {
                    background: #e9ecef !important;
                }
                
                /* Sticky header active state */
                .sticky-active .dataTables_wrapper .dataTable thead th {
                    background: #ffffff !important;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
                    border-bottom: 2px solid #007bff !important;
                }
                
                /* Sticky header indicator */
                .sticky-active.indicator-shown::before {
                    content: "📌 Headers Fixed";
                    position: fixed;
                    top: 10px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 12px;
                    z-index: 1000;
                    animation: fadeInOut 3s ease-in-out;
                }
                
                @keyframes fadeInOut {
                    0% { opacity: 0; transform: translateY(-10px); }
                    20% { opacity: 1; transform: translateY(0); }
                    80% { opacity: 1; transform: translateY(0); }
                    100% { opacity: 0; transform: translateY(-10px); }
                }
                
                .filter-select {
                    width: 100%;
                    padding: 4px 6px;
                    border: 1px solid #ced4da;
                    border-radius: 3px;
                    font-size: 12px;
                    background: white;
                    cursor: pointer;
                }
                
                .filter-clear {
                    background: none;
                    border: none;
                    color: #dc3545;
                    font-size: 12px;
                    cursor: pointer;
                    padding: 2px 4px;
                    margin-left: 4px;
                }
                
                .filter-clear:hover {
                    background: #f8d7da;
                    border-radius: 2px;
                }
                
                /* Fixed footer with pagination */
                .dataTables_wrapper .dataTables_paginate,
                .dataTables_wrapper .dataTables_length {
                    position: sticky;
                    bottom: 0;
                    background: white;
                    padding: 10px;
                    border-top: 1px solid #dee2e6;
                }
                
                .dataTables_wrapper .dataTables_info {
                    position: sticky;
                    bottom: 0;
                    background: white;
                    padding: 10px;
                }
                
                /* Toolbar styling */
                .toolbar {
                    background: white;
                    padding: 10px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .toolbar .btn {
                    margin-right: 10px;
                }
                
                /* Status indicators */
                .save-indicator {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    display: none;
                }
                
                /* Filter status */
                .filter-status {
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                    margin-left: 10px;
                }
                
                /* User info */
                .user-info {
                    background: #007bff;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 14px;
                    margin-right: 10px;
                }
                
                /* Ensure sticky headers work properly */
                .dataTables_wrapper {
                    position: relative;
                }
                
                .dataTables_wrapper .dataTable {
                    border-collapse: separate;
                    border-spacing: 0;
                }
                
                /* Read-only cell styling */
                .readonly-cell {
                    padding: 8px 12px !important;
                    border: 1px solid #dee2e6 !important;
                    background: #f8f9fa;
                    min-width: 120px;
                }
                
                .readonly-cell:hover {
                    background-color: #e9ecef !important;
                }
                
                /* Ensure DataTables wrapper allows sticky positioning */
                .dataTables_wrapper {
                    position: relative;
                }
                
                .dataTables_wrapper .dataTables_scroll {
                    position: relative;
                }
                
                /* DataTables scroll container styling */
                .dataTables_wrapper .dataTables_scroll {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    background: white;
                }
                
                .dataTables_wrapper .dataTables_scrollBody {
                    max-height: 60vh;
                }
                
                /* Sticky header styling - target DataTables elements */
                .dataTables_wrapper .dataTable thead th {
                    position: sticky !important;
                    top: 0 !important;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
                    z-index: 10 !important;
                    border: 1px solid #dee2e6 !important;
                    padding: 12px 8px !important;
                    font-weight: 600 !important;
                    font-size: 14px !important;
                    text-align: center !important;
                    vertical-align: middle !important;
                    min-width: 120px !important;
                }
                
                .dataTables_wrapper .dataTable thead th:hover {
                    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
                }
                
                /* Filter row styling */
                .filter-row th {
                    position: sticky !important;
                    top: 50px !important;
                    background: #e9ecef !important;
                    padding: 4px 8px !important;
                    border-bottom: 2px solid #dee2e6 !important;
                    z-index: 9 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark">
                <a class="navbar-brand" href="#"><i class="fas fa-database mr-2"></i>ICT Inventory - Admin</a>
                <div class="navbar-nav ml-auto">
                    <span class="user-info">
                        <i class="fas fa-user-shield mr-2"></i>{{ username }} (Admin)
                    </span>
                    <a class="nav-link" href="{{ url_for('logout') }}">
                        <i class="fas fa-sign-out-alt mr-2"></i>Logout
                    </a>
                </div>
            </nav>
            
            <!-- Save indicator -->
            <div id="saveIndicator" class="save-indicator">
                <div class="alert alert-success" role="alert">
                    <i class="fas fa-check-circle mr-2"></i>Changes saved!
                </div>
            </div>
            
            <div class="container-fluid mt-5">
                <div class="row mb-4">
                    <div class="col-12 text-center">
                        <div class="dashboard-title mb-2"><i class="fas fa-laptop-code mr-2"></i>Admin Dashboard</div>
                        <div class="dashboard-subtitle">Full access: Edit, filter, add, delete, and manage inventory data</div>
                    </div>
                </div>
                
                <!-- Toolbar -->
                <div class="row mb-3">
                    <div class="col-12">
                        <div class="toolbar">
                            <button class="btn btn-success" id="addNewBtn">
                                <i class="fas fa-plus mr-2"></i>Add New Row
                            </button>
                            <button class="btn btn-primary" id="copySelectedBtn" disabled>
                                <i class="fas fa-copy mr-2"></i>Copy Selected (<span id="selectedCount">0</span>)
                            </button>
                            <button class="btn btn-danger" id="deleteSelectedBtn" disabled>
                                <i class="fas fa-trash mr-2"></i>Delete Selected
                            </button>
                            <button class="btn btn-info" id="selectAllBtn">
                                <i class="fas fa-check-square mr-2"></i>Select All
                            </button>
                            <button class="btn btn-secondary" id="clearSelectionBtn">
                                <i class="fas fa-square mr-2"></i>Clear Selection
                            </button>
                            <button class="btn btn-warning" id="clearFiltersBtn">
                                <i class="fas fa-filter mr-2"></i>Clear All Filters
                            </button>
                            <a href="{{ url_for('manage_users') }}" class="btn btn-info">
                                <i class="fas fa-users mr-2"></i>Manage Users
                            </a>
                            <a href="{{ url_for('download') }}" class="btn btn-success">
                                <i class="fas fa-download mr-2"></i>Download CSV
                            </a>
                            <div class="float-right">
                                <span class="text-muted">
                                    <i class="fas fa-info-circle mr-1"></i>
                                    Click cells to edit • Use dropdown filters • Select rows with checkboxes
                                </span>
                                <span id="filterStatus" class="filter-status" style="display: none;">
                                    <i class="fas fa-filter mr-1"></i>Filters active
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row justify-content-center">
                    <div class="col-12">
                        <div class="card p-4">
                            <table id="excelTable" class="table table-striped table-bordered" style="width:100%">
                                <thead></thead>
                                <tbody></tbody>
                            </table>
                            <p class="text-muted mt-2">(Admin view with full editing capabilities and filtering.)</p>
                        </div>
                    </div>
                </div>
            </div>

            <footer class="footer">
                <div>ICT Inventory &copy; 2024 | Admin Interface | Powered by Flask & MongoDB</div>
            </footer>
            
            <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
            <script src="https://cdn.datatables.net/fixedheader/3.4.0/js/dataTables.fixedHeader.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js"></script>
            <script>
            let table;
            let columns = {{ columns_list|tojson }};
            let editingCell = null;
            let selectedRows = new Set();
            let columnFilters = {};
            let allData = [];
            
            $(document).ready(function() {
                // Initialize DataTable
                table = $('#excelTable').DataTable({
                    processing: true,
                    serverSide: false,
                    ajax: {
                        url: '/data',
                        type: 'POST',
                        dataSrc: function(json) {
                            allData = json.data || [];
                            return allData;
                        }
                    },
                    columns: [
                        {
                            data: null,
                            title: '<input type="checkbox" id="selectAllCheckbox">',
                            orderable: false,
                            className: 'row-checkbox',
                            render: function(data, type, row) {
                                return '<input type="checkbox" class="row-select" data-id="' + row.record_id + '">';
                            }
                        },
                        {% for i, col in enumerated_columns %}
                        {
                            data: "col_{{ i }}",
                            name: "col_{{ i }}",
                            title: {{ col|tojson }},
                            className: 'excel-cell',
                            render: function(data, type, row, meta) {
                                if (type === 'display') {
                                    return '<div class="cell-content" data-column="{{ i }}" data-id="' + row.record_id + '">' + (data || '') + '</div>';
                                }
                                return data;
                            }
                        },
                        {% endfor %}
                        {
                            data: null,
                            title: "Actions",
                            orderable: false,
                            className: 'action-buttons',
                            render: function(data, type, row) {
                                return '<button class="btn btn-danger btn-sm delete-btn" data-id="' + row.record_id + '">' +
                                       '<i class="fas fa-trash"></i></button>';
                            }
                        }
                    ],
                    pageLength: 25,
                    lengthMenu: [[25, 50, 100, -1], ["25", "50", "100", "All"]],
                    dom: '<"top"l>rt<"bottom"ip>',
                    ordering: true,
                    searching: true,
                    scrollX: true,
                    scrollY: '60vh',
                    scrollCollapse: true,
                    fixedHeader: false,
                    language: {
                        processing: "Loading...",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries (filtered from _MAX_ total entries)",
                        emptyTable: "No data available"
                    },
                    initComplete: function() {
                        createFilterRow();
                        updateSelectionUI();
                    },
                    drawCallback: function() {
                        updateSelectionUI();
                    }
                });

                // Cell click for inline editing
                $('#excelTable').on('click', '.cell-content', function(e) {
                    e.stopPropagation();
                    startCellEdit($(this));
                });

                // Row selection
                $('#excelTable').on('change', '.row-select', function() {
                    const recordId = $(this).data('id');
                    const row = $(this).closest('tr');
                    
                    if ($(this).is(':checked')) {
                        selectedRows.add(recordId);
                        row.addClass('row-selected');
                    } else {
                        selectedRows.delete(recordId);
                        row.removeClass('row-selected');
                    }
                    updateSelectionUI();
                });

                // Select all checkbox
                $('#selectAllCheckbox').on('change', function() {
                    const isChecked = $(this).is(':checked');
                    $('.row-select:visible').prop('checked', isChecked).trigger('change');
                });

                // Toolbar buttons
                $('#addNewBtn').click(function() {
                    addNewRow();
                });

                $('#copySelectedBtn').click(function() {
                    copySelectedRows();
                });

                $('#deleteSelectedBtn').click(function() {
                    deleteSelectedRows();
                });

                $('#selectAllBtn').click(function() {
                    $('#selectAllCheckbox').prop('checked', true).trigger('change');
                });

                $('#clearSelectionBtn').click(function() {
                    $('#selectAllCheckbox').prop('checked', false).trigger('change');
                });

                // Individual delete button
                $('#excelTable').on('click', '.delete-btn', function() {
                    const recordId = $(this).data('id');
                    if (confirm('Are you sure you want to delete this record?')) {
                        deleteRecord(recordId);
                    }
                });

                // Click outside to finish editing
                $(document).on('click', function(e) {
                    if (editingCell && !$(e.target).closest('.excel-cell').length) {
                        finishCellEdit();
                    }
                });

                // Keyboard shortcuts
                $(document).on('keydown', function(e) {
                    if (editingCell) {
                        if (e.key === 'Enter' || e.key === 'Tab') {
                            e.preventDefault();
                            finishCellEdit();
                        } else if (e.key === 'Escape') {
                            cancelCellEdit();
                        }
                    }
                });
                
                // Enhance sticky header behavior
                $('.table-scroll').on('scroll', function() {
                    const scrollTop = $(this).scrollTop();
                    const thead = $(this).find('thead');
                    const tableContainer = $(this).closest('.table-container');
                    
                    if (scrollTop > 0) {
                        thead.addClass('sticky-active');
                        tableContainer.addClass('sticky-active');
                        
                        // Show indicator briefly
                        if (!tableContainer.hasClass('indicator-shown')) {
                            tableContainer.addClass('indicator-shown');
                            setTimeout(() => {
                                tableContainer.removeClass('indicator-shown');
                            }, 3000);
                        }
                    } else {
                        thead.removeClass('sticky-active');
                        tableContainer.removeClass('sticky-active');
                    }
                });
                
                // Force DataTables to recalculate sticky headers
                $(window).on('resize', function() {
                    if (table) {
                        table.columns.adjust();
                        table.fixedHeader.adjust();
                    }
                });
            });

            function createFilterRow() {
                const filterRow = $('<tr class="filter-row"></tr>');
                filterRow.append('<th></th>');
                columns.forEach((columnName, index) => {
                    const uniqueValues = getUniqueValues(index);
                    const selectHtml = createFilterSelect(index, uniqueValues);
                    filterRow.append('<th>' + selectHtml + '</th>');
                });
                filterRow.append('<th></th>');
                $('#excelTable thead').append(filterRow);
                
                $('.filter-select').on('change', function() {
                    const columnIndex = $(this).data('column');
                    const value = $(this).val();
                    applyFilter(columnIndex, value);
                });
                
                $('.filter-clear').on('click', function() {
                    const columnIndex = $(this).data('column');
                    clearFilter(columnIndex);
                });
            }

            function getUniqueValues(columnIndex) {
                const values = new Set();
                allData.forEach(row => {
                    const value = row['col_' + columnIndex];
                    if (value && value.toString().trim() !== '') {
                        values.add(value.toString().trim());
                    }
                });
                return Array.from(values).sort();
            }

            function createFilterSelect(columnIndex, uniqueValues) {
                let html = '<select class="filter-select" data-column="' + columnIndex + '">';
                html += '<option value="">All</option>';
                uniqueValues.forEach(value => {
                    html += '<option value="' + value + '">' + value + '</option>';
                });
                html += '</select>';
                html += '<button class="filter-clear" data-column="' + columnIndex + '" title="Clear filter">×</button>';
                return html;
            }

            function applyFilter(columnIndex, value) {
                if (value === '') {
                    delete columnFilters[columnIndex];
                } else {
                    columnFilters[columnIndex] = value;
                }
                
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                    for (let colIndex in columnFilters) {
                        const filterValue = columnFilters[colIndex];
                        const cellValue = data[parseInt(colIndex) + 1];
                        if (cellValue !== filterValue) {
                            return false;
                        }
                    }
                    return true;
                });
                
                table.draw();
                updateFilterStatus();
            }

            function clearFilter(columnIndex) {
                $('.filter-select[data-column="' + columnIndex + '"]').val('');
                applyFilter(columnIndex, '');
            }

            function clearAllFilters() {
                columnFilters = {};
                $('.filter-select').val('');
                $.fn.dataTable.ext.search.pop();
                table.draw();
                updateFilterStatus();
            }

            function updateFilterStatus() {
                const activeFilters = Object.keys(columnFilters).length;
                if (activeFilters > 0) {
                    $('#filterStatus').show().text('Filters active (' + activeFilters + ')');
                } else {
                    $('#filterStatus').hide();
                }
            }

            function startCellEdit(cellElement) {
                if (editingCell) {
                    finishCellEdit();
                }

                editingCell = cellElement;
                const currentValue = cellElement.text();
                const cell = cellElement.closest('td');
                
                cell.addClass('editing');
                cellElement.html('<input type="text" value="' + currentValue + '" class="cell-input">');
                
                const input = cellElement.find('input');
                input.focus().select();
            }

            function finishCellEdit() {
                if (!editingCell) return;

                const input = editingCell.find('input');
                const newValue = input.val();
                const oldValue = input.attr('value');
                const recordId = editingCell.data('id');
                const columnIndex = editingCell.data('column');
                const columnName = columns[columnIndex];

                editingCell.closest('td').removeClass('editing');
                editingCell.html(newValue);

                if (newValue !== oldValue) {
                    saveCellChange(recordId, columnName, newValue);
                    updateLocalData(recordId, columnIndex, newValue);
                    refreshFilters();
                }

                editingCell = null;
            }

            function cancelCellEdit() {
                if (!editingCell) return;

                const input = editingCell.find('input');
                const originalValue = input.attr('value');
                
                editingCell.closest('td').removeClass('editing');
                editingCell.html(originalValue);
                editingCell = null;
            }

            function updateLocalData(recordId, columnIndex, newValue) {
                const rowIndex = allData.findIndex(row => row.record_id === recordId);
                if (rowIndex !== -1) {
                    allData[rowIndex]['col_' + columnIndex] = newValue;
                }
            }

            function refreshFilters() {
                columns.forEach((columnName, index) => {
                    const uniqueValues = getUniqueValues(index);
                    const currentValue = $('.filter-select[data-column="' + index + '"]').val();
                    const selectHtml = createFilterSelect(index, uniqueValues);
                    $('.filter-select[data-column="' + index + '"]').parent().html(selectHtml);
                    $('.filter-select[data-column="' + index + '"]').val(currentValue);
                });
                
                $('.filter-select').on('change', function() {
                    const columnIndex = $(this).data('column');
                    const value = $(this).val();
                    applyFilter(columnIndex, value);
                });
                
                $('.filter-clear').on('click', function() {
                    const columnIndex = $(this).data('column');
                    clearFilter(columnIndex);
                });
            }

            function saveCellChange(recordId, columnName, newValue) {
                const data = {};
                data[columnName] = newValue;

                $.ajax({
                    url: '/edit/' + recordId,
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function(response) {
                        if (response.success) {
                            showSaveIndicator();
                        } else {
                            alert('Error saving: ' + response.message);
                            table.ajax.reload();
                        }
                    },
                    error: function() {
                        alert('Error saving changes');
                        table.ajax.reload();
                    }
                });
            }

            function addNewRow() {
                const newData = {};
                columns.forEach(col => {
                    newData[col] = '';
                });

                $.ajax({
                    url: '/add',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(newData),
                    success: function(response) {
                        if (response.success) {
                            table.ajax.reload();
                            showSaveIndicator();
                        } else {
                            alert('Error adding row: ' + response.message);
                        }
                    },
                    error: function() {
                        alert('Error adding new row');
                    }
                });
            }

            function copySelectedRows() {
                if (selectedRows.size === 0) return;

                const selectedData = [];
                $('.row-select:checked').each(function() {
                    const row = table.row($(this).closest('tr')).data();
                    const rowData = {};
                    columns.forEach((col, index) => {
                        rowData[col] = row['col_' + index] || '';
                    });
                    selectedData.push(rowData);
                });

                let completed = 0;
                selectedData.forEach(rowData => {
                    $.ajax({
                        url: '/add',
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify(rowData),
                        success: function(response) {
                            completed++;
                            if (completed === selectedData.length) {
                                table.ajax.reload();
                                clearSelection();
                                showSaveIndicator();
                                alert(selectedData.length + ' row(s) copied successfully!');
                            }
                        },
                        error: function() {
                            alert('Error copying rows');
                        }
                    });
                });
            }

            function deleteSelectedRows() {
                if (selectedRows.size === 0) return;

                if (!confirm('Are you sure you want to delete ' + selectedRows.size + ' selected row(s)?')) {
                    return;
                }

                let completed = 0;
                const totalRows = selectedRows.size;
                
                selectedRows.forEach(recordId => {
                    $.ajax({
                        url: '/delete/' + recordId,
                        method: 'DELETE',
                        success: function(response) {
                            completed++;
                            if (completed === totalRows) {
                                table.ajax.reload();
                                clearSelection();
                                showSaveIndicator();
                                alert(totalRows + ' row(s) deleted successfully!');
                            }
                        },
                        error: function() {
                            alert('Error deleting rows');
                        }
                    });
                });
            }

            function deleteRecord(recordId) {
                $.ajax({
                    url: '/delete/' + recordId,
                    method: 'DELETE',
                    success: function(response) {
                        if (response.success) {
                            table.ajax.reload();
                            showSaveIndicator();
                        } else {
                            alert('Error: ' + response.message);
                        }
                    },
                    error: function() {
                        alert('Error deleting record');
                    }
                });
            }

            function updateSelectionUI() {
                const count = selectedRows.size;
                $('#selectedCount').text(count);
                $('#copySelectedBtn, #deleteSelectedBtn').prop('disabled', count === 0);
            }

            function clearSelection() {
                selectedRows.clear();
                $('.row-select').prop('checked', false);
                $('#selectAllCheckbox').prop('checked', false);
                $('.row-selected').removeClass('row-selected');
                updateSelectionUI();
            }

            function showSaveIndicator() {
                $('#saveIndicator').fadeIn(300).delay(2000).fadeOut(300);
            }

            function syncHeaderWidths() {
                // This function is no longer needed with the simple sticky header approach
                // DataTables handles column alignment automatically
            }

            function createFixedHeader() {
                // This function is no longer needed - headers are created by DataTables
            }

            function setupSynchronizedScrolling() {
                // This function is no longer needed - using simple sticky headers
            }
            </script>
        </body>
        </html>
    ''', columns_list=columns_list, enumerated_columns=enumerated_columns, shape=shape, username=username)

@app.route('/user')
@login_required
def user_dashboard():
    try:
        # Fetch all documents from MongoDB
        data = list(mongo_collection.find({}, {"_id": 0}))
        if not data:
            raise Exception("No data found in MongoDB collection 'ict_inventory'.")
        
        # Apply column permissions for users
        all_columns = [str(col).strip() for col in data[0].keys()]
        column_permissions = session.get('column_permissions', [])
        
        # If user has column permissions, filter columns
        if column_permissions and session.get('role') != 'admin':
            original_columns = [col for col in all_columns if col in column_permissions]
            # Filter data to only include allowed columns
            filtered_data = []
            for row in data:
                filtered_row = {col: row[col] for col in original_columns if col in row}
                filtered_data.append(filtered_row)
            data = filtered_data
        else:
            original_columns = all_columns
        
        # Create a mapping of display names to safe names
        safe_columns = [f"col_{i}" for i in range(len(original_columns))]
        column_mapping = dict(zip(original_columns, safe_columns))
        reverse_mapping = dict(zip(safe_columns, original_columns))
        # Convert data to safe columns
        for row in data:
            for orig, safe in column_mapping.items():
                if orig in row:
                    row[safe] = row.pop(orig)
        # Create DataFrame for shape
        import pandas as pd
        df = pd.DataFrame(data)
    except Exception as e:
        import traceback
        error_message = str(e)
        tb = traceback.format_exc()
        return render_template_string('''
            <html>
            <head>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
            </head>
            <body>
                <div class="container mt-4">
                    <h2>Error loading MongoDB data</h2>
                    <div class="alert alert-danger">
                        Could not load the MongoDB data.<br>
                        <br>Error details: {{ error_message }}
                        <pre>{{ tb }}</pre>
                    </div>
                </div>
            </body>
            </html>
        ''', error_message=error_message, tb=tb)
    # Create enumerated columns for the template
    columns_list = original_columns  # Use original column names for display
    enumerated_columns = list(enumerate(columns_list))
    shape = df.shape
    username = session.get('username', 'User')
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>ICT Inventory - User Dashboard</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/fixedheader/3.4.0/css/fixedHeader.dataTables.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body { background: #f8f9fa; }
                .navbar { background: #28a745; }
                .navbar-brand, .navbar-nav .nav-link { color: #fff !important; }
                .dashboard-title { font-size: 2.2rem; font-weight: 700; color: #28a745; }
                .dashboard-subtitle { font-size: 1.1rem; color: #6c757d; }
                .card { box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-radius: 1rem; position: relative; }
                .footer { background: #28a745; color: #fff; padding: 1rem 0; text-align: center; margin-top: 2rem; }
                
                /* Read-only table styling */
                .table-container { 
                    position: relative; 
                    overflow: hidden;
                }
                
                /* DataTables scroll container styling */
                .dataTables_wrapper .dataTables_scroll {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    background: white;
                }
                
                .dataTables_wrapper .dataTables_scrollBody {
                    max-height: 60vh;
                }
                
                /* Sticky header styling - target DataTables elements */
                .dataTables_wrapper .dataTable thead th {
                    position: sticky !important;
                    top: 0 !important;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
                    z-index: 10 !important;
                    border: 1px solid #dee2e6 !important;
                    padding: 12px 8px !important;
                    font-weight: 600 !important;
                    font-size: 14px !important;
                    text-align: center !important;
                    vertical-align: middle !important;
                    min-width: 120px !important;
                }
                
                .dataTables_wrapper .dataTable thead th:hover {
                    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
                }
                
                /* Filter row styling */
                .filter-row th {
                    position: sticky !important;
                    top: 50px !important;
                    background: #e9ecef !important;
                    padding: 4px 8px !important;
                    border-bottom: 2px solid #dee2e6 !important;
                    z-index: 9 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
                
                /* Data table styling */
                .table-body-wrapper table {
                    margin-bottom: 0 !important;
                    width: 100%;
                    min-width: 100%;
                }
                
                .table-body-wrapper th {
                    display: none !important; /* Hide headers in body */
                }
                
                /* Allow natural column expansion */
                .table-body-wrapper td {
                    padding: 8px 12px !important;
                    border: 1px solid #dee2e6 !important;
                    min-width: 120px !important;
                }
                
                /* Excel-like cell styling */
                .excel-cell {
                    cursor: pointer;
                    padding: 8px 12px !important;
                    border: 1px solid #dee2e6 !important;
                    position: relative;
                    background: white;
                    min-width: 120px;
                }
                
                .excel-cell:hover {
                    background-color: #e3f2fd !important;
                    border-color: #2196f3 !important;
                }
                
                .excel-cell.editing {
                    background-color: #fff3e0 !important;
                    border-color: #ff9800 !important;
                    border-width: 2px !important;
                }
                
                .excel-cell input {
                    border: none;
                    background: transparent;
                    width: 100%;
                    padding: 0;
                    margin: 0;
                    outline: none;
                    font-size: inherit;
                    font-family: inherit;
                }
                
                /* Row selection */
                .row-selected {
                    background-color: #e8f5e8 !important;
                }
                
                .row-checkbox {
                    width: 20px;
                    text-align: center;
                }
                
                /* Action buttons */
                .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
                .action-buttons { white-space: nowrap; min-width: 120px; }
                
                /* Fixed header with filters */
                .dataTables_wrapper .dataTable thead th {
                    position: sticky !important;
                    top: 0 !important;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
                    z-index: 10 !important;
                    border: 1px solid #dee2e6 !important;
                    padding: 8px 12px !important;
                    font-weight: 600 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    transition: all 0.3s ease !important;
                }
                
                .dataTables_wrapper .dataTable thead th:hover {
                    background: #e9ecef !important;
                }
                
                /* Sticky header active state */
                .sticky-active .dataTables_wrapper .dataTable thead th {
                    background: #ffffff !important;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
                    border-bottom: 2px solid #007bff !important;
                }
                
                /* Sticky header indicator */
                .sticky-active.indicator-shown::before {
                    content: "📌 Headers Fixed";
                    position: fixed;
                    top: 10px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 12px;
                    z-index: 1000;
                    animation: fadeInOut 3s ease-in-out;
                }
                
                @keyframes fadeInOut {
                    0% { opacity: 0; transform: translateY(-10px); }
                    20% { opacity: 1; transform: translateY(0); }
                    80% { opacity: 1; transform: translateY(0); }
                    100% { opacity: 0; transform: translateY(-10px); }
                }
                
                .filter-select {
                    width: 100%;
                    padding: 4px 6px;
                    border: 1px solid #ced4da;
                    border-radius: 3px;
                    font-size: 12px;
                    background: white;
                    cursor: pointer;
                }
                
                .filter-clear {
                    background: none;
                    border: none;
                    color: #dc3545;
                    font-size: 12px;
                    cursor: pointer;
                    padding: 2px 4px;
                    margin-left: 4px;
                }
                
                .filter-clear:hover {
                    background: #f8d7da;
                    border-radius: 2px;
                }
                
                /* Fixed footer with pagination */
                .dataTables_wrapper .dataTables_paginate,
                .dataTables_wrapper .dataTables_length {
                    position: sticky;
                    bottom: 0;
                    background: white;
                    padding: 10px;
                    border-top: 1px solid #dee2e6;
                }
                
                .dataTables_wrapper .dataTables_info {
                    position: sticky;
                    bottom: 0;
                    background: white;
                    padding: 10px;
                }
                
                /* Toolbar styling */
                .toolbar {
                    background: white;
                    padding: 10px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .toolbar .btn {
                    margin-right: 10px;
                }
                
                /* Filter status */
                .filter-status {
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                    margin-left: 10px;
                }
                
                /* User info */
                .user-info {
                    background: #28a745;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 14px;
                    margin-right: 10px;
                }
                
                /* Read-only notice */
                .readonly-notice {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 12px 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                
                /* Ensure sticky headers work properly */
                .dataTables_wrapper {
                    position: relative;
                }
                
                .dataTables_wrapper .dataTable {
                    border-collapse: separate;
                    border-spacing: 0;
                }
                
                /* Read-only cell styling */
                .readonly-cell {
                    padding: 8px 12px !important;
                    border: 1px solid #dee2e6 !important;
                    background: #f8f9fa;
                    min-width: 120px;
                }
                
                .readonly-cell:hover {
                    background-color: #e9ecef !important;
                }
                
                /* Ensure DataTables wrapper allows sticky positioning */
                .dataTables_wrapper {
                    position: relative;
                }
                
                .dataTables_wrapper .dataTables_scroll {
                    position: relative;
                }
                
                /* DataTables scroll container styling */
                .dataTables_wrapper .dataTables_scroll {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    background: white;
                }
                
                .dataTables_wrapper .dataTables_scrollBody {
                    max-height: 60vh;
                }
                
                /* Sticky header styling - target DataTables elements */
                .dataTables_wrapper .dataTable thead th {
                    position: sticky !important;
                    top: 0 !important;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
                    z-index: 10 !important;
                    border: 1px solid #dee2e6 !important;
                    padding: 12px 8px !important;
                    font-weight: 600 !important;
                    font-size: 14px !important;
                    text-align: center !important;
                    vertical-align: middle !important;
                    min-width: 120px !important;
                }
                
                .dataTables_wrapper .dataTable thead th:hover {
                    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
                }
                
                /* Filter row styling */
                .filter-row th {
                    position: sticky !important;
                    top: 50px !important;
                    background: #e9ecef !important;
                    padding: 4px 8px !important;
                    border-bottom: 2px solid #dee2e6 !important;
                    z-index: 9 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark">
                <a class="navbar-brand" href="#"><i class="fas fa-database mr-2"></i>ICT Inventory - User</a>
                <div class="navbar-nav ml-auto">
                    <span class="user-info">
                        <i class="fas fa-user mr-2"></i>{{ username }} (User)
                    </span>
                    <a class="nav-link" href="{{ url_for('logout') }}">
                        <i class="fas fa-sign-out-alt mr-2"></i>Logout
                    </a>
                </div>
            </nav>
            
            <div class="container-fluid mt-5">
                <div class="row mb-4">
                    <div class="col-12 text-center">
                        <div class="dashboard-title mb-2"><i class="fas fa-eye mr-2"></i>User Dashboard</div>
                        <div class="dashboard-subtitle">Read-only access: View and filter inventory data</div>
                    </div>
                </div>
                
                <!-- Read-only notice -->
                <div class="row mb-3">
                    <div class="col-12">
                        <div class="readonly-notice">
                            <i class="fas fa-info-circle mr-2"></i>
                            <strong>Read-Only Mode:</strong> You can view and filter data, but editing is not permitted. Contact an administrator for data changes.
                        </div>
                    </div>
                </div>
                
                <!-- Toolbar -->
                <div class="row mb-3">
                    <div class="col-12">
                        <div class="toolbar">
                            <button class="btn btn-warning" id="clearFiltersBtn">
                                <i class="fas fa-filter mr-2"></i>Clear All Filters
                            </button>
                                                        <div class="float-right">
                                <span class="text-muted">
                                    <i class="fas fa-info-circle mr-1"></i>
                                    Use dropdown filters to search data • Download available
                                </span>
                                <span id="filterStatus" class="filter-status" style="display: none;">
                                    <i class="fas fa-filter mr-1"></i>Filters active
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row justify-content-center">
                    <div class="col-12">
                        <div class="card p-4">
                            <table id="excelTable" class="table table-striped table-bordered" style="width:100%">
                                <thead></thead>
                                <tbody></tbody>
                            </table>
                            <p class="text-muted mt-2">(Read-only view with filtering capabilities. {{ shape[0] }} total records.)</p>
                        </div>
                    </div>
                </div>
            </div>

            <footer class="footer">
                <div>ICT Inventory &copy; 2024 | User Interface | Powered by Flask & MongoDB</div>
            </footer>
            
            <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
            <script src="https://cdn.datatables.net/fixedheader/3.4.0/js/dataTables.fixedHeader.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js"></script>
            <script>
            let table;
            let columns = {{ columns_list|tojson }};
            let columnFilters = {};
            let allData = [];
            
            $(document).ready(function() {
                // Initialize DataTable (Read-only version)
                table = $('#excelTable').DataTable({
                    processing: true,
                    serverSide: false,
                    ajax: {
                        url: '/data',
                        type: 'POST',
                        dataSrc: function(json) {
                            allData = json.data || [];
                            return allData;
                        }
                    },
                    columns: [
                        {% for i, col in enumerated_columns %}
                        {
                            data: "col_{{ i }}",
                            name: "col_{{ i }}",
                            title: {{ col|tojson }},
                            className: 'readonly-cell',
                            render: function(data, type, row, meta) {
                                return data || '';
                            }
                        }{% if not loop.last %},{% endif %}
                        {% endfor %}
                    ],
                    pageLength: 25,
                    lengthMenu: [[25, 50, 100, -1], ["25", "50", "100", "All"]],
                    dom: '<"top"l>rt<"bottom"ip>',
                    ordering: true,
                    searching: true,
                    scrollX: true,
                    scrollY: '60vh',
                    scrollCollapse: true,
                    fixedHeader: false,
                    language: {
                        processing: "Loading...",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries (filtered from _MAX_ total entries)",
                        emptyTable: "No data available"
                    },
                    initComplete: function() {
                        createFilterRow();
                    },
                    drawCallback: function() {
                        // No additional callbacks needed
                    }
                });

                // Clear filters button
                $('#clearFiltersBtn').click(function() {
                    clearAllFilters();
                });
            });

            function createFilterRow() {
                const filterRow = $('<tr class="filter-row"></tr>');
                
                columns.forEach((columnName, index) => {
                    const uniqueValues = getUniqueValues(index);
                    const selectHtml = createFilterSelect(index, uniqueValues);
                    filterRow.append('<th>' + selectHtml + '</th>');
                });
                
                $('#excelTable thead').append(filterRow);
                
                $('.filter-select').on('change', function() {
                    const columnIndex = $(this).data('column');
                    const value = $(this).val();
                    applyFilter(columnIndex, value);
                });
                
                $('.filter-clear').on('click', function() {
                    const columnIndex = $(this).data('column');
                    clearFilter(columnIndex);
                });
            }

            function getUniqueValues(columnIndex) {
                const values = new Set();
                allData.forEach(row => {
                    const value = row['col_' + columnIndex];
                    if (value && value.toString().trim() !== '') {
                        values.add(value.toString().trim());
                    }
                });
                return Array.from(values).sort();
            }

            function createFilterSelect(columnIndex, uniqueValues) {
                let html = '<select class="filter-select" data-column="' + columnIndex + '">';
                html += '<option value="">All</option>';
                uniqueValues.forEach(value => {
                    html += '<option value="' + value + '">' + value + '</option>';
                });
                html += '</select>';
                html += '<button class="filter-clear" data-column="' + columnIndex + '" title="Clear filter">×</button>';
                return html;
            }

            function applyFilter(columnIndex, value) {
                if (value === '') {
                    delete columnFilters[columnIndex];
                } else {
                    columnFilters[columnIndex] = value;
                }
                
                $.fn.dataTable.ext.search.pop();
                $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                    for (let colIndex in columnFilters) {
                        const filterValue = columnFilters[colIndex];
                        const cellValue = data[parseInt(colIndex)];
                        if (cellValue !== filterValue) {
                            return false;
                        }
                    }
                    return true;
                });
                
                table.draw();
                updateFilterStatus();
            }

            function clearFilter(columnIndex) {
                $('.filter-select[data-column="' + columnIndex + '"]').val('');
                applyFilter(columnIndex, '');
            }

            function clearAllFilters() {
                columnFilters = {};
                $('.filter-select').val('');
                $.fn.dataTable.ext.search.pop();
                table.draw();
                updateFilterStatus();
            }

            function updateFilterStatus() {
                const activeFilters = Object.keys(columnFilters).length;
                if (activeFilters > 0) {
                    $('#filterStatus').show().text('Filters active (' + activeFilters + ')');
                } else {
                    $('#filterStatus').hide();
                }
            }

            function createFixedHeader() {
                // This function is no longer needed - headers are created by DataTables
            }

            function syncHeaderWidths() {
                // This function is no longer needed with the simple sticky header approach
                // DataTables handles column alignment automatically
            }

            function setupSynchronizedScrolling() {
                // This function is no longer needed - using simple sticky headers
            }
            </script>
        </body>
        </html>
    ''', columns_list=columns_list, enumerated_columns=enumerated_columns, shape=shape, username=username)

@app.route('/data', methods=['POST'])
@login_required
def data():
    try:
        # Get form data from request
        req = request.form
        print("Received data request:", req)

        # Build query based on user permissions
        query = {}
        location_permissions = session.get('location_permissions', {})
        
        # Apply location-based filtering for users with permissions
        if location_permissions and session.get('role') != 'admin':
            or_conditions = []
            for column, allowed_values in location_permissions.items():
                if allowed_values:  # Only add condition if there are allowed values
                    or_conditions.append({column: {"$in": allowed_values}})
            
            if or_conditions:
                query = {"$or": or_conditions}

        # Fetch documents from MongoDB based on query
        if session.get('role') == 'admin':
            data_list = list(mongo_collection.find(query))
        else:
            data_list = list(mongo_collection.find(query, {"_id": 0}))
            
        if not data_list:
            return jsonify({
                'draw': int(req.get('draw', 1)),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            })

        # Create safe column names (exclude _id from display columns for users)
        if session.get('role') == 'admin':
            original_columns = [str(col).strip() for col in data_list[0].keys() if col != '_id']
            safe_columns = [f"col_{i}" for i in range(len(original_columns))]
            column_mapping = dict(zip(original_columns, safe_columns))
            
            # Convert data to safe columns and add record_id for admin
            for row in data_list:
                row['record_id'] = str(row['_id'])
                del row['_id']
                for orig, safe in column_mapping.items():
                    if orig in row:
                        row[safe] = row.pop(orig)
        else:
            # For users, apply column permissions
            all_columns = [str(col).strip() for col in data_list[0].keys()]
            column_permissions = session.get('column_permissions', [])
            
            # If user has column permissions, filter columns
            if column_permissions:
                original_columns = [col for col in all_columns if col in column_permissions]
            else:
                original_columns = all_columns
            
            safe_columns = [f"col_{i}" for i in range(len(original_columns))]
            column_mapping = dict(zip(original_columns, safe_columns))
            
            # Convert data to safe columns and filter out restricted columns
            for row in data_list:
                # Remove columns that user doesn't have permission to see
                if column_permissions:
                    keys_to_remove = [key for key in row.keys() if key not in column_permissions]
                    for key in keys_to_remove:
                        del row[key]
                
                # Convert remaining columns to safe names
                for orig, safe in column_mapping.items():
                    if orig in row:
                        row[safe] = row.pop(orig)

        import pandas as pd
        df = pd.DataFrame(data_list)
        if df.empty:
            return jsonify({
                'draw': int(req.get('draw', 1)),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            })

        # For client-side processing, return all data
        total_records = len(df)
        data = df.fillna('').to_dict(orient='records')

        # Ensure all values are JSON serializable
        for row in data:
            for key, value in row.items():
                if value is None:
                    row[key] = ''

        print(f"Returning {len(data)} rows for user {session.get('username')} with permissions {location_permissions}")
        response_data = {
            'draw': int(req.get('draw', 1)),
            'recordsTotal': int(total_records),
            'recordsFiltered': int(total_records),
            'data': data
        }
        return jsonify(response_data)
    except Exception as e:
        import traceback
        print(f"Error processing data request: {str(e)}")
        print(traceback.format_exc())
        # Always return a valid DataTables response, even on error
        return jsonify({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': f"Error processing request: {str(e)}"
        })

@app.route('/edit/<record_id>', methods=['POST'])
@login_required
@admin_required
def edit_record(record_id):
    try:
        data = request.get_json()
        print(f"Editing record {record_id} with data: {data}")
        
        # Update the document in MongoDB
        result = mongo_collection.update_one(
            {"_id": ObjectId(record_id)},
            {"$set": data}
        )
        
        if result.matched_count > 0:
            return jsonify({"success": True, "message": "Record updated successfully"})
        else:
            return jsonify({"success": False, "message": "Record not found"}), 404
            
    except Exception as e:
        print(f"Error updating record: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/delete/<record_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_record(record_id):
    try:
        print(f"Deleting record {record_id}")
        
        # Delete the document from MongoDB
        result = mongo_collection.delete_one({"_id": ObjectId(record_id)})
        
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "Record deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Record not found"}), 404
            
    except Exception as e:
        print(f"Error deleting record: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/add', methods=['POST'])
@login_required
@admin_required
def add_record():
    try:
        data = request.get_json()
        print(f"Adding new record with data: {data}")
        
        # Insert the new document into MongoDB
        result = mongo_collection.insert_one(data)
        
        if result.inserted_id:
            return jsonify({"success": True, "message": "Record added successfully", "id": str(result.inserted_id)})
        else:
            return jsonify({"success": False, "message": "Failed to add record"}), 500
            
    except Exception as e:
        print(f"Error adding record: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_columns')
@login_required
def get_columns():
    try:
        # Get a sample document to determine the columns
        sample_doc = mongo_collection.find_one({}, {"_id": 0})
        if sample_doc:
            columns = list(sample_doc.keys())
            return jsonify({"success": True, "columns": columns})
        else:
            return jsonify({"success": False, "message": "No data found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/download')
@login_required
def download():
    # Download as CSV from MongoDB
    import pandas as pd
    data = list(mongo_collection.find({}, {"_id": 0}))
    if not data:
        return "No data available.", 404
    df = pd.DataFrame(data)
    temp_path = os.path.join(tempfile.gettempdir(), 'ICT_Inventory_mongodb.csv')
    df.to_csv(temp_path, index=False)
    return send_file(temp_path, as_attachment=True)

# User Management Routes
@app.route('/manage_users')
@login_required
@admin_required
def manage_users():
    # Get all users from MongoDB (excluding hidden ones)
    users = list(users_collection.find({}))
    
    # Get unique location values for permissions and all columns for column permissions
    try:
        # Use the same logic as the data table: get columns from the first document
        data_list = list(mongo_collection.find({}, {"_id": 0}))
        location_columns = []
        all_columns = []
        if data_list:
            all_columns = [str(col).strip() for col in data_list[0].keys()]
            for key in data_list[0].keys():
                key_lower = str(key).lower()
                if any(term in key_lower for term in ['location', 'batiment', 'building', 'room', 'site']):
                    location_columns.append(str(key).strip())
        # Get unique values for each location column
        location_values = {}
        for col in location_columns:
            values = mongo_collection.distinct(col)
            location_values[col] = [v for v in values if v and str(v).strip()]
    except Exception as e:
        print(f"Error getting columns: {e}")
        location_columns = []
        location_values = {}
        all_columns = []
    
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>ICT Inventory - User Management</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body { background: #f8f9fa; }
                .navbar { background: #343a40; }
                .navbar-brand, .navbar-nav .nav-link { color: #fff !important; }
                .card { box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-radius: 1rem; }
                .user-info { background: #007bff; color: white; padding: 8px 15px; border-radius: 20px; font-size: 14px; margin-right: 10px; }
                .permission-item { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; margin: 5px 0; }
                .permission-remove { color: #dc3545; cursor: pointer; float: right; }
                .permission-remove:hover { color: #c82333; }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark">
                <a class="navbar-brand" href="{{ url_for('admin_dashboard') }}"><i class="fas fa-database mr-2"></i>ICT Inventory - User Management</a>
                <div class="navbar-nav ml-auto">
                    <span class="user-info">
                        <i class="fas fa-user-shield mr-2"></i>{{ session.username }} (Admin)
                    </span>
                    <a class="nav-link" href="{{ url_for('logout') }}">
                        <i class="fas fa-sign-out-alt mr-2"></i>Logout
                    </a>
                </div>
            </nav>
            
            <div class="container mt-5">
                <div class="row">
                    <div class="col-12">
                        <h2><i class="fas fa-users mr-2"></i>User Management</h2>
                        <p class="text-muted">Manage user accounts and their location-based permissions</p>
                    </div>
                </div>
                
                <!-- Add New User -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-user-plus mr-2"></i>Add New User</h5>
                            </div>
                            <div class="card-body">
                                <form id="addUserForm">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="form-group">
                                                <label for="username">Username</label>
                                                <input type="text" class="form-control" id="username" name="username" required>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="form-group">
                                                <label for="password">Password</label>
                                                <input type="password" class="form-control" id="password" name="password" required>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="form-group">
                                                <label for="role">Role</label>
                                                <select class="form-control" id="role" name="role">
                                                    <option value="user">User</option>
                                                    <option value="admin">Admin</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Location Permissions -->
                                    <div class="form-group">
                                        <label>Location Permissions</label>
                                        <div id="locationPermissions">
                                            {% for col in location_columns %}
                                            <div class="row mb-2">
                                                <div class="col-md-4">
                                                    <label>{{ col }}</label>
                                                </div>
                                                <div class="col-md-8">
                                                    <div style="max-height: 120px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px; background: #f9f9f9;">
                                                    {% if location_values[col] %}
                                                        {% for value in location_values[col] %}
                                                        <div class="form-check">
                                                            <input class="form-check-input location-checkbox" type="checkbox" name="location_{{ col }}" value="{{ value }}" data-column="{{ col }}" id="loc_{{ col }}_{{ loop.index }}">
                                                            <label class="form-check-label" for="loc_{{ col }}_{{ loop.index }}">{{ value }}</label>
                                                        </div>
                                                        {% endfor %}
                                                    {% else %}
                                                        <span class="text-muted">No values found</span>
                                                    {% endif %}
                                                    </div>
                                                </div>
                                            </div>
                                            {% endfor %}
                                        </div>
                                    </div>
                                    
                                    <!-- Column Permissions -->
                                    <div class="form-group">
                                        <label>Column Permissions (Visible Columns)</label>
                                        <div class="row">
                                            <div class="col-12">
                                                <div style="max-height: 160px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px; background: #f9f9f9;">
                                                {% if all_columns %}
                                                    {% for col in all_columns %}
                                                    <div class="form-check">
                                                        <input class="form-check-input column-checkbox" type="checkbox" name="column_permissions" value="{{ col }}" id="colperm_{{ loop.index }}">
                                                        <label class="form-check-label" for="colperm_{{ loop.index }}">{{ col }}</label>
                                                    </div>
                                                    {% endfor %}
                                                {% else %}
                                                    <span class="text-muted">No columns found. Please upload data first.</span>
                                                {% endif %}
                                                </div>
                                                <div><small class="text-muted">Check columns to allow. Leave all unchecked for full access.</small></div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <button type="submit" class="btn btn-success">
                                        <i class="fas fa-plus mr-2"></i>Add User
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Existing Users -->
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-users mr-2"></i>Existing Users</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped">
                                        <thead>
                                            <tr>
                                                <th>Username</th>
                                                <th>Role</th>
                                                <th>Location Permissions</th>
                                                <th>Column Permissions</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="usersTable">
                                            {% for user in users %}
                                            <tr data-user-id="{{ user._id }}">
                                                <td>{{ user.username }}</td>
                                                <td>
                                                    <span class="badge badge-{% if user.role == 'admin' %}danger{% else %}primary{% endif %}">
                                                        {{ user.role.title() }}
                                                    </span>
                                                </td>
                                                <td>
                                                    {% if user.get('location_permissions') %}
                                                        {% for col, values in user.location_permissions.items() %}
                                                            <div class="permission-item">
                                                                <strong>{{ col }}:</strong> {{ values|join(', ') }}
                                                            </div>
                                                        {% endfor %}
                                                    {% else %}
                                                        <span class="text-muted">No restrictions (Full access)</span>
                                                    {% endif %}
                                                </td>
                                                <td>
                                                    {% if user.get('column_permissions') %}
                                                        <div class="permission-item">
                                                            <strong>Visible Columns:</strong> {{ user.column_permissions|join(', ') }}
                                                        </div>
                                                    {% else %}
                                                        <span class="text-muted">All columns visible</span>
                                                    {% endif %}
                                                </td>
                                                <td>
                                                    <button class="btn btn-sm btn-warning edit-user-btn" data-user-id="{{ user._id }}">
                                                        <i class="fas fa-edit"></i> Edit
                                                    </button>
                                                    <button class="btn btn-sm btn-info reset-password-btn" data-user-id="{{ user._id }}">
                                                        <i class="fas fa-key"></i> Reset Password
                                                    </button>
                                                    <button class="btn btn-sm btn-danger delete-user-btn" data-user-id="{{ user._id }}">
                                                        <i class="fas fa-trash"></i> Delete
                                                    </button>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Edit User Modal -->
            <div class="modal fade" id="editUserModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Edit User</h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <form id="editUserForm">
                                <input type="hidden" id="editUserId" name="user_id">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="form-group">
                                            <label for="editUsername">Username</label>
                                            <input type="text" class="form-control" id="editUsername" name="username" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-group">
                                            <label for="editRole">Role</label>
                                            <select class="form-control" id="editRole" name="role">
                                                <option value="user">User</option>
                                                <option value="admin">Admin</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Location Permissions for Edit -->
                                <div class="form-group">
                                    <label>Location Permissions</label>
                                    <div id="editLocationPermissions">
                                        {% for col in location_columns %}
                                        <div class="row mb-2">
                                            <div class="col-md-4">
                                                <label>{{ col }}</label>
                                            </div>
                                            <div class="col-md-8">
                                                <div style="max-height: 120px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px; background: #f9f9f9;">
                                                {% if location_values[col] %}
                                                    {% for value in location_values[col] %}
                                                    <div class="form-check">
                                                        <input class="form-check-input edit-location-checkbox" type="checkbox" name="edit_location_{{ col }}" value="{{ value }}" data-column="{{ col }}" id="edit_loc_{{ col }}_{{ loop.index }}">
                                                        <label class="form-check-label" for="edit_loc_{{ col }}_{{ loop.index }}">{{ value }}</label>
                                                    </div>
                                                    {% endfor %}
                                                {% else %}
                                                    <span class="text-muted">No values found</span>
                                                {% endif %}
                                                </div>
                                            </div>
                                        </div>
                                        {% endfor %}
                                    </div>
                                </div>
                                <!-- Column Permissions for Edit -->
                                <div class="form-group">
                                    <label>Column Permissions (Visible Columns)</label>
                                    <div class="row">
                                        <div class="col-12">
                                            <div style="max-height: 160px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px; background: #f9f9f9;">
                                            {% if all_columns %}
                                                {% for col in all_columns %}
                                                <div class="form-check">
                                                    <input class="form-check-input edit-column-checkbox" type="checkbox" name="edit_column_permissions" value="{{ col }}" id="edit_colperm_{{ loop.index }}">
                                                    <label class="form-check-label" for="edit_colperm_{{ loop.index }}">{{ col }}</label>
                                                </div>
                                                {% endfor %}
                                            {% else %}
                                                <span class="text-muted">No columns found. Please upload data first.</span>
                                            {% endif %}
                                            </div>
                                            <div><small class="text-muted">Check columns to allow. Leave all unchecked for full access.</small></div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveUserChanges">Save Changes</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
            $(document).ready(function() {
                // Add new user
                $('#addUserForm').on('submit', function(e) {
                    e.preventDefault();
                    
                    const formData = {
                        username: $('#username').val(),
                        password: $('#password').val(),
                        role: $('#role').val(),
                        location_permissions: {},
                        column_permissions: []
                    };
                    
                    // Collect location permissions from checkboxes
                    $('.location-checkbox:checked').each(function() {
                        const column = $(this).data('column');
                        const value = $(this).val();
                        if (!formData.location_permissions[column]) {
                            formData.location_permissions[column] = [];
                        }
                        formData.location_permissions[column].push(value);
                    });
                    
                    // Collect column permissions from checkboxes
                    $('.column-checkbox:checked').each(function() {
                        formData.column_permissions.push($(this).val());
                    });
                    
                    $.ajax({
                        url: '/api/users',
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify(formData),
                        success: function(response) {
                            if (response.success) {
                                alert('User added successfully!');
                                location.reload();
                            } else {
                                alert('Error: ' + response.message);
                            }
                        },
                        error: function() {
                            alert('Error adding user');
                        }
                    });
                });
                
                // Edit user
                $('.edit-user-btn').on('click', function() {
                    const userId = $(this).data('user-id');
                    
                    $.ajax({
                        url: '/api/users/' + userId,
                        method: 'GET',
                        success: function(user) {
                            $('#editUserId').val(user._id);
                            $('#editUsername').val(user.username);
                            $('#editRole').val(user.role);
                            
                            // Set location permissions via checkboxes
                            $('.edit-location-checkbox').prop('checked', false);
                            if (user.location_permissions) {
                                Object.entries(user.location_permissions).forEach(([col, vals]) => {
                                    vals.forEach(val => {
                                        $(`.edit-location-checkbox[data-column="${col}"][value="${val}"]`).prop('checked', true);
                                    });
                                });
                            }

                            // Set column permissions via checkboxes
                            $('.edit-column-checkbox').prop('checked', false);
                            if (user.column_permissions) {
                                user.column_permissions.forEach(col => {
                                    $(`.edit-column-checkbox[value="${col}"]`).prop('checked', true);
                                });
                            }

                            $('#editUserModal').modal('show');
                        },
                        error: function() {
                            alert('Error loading user data');
                        }
                    });
                });
                
                // Save user changes
                $('#saveUserChanges').on('click', function() {
                    const userId = $('#editUserId').val();
                    const formData = {
                        username: $('#editUsername').val(),
                        role: $('#editRole').val(),
                        location_permissions: {},
                        column_permissions: []
                    };
                    
                    // Collect location permissions from checkboxes
                    $('.edit-location-checkbox:checked').each(function() {
                        const column = $(this).data('column');
                        const value = $(this).val();
                        if (!formData.location_permissions[column]) {
                            formData.location_permissions[column] = [];
                        }
                        formData.location_permissions[column].push(value);
                    });
                    
                    // Collect column permissions from checkboxes
                    $('.edit-column-checkbox:checked').each(function() {
                        formData.column_permissions.push($(this).val());
                    });
                    
                    $.ajax({
                        url: '/api/users/' + userId,
                        method: 'PUT',
                        contentType: 'application/json',
                        data: JSON.stringify(formData),
                        success: function(response) {
                            if (response.success) {
                                alert('User updated successfully!');
                                location.reload();
                            } else {
                                alert('Error: ' + response.message);
                            }
                        },
                        error: function() {
                            alert('Error updating user');
                        }
                    });
                });
                
                // Reset password
                $('.reset-password-btn').on('click', function() {
                    const userId = $(this).data('user-id');
                    const newPassword = prompt('Enter new password:');
                    
                    if (newPassword) {
                        $.ajax({
                            url: '/api/users/' + userId + '/reset-password',
                            method: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({password: newPassword}),
                            success: function(response) {
                                if (response.success) {
                                    alert('Password reset successfully!');
                                } else {
                                    alert('Error: ' + response.message);
                                }
                            },
                            error: function() {
                                alert('Error resetting password');
                            }
                        });
                    }
                });
                
                // Delete user
                $('.delete-user-btn').on('click', function() {
                    const userId = $(this).data('user-id');
                    
                    if (confirm('Are you sure you want to delete this user?')) {
                        $.ajax({
                            url: '/api/users/' + userId,
                            method: 'DELETE',
                            success: function(response) {
                                if (response.success) {
                                    alert('User deleted successfully!');
                                    location.reload();
                                } else {
                                    alert('Error: ' + response.message);
                                }
                            },
                            error: function() {
                                alert('Error deleting user');
                            }
                        });
                    }
                });
            });
            </script>
        </body>
        </html>
    ''', users=users, location_columns=location_columns, location_values=location_values, all_columns=all_columns, session=session)

# User Management API Routes
@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    try:
        data = request.get_json()
        
        # Check if username already exists
        if users_collection.find_one({"username": data['username']}):
            return jsonify({"success": False, "message": "Username already exists"}), 400
        
        # Create user document
        user_doc = {
            "username": data['username'],
            "password": data['password'],  # In production, hash this password
            "role": data['role'],
            "location_permissions": data.get('location_permissions', {}),
            "column_permissions": data.get('column_permissions', [])
        }
        
        result = users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            return jsonify({"success": True, "message": "User created successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to create user"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users/<user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
            return jsonify(user)
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    try:
        data = request.get_json()
        
        # Check if username already exists (excluding current user)
        existing_user = users_collection.find_one({"username": data['username'], "_id": {"$ne": ObjectId(user_id)}})
        if existing_user:
            return jsonify({"success": False, "message": "Username already exists"}), 400
        
        update_data = {
            "username": data['username'],
            "role": data['role'],
            "location_permissions": data.get('location_permissions', {}),
            "column_permissions": data.get('column_permissions', [])
        }
        
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count > 0:
            return jsonify({"success": True, "message": "User updated successfully"})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users/<user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    try:
        data = request.get_json()
        
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": data['password']}}  # In production, hash this password
        )
        
        if result.matched_count > 0:
            return jsonify({"success": True, "message": "Password reset successfully"})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "User deleted successfully"})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    tb = traceback.format_exc()
    return render_template_string('''
        <html>
        <head>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
        </head>
        <body>
            <div class="container mt-4">
                <h2>Unexpected Error</h2>
                <div class="alert alert-danger">
                    <pre>{{ tb }}</pre>
                </div>
            </div>
        </body>
        </html>
    ''', tb=tb), 500

if __name__ == '__main__':
    import socket
    import subprocess
    import sys
    import time
    import webbrowser
    from threading import Thread
    
    def get_local_ip():
        """Get the local IP address of the machine"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def check_ngrok_installed():
        """Check if ngrok is installed"""
        # First check if ngrok is in the current directory
        current_dir_ngrok = os.path.join(os.getcwd(), "ngrok.exe")
        if os.path.exists(current_dir_ngrok):
            print(f"✅ Found ngrok in current directory: {current_dir_ngrok}")
            return True
        
        # Then check if ngrok is in PATH
        try:
            subprocess.run(["ngrok", "version"], capture_output=True, check=True)
            print("✅ Found ngrok in system PATH")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ ngrok not found in PATH")
            return False
    
    def start_ngrok(port):
        """Start ngrok tunnel"""
        try:
            # Kill any existing ngrok processes
            subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], capture_output=True)
            time.sleep(1)
            
            # Determine ngrok executable path
            current_dir_ngrok = os.path.join(os.getcwd(), "ngrok.exe")
            if os.path.exists(current_dir_ngrok):
                ngrok_cmd = current_dir_ngrok
                print(f"Using ngrok from current directory: {ngrok_cmd}")
            else:
                ngrok_cmd = "ngrok"
                print("Using ngrok from system PATH")
            
            # Start ngrok
            ngrok_process = subprocess.Popen(
                [ngrok_cmd, "http", str(port), "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start and get the public URL
            time.sleep(3)
            
            # Try to get the ngrok URL from the API
            try:
                import requests
                response = requests.get("http://localhost:4040/api/tunnels")
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    if tunnels:
                        public_url = tunnels[0]["public_url"]
                        print(f"✅ ngrok tunnel established: {public_url}")
                        return public_url, ngrok_process
            except Exception as e:
                print(f"⚠️  Could not get ngrok URL from API: {e}")
            
            print("⚠️  ngrok started but URL not available yet")
            return None, ngrok_process
            
        except Exception as e:
            print(f"❌ Error starting ngrok: {e}")
            return None, None
    
    def print_access_info(port, public_url=None):
        """Print access information"""
        local_ip = get_local_ip()
        
        print("\n" + "="*60)
        print("🚀 ICT Inventory Application Started!")
        print("="*60)
        print(f"📱 Local Access:")
        print(f"   • http://localhost:{port}")
        print(f"   • http://{local_ip}:{port}")
        
        if public_url:
            print(f"\n🌐 Public Access (via ngrok):")
            print(f"   • {public_url}")
            print(f"\n💡 You can now access the app from anywhere!")
            print(f"   • Share the ngrok URL with others")
            print(f"   • The URL will work on any device with internet")
        else:
            print(f"\n⚠️  ngrok not available - only local access")
            print(f"   • Install ngrok for public access: https://ngrok.com/download")
            print(f"   • Or place ngrok.exe in the same folder as app.py")
            print(f"   • Or place ngrok.exe in the same folder as app.py")
        
        print(f"\n🔐 Login Credentials:")
        print(f"   • Admin: admin / admin123")
        print(f"   • User: user / user123")
        print("="*60)
        print("\nPress Ctrl+C to stop the server")
    
    # Configuration
    PORT = 5000
    HOST = "0.0.0.0"  # Allow external connections
    
    # Check if ngrok is available
    print("🔍 Checking for ngrok...")
    ngrok_available = check_ngrok_installed()
    public_url = None
    ngrok_process = None
    
    if ngrok_available:
        print("🔍 Starting ngrok tunnel...")
        public_url, ngrok_process = start_ngrok(PORT)
    
    # Print access information
    print_access_info(PORT, public_url)
    
    try:
        # Start Flask app
        app.run(host=HOST, port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        if ngrok_process:
            ngrok_process.terminate()
            print("✅ ngrok tunnel closed")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        if ngrok_process:
            ngrok_process.terminate()