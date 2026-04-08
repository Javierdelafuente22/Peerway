import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

def apply_lifestyle_update(json_payload, input_csv="data/demand.csv", output_csv="data/chatbot/demand.csv"):
    """
    Takes the JSON from the chatbot, applies the modifications to the demand time-series,
    and outputs a detailed CSV for verification and graphing.
    """
    print("\nLoading dataset and applying logic...")
    
    # 1. Load the data
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: Could not find {input_csv}.")
        return None

    # 2. Parse the timestamp securely 
    # (dayfirst=True ensures DD/MM/YYYY is read correctly, even if hours are missing)
    df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True)

    # 3. Setup our Output/Audit columns
    df['pre_demand'] = df['User']
    df['post_demand'] = df['User'].copy()
    df['multiplier_applied'] = np.nan # NaN by default (easier to read in CSV)
    df['is_masked'] = False           # Will turn True only for rows we modify

    # 4. Extract logic from the JSON payload
    mod_type = json_payload['modification']['type']
    mod_value = float(json_payload['modification']['value'])
    
    timing = json_payload['timing']
    days_of_week = timing['days_of_week']
    start_hour = int(timing['start_hour'])
    end_hour = int(timing['end_hour'])
    
    start_date = pd.to_datetime(timing['start_date'], dayfirst=True)
    end_date = pd.to_datetime(timing['end_date'], dayfirst=True)
    
    # Push the end_date to 23:59 so it includes the entirety of the final day
    if end_date.hour == 0 and end_date.minute == 0:
         end_date = end_date.replace(hour=23, minute=59)

    # 5. Create the Masks (The Filters)
    date_mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
    day_mask = df['timestamp'].dt.dayofweek.isin(days_of_week)
    hour_mask = (df['timestamp'].dt.hour >= start_hour) & (df['timestamp'].dt.hour <= end_hour)

    # Combine all 3 filters together
    final_mask = date_mask & day_mask & hour_mask
    
    # Tag the rows that made it through the filter
    df.loc[final_mask, 'is_masked'] = True

    # 6. Apply the Modification Math
    if mod_type == 'scale':
        df.loc[final_mask, 'post_demand'] = df.loc[final_mask, 'pre_demand'] * mod_value
        df.loc[final_mask, 'multiplier_applied'] = mod_value
        
        # Apply your constraint: Clip the new values so nothing exceeds 1.0
        df['post_demand'] = df['post_demand'].clip(upper=1.0)
        
    elif mod_type == 'fixed':
        df.loc[final_mask, 'post_demand'] = mod_value
        df.loc[final_mask, 'multiplier_applied'] = mod_value # Tracking the fixed value applied

    # 7. Format the Final DataFrame for the Output CSV
    # Re-order columns to exactly what you requested
    output_df = df[['timestamp', 'pre_demand', 'post_demand', 'multiplier_applied', 'is_masked']]
    
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Save the CSV
    output_df.to_csv(output_csv, index=False)
    print(f"Success! Modified data saved to: {output_csv}")
    
    return output_df

def get_plot_window(df, json_payload):
    """
    Intelligently slices the dataframe to find the best window to plot
    based on the category of the lifestyle change.
    """
    if not df['is_masked'].any():
        return df.head(100) # Fallback if no data was modified

    category = json_payload.get('category', '')
    
    # Find the very first timestamp where a modification occurred
    first_masked_time = df[df['is_masked']]['timestamp'].iloc[0]
    
    if category == 'Vacation':
        # Plot the whole vacation + 1 day padding on each side
        start_date = pd.to_datetime(json_payload['timing']['start_date'], dayfirst=True)
        end_date = pd.to_datetime(json_payload['timing']['end_date'], dayfirst=True)
        plot_start = start_date - pd.Timedelta(days=1)
        plot_end = end_date + pd.Timedelta(days=1)
        
    elif category == 'Worker':
        # Plot a full week (Monday to Sunday) containing the first modified day
        # .normalize() sets time to 00:00:00
        plot_start = first_masked_time.normalize() - pd.Timedelta(days=first_masked_time.weekday())
        plot_end = plot_start + pd.Timedelta(days=6, hours=23, minutes=59)
        
    else: # Default / EV
        # Plot 48 hours starting from the morning of the first modified day
        plot_start = first_masked_time.normalize()
        plot_end = plot_start + pd.Timedelta(days=2)

    # Slice the dataframe to our smart window
    plot_df = df[(df['timestamp'] >= plot_start) & (df['timestamp'] <= plot_end)]
    return plot_df

def plot_demand_comparison(plot_df, category):
    """
    Creates a clean, readable line chart comparing pre and post demand.
    """
    print("\nGenerating comparison graph...")
    
    plt.figure(figsize=(10, 5))
    
    # Plot Original Demand (Grey, slightly transparent)
    plt.plot(plot_df['timestamp'], plot_df['pre_demand'], 
             label='Original Demand', color='grey', alpha=0.5, linestyle='--')
    
    # Plot New Demand (Blue, bold)
    plt.plot(plot_df['timestamp'], plot_df['post_demand'], 
             label='Updated Demand', color='#1f77b4', linewidth=2)
    
    # Highlight the area between the lines to show the delta
    plt.fill_between(plot_df['timestamp'], plot_df['pre_demand'], plot_df['post_demand'], 
                     where=(plot_df['post_demand'] != plot_df['pre_demand']),
                     color='orange', alpha=0.3, label='Net Change')

    plt.title(f"Energy Demand Shift: {category} Profile", fontsize=14)
    plt.xlabel("Time", fontsize=12)
    plt.ylabel("Normalized Demand (0-1)", fontsize=12)
    plt.ylim(0, 1.05) # Keep Y-axis fixed so changes are visually relative
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # For now, we just show it. Later, you can pass this to your UI framework.
    plt.show()

# --- Local Testing Block ---
if __name__ == "__main__":
    # If you run this file directly, it tests the logic with our mock JSON
    mock_payload = {
        "mission_check": "Scale demand for Working from Home?",
        "category": "Worker",
        "modification": {"type": "scale", "value": 1.2},
        "timing": {
            "repeat": "weekly",
            "days_of_week": [4], # Friday
            "start_date": "01/01/2024",
            "end_date": "31/12/2025",
            "start_hour": 9,
            "end_hour": 17
        }
    }
    
    # Ensure you have a 'data/demand.csv' file before running this!
    test_run = apply_lifestyle_update(mock_payload)
    if test_run is not None:
        print("\nPreview of modified rows:")
        print(test_run[test_run['is_masked'] == True].head())