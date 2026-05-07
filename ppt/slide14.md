# Priority Scoring System

* **Detected Issue:** Battery Performance (Rapid Draining/Heating)

## Priority Formula
* Priority = (Frequency &times; 0.4) + (|Impact| &times; 20 &times; 0.4) + (Trend &times; 0.2)

## Input Values
* **Frequency = 30%** (issue appears in many negative reviews)
* **Impact = -0.8 stars** (reduces average predicted rating significantly)
* **Trend = Increasing (1)** (recent reviews show a spike in complaints)

## Calculation
* Priority = (30 &times; 0.4) + (0.8 &times; 20 &times; 0.4) + (1 &times; 0.2)
* Priority = 12 + 6.4 + 0.2
* **Priority = 18.6**

## Final Result
* **Priority Level: HIGH**
* **Action:** Battery optimization and thermal management should be fixed first in the next software update.