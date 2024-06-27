import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

'''
Based on data from:
Brysbaert, Marc, and Françoise Vitu. "Word skipping: Implications for theories 
of eye movement control in reading." Eye guidance in reading and scene 
perception. Elsevier Science Ltd, 1998. 125-147.

'''

# Example digitized data points for high-frequency and low-frequency curves
# Replace these with actual digitized points from the graph
word_length = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
high_freq_prob = np.array([1, 0.8, 0.65, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1, 0.08, 0.06, 0.04, 0.03, 0.02, 0.01])
low_freq_prob = np.array([1, 0.75, 0.55, 0.4, 0.3, 0.22, 0.18, 0.14, 0.11, 0.08, 0.06, 0.05, 0.03, 0.02, 0.015, 0.01])

# Define the exponential function
def exp_func(x, k, lam):
    return k * np.exp(-lam * x)

# Fit the high-frequency data
popt_high, pcov_high = curve_fit(exp_func, word_length, high_freq_prob)
k_high, lam_high = popt_high

# Fit the low-frequency data
popt_low, pcov_low = curve_fit(exp_func, word_length, low_freq_prob)
k_low, lam_low = popt_low

# Plot the original data points and the fitted curves
plt.figure(figsize=(10, 6))
plt.scatter(word_length, high_freq_prob, color='red', label='High-Freq Data')
plt.scatter(word_length, low_freq_prob, color='blue', label='Low-Freq Data')
plt.plot(word_length, exp_func(word_length, k_high, lam_high), color='red', linestyle='-', label='High-Freq Fit')
plt.plot(word_length, exp_func(word_length, k_low, lam_low), color='blue', linestyle='--', label='Low-Freq Fit')
plt.xlabel('Word Length')
plt.ylabel('Skipping Probability')
plt.legend()
plt.show()

print(f'High-Freq Parameters: k = {k_high}, lambda = {lam_high}')
print(f'Low-Freq Parameters: k = {k_low}, lambda = {lam_low}')
