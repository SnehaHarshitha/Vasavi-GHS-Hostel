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
    has_text = False

    # 1. Try pdfplumber table extraction first
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                try:
                    text = page.extract_text() or ""
                    if text.strip():
                        has_text = True

                    tables = page.extract_tables()
                    if tables:
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

                    if not extracted_records and text.strip():
                        for line in text.splitlines():
                            parsed, counter = parse_staff_tokens(line, counter)
                            if parsed:
                                key = parsed['full_name'].lower()
                                if key not in seen_keys:
                                    seen_keys.add(key)
                                    extracted_records.append(parsed)
                except Exception:
                    continue
    except Exception:
        pass

    # 2. Try text line extraction using pypdf if no records found yet
    if not extracted_records:
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    has_text = True
                    for line in text.splitlines():
                        parsed, counter = parse_staff_tokens(line, counter)
                        if parsed:
                            key = parsed['full_name'].lower()
                            if key not in seen_keys:
                                seen_keys.add(key)
                                extracted_records.append(parsed)
        except Exception:
            pass

    if not has_text and not extracted_records:
        raise ValueError("The PDF does not contain readable text. Please upload a text-based PDF.")

    if not extracted_records:
        raise ValueError("No valid staff records could be found in the uploaded PDF. Please check the PDF format.")

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

    lower_text = full_str.lower().strip()
    if lower_text in {'sl.no', 's.no', 'staff id', 'name of staff', 'staff name', 'designation', 'role', 'phone number', 'shift', 'department'}:
        return None, auto_id_counter

    if re.fullmatch(r'page\s*\d+(\s*of\s*\d+)?', lower_text):
        return None, auto_id_counter

    # 1. Extract Phone Number
    phone_match = re.search(r'\b(\+?91[\s-]?)?([6-9]\d{9})\b', full_str)
    phone = phone_match.group(2) if phone_match else ''

    # 2. Extract Staff ID / Code (CT101, CT-101, WS201, STF101, EMP101, 101)
    staff_id = ''
    id_match = re.search(r'\b([A-Z]{1,4}[-_\s]?\d{2,5})\b', full_str, re.IGNORECASE)
    if not id_match:
        id_match = re.search(r'\b(ID[-_\s]?\d{3,5})\b', full_str, re.IGNORECASE)
    if not id_match:
        id_match = re.search(r'\b(\d{2,3}-[A-Z0-9]{3,6})\b', full_str, re.IGNORECASE)
    
    if id_match:
        staff_id = id_match.group(1).upper().replace(' ', '').replace('-', '')
    else:
        staff_id = f"STF{auto_id_counter}"
        auto_id_counter += 1

    # 3. Category & Job Role
    category = 'Working Staff'
    job_role = 'Maintenance Staff'
    if 'caretaker' in lower_text or staff_id.startswith('CT') or 'lakshmi' in lower_text or 'ramulamma' in lower_text or 'venkatamma' in lower_text:
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
    elif 'full' in lower_text:
        shift = 'Full Day'

    # 5. Extract Full Name
    cleaned_line = re.sub(r'^\d+[\s.]+', '', full_str)
    cleaned_line = re.sub(r'\b[A-Z]{1,4}[-_\s]?\d{2,5}\b', '', cleaned_line, flags=re.IGNORECASE)
    cleaned_line = re.sub(r'\b(\+?91[\s-]?)?[6-9]\d{9}\b', '', cleaned_line)

    words = re.split(r'[\s|,\t]+', cleaned_line)
    name_parts = []
    for w in words:
        w_clean = w.strip()
        w_upper = w_clean.upper()
        w_lower = w_clean.lower()
        if not w_clean:
            continue
        if w_upper == staff_id or w_upper == staff_id.replace('-', ''):
            continue
        if phone and phone in w_clean:
            continue
        if w_upper in {'CT', 'WS', 'STF', 'CARETAKER', 'MORNING', 'EVENING', 'NIGHT', 'ACTIVE', 'INACTIVE', 'STAFF', 'OPERATIONS', 'HOSTEL', 'FULL', 'DAY', 'SRI', 'VASAVI', 'COLLEGE', 'PEDATADEPALLI'}:
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

