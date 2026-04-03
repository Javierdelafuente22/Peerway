import pandas as pd
import numpy as np

def normalize_prices(input_file, output_file):
    # Load the dataset
    # Assuming Column B is index 1 and Column C is index 2
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return

    # Extract Import and Export columns (B and C)
    # Using iloc to ensure we get the columns regardless of header names
    import_prices = df.iloc[:, 1]
    export_prices = df.iloc[:, 2]

    # Combine both to find global statistics
    combined_prices = pd.concat([import_prices, export_prices])

    # Calculate 1st and 99th percentiles to handle outliers
    p1 = combined_prices.quantile(0.01)
    p99 = combined_prices.quantile(0.99)
    
    print(f"Global Min (1st percentile): {p1}")
    print(f"Global Max (99th percentile): {p99}")

    # Normalization function: (x - min) / (max - min)
    # This preserves the relative spread between the two columns
    def global_scale(x):
        norm_val = (x - p1) / (p99 - p1)
        # Clip values to [0, 1] to handle outliers outside the 99th percentile
        return np.clip(norm_val, 0, 1)

    # Apply the normalization
    df['import_norm'] = import_prices.apply(global_scale).round(4)
    df['export_norm'] = export_prices.apply(global_scale).round(4)

    # Calculate the normalized spread as a sanity check
    df['norm_spread'] = (df['import_norm'] - df['export_norm']).round(4)

    # Save to a new CSV
    df.to_csv(output_file, index=False)
    print(f"Success! Normalized prices saved to {output_file}")

if __name__ == "__main__":
    normalize_prices('prices.csv', 'normalized_prices_output.csv')