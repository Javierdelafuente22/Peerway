import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Load your dataset
path = "weave_processed.csv"  # <-- Replace with your file path
df = pd.read_csv(path)

# 2. Identify the columns to normalize (all except the first one)
# df.columns[1:] selects every column name starting from the second column
cols_to_normalize = df.columns[1:]

for col in cols_to_normalize:
    # Check if the column is numerical to avoid errors with strings/dates
    if np.issubdtype(df[col].dtype, np.number):
        
        # Calculate 99th percentile and minimum
        p99 = df[col].quantile(0.99)
        col_min = df[col].min()
        
        # Avoid division by zero if the column has constant values or 
        # if the 99th percentile equals the minimum
        if p99 > col_min:
            # Apply scaling: (x - min) / (p99 - min)
            df[col] = (df[col] - col_min) / (p99 - col_min)
            
            # Clip values to [0, 1]
            # This turns everything above the 99th percentile into 1
            df[col] = df[col].clip(lower=0, upper=1).round(4)
        else:
            # If p99 == min, the column is essentially constant; 
            # we can set it to 0 or leave it as is.
            df[col] = 0.0

# 4. Slicing for the Plot 
start_row = 24 # 1st Jan (0) or 1st July (4369) 2024
end_row = start_row + 24
df_plot = df.iloc[start_row:end_row, :16]

plot_cols = df_plot.columns[1:]
time_col = df_plot.columns[0]

# 5. Plotting the curves
plt.figure(figsize=(15, 8))

# Using a colormap to ensure 15 distinct colors
colors = plt.cm.tab20(np.linspace(0, 1, len(plot_cols)))

for i, col in enumerate(plot_cols):
    # Plotting against a range of 48 points to keep x-axis clean
    plt.plot(range(24), df_plot[col], label=col, color=colors[i], linewidth=2.0, alpha=0.8)

plt.title("Normalized Consumption Data (Summer Day - 24 periods, 15 profiles)", fontsize=14)
plt.xlabel("Hourly Intervals", fontsize=12)
plt.ylabel("Normalized Demand Value (0-1) [kWh]", fontsize=12)

# REMOVE X-AXIS LABELS
plt.xticks([]) 

plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1), fontsize='small', ncol=1)
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
plt.tight_layout()

plt.show()