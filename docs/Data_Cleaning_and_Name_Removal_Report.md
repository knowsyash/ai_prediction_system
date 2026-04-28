
# In-Depth Report: Data Cleaning and Name Removal Strategy

**Version 2.0 - Last Updated: 2026-04-28**

## 1. The Critical Role of Data Cleaning in Sentiment Analysis

In any data science pipeline, particularly within the realm of Natural Language Processing (NLP) and sentiment analysis, the quality of the input data directly and profoundly impacts the quality of the output. The principle of "Garbage In, Garbage Out" (GIGO) is especially pertinent here. Raw, unstructured text data scraped from the web is invariably "dirty," containing a wide array of noise and artifacts that can mislead analytical models.

For our AI Prediction System, which aims to derive market sentiment from customer reviews, the data cleaning phase is arguably one of the most critical steps. The primary goal is to isolate the pure, subjective opinion of the reviewer from all other confounding information. Failure to do so can lead to:

- **Inaccurate Sentiment Scoring:** Models may misinterpret non-opinionated text (like names, locations, or product codes) as having positive, negative, or neutral sentiment.
- **Model Bias:** The presence of specific names or patterns could introduce biases, causing the model to associate certain names with certain sentiments.
- **Reduced Model Performance:** Noise increases the dimensionality and complexity of the data, making it harder for models to identify the true signals of sentiment.
- **Privacy Concerns:** While the names are publicly available on the e-commerce site, it is best practice in data analysis to anonymize or remove personally identifiable information (PII) where it is not essential for the analysis.

This report provides a deep dive into the specific data cleaning challenge encountered in our dataset—appended reviewer names—and the sophisticated, rule-based approach developed in the `clean_names.py` script to address it.

---

## 2. The Problem: Identifying Appended Reviewer Names

**Source Folder:** `2_dataset_final_folder/`

Upon initial inspection of the raw data scraped from Flipkart, a consistent and problematic pattern emerged: a significant number of reviews had the reviewer's name appended directly to the end of the review text. There was no clear delimiter or metadata field separating the review content from the reviewer's name.

Here are some representative examples of the pattern from `iphone15_before_name_clean.csv`:

- *"Good design and performance is also good **danish pasha**"*
- *"It's a value for money product for sure **sarath kumar**"*
- *"Just go for it.Amazing one.Beautiful camera with super fast processor **bijaya mohanty**"*
- *"best camera and battery is also very good In love with dynamic Island Type-c charging is very fast. Overall best phone **AYUSH singh**"*

This presents a non-trivial cleaning challenge. A naive approach, such as simply removing the last two words of every review, would be catastrophic. It would incorrectly truncate countless legitimate reviews, such as:

- *"The battery life is **very good**."*
- *"I would not recommend **this phone**."*
- *"The camera is the **best part**."*

Therefore, a more intelligent and context-aware solution was required. The `clean_names.py` script was engineered to be this solution, employing a conservative, heuristic-based algorithm to precisely identify and remove only the appended names, leaving the actual review text intact.

---

## 3. The Solution: A Deep Dive into `clean_names.py`

The `clean_names.py` script implements a multi-layered filtering strategy. It decides to strip trailing words only if they satisfy a strict set of cumulative conditions. This conservative approach is designed to minimize "false positives" (i.e., incorrectly removing parts of a valid review). The core philosophy is that it is better to leave a few names in the dataset than to risk corrupting the review content itself.

Let's break down the methodology step-by-step.

### 3.1. The Core Heuristic: Analyzing Word Tokens

The script processes each review by tokenizing it (splitting it into a list of words). It then focuses its analysis on the last two or three tokens, as these are the most likely candidates for a reviewer's name.

The algorithm checks for both two-word names (e.g., "ashwin roy") and three-word names (e.g., "amit kumar singh"), but applies slightly different rules for each to maintain its conservative stance.

### 3.2. Filter 1: The `ENGLISH` Word Blocklist

The most powerful tool in the script's arsenal is a large, pre-compiled set of common English words, named `ENGLISH`. This set contains over 200 common adjectives, nouns, pronouns, and function words that are frequently used in reviews.

**Purpose:** This set acts as a "negative dictionary" for names. The fundamental assumption is that a person's name is highly unlikely to be a common English word like "phone," "good," "very," or "the."

**Implementation:** Before the script considers a trailing word as part of a potential name, it first checks if that word exists in the `ENGLISH` set.

- `if token in ENGLISH:` -> The token is a common word, **not a name**. The script immediately stops considering it a name candidate.
- `if token not in ENGLISH:` -> The token is not a common word, so it **could be part of a name**. The script proceeds to the next filter.

This single check is incredibly effective at preventing the algorithm from stripping legitimate review endings. For example, in "The battery life is very good," both "very" and "good" are in the `ENGLISH` set, so the script will not touch them.

### 3.3. Filter 2: Word Characteristics (Alphabetic and Length)

If a token passes the `ENGLISH` blocklist filter, the script then examines its basic characteristics. It checks if the token:
1.  Consists purely of alphabetic characters (`token.isalpha()`).
2.  Has a reasonable length for a name component (between 2 and 20 characters).

