import pandas as pd

# Read the enriched data
df = pd.read_csv("data/rq2_8_enriched.csv")

# Count patched vs unpatched vulnerabilities
patched_count = df[df["cve_patched"] == True].shape[0]
unpatched_count = df[df["cve_patched"] == False].shape[0]

print("\nVulnerability Patch Status:")
print(f"Patched vulnerabilities: {patched_count}")
print(f"Unpatched vulnerabilities: {unpatched_count}")
print(f"Total vulnerabilities: {patched_count + unpatched_count}")

# Calculate percentages
total = patched_count + unpatched_count
patched_percent = (patched_count / total) * 100
unpatched_percent = (unpatched_count / total) * 100

print(f"\nPercentages:")
print(f"Patched: {patched_percent:.1f}%")
print(f"Unpatched: {unpatched_percent:.1f}%")
