import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Load the brain
q_table = np.load('trained_q_table.npy')

# Let's look at Hour 18 (6 PM - Peak Time) and Price Bin 4 (Very Expensive)
# q_table shape is (SoC, Price, Hour, Action)
hour_to_check = 18
price_bin_to_check = 4 

# Extract the Q-values for all 3 actions across all SoC levels
data = q_table[:, price_bin_to_check, hour_to_check, :]

plt.figure(figsize=(10, 6))
sns.heatmap(data, annot=True, fmt=".2f", 
            xticklabels=['Charge', 'Hold', 'Discharge'],
            yticklabels=[f'SoC {i}' for i in range(11)])
plt.title(f"Brain Logic at Hour {hour_to_check} when Price is High")
plt.xlabel("Action")
plt.ylabel("Battery Level (SoC)")
plt.show()