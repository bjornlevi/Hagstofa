from Hagstofan.api_client import APIClient
from Hagstofan.economy.construction_price_index import ConstructionPriceIndex
from statistics import mean, median
import matplotlib.pyplot as plt

# Setup
client = APIClient(base_url='https://px.hagstofa.is:443/pxis/api/v1')
cindex = ConstructionPriceIndex(client)

print("\nSögulegar tölur eftir undirvísitölum byggingarvísitölu:")

# Prepare plot
plt.figure(figsize=(12, 6))
plotted_categories = 0

for category in cindex.list_categories():
    label = cindex.get_label_for_category(category)
    historical = cindex.get_historical_values(category, months=60)

    if len(historical) < 2:
        continue

    # Split into months and values
    months, values = zip(*historical)

    # Calculate monthly % changes
    changes = [
        ((values[i] - values[i - 1]) / values[i - 1]) * 100
        for i in range(1, len(values))
    ]

    print(f"{label}: meðaltal = {mean(changes):.2f}%, miðgildi = {median(changes):.2f}%")

    # Plot line for this category
    plt.plot(months, values, label=label)
    plotted_categories += 1

# Finalize plot
plt.title("Söguleg þróun byggingarvísitölu (síðustu 60 mánuðir)")
plt.xlabel("Tímabil (YYYYMmm)")
plt.ylabel("Vísitala")
plt.xticks(ticks=range(0, len(months), 12), labels=months[::12], rotation=45)
plt.grid(True, axis='y')
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.tight_layout()
plt.show()

if plotted_categories == 0:
    print("Engin gögn fundust til að birta línurit.")
