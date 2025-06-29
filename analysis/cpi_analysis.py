
from Hagstofan.api_client import APIClient
from Hagstofan.economy.cpi import CPI
from statistics import mean, median
from datetime import datetime
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import pandas as pd
from statistics import mean

# Reikna breytingar sögulega
def historical_changes_for_isnr(isnr):
    dates = sorted({d for (d, i) in cpi.index if i == isnr})
    values = [cpi.get_value_for(d, isnr) for d in dates if isinstance(cpi.get_value_for(d, isnr), float)]
    if len(values) > 1:
        return [((values[i] - values[i - 1]) / values[i - 1]) * 100 for i in range(1, len(values))]
    return []

# Setup
client = APIClient(base_url='https://px.hagstofa.is:443/pxis/api/v1')
cpi = CPI(client)

# Get all historical CPI values for IS00
cpi_code = "IS00"
all_data = sorted(((d, cpi.get_value_for(d, cpi_code)) for (d, i) in cpi.index if i == cpi_code and isinstance(cpi.get_value_for(d, cpi_code), float)))
historical_labels = [d for d, _ in all_data]
historical_values = [v for _, v in all_data]

# Calculate historical monthly changes
historical_changes = [
    ((historical_values[i] - historical_values[i - 1]) / historical_values[i - 1]) * 100
    for i in range(1, len(historical_values))
]
print("\nSöguleg tölfræði vísitölu neysluverðs:")
print(f" - Average monthly CPI increase: {mean(historical_changes):.2f}%")
print(f" - Median monthly CPI increase: {median(historical_changes):.2f}%")

# Historical avg/median increase for each ISNR
print("\nSögulegt meðaltal og miðgildi hverrar undirvísitölu:")
historical_isnr_changes = {}
for isnr in cpi.list_is_nr_values():
    dates = sorted({d for (d, i) in cpi.index if i == isnr})
    values = [cpi.get_value_for(d, isnr) for d in dates if isinstance(cpi.get_value_for(d, isnr), float)]
    if len(values) > 1:
        changes = [
            ((values[i] - values[i - 1]) / values[i - 1]) * 100
            for i in range(1, len(values))
        ]
        historical_isnr_changes[isnr] = mean(changes)
        print(f"{isnr} ({cpi.get_label_for_is_nr(isnr)}): avg = {mean(changes):.2f}%, median = {median(changes):.2f}%")

# Predict next 6 months CPI using a sliding average of the last 12 changes
projected_values = historical_values.copy()
projected_labels = historical_labels.copy()
projected = []
projected_changes = []
base_date = datetime.strptime(historical_labels[-1], "%YM%m")

for i in range(6):
    recent_changes = [
        ((projected_values[j] - projected_values[j - 1]) / projected_values[j - 1]) * 100
        for j in range(len(projected_values) - 12, len(projected_values))
    ]
    next_change = mean(recent_changes)
    next_value = projected_values[-1] * (1 + next_change / 100)
    projected_values.append(next_value)
    projected_changes.append(round(next_change, 2))

    next_label = (base_date + relativedelta(months=i + 1)).strftime("%YM%m")
    projected_labels.append(next_label)
    projected.append(round(next_value, 2))

# Projection using historical average
avg_monthly_increase = mean(historical_changes)
historical_projection = [historical_values[-1]]
hist_date = datetime.strptime(historical_labels[-1], "%YM%m")
for _ in range(6):
    next_val = historical_projection[-1] * (1 + avg_monthly_increase / 100)
    historical_projection.append(next_val)
historical_projection = historical_projection[1:]

# Top ISNR áhrif
increases = cpi.get_increase_over_months(12)
latest_date = max([d for (d, _) in cpi.weights])
weights = {
    isnr: cpi.get_weight(latest_date, isnr)
    for isnr in cpi.list_is_nr_values()
    if cpi.get_weight(latest_date, isnr) is not None
}
impact_scores = {
    isnr: (increases.get(isnr, 0) * weights.get(isnr, 0)) / 100
    for isnr in weights
}
top_impacts = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)[:25]

# Setja saman töflu
records = []
for isnr, score in top_impacts:
    label = cpi.get_label_for_is_nr(isnr)
    pct_increase = increases.get(isnr, 0)
    monthly_avg = pct_increase / 12
    hist_changes = historical_changes_for_isnr(isnr)
    historical_avg = mean(hist_changes) if hist_changes else 0
    records.append({
        "Undirvísitala": f"{isnr} ({label})",
        "Breyting (%)": round(pct_increase, 2),
        "Mánaðarlegt meðaltal (%)": round(monthly_avg, 2),
        "Sögulegt meðaltal (%)": round(historical_avg, 2),
        "Mismunur frá sögulegu (%)": round(monthly_avg - historical_avg, 2)
    })

df = pd.DataFrame(records)
df = df.sort_values(by="Mismunur frá sögulegu (%)", ascending=False)

print("\nTopplisti breytinga frá sögulegu meðaltali:")
print(df.to_string(index=False))
    
print("\nSpá um þróun vísitölu neysluverðs (VNV) næstu 6 mánuði:")
for i, val in enumerate(projected[-6:]):
    pct = projected_changes[i]
    print(f"Mánuður {i + 1}: {val:.2f}  (+{pct:.2f}%)")

# Plot historical + projections
plt.figure(figsize=(12, 6))
years = [datetime.strptime(d, "%YM%m").year for d in projected_labels]
ticks = [i for i in range(len(projected_labels)) if i == 0 or years[i] != years[i - 1]]
tick_labels = [str(years[i]) for i in ticks]

plt.plot(range(len(historical_values)), historical_values, label="Söguleg VNV", color='blue')
plt.plot(range(len(historical_values), len(projected_values)), projected[-6:], label="Spá VNV (Sliding Avg)", color='orange')
plt.plot(range(len(historical_values), len(historical_values) + 6), historical_projection, label="Spá VNV (Hist. Avg)", color='green', linestyle='--')

plt.title("VNV Sögulegt gildi og spá")
plt.xlabel("Ár")
plt.ylabel("VNV gildi")
plt.xticks(ticks, tick_labels, rotation=45)
plt.grid(axis='x')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()

# Velja ISNR kóða fyrir rafmagn
isnr_code = "IS0451"
label = cpi.get_label_for_is_nr(isnr_code)

# Ná í dagsetningar og gildi
dates = sorted({d for (d, i) in cpi.index if i == isnr_code})
values = [cpi.get_value_for(d, isnr_code) for d in dates if isinstance(cpi.get_value_for(d, isnr_code), float)]

# Breyta YYYYMM strengi í datetime fyrir betri merkingu á x-ás
from datetime import datetime
parsed_dates = [datetime.strptime(d, "%YM%m") for d in dates[:len(values)]]

# Teikna línurit
plt.figure(figsize=(10, 5))
plt.plot(parsed_dates, values, label=label, color='red')
plt.plot(parsed_dates, historical_values, label=cpi.get_label_for_is_nr("IS00"), color='green', linestyle='--', alpha=0.5)
plt.title(f"Söguleg þróun: {label} ({isnr_code})")
plt.xlabel("Tími")
plt.ylabel("Vísitölugildi")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()