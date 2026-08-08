import re
import pdfplumber
from debug_print import debug_print

# Directory where your PDFs were downloaded
PDF_DIR = "./LN2025_10.pdf"
OUTPUT_CSV = "detention_orders_extracted.csv"

def extract_text_from_pdf() -> str:
    debug_print("  └── Extrating text from pdf", 2)
    full_text = []
    try:
        with pdfplumber.open("./detention_order_temp.pdf") as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        
        debug_print("        └── PDF text extracted.", 2)
        return " ".join(full_text)
    except Exception as e:
        debug_print(f"        └── Error reading pdf: {e}.", 2)
        return ""


def clean_pdf_text(raw_text: str) -> str:
    debug_print("  └── Cleaning pdf text", 2)
    # 1. Strip gazette running headers (e.g., Legal Supplement Part B—Vol. 64, No. 188... 1973)
    cleaned = re.sub(r'Legal Supplement Part [A-Z].*?\d{4}(?:\s+\d+)?', '', raw_text, flags=re.IGNORECASE)
    
    # 2. Strip standalone page numbers and header titles
    cleaned = re.sub(r'^\s*\d+\s*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+\s+Detention Order\s*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*Detention Order\s*$', '', cleaned, flags=re.MULTILINE)

    # 3. Collapse newlines and extra spaces into a single space
    debug_print("        └── PDF text cleaned.", 2)
    return " ".join(cleaned.split())

def parse_detention_order(id) -> dict:
    debug_print("Parsing detention order", 1)
    extracted_text = extract_text_from_pdf()
    clean_text = clean_pdf_text(extracted_text)

    # -------------------------------------------------------------
    # 1. EXTRACT DATE
    # -------------------------------------------------------------
    date_pattern = re.compile(
        r"(?:Made|Dated)\s+this\s+(?P<date>\d+(?:st|nd|rd|th)?\s+day\s+of\s+[A-Za-z]+,\s*\d{4})",
        re.IGNORECASE
    )
    date_match = date_pattern.search(clean_text)
    order_date = date_match.group("date") if date_match else None

    # -------------------------------------------------------------
    # 2. EXTRACT JUSTIFICATION / GROUNDS BLOCK
    # -------------------------------------------------------------
    grounds_pattern = re.compile(
        r"TAKE\s+NOTICE\s+that\s+the\s+grounds?\s+upon\s+which\s+this\s+detention\s+order\s+is\s+made\s+(?:is|are)\s+as\s+follows:\s*"
        r"(?P<grounds>.*?)"
        r"(?=(?:A\s+Preventive\s+Detention\s+Order|Made\s+this|Dated\s+this|PRINTED\s+AND\s+PUBLISHED|$))",
        re.IGNORECASE
    )
    grounds_match = grounds_pattern.search(clean_text)
    grounds_text = grounds_match.group("grounds").strip() if grounds_match else None

    # -------------------------------------------------------------
    # 3. EXTRACT NAMES & LOCATIONS BLOCKS
    # Flexible prefix handles "respect to to" typo and missing commas before "that it is necessary"
    # -------------------------------------------------------------
    macro_pattern = re.compile(
        r"(?:am satisfied with respect to(?:\s+to)?|order that the said)\s+"
        r"(?P<names_block>.+?)\s+"
        r"\bof\s+(?P<locations_block>.+?)"
        r"(?:,|\b)\s*(?=that it is necessary|be detained|shall be detained)",
        re.IGNORECASE
    )
    
    names_block, locations_block = None, None
    macro_match = macro_pattern.search(clean_text)
    if macro_match:
        names_block = macro_match.group("names_block")
        locations_block = macro_match.group("locations_block")

    # Parse Names & Aliases
    primary_name, aliases = None, []
    if names_block:
        alias_delim = re.compile(r'\balso\s+(?:known\s+as|called)\b|\ba/?k/?a\b', re.IGNORECASE)
        # Strip straight quotes, curly quotes, and spaces
        raw_names = [n.strip(' "\'“”‘’').strip() for n in alias_delim.split(names_block) if n.strip()]
        primary_name = raw_names[0] if raw_names else None
        aliases = raw_names[1:] if len(raw_names) > 1 else []

    # Parse Locations
    primary_location, secondary_locations = None, []
    if locations_block:
        loc_delim = re.compile(r'\band\s+(?:also\s+)?of\b', re.IGNORECASE)
        raw_locs = [l.strip(' ,').strip() for l in loc_delim.split(locations_block) if l.strip()]
        primary_location = raw_locs[0] if raw_locs else None
        secondary_locations = raw_locs[1:] if len(raw_locs) > 1 else []

    debug_print("  └── Detention order parsed.", 1)
    return {
        "order_date": order_date,
        "order_id": id,
        "primary_name": primary_name,
        "aliases": aliases,
        "primary_location": primary_location,
        "secondary_locations": secondary_locations,
        "justification_grounds": grounds_text
    }