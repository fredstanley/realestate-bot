from pdf_report import generate_pdf
import os

comps = [
    {
        "address": "123 Main St",
        "price": 1000000,
        "date": "2023-01-01",
        "sqft": 2000,
        "beds": 3,
        "baths": 2,
        "distance": 0.5
    },
    {
        "address": "456 Oak Ave",
        "price": 950000,
        "date": "2023-02-15",
        "sqft": 1800,
        "beds": 3,
        "baths": 2,
        "distance": 0.3
    }
]

arv_text = """
# ARV Analysis
Based on the comps, the property is valued at **$1,100,000**.
The market is trending upwards – significantly. 
Here are some "quotes" and a ‘smart quote’.
- Point 1
- Point 2
* Point 3
"""

pdf_bytes = generate_pdf(arv_text, comps, "789 Pine Ln")
print(f"Type of pdf_bytes: {type(pdf_bytes)}")

with open("test_report.pdf", "wb") as f:
    f.write(pdf_bytes)

if os.path.exists("test_report.pdf") and os.path.getsize("test_report.pdf") > 0:
    print("SUCCESS: PDF created.")
else:
    print("FAILURE: PDF not created.")
