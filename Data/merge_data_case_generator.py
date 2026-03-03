import pandas as pd
import numpy as np

# --- CONFIGURATION: CASE STUDY SETUP ---
# Define the role for each of the 10 IDs.
# Options: "Prosumer", "Buyer", "Seller"
ROLES = [
    "Prosumer", # Fixed: ID 1 is user profile
    "Prosumer", # ID 2
    "Prosumer", # ID 3
    "Prosumer", # ID 4
    "Prosumer", # ID 5
    "Buyer",    # ID 6
    "Buyer",    # ID 7
    "Seller",   # ID 8
    "Seller",   # ID 9
    "Seller"    # Fixed: ID 10 is windfarm
]

def generate_case_study():
    print("--- Starting Case Study Generator ---")

    # 1. Validation
    if len(ROLES) != 10:
        raise ValueError(f"Configuration Error: You defined {len(ROLES)} roles, but there are 9 profiles.")

    # 2. Load Data
    print("Loading raw files...")
    # We use dayfirst=False as per your fix
    df_prices = pd.read_csv('prices.csv')
    df_demand = pd.read_csv('demand.csv')
    df_supply = pd.read_csv('supply.csv')

    # Extract the Master Timestamp (from Prices file)
    # We force convert to datetime to ensure sin/cos works
    timestamp_col = pd.to_datetime(df_prices.iloc[:, 0], dayfirst=False)
    
    # 3. GENERATE CYCLIC FEATURES (Rounded to 4 decimals)
    print("Generating Time Features...")
    
    # Time of Day (24h)
    hours_float = timestamp_col.dt.hour + timestamp_col.dt.minute / 60.0
    day_sin = np.sin(2 * np.pi * hours_float / 24.0).round(4)
    day_cos = np.cos(2 * np.pi * hours_float / 24.0).round(4)

    # Time of Year (Annual)
    year_sin = np.sin(2 * np.pi * timestamp_col.dt.dayofyear / 365.25).round(4)
    year_cos = np.cos(2 * np.pi * timestamp_col.dt.dayofyear / 365.25).round(4)

    df_features = pd.DataFrame({
        'time_year_sin': year_sin,
        'time_year_cos': year_cos,
        'time_day_sin': day_sin,
        'time_day_cos': day_cos
    })

    # 4. CALCULATE PROFILES BASED ON ROLES
    print("Calculating profiles based on roles...")
    
    profile_data = {}

    # We loop through 0 to 8 (corresponding to columns 1 to 9 in raw files)
    for i, role in enumerate(ROLES):
        # We skip the first column (timestamp) using i+1
        # .values ensures we calculate using raw numbers (no index mismatch errors)
        demand_vals = df_demand.iloc[:, i+1].values
        supply_vals = df_supply.iloc[:, i+1].values
        
        column_name = f"{i+1}_{role}"
        
        if role == "Prosumer":
            # Demand - Supply
            profile_data[column_name] = demand_vals - supply_vals
            
        elif role == "Buyer":
            # Just Demand
            profile_data[column_name] = demand_vals
            
        elif role == "Seller":
            # Negative Supply (Exporting)
            profile_data[column_name] = -supply_vals
            
        else:
            raise ValueError(f"Unknown role: {role}")

    # Convert dictionary to DataFrame
    df_profiles = pd.DataFrame(profile_data)

    # 5. ASSEMBLE FINAL DATAFRAME
    print("Assembling final file...")
    
    # Get Import/Export Prices (Columns 1 and 2)
    df_price_data = df_prices.iloc[:, 1:3]

    final_df = pd.concat([
        timestamp_col.rename("timestamp"), # 1. Time
        df_features,                       # 2. Sin/Cos Features
        df_price_data,                     # 3. Prices
        df_profiles                        # 4. The 9 Generated Profiles
    ], axis=1)

    # 6. Save
    output_filename = 'orderbook.csv'
    final_df.to_csv(output_filename, index=False)
    
    print("SUCCESS!")
    print(f"File saved as: {output_filename}")
    print("\nGenerated Columns:")
    print(list(final_df.columns))

if __name__ == "__main__":
    generate_case_study()