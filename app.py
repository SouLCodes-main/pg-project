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
    """Initialize CSV files with headers if they don't exist"""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'Date', 'Site_Name', 'Material_Type', 'Material_Name', 
            'Quantity', 'Unit', 'Unit_Cost', 'Total_Cost', 'Supplier', 'Notes'
        ])
        df.to_csv(DATA_FILE, index=False)
    
    # Initialize usage tracking file
    usage_file = 'material_usage.csv'
    if not os.path.exists(usage_file):
        df_usage = pd.DataFrame(columns=[
            'Usage_Date', 'Material_ID', 'Site_Name', 'Material_Name', 
            'Used_Quantity', 'Unit', 'Usage_Purpose', 'Used_By', 'Notes'
        ])
        df_usage.to_csv(usage_file, index=False)

def load_usage_data():
    """Load usage data from CSV file"""
    try:
        df = pd.read_csv('material_usage.csv')
        if not df.empty:
            df['Usage_Date'] = pd.to_datetime(df['Usage_Date'])
        return df
    except:
        return pd.DataFrame(columns=[
            'Usage_Date', 'Material_ID', 'Site_Name', 'Material_Name', 
            'Used_Quantity', 'Unit', 'Usage_Purpose', 'Used_By', 'Notes'
        ])

def save_usage_data(df):
    """Save usage dataframe to CSV file"""
    df.to_csv('material_usage.csv', index=False)

def calculate_remaining_materials():
    """Calculate remaining quantities for all materials"""
    materials_df = load_data()
    usage_df = load_usage_data()
    
    if materials_df.empty:
        return pd.DataFrame()
    
    # Add material ID to materials (using index)
    materials_df = materials_df.reset_index()
    materials_df['Material_ID'] = materials_df.index
    
    remaining_materials = []
    
    for _, material in materials_df.iterrows():
        material_id = material['Material_ID']
        original_quantity = material['Quantity']
        
        # Calculate total used for this material
        material_usage = usage_df[usage_df['Material_ID'] == material_id]
        total_used = material_usage['Used_Quantity'].sum() if not material_usage.empty else 0
        
        remaining_quantity = original_quantity - total_used
        usage_percentage = (total_used / original_quantity * 100) if original_quantity > 0 else 0
        remaining_percentage = 100 - usage_percentage
        
        remaining_materials.append({
            'Material_ID': material_id,
            'Date': material['Date'],
            'Site_Name': material['Site_Name'],
            'Material_Type': material['Material_Type'],
            'Material_Name': material['Material_Name'],
            'Original_Quantity': original_quantity,
            'Used_Quantity': total_used,
            'Remaining_Quantity': remaining_quantity,
            'Unit': material['Unit'],
            'Usage_Percentage': usage_percentage,
            'Remaining_Percentage': remaining_percentage,
            'Unit_Cost': material['Unit_Cost'],
            'Remaining_Value': remaining_quantity * material['Unit_Cost'],
            'Supplier': material['Supplier'],
            'Status': 'Depleted' if remaining_quantity <= 0 else 'Available'
        })
    
    return pd.DataFrame(remaining_materials)

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
        
    elif chart_type == 'material_usage_status':
        remaining_df = calculate_remaining_materials()
        if not remaining_df.empty:
            status_counts = remaining_df['Status'].value_counts()
            colors = ['#28a745' if status == 'Available' else '#dc3545' for status in status_counts.index]
            ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors)
            ax.set_title('Material Status Distribution')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Material Status Distribution')
            
    elif chart_type == 'remaining_value_by_site':
        remaining_df = calculate_remaining_materials()
        if not remaining_df.empty:
            site_values = remaining_df.groupby('Site_Name')['Remaining_Value'].sum().sort_values(ascending=False)
            ax.bar(range(len(site_values)), site_values.values, color='#20c997')
            ax.set_xticks(range(len(site_values)))
            ax.set_xticklabels(site_values.index, rotation=45, ha='right')
            ax.set_title('Remaining Material Value by Site')
            ax.set_ylabel('Remaining Value (₹)')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Remaining Material Value by Site')
    
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
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_material.html', today=today)

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
        # Add usage-related charts
        charts['material_usage_status'] = create_chart('material_usage_status', df)
        charts['remaining_value_by_site'] = create_chart('remaining_value_by_site', df)
    except Exception as e:
        print(f"Error creating charts: {e}")
        charts = {}
    
    # Calculate summary statistics
    remaining_df = calculate_remaining_materials()
    summary = {
        'total_cost': df['Total_Cost'].sum(),
        'avg_cost_per_entry': df['Total_Cost'].mean(),
        'most_expensive_site': df.groupby('Site_Name')['Total_Cost'].sum().idxmax(),
        'most_used_material': df['Material_Type'].mode().iloc[0] if not df['Material_Type'].mode().empty else 'N/A',
        'date_range': f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}",
        'total_remaining_value': remaining_df['Remaining_Value'].sum() if not remaining_df.empty else 0,
        'available_materials': len(remaining_df[remaining_df['Status'] == 'Available']) if not remaining_df.empty else 0,
        'depleted_materials': len(remaining_df[remaining_df['Status'] == 'Depleted']) if not remaining_df.empty else 0
    }
    
    return render_template('analytics.html', charts=charts, summary=summary)

