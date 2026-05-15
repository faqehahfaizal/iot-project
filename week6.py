import sqlite3

# 1. Configuration
DB_FILE = "sensor_data.db"

def get_summary_stats():
    """Compute summary statistics from the database"""
    # Using a 'with' statement is a cleaner way to handle connections
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            COUNT(*) as count, 
            AVG(temperature) as avg_temp, 
            MIN(temperature) as min_temp, 
            MAX(temperature) as max_temp, 
            AVG(humidity) as avg_hum 
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
            'avg_temp': 0,
            'min_temp': 0,
            'max_temp': 0,
            'avg_humidity': 0
        }

    return {
        'count': row[0],
        'avg_temp': round(row[1], 1) if row[1] is not None else 0,
        'min_temp': row[2] if row[2] is not None else 0,
        'max_temp': row[3] if row[3] is not None else 0,
        'avg_humidity': round(row[4], 1) if row[4] is not None else 0
    }

# 2. Main Execution
if __name__ == "__main__":
    stats = get_summary_stats()
    
    if stats:
        print(f"\n{'='*10} Sensor Data Summary {'='*10}")
        print(f"Total readings:  {stats['count']}")
        print(f"Temperature:     {stats['avg_temp']}Â°C (Range: {stats['min_temp']}Â°C to {stats['max_temp']}Â°C)")
        print(f"Humidity:        {stats['avg_humidity']}%")
        print(f"{'='*31}\n")
    else:
        print("No data available to analyze.")
