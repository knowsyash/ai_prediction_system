# Dataset & Preprocessing

## Dataset Overview & Size
* Raw customer reviews scraped from e-commerce platforms (Flipkart) using automated Python scripts.
* Collected incrementally with request throttling and User-Agent rotation to ensure robust data extraction.
* **Dataset Volumes (4 columns each: rating, text, name, date):**
  * **iPhone 15:** ~3,315 reviews
  * **iPhone 16:** ~719 reviews
  * **iQOO Z10:** ~46 reviews

## Useful Columns Extracted
* **rating** - The star rating given by the user (1-5 stars)
* **text** - The full text of the customer review
* **name** - The name of the reviewer (collected initially for integrity, cleaned later)
* **date** - The date the review was posted (critical for time-series forecasting)

## Preprocessing Pipeline (2_dataset_final_folder)
* **Automated Name Removal:** Used deep NLP dictionary checks (`clean_names.py`) to systematically remove reviewer names from the end of unstructured text, isolating pure feedback.
* **Data Formatting:** Standardized the CSV files, removing corrupted records and preparing clean textual inputs (`iphone15.csv`, `iphone16.csv`, `iqoo_z10.csv`) for the sentiment analysis models.