@app.route('/material_usage')
def material_usage():
    """View material usage and remaining quantities"""
    remaining_df = calculate_remaining_materials()
    
    # Get filter parameters
    site_filter = request.args.get('site', '')
    material_filter = request.args.get('material_type', '')
    status_filter = request.args.get('status', '')
    
    # Apply filters
    filtered_df = remaining_df.copy()
    
    if site_filter:
        filtered_df = filtered_df[filtered_df['Site_Name'].str.contains(site_filter, case=False, na=False)]
    
    if material_filter:
        filtered_df = filtered_df[filtered_df['Material_Type'].str.contains(material_filter, case=False, na=False)]
    
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    
    # Get unique values for filters
    sites = remaining_df['Site_Name'].unique().tolist() if not remaining_df.empty else []
    material_types = remaining_df['Material_Type'].unique().tolist() if not remaining_df.empty else []
    
    # Convert to records
    materials = filtered_df.to_dict('records')
    
    # Calculate summary
    total_remaining_value = filtered_df['Remaining_Value'].sum() if not filtered_df.empty else 0
    available_count = len(filtered_df[filtered_df['Status'] == 'Available']) if not filtered_df.empty else 0
    depleted_count = len(filtered_df[filtered_df['Status'] == 'Depleted']) if not filtered_df.empty else 0
    
    return render_template('material_usage.html',
                         materials=materials,
                         sites=sites,
                         material_types=material_types,
                         total_remaining_value=total_remaining_value,
                         available_count=available_count,
                         depleted_count=depleted_count,
                         current_filters={
                             'site': site_filter,
                             'material_type': material_filter,
                             'status': status_filter
                         })

@app.route('/add_usage/<int:material_id>', methods=['GET', 'POST'])
def add_usage(material_id):
    """Add usage record for a specific material"""
    materials_df = load_data()
    
    if material_id >= len(materials_df):
        return redirect(url_for('material_usage'))
    
    # Convert the material series to a dictionary and ensure date is datetime
    material = materials_df.iloc[material_id].to_dict()
    if 'Date' in material and pd.notnull(material['Date']):
        material['Date'] = pd.to_datetime(material['Date'])
    
    remaining_df = calculate_remaining_materials()
    material_remaining = remaining_df[remaining_df['Material_ID'] == material_id].iloc[0]
    
    if request.method == 'POST':
        used_quantity = float(request.form['used_quantity'])
        
        # Check if usage exceeds remaining quantity
        if used_quantity > material_remaining['Remaining_Quantity']:
            error_message = f"Cannot use {used_quantity} {material['Unit']}. Only {material_remaining['Remaining_Quantity']} {material['Unit']} remaining."
            return render_template('add_usage.html', material=material, 
                                 material_remaining=material_remaining, error=error_message)
        
        # Add usage record
        usage_data = {
            'Usage_Date': datetime.strptime(request.form['usage_date'], '%Y-%m-%d'),
            'Material_ID': material_id,
            'Site_Name': material['Site_Name'],
            'Material_Name': material['Material_Name'],
            'Used_Quantity': used_quantity,
            'Unit': material['Unit'],
            'Usage_Purpose': request.form['usage_purpose'],
            'Used_By': request.form['used_by'],
            'Notes': request.form['notes']
        }
        
        usage_df = load_usage_data()
        new_usage = pd.DataFrame([usage_data])
        usage_df = pd.concat([usage_df, new_usage], ignore_index=True)
        save_usage_data(usage_df)
        
        return redirect(url_for('material_usage'))
    
    # Get today's date for the form
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_usage.html', material=material, material_remaining=material_remaining, today=today)

@app.route('/usage_history/<int:material_id>')
def usage_history(material_id):
    """View usage history for a specific material"""
    materials_df = load_data()
    usage_df = load_usage_data()
    
    if material_id >= len(materials_df):
        return redirect(url_for('material_usage'))
    
    material = materials_df.iloc[material_id]
    material_usage = usage_df[usage_df['Material_ID'] == material_id].sort_values('Usage_Date', ascending=False)
    
    # Calculate running totals
    usage_records = []
    cumulative_used = 0
    
    for _, usage in material_usage.iterrows():
        cumulative_used += usage['Used_Quantity']
        remaining_at_time = material['Quantity'] - cumulative_used
        
        usage_records.append({
            'Usage_Date': usage['Usage_Date'],
            'Used_Quantity': usage['Used_Quantity'],
            'Unit': usage['Unit'],
            'Usage_Purpose': usage['Usage_Purpose'],
            'Used_By': usage['Used_By'],
            'Notes': usage['Notes'],
            'Cumulative_Used': cumulative_used,
            'Remaining_After': remaining_at_time
        })
    
    # Reverse to show latest first
    usage_records.reverse()
    
    return render_template('usage_history.html', material=material, usage_records=usage_records)

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """Delete a specific entry"""
    try:
        # Load both materials and usage data
        materials_df = load_data()
        usage_df = load_usage_data()
        
        if 0 <= entry_id < len(materials_df):
            # Delete the material entry
            deleted_material = materials_df.iloc[entry_id]
            materials_df = materials_df.drop(materials_df.index[entry_id]).reset_index(drop=True)
            save_data(materials_df)
            
            # Delete associated usage records
            usage_df = usage_df[usage_df['Material_ID'] != entry_id]
            # Update material IDs that are greater than the deleted ID
            usage_df.loc[usage_df['Material_ID'] > entry_id, 'Material_ID'] -= 1
            save_usage_data(usage_df)
            
            return jsonify({
                'success': True, 
                'message': f'Successfully deleted {deleted_material["Material_Name"]} and its usage records'
            })
        else:
            return jsonify({'success': False, 'message': 'Entry not found'}), 404
            
    except Exception as e:
        print(f"Error in delete_entry: {str(e)}")  # For debugging
        return jsonify({'success': False, 'message': f'Error deleting entry: {str(e)}'}), 500

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

initialize_data()

if __name__ == '__main__':
    app.run()