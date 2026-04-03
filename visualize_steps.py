"""
Script to visualize daily step count data from Garmin Connect as a bar chart.

This script fetches the last 30 days of step count data from Garmin Connect
and creates a bar chart visualization with a dark green line and
light green fill. The chart is exported as a high-quality PDF file.
"""
import logging
import sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from DatabaseManager import DatabaseManager
from GarminConnectSync import GarminConnectSync
from config import GARMIN_EMAIL, GARMIN_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('garmin_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def init_database():
    """Initialize the database and create the steps table if it doesn't exist"""
    db = DatabaseManager()

    if not db.connect():
        return False

    try:
        # Create steps table if it doesn't exist
        db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_steps (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                step_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.connection.commit()
        logging.info("Database initialized successfully")
        return True

    except Exception as exc:
        logging.error("Error initializing database: %s", exc)
        db.connection.rollback()
        return False
    finally:
        db.close()

def record_exists(date_str):
    """Check if a record already exists for the given date"""
    db = DatabaseManager()

    if not db.connect():
        return False

    try:
        db.cursor.execute("SELECT COUNT(*) FROM daily_steps WHERE date = %s", (date_str,))
        count = db.cursor.fetchone()['count']
        return count > 0

    except Exception as exc:
        logging.error("Error checking if record exists: %s", exc)
        return False
    finally:
        db.close()

def save_step_data_to_db(step_data):
    """Save step data to PostgreSQL database, avoiding duplicates"""
    if not step_data:
        return

    db = DatabaseManager()

    if not db.connect():
        return

    try:
        new_records = 0
        skipped_records = 0

        for day in step_data:
            date_str = day.get('calendarDate', '')
            total_steps = day.get('totalSteps', 0)

            if not date_str or total_steps is None:
                continue

            # Convert to int and handle invalid values
            try:
                steps_int = int(total_steps)
            except (ValueError, TypeError):
                logging.warning("Invalid step count for %s: %s", date_str, total_steps)
                continue

            # Insert and let the database handle duplicates
            db.cursor.execute("""
                INSERT INTO daily_steps (date, step_count)
                VALUES (%s, %s)
                ON CONFLICT (date) DO NOTHING
            """, (date_str, steps_int))

            if db.cursor.rowcount > 0:
                new_records += 1
                logging.info("Saved step data for %s: %d steps", date_str, steps_int)
            else:
                skipped_records += 1
                logging.debug("Record already exists for %s, skipping", date_str)

        db.connection.commit()
        logging.info("Database save complete. New records: %d, Skipped: %d",
                    new_records, skipped_records)

    except Exception as exc:
        logging.error("Error saving step data to database: %s", exc)
        db.connection.rollback()
    finally:
        db.close()

def get_step_data_for_last_month():
    """Fetch step count data for the last 30 days from Garmin Connect"""
    logging.info("Starting to fetch step count data for the last month...")

    # Check credentials
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        logging.error("Garmin Connect credentials not configured in .env file")
        return None

    # Initialize Garmin Connect client
    garmin = GarminConnectSync(GARMIN_EMAIL, GARMIN_PASSWORD)

    try:
        # Login to Garmin Connect
        if not garmin.login():
            logging.error("Failed to login to Garmin Connect")
            return None

        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logging.info("Fetching step data from %s to %s", start_date_str, end_date_str)

        # Get daily step data
        step_data = garmin.client.get_daily_steps(start_date_str, end_date_str)

        logging.info("Retrieved step data for %d days", len(step_data))

        # Save to database
        save_step_data_to_db(step_data)

        return step_data

    except Exception as exc:
        logging.error("Error fetching step data: %s", exc)
        return None

def create_bar_chart(step_data, output_file='step_count_chart.pdf'):
    """Create a bar chart of step counts and export to PDF"""
    if not step_data:
        logging.error("No step data to visualize")
        return False

    try:
        # Extract dates and step counts
        dates = []
        steps = []

        for day in step_data:
            # Parse the calendar date
            date_str = day.get('calendarDate', '')
            if date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                # Get total steps for the day and ensure it's a valid number
                total_steps = day.get('totalSteps', 0)

                # Convert to int and handle None or invalid values
                if total_steps is not None:
                    try:
                        steps_int = int(total_steps)
                        dates.append(date_obj)
                        steps.append(steps_int)
                    except (ValueError, TypeError):
                        logging.warning("Invalid step count for %s: %s", date_str, total_steps)
                        continue
                else:
                    logging.warning("No step count data for %s", date_str)
                    continue

        if not dates or not steps:
            logging.error("No valid date/step data found")
            return False

        logging.info("Processing %d days with valid step data", len(dates))

        # Create the plot
        _, ax = plt.subplots(figsize=(14, 8))

        # Create the bar chart with individual bars for each day
        bars = ax.bar(dates, steps, color='darkblue', alpha=0.8, width=0.8)

        # Add value labels on top of each bar
        for bar, step_count in zip(bars, steps):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(steps)*0.01,
                   f'{step_count:,}', ha='center', va='bottom', fontsize=8, rotation=45)

        # Format the chart
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Step Count', fontsize=12, fontweight='bold')
        ax.set_title('Daily Step Count - Last 30 Days', fontsize=14, fontweight='bold', pad=20)

        # Format x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.xticks(rotation=45, ha='right')

        # Add grid for better readability (horizontal only)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')

        # Format y-axis with comma separator for thousands
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # Set y-axis to start from 0 and add some padding at the top
        ax.set_ylim(0, max(steps) * 1.15)

        # Tight layout to prevent label cutoff
        plt.tight_layout()

        # Save as PDF
        plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
        logging.info("Chart saved successfully to %s", output_file)

        # Also display some statistics
        avg_steps = sum(steps) / len(steps)
        max_steps = max(steps)
        min_steps = min(steps)
        logging.info("Statistics - Average: %.0f, Max: %d, Min: %d",
                     avg_steps, max_steps, min_steps)

        return True

    except Exception as exc:
        logging.error("Error creating bar chart: %s", exc)
        return False

def main():
    """Main function to fetch step data and create visualization"""
    logging.info("Starting step count visualization process...")

    # Initialize database
    if not init_database():
        logging.error("Failed to initialize database")
        return

    # Fetch step data
    step_data = get_step_data_for_last_month()

    if not step_data:
        logging.error("Failed to fetch step data")
        return

    # Create and save the chart
    success = create_bar_chart(step_data)

    if success:
        logging.info("Visualization completed successfully")
    else:
        logging.error("Failed to create visualization")

if __name__ == "__main__":
    main()
