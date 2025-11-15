"""Script to visualize daily step count data from Garmin Connect as an area chart."""
import logging
import sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
        return step_data

    except Exception as exc:
        logging.error("Error fetching step data: %s", exc)
        return None

def create_area_chart(step_data, output_file='step_count_chart.pdf'):
    """Create an area chart of step counts and export to PDF"""
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
                dates.append(date_obj)

                # Get total steps for the day
                total_steps = day.get('totalSteps', 0)
                steps.append(total_steps)

        if not dates or not steps:
            logging.error("No valid date/step data found")
            return False

        # Create the plot
        _, ax = plt.subplots(figsize=(12, 6))

        # Create the area chart with dark green line and light green fill
        ax.plot(dates, steps, color='darkgreen', linewidth=2, label='Daily Steps')
        ax.fill_between(dates, steps, color='lightgreen', alpha=0.5)

        # Format the chart
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Step Count', fontsize=12, fontweight='bold')
        ax.set_title('Daily Step Count - Last 30 Days', fontsize=14, fontweight='bold', pad=20)

        # Format x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        plt.xticks(rotation=45, ha='right')

        # Add grid for better readability
        ax.grid(True, alpha=0.3, linestyle='--')

        # Format y-axis with comma separator for thousands
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # Add legend
        ax.legend(loc='upper right')

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
        logging.error("Error creating area chart: %s", exc)
        return False

def main():
    """Main function to fetch step data and create visualization"""
    logging.info("Starting step count visualization process...")

    # Fetch step data
    step_data = get_step_data_for_last_month()

    if not step_data:
        logging.error("Failed to fetch step data")
        return

    # Create and save the chart
    success = create_area_chart(step_data)

    if success:
        logging.info("Visualization completed successfully")
    else:
        logging.error("Failed to create visualization")

if __name__ == "__main__":
    main()
