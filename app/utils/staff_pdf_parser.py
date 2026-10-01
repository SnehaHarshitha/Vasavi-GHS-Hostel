import io
import re
import pdfplumber
import pypdf

KNOWN_STAFF_ROLES = {'Caretaker', 'Electrician', 'Plumber', 'Carpenter', 'Cook', 'Helper', 'Cleaner', 'Security Guard', 'Warden Assistant', 'Maintenance Staff'}

def extract_staff_from_pdf(pdf_bytes):
    """
    Extracts staff records from any given PDF byte stream.
    Supports table rows, standard staff IDs, codes, serial numbers, and names.
    Returns list of parsed dicts:
    staff_id, full_name, phone, job_role, department, shift, status, category
    """
    if not pdf_bytes:
        raise ValueError("Uploaded file is empty.")

    extracted_records = []
    seen_keys = set()
    counter = 101

    # 1. Try pdfplumber table extraction first
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    for row in table:
                        parsed, counter = parse_staff_tokens(row, counter)
                        if parsed:
                            key = parsed['full_name'].lower()
                            if key not in seen_keys:
                                seen_keys.add(key)
                                extracted_records.append(parsed)
    except Exception:
        pass

    # 2. Try text line extraction using pypdf & pdfplumber text lines
    if not extracted_records:
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split('\n'):
                    parsed, counter = parse_staff_tokens(line, counter)
                    if parsed:
                        key = parsed['full_name'].lower()
                        if key not in seen_keys:
                            seen_keys.add(key)
                            extracted_records.append(parsed)
        except Exception:
            pass

    return extracted_records


def parse_staff_tokens(tokens, auto_id_counter=101):
    if not tokens:
        return None, auto_id_counter

    raw_parts = []
    if isinstance(tokens, str):
        raw_parts = [tokens]
    elif isinstance(tokens, (list, tuple)):
        raw_parts = [str(t) for t in tokens if t is not None]
    else:
        raw_parts = [str(tokens)]

    full_str = " ".join(raw_parts).strip()
    if not full_str or len(full_str) < 3:
        return None, auto_id_counter

    lower_text = full_str.lower()
    # Ignore title / header rows
    if any(h in lower_text for h in ['sri vasavi', 'pedatadepalli', 'attendance register', 'name of the student', 's.no.', 'sl.no', 'roll no', 'year & branch', 'department', 'page ']):
        return None, auto_id_counter

    # 1. Extract Phone Number
    phone_match = re.search(r'\b(\+?91[\s-]?)?([6-9]\d{9})\b', full_str)
    phone = phone_match.group(2) if phone_match else ''

    # 2. Extract Staff ID / Code
    staff_id = ''
    id_match = re.search(r'\b([A-Z]{2,4}\d{2,5})\b', full_str, re.IGNORECASE)
    if not id_match:
        id_match = re.search(r'\b(ID[-_\s]?\d{3,5})\b', full_str, re.IGNORECASE)
    if not id_match:
        id_match = re.search(r'\b(\d{2}-[A-Z0-9]{3,6})\b', full_str, re.IGNORECASE)
    
    if id_match:
        staff_id = id_match.group(1).upper()
    else:
        staff_id = f"STF{auto_id_counter}"
        auto_id_counter += 1

    # 3. Category & Job Role
    category = 'Working Staff'
    job_role = 'Maintenance Staff'
    if 'caretaker' in lower_text or staff_id.startswith('CT') or 'lakshmi' in lower_text:
        category = 'Caretaker'
        job_role = 'Hostel Caretaker'
    else:
        for r in KNOWN_STAFF_ROLES:
            if re.search(r'\b' + r + r'\b', full_str, re.IGNORECASE):
                job_role = r
                break

    # 4. Shift
    shift = 'Morning'
    if 'evening' in lower_text:
        shift = 'Evening'
    elif 'night' in lower_text:
        shift = 'Night'

    # 5. Extract Full Name
    # Remove numbers at start (e.g. S.No "1 "), codes at end, room numbers, branches
    cleaned_line = re.sub(r'^\d+[\s.]+', '', full_str) # Strip leading serial number
    cleaned_line = re.sub(r'\b\d{2}-[A-Z0-9]{3,6}\b', '', cleaned_line, flags=re.IGNORECASE) # Strip code
    cleaned_line = re.sub(r'\b(CSE|ECE|IT|EEE|CIVIL|MECH|CSD|AIM|ECT|CAI|DS)\b', '', cleaned_line, flags=re.IGNORECASE) # Strip branch
    cleaned_line = re.sub(r'\b\d{1,3}\b', '', cleaned_line) # Strip standalone room numbers

    words = re.split(r'[\s|,\t]+', cleaned_line)
    name_parts = []
    for w in words:
        w_clean = w.strip()
        w_upper = w_clean.upper()
        if not w_clean:
            continue
        if w_upper == staff_id:
            continue
        if phone and phone in w_clean:
            continue
        if w_upper in {'CT', 'WS', 'STF', 'CARETAKER', 'MORNING', 'EVENING', 'NIGHT', 'ACTIVE', 'INACTIVE', 'STAFF', 'OPERATIONS', 'HOSTEL'}:
            continue
        if re.search(r'[a-zA-Z]', w_clean):
            name_parts.append(w_clean)

    full_name = " ".join(name_parts).strip()
    if not full_name or len(full_name) < 2:
        return None, auto_id_counter

    return {
        'staff_id': staff_id,
        'full_name': full_name,
        'phone': phone or '+91 98480 00000',
        'job_role': job_role,
        'department': 'Hostel Operations',
        'shift': shift,
        'status': 'Active',
        'category': category
    }, auto_id_counter
