from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg
import seaborn as sns

app = Flask(__name__)

# Set matplotlib style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Data file path
DATA_FILE = 'construction_materials.csv'

def initialize_data():
    """Initialize CSV file with headers if it doesn't exist"""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'Date', 'Site_Name', 'Material_Type', 'Material_Name', 
            'Quantity', 'Unit', 'Unit_Cost', 'Total_Cost', 'Supplier', 'Notes'
        ])
        df.to_csv(DATA_FILE, index=False)

def load_data():
    """Load data from CSV file"""
    try:
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return pd.DataFrame(columns=[
            'Date', 'Site_Name', 'Material_Type', 'Material_Name', 
            'Quantity', 'Unit', 'Unit_Cost', 'Total_Cost', 'Supplier', 'Notes'
        ])

def save_data(df):
    """Save dataframe to CSV file"""
    df.to_csv(DATA_FILE, index=False)

def create_chart(chart_type, df):
    """Create various charts based on the data"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if chart_type == 'cost_by_site':
        site_costs = df.groupby('Site_Name')['Total_Cost'].sum().sort_values(ascending=False)
        ax.bar(range(len(site_costs)), site_costs.values)
        ax.set_xticks(range(len(site_costs)))
        ax.set_xticklabels(site_costs.index, rotation=45, ha='right')
        ax.set_title('Total Cost by Construction Site')
        ax.set_ylabel('Total Cost (₹)')
        
    elif chart_type == 'cost_over_time':
        df_sorted = df.sort_values('Date')
        df_sorted['Cumulative_Cost'] = df_sorted['Total_Cost'].cumsum()
        ax.plot(df_sorted['Date'], df_sorted['Cumulative_Cost'], marker='o')
        ax.set_title('Cumulative Cost Over Time')
        ax.set_ylabel('Cumulative Cost (₹)')
        ax.set_xlabel('Date')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        plt.xticks(rotation=45)
        
    elif chart_type == 'material_distribution':
        material_costs = df.groupby('Material_Type')['Total_Cost'].sum()
        ax.pie(material_costs.values, labels=material_costs.index, autopct='%1.1f%%')
        ax.set_title('Cost Distribution by Material Type')
        
    elif chart_type == 'monthly_spending':
        df['Month'] = df['Date'].dt.to_period('M')
        monthly_costs = df.groupby('Month')['Total_Cost'].sum()
        ax.bar(range(len(monthly_costs)), monthly_costs.values)
        ax.set_xticks(range(len(monthly_costs)))
        ax.set_xticklabels([str(m) for m in monthly_costs.index], rotation=45)
        ax.set_title('Monthly Spending')
        ax.set_ylabel('Total Cost (₹)')
        
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return plot_url

@app.route('/')
def index():
    """Home page"""
    df = load_data()
    
    # Calculate summary statistics
    total_cost = df['Total_Cost'].sum() if not df.empty else 0
    total_entries = len(df)
    unique_sites = df['Site_Name'].nunique() if not df.empty else 0
    
    # Get recent entries
    recent_entries = df.tail(5).to_dict('records') if not df.empty else []
    
    return render_template('index.html', 
                         total_cost=total_cost,
                         total_entries=total_entries,
                         unique_sites=unique_sites,
                         recent_entries=recent_entries)

@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    """Add new material entry"""
    if request.method == 'POST':
        # Get form data
        data = {
            'Date': datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'Site_Name': request.form['site_name'],
            'Material_Type': request.form['material_type'],
            'Material_Name': request.form['material_name'],
            'Quantity': float(request.form['quantity']),
            'Unit': request.form['unit'],
            'Unit_Cost': float(request.form['unit_cost']),
            'Total_Cost': float(request.form['quantity']) * float(request.form['unit_cost']),
            'Supplier': request.form['supplier'],
            'Notes': request.form['notes']
        }
        
        # Load existing data and append new entry
        df = load_data()
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        
        return redirect(url_for('view_materials'))
    
    return render_template('add_material.html')

@app.route('/view_materials')
def view_materials():
    """View all materials with filtering and sorting"""
    df = load_data()
    
    # Get filter parameters
    site_filter = request.args.get('site', '')
    material_filter = request.args.get('material_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort_by', 'Date')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Apply filters
    filtered_df = df.copy()
    
    if site_filter:
        filtered_df = filtered_df[filtered_df['Site_Name'].str.contains(site_filter, case=False, na=False)]
    
    if material_filter:
        filtered_df = filtered_df[filtered_df['Material_Type'].str.contains(material_filter, case=False, na=False)]
    
    if date_from:
        date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
        filtered_df = filtered_df[filtered_df['Date'] >= date_from_dt]
    
    if date_to:
        date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
        filtered_df = filtered_df[filtered_df['Date'] <= date_to_dt]
    
    # Apply sorting
    if not filtered_df.empty and sort_by in filtered_df.columns:
        ascending = sort_order == 'asc'
        filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)
    
    # Get unique values for filter dropdowns
    sites = df['Site_Name'].unique().tolist() if not df.empty else []
    material_types = df['Material_Type'].unique().tolist() if not df.empty else []
    
    # Convert to records for template
    materials = filtered_df.to_dict('records')
    
    # Calculate filtered totals
    filtered_total_cost = filtered_df['Total_Cost'].sum() if not filtered_df.empty else 0
    filtered_count = len(filtered_df)
    
    return render_template('view_materials.html',
                         materials=materials,
                         sites=sites,
                         material_types=material_types,
                         filtered_total_cost=filtered_total_cost,
                         filtered_count=filtered_count,
                         current_filters={
                             'site': site_filter,
                             'material_type': material_filter,
                             'date_from': date_from,
                             'date_to': date_to,
                             'sort_by': sort_by,
                             'sort_order': sort_order
                         })

@app.route('/analytics')
def analytics():
    """Analytics dashboard with charts"""
    df = load_data()
    
    if df.empty:
        return render_template('analytics.html', charts={}, summary={})
    
    # Generate charts
    charts = {}
    try:
        charts['cost_by_site'] = create_chart('cost_by_site', df)
        charts['cost_over_time'] = create_chart('cost_over_time', df)
        charts['material_distribution'] = create_chart('material_distribution', df)
        charts['monthly_spending'] = create_chart('monthly_spending', df)
    except Exception as e:
        print(f"Error creating charts: {e}")
        charts = {}
    
    # Calculate summary statistics
    summary = {
        'total_cost': df['Total_Cost'].sum(),
        'avg_cost_per_entry': df['Total_Cost'].mean(),
        'most_expensive_site': df.groupby('Site_Name')['Total_Cost'].sum().idxmax(),
        'most_used_material': df['Material_Type'].mode().iloc[0] if not df['Material_Type'].mode().empty else 'N/A',
        'date_range': f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
    }
    
    return render_template('analytics.html', charts=charts, summary=summary)

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """Delete a specific entry"""
    df = load_data()
    
    if 0 <= entry_id < len(df):
        # Remove the entry at the specified index
        df = df.drop(df.index[entry_id]).reset_index(drop=True)
        save_data(df)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Entry not found'}), 404

@app.route('/export')
def export_data():
    """Export data to CSV"""
    df = load_data()
    
    # Create a BytesIO object
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'construction_materials_{datetime.now().strftime("%Y%m%d")}.csv'
    )

if __name__ == '__main__':
    initialize_data()
    app.run(debug=True)