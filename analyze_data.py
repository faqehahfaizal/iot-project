import sqlite3

# 1. Configuration
DB_FILE = "sensor_data.db"

def get_summary_stats():
    """Compute summary statistics from the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Updated query to include MIN and MAX for humidity as well
    query = '''
        SELECT 
            COUNT(*) as count, 
            AVG(temperature) as avg_temp, 
            MIN(temperature) as min_temp, 
            MAX(temperature) as max_temp, 
            AVG(humidity) as avg_hum,
            MIN(humidity) as min_hum,
            MAX(humidity) as max_hum
        FROM readings
    '''
    
    try:
        cursor.execute(query)
        row = cursor.fetchone()
    except sqlite3.OperationalError as e:
        print(f"Error: Could not read database. {e}")
        return None
    finally:
        conn.close()

    # Handle the case where the table exists but has no data yet
    if not row or row[0] == 0:
        return {
            'count': 0,
            'avg_temp': 0, 'min_temp': 0, 'max_temp': 0,
            'avg_humidity': 0, 'min_humidity': 0, 'max_humidity': 0
        }

    return {
        'count': row[0],
        'avg_temp': round(row[1], 2) if row[1] is not None else 0,
        'min_temp': row[2] if row[2] is not None else 0,
        'max_temp': row[3] if row[3] is not None else 0,
        'avg_humidity': round(row[4], 2) if row[4] is not None else 0,
        'min_humidity': row[5] if row[5] is not None else 0,
        'max_humidity': row[6] if row[6] is not None else 0
    }

# 2. Main Execution
if __name__ == "__main__":
    stats = get_summary_stats()
    
    if stats:
        print(f"\n==================================================")
        print(f" IOT LABORATORY HISTORICAL DATA ANALYSIS REPORT")
        print(f"==================================================")
        print(f"Total Records Evaluated : {stats['count']} entries\n")
        
        print(f" TEMPERATURE STATISTICS:")
        print(f"   - Minimum Recorded : {stats['min_temp']}°C")
        print(f"   - Maximum Recorded : {stats['max_temp']}°C")
        print(f"   - Arithmetic Mean  : {stats['avg_temp']}°C\n")
        
        print(f" HUMIDITY STATISTICS:")
        print(f"   - Minimum Recorded : {stats['min_humidity']}%")
        print(f"   - Maximum Recorded : {stats['max_humidity']}%")
        print(f"   - Arithmetic Mean  : {stats['avg_humidity']}%")
        print(f"==================================================\n")
    else:
        print("No data available to analyze.")