This filter helps discard tokens that are clearly not names, such as:
- **Numbers:** "Model 5"
- **Punctuation:** "!"
- **Product Codes:** "XR500"
- **Single letters or typos:** "a"

### 3.4. Filter 3: Contextual Analysis - The Preceding Word

This is a crucial step that adds contextual awareness. The script doesn't just look at the potential name tokens; it looks at the word *immediately before* them. This helps it understand the grammatical context to differentiate between the end of a sentence and an appended name.

The logic is as follows:

- **For a 2-word name candidate (e.g., "sarath kumar"):** The script will strip the name if the word just before it ("money" in "Value for money sarath kumar") is a content word (i.e., it is also in the `ENGLISH` set). This indicates that the review's main content flowed right up to the name.
- **For a 3-word name candidate (e.g., "amit kumar singh"):** The rule is stricter. The script will only strip the name if the word just before it ends with punctuation (e.g., a period, question mark, or exclamation mark). This is a very strong signal that the sentence has concluded and the following words are metadata.

This dual-pronged contextual check is vital for accuracy. It allows the script to be more lenient with two-word names (which are more common) while being more cautious with three-word names.

### 3.5. The Final Algorithm: Putting It All Together

Here is the complete, logical flow for processing a single review:

1.  **Tokenize:** The review text is cleaned (converted to lowercase, extra spaces removed) and split into a list of word tokens.
2.  **Check for 3-Word Name:**
    a. Are there at least 4 tokens in the review?
    b. Do the last three tokens pass the `ENGLISH` blocklist and word characteristic filters?
    c. Does the fourth-to-last token end with punctuation?
    d. **If all are true:** The last three words are removed, and the process is complete for this review.
3.  **Check for 2-Word Name (if 3-word name was not found):**
    a. Are there at least 3 tokens in the review?
    b. Do the last two tokens pass the `ENGLISH` blocklist and word characteristic filters?
    c. Does the third-to-last token pass the `ENGLISH` blocklist filter (i.e., is it a content word)?
    d. **If all are true:** The last two words are removed.
4.  **No Name Found:** If neither of the above conditions is met, the review text is left unchanged.

This methodical, filter-based process ensures that the cleaning is both precise and safe, preserving the integrity of the vast majority of the data while effectively removing the targeted noise.

---

## 4. Proven Results: Before-and-After Examples

To demonstrate the script's effectiveness and precision, let's examine concrete examples by comparing the `iphone15_before_name_clean.csv` and `iphone15.csv` files.

### Example 1: Standard Two-Word Name Removal
- **Before:** `"Just go for it.Amazing one.Beautiful camera with super fast processor bijaya mohanty"`
- **After:** `"Just go for it.Amazing one.Beautiful camera with super fast processor"`
- **Analysis:** The script correctly identified that "bijaya" and "mohanty" are not in the `ENGLISH` blocklist and that the preceding word "processor" is a common noun. It successfully stripped the name.

### Example 2: Name Following a Complete Sentence
- **Before:** `"best camera and battery is also very good In love with dynamic Island Type-c charging is very fast. Overall best phone AYUSH singh"`
- **After:** `"best camera and battery is also very good In love with dynamic Island Type-c charging is very fast. Overall best phone"`
- **Analysis:** Similar to the first example, "ayush" and "singh" were identified as non-English content words, and the preceding word "phone" triggered the removal.

### Example 3: Handling Repetitive/Erroneous Names
- **Before:** `"Nice phone good VinodKUMAR VinodKUMAR"`
- **After:** `"Nice phone good"`
- **Analysis:** The script's tokenization and filtering logic were robust enough to handle this unusual, repeated name format and correctly remove the noise.

### Example 4: Demonstrating the Conservative Approach
- **Before:** `"High quality camera Ajin V"`
- **After:** `"High quality camera Ajin V"`
- **Analysis:** This is a critical example of the script's safety-first design. The name was **not** removed. This is because the token "V" has a length of 1, failing the `len(token) >= 2` check. The script conservatively assumes a single letter is more likely to be part of the review (e.g., a typo or initial) than a name. This prevents incorrect data removal and proves the value of the multi-filter approach.

---

## 5. Output and Impact

The execution of the `clean_names.py` script results in the creation of the final, cleaned datasets used by all downstream processes:

- `iphone15.csv`
- `iphone16.csv`
- `iqoo_z10.csv`

By removing the appended names, the `text` column in these files is now a much cleaner representation of customer sentiment. This directly leads to:

- **More Accurate Sentiment Models:** The sentiment analysis models (VADER, BERT) can now operate on text that is almost entirely composed of the reviewer's opinion.
- **Better Feature Extraction:** For models like the Word Cloud proxy, TF-IDF scores are more meaningful as they are not skewed by the frequency of common names.
- **Reliable Predictive Insights:** The entire predictive pipeline, from ensemble analysis to next-month forecasting, is built upon this clean foundation, making the final predictions more trustworthy and robust.

In conclusion, the thoughtful and detailed approach to data cleaning, exemplified by the `clean_names.py` script, is a cornerstone of this project's success. The concrete examples above provide definitive proof of its ability to handle real-world, messy data with both precision and caution.

