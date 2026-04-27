# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
Clean reviewer names appended at the end of the 'text' column in CSV files.

PATTERN: Flipkart reviewers' names appear at the very END of the review text,
space-separated with no punctuation. Examples:
  "Good design danish pasha"
  "Value for money sarath kumar"
  "Fell in love with the colour sai kumar"
  "Awesome product ashwin roy"

CONSERVATIVE APPROACH (avoids over-stripping):
  Strip only if the last 2 tokens satisfy ALL of:
    1. Both are alphabetic-only lowercase words (2-20 chars each)
    2. Neither word is in a large English dictionary blocklist
    3. The word just BEFORE the 2-token block either:
       a. ends with punctuation (.,!?:;), OR
       b. is itself a non-name token (content word)
    This way "Value for money sarath kumar" -> strips "sarath kumar"
    because "money" is a content word preceding the name block.
  
  We also handle 3-word names (e.g., "amit kumar singh") but require
  that the word before the 3-token block ends with punctuation.
"""

import pandas as pd
import re
import os
import shutil

# ── File paths ───────────────────────────────────────────────────────────────
FILES = [
    r"c:\Users\Simmon\Desktop\p3\ai_prediction_system_yash\2_dataset_final_folder\iphone15.csv",
    r"c:\Users\Simmon\Desktop\p3\ai_prediction_system_yash\2_dataset_final_folder\iphone16.csv",
    r"c:\Users\Simmon\Desktop\p3\ai_prediction_system_yash\2_dataset_final_folder\iqoo_z10.csv",
]

TEXT_COL = "text"

# ── Large English word set (any word here = NOT a name token) ─────────────────
# Built from common English words that could appear at end of a review sentence.
# The broader this is, the fewer false positives we get.
ENGLISH = {
    # function words
    "a","an","the","of","in","on","at","to","for","with","by","as","from",
    "is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might",
    "shall","can","and","or","but","not","so","yet","nor","both",
    "either","neither","than","that","this","these","those","which",
    "who","what","when","where","why","how","if","because","although",
    "though","while","after","before","since","until","unless","also",
    "too","very","just","only","even","still","already","again",
    "always","never","often","sometimes","here","there","up","down",
    "out","about","over","under","between","through","during","without",
    # pronouns
    "i","me","my","myself","we","us","our","you","your",
    "he","him","his","she","her","it","its","they","them","their",
    # common review vocabulary — adjectives
    "good","great","best","bad","poor","nice","fine","well","super",
    "amazing","awesome","excellent","perfect","brilliant","terrible",
    "horrible","worst","better","worse","okay","ok","beautiful",
    "elegant","stylish","sleek","thin","thick","wide","narrow",
    "small","large","big","huge","medium","mini","light","heavy",
    "smooth","fast","slow","clean","crisp","sharp","clear","bright",
    "dark","loud","quiet","strong","weak","cool","hot","warm","cold",
    "solid","soft","hard","premium","budget","basic","simple","complex",
    "advanced","modern","classic","traditional","innovative","creative",
    "genuine","original","authentic","fake","normal","regular","special",
    "standard","latest","new","old","first","last","next","same",
    "different","similar","equal","unique","common","rare","average",
    "ordinary","impressive","outstanding","remarkable","stunning",
    "unbelievable","incredible","fantastic","fabulous","wonderful",
    "disappointing","satisfied","happy","unhappy","glad","sad",
    "excited","worried","confused","surprised","shocked","upset",
    "pleased","annoyed","frustrated","angry","calm","relaxed",
    "impressed","dissatisfied","disappointed","disappointed",
    # common review vocabulary — nouns
    "phone","mobile","camera","battery","display","screen","product",
    "device","model","charger","box","package","packing","packaging",
    "quality","price","money","value","cost","rate","rating","review",
    "star","stars","point","points","performance","speed","design",
    "color","colour","size","weight","build","feature","features",
    "app","software","update","hardware","processor","chipset","chip",
    "ram","storage","memory","gb","tb","mb","battery","charging",
    "speaker","speakers","sound","audio","music","video","photo","pic",
    "image","camera","lens","zoom","portrait","mode","night","ai",
    "display","screen","refresh","rate","resolution","brightness",
    "signal","network","wifi","bluetooth","nfc","sim","call","calls",
    "data","internet","connectivity","reception","coverage",
    "fingerprint","face","touch","sensor","button","usb","port",
    "delivery","seller","buyer","service","support","warranty",
    "return","replace","replacement","refund","exchange","repair",
    "purchase","bought","buying","sell","sold","selling","order",
    "experience","upgrade","downgrade","switch","switching","compare",
    "comparison","advantage","disadvantage","weakness","strength",
    "issue","problem","bug","glitch","crash","error","fix","solve",
    "update","patch","version","ui","interface","settings","option",
    "choice","decision","reason","purpose","condition","damage",
    "scratch","seal","pack","open","close","box","bag","case","cover",
    "deal","offer","sale","discount","cashback","emi","bank","offer",
    # adverbs
    "definitely","certainly","probably","possibly","likely","unlikely",
    "unfortunately","fortunately","luckily","sadly","honestly",
    "seriously","absolutely","completely","totally","exactly",
    "truly","clearly","simply","mostly","nearly","almost","quite",
    "anyway","however","therefore","moreover","besides","meanwhile",
    "suddenly","immediately","eventually","finally","initially",
    "currently","recently","already","still","yet","again","always",
    "never","often","sometimes","usually","generally","typically",
    "basically","essentially","primarily","mainly","mostly",
    "especially","particularly","specifically","generally",
    "incredibly","extremely","highly","strongly","deeply","truly",
    "really","actually","overall","totally","purely","largely",
    # verbs (base, past, present)
    "take","takes","taken","give","given","come","came","look","looks",
    "feel","feels","seem","seems","think","thought","know","want",
    "use","used","using","need","get","got","go","went","see","saw",
    "say","said","make","made","work","works","working","run","runs",
    "charge","charges","support","show","shows","buy","bought","sell",
    "sold","love","loved","like","liked","hate","hated","miss","want",
    "try","tried","read","write","play","watch","listen","call",
    "recommend","suggest","expect","hope","wish","believe","think",
    "found","find","check","test","tested","compare","switch","turn",
    "start","stop","open","close","send","receive","connect","set",
    # numbers (written out)
    "zero","one","two","three","four","five","six","seven","eight",
    "nine","ten","hundred","thousand","lakh","crore",
    # time
    "day","days","month","months","week","weeks","year","years",
    "hour","hours","minute","minutes","second","seconds",
    "morning","afternoon","evening","night","today","yesterday",
    "tomorrow","now","then","ago","since","during","before","after",
    # brands / platforms
    "apple","iphone","samsung","pixel","google","oneplus","motorola",
    "realme","redmi","xiaomi","oppo","vivo","nokia","iqoo","poco",
    "flipkart","amazon","meesho","myntra","snapdeal",
    # miscellaneous
    "thanks","thank","please","yes","no","ok","okay","wow","oh","ah",
    "well","right","wrong","true","false","real","fake","safe","secure",
    "promise","safety","trust","trusted","reliable","genuine",
    "fast","processor","usage","regular","useful","useless","usage",
    "steal","absolute","placement","felt","deal","details","clarity",
    "option","advantage","detail","zero","offer","sale","paid","pay",
    "condition","damage","scratch","return","repair","service",
    "warranty","reason","purpose","choice","decision","strength",
    "weakness","comparison","compare","upgrade","downgrade",
    "satisfied","excited","worried","surprised","annoyed",
    "processor","chipset","flagship","midrange","budget","lineup",
    # short noise tokens that could look like names
    "sk","jr","sr","mr","mrs","ms","dr","prof",
}

# ── Regex: a name-like token ─────────────────────────────────────────────────
# All lowercase, letters only, length 2-20
NAME_RE = re.compile(r'^[a-z]{2,20}$')

def is_name_token(word: str) -> bool:
    w = word.lower().strip(".,!?;:'\"()-")
    return bool(NAME_RE.match(w)) and w not in ENGLISH

def ends_with_punct(token: str) -> bool:
    """True if token ends with sentence-ending punctuation."""
    return bool(re.search(r'[.!?;,:]$', token))

def strip_trailing_name(text: str) -> str:
    """
    Strip a 2–3 word reviewer name from the end of text.
    Conservative: only strips when confident it's a name.
    """
    if not isinstance(text, str):
        return text

    text = text.strip()

    # Don't touch truncated reviews
    if text.endswith('...'):
        return text

    tokens = text.split()
    n = len(tokens)

    if n < 4:
        return text  # too short, risky

    # ── Try 3-token name block first (e.g. "amit kumar singh") ──────────────
    if n >= 5:
        t1, t2, t3 = tokens[-3], tokens[-2], tokens[-1]
        if is_name_token(t1) and is_name_token(t2) and is_name_token(t3):
            # Require the token before the 3-block to end with punctuation
            prev = tokens[n - 4]
            if ends_with_punct(prev):
                cleaned = ' '.join(tokens[:n-3]).rstrip(' .,!?;:')
                return cleaned if cleaned else text

    # ── Try 2-token name block (e.g. "danish pasha", "sarath kumar") ────────
    if n >= 4:
        t1, t2 = tokens[-2], tokens[-1]
        if is_name_token(t1) and is_name_token(t2):
            # The word before the name block should be a content word OR end in punct
            prev = tokens[n - 3]
            prev_clean = prev.lower().strip(".,!?;:'\"()-")
            if ends_with_punct(prev) or prev_clean in ENGLISH:
                cleaned = ' '.join(tokens[:n-2]).rstrip(' .,!?;:')
                return cleaned if cleaned else text

    return text


def restore_from_backup(filepath: str):
    backup = filepath.replace('.csv', '_before_name_clean.csv')
    if os.path.exists(backup):
        shutil.copy2(backup, filepath)
        print(f"  Restored from backup.")
    # else first run — no backup yet


def clean_csv(filepath: str):
    print(f"\n{'='*60}")
    print(f"Processing: {os.path.basename(filepath)}")

    restore_from_backup(filepath)
    df = pd.read_csv(filepath)

    if TEXT_COL not in df.columns:
        print(f"  Column '{TEXT_COL}' not found -- skipping.")
        return

    original = df[TEXT_COL].copy()
    df[TEXT_COL] = df[TEXT_COL].apply(strip_trailing_name)

    changed = (original != df[TEXT_COL]).sum()
    print(f"  Rows modified: {changed} / {len(df)}")

    mask = original != df[TEXT_COL]
    for idx in df[mask].head(10).index:
        print(f"    BEFORE: {original[idx]!r}")
        print(f"    AFTER : {df.at[idx, TEXT_COL]!r}")
        print()

    backup = filepath.replace('.csv', '_before_name_clean.csv')
    shutil.copy2(filepath, backup)
    print(f"  Backup saved: {os.path.basename(backup)}")
    df.to_csv(filepath, index=False)
    print(f"  Saved.")


if __name__ == "__main__":
    for f in FILES:
        if os.path.exists(f):
            clean_csv(f)
        else:
            print(f"File not found: {f}")
    print("\nAll done!")
