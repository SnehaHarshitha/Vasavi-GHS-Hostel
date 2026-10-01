import io
import re
import pdfplumber
import pypdf

KNOWN_DEPARTMENTS = {'CSE', 'ECE', 'IT', 'EEE', 'MECH', 'CIVIL', 'AIML', 'DS', 'CS', 'AI'}

def parse_student_row(tokens):
    """
    Given a list or string of tokens representing a student record line/row,
    extract roll_number, full_name, email, department, semester.
    """
    if not tokens:
        return None

    # Standardize tokens into a flat text string
    raw_parts = []
    if isinstance(tokens, str):
        raw_parts = [tokens]
    elif isinstance(tokens, (list, tuple)):
        raw_parts = [str(t) for t in tokens if t is not None]
    else:
        raw_parts = [str(tokens)]

    full_str = " ".join(raw_parts).strip()
    if not full_str:
        return None

    # Ignore header/footer lines
    lower_text = full_str.lower()
    if any(h in lower_text for h in ['roll number', 'student name', 'full name', 'email address', 'department', 'semester', 's.no', 'sl.no', 'page ', 'college']):
        return None

    # 1. Extract Roll Number
    roll_number = ""
    roll_match = re.search(r'\b([0-9]{2}[A-Z0-9]{8,10})\b', full_str, re.IGNORECASE)
    if not roll_match:
        roll_match = re.search(r'\b([A-Z0-9]{8,12})\b', full_str, re.IGNORECASE)
    if roll_match:
        roll_number = roll_match.group(1).upper()

    # 2. Extract Email
    email = ""
    email_match = re.search(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', full_str)
    if email_match:
        email = email_match.group(1).lower()

    # 3. Extract Department
    department = "CSE"
    for dept in KNOWN_DEPARTMENTS:
        if re.search(r'\b' + dept + r'\b', full_str, re.IGNORECASE):
            department = dept
            break

    # 4. Extract Semester
    semester = "5"
    sem_match = re.search(r'\b(?:sem(?:ester)?\s*)?([1-8])\b', full_str, re.IGNORECASE)
    if sem_match:
        semester = sem_match.group(1)

    # 5. Extract Full Name
    words = re.split(r'[\s|,\t]+', full_str)
    name_parts = []
    for w in words:
        w_clean = w.strip()
        w_upper = w_clean.upper()
        w_lower = w_clean.lower()

        if not w_clean:
            continue
        if roll_number and w_upper == roll_number:
            continue
        if email and w_lower == email:
            continue
        if w_upper in KNOWN_DEPARTMENTS:
            continue
        if re.fullmatch(r'[1-8]|sem\s*[1-8]|semester\s*[1-8]', w_clean, re.IGNORECASE):
            continue
        if re.fullmatch(r'\d+', w_clean):
            continue
        if w_lower in {'s.no', 'sl.no', 'no.', 'roll', 'name', 'email', 'dept', 'sem', 'branch', 'status'}:
            continue
        if re.search(r'[a-zA-Z]', w_clean) and not w_lower.startswith('http'):
            name_parts.append(w_clean)

    full_name = " ".join(name_parts).strip()

    if not roll_number and not full_name:
        return None

    return {
        'roll_number': roll_number,
        'full_name': full_name,
        'email': email or (f"{roll_number.lower()}@srivasaviengg.ac.in" if roll_number else ""),
        'department': department,
        'semester': semester
    }


def find_column_indices(header_row):
    col_map = {}
    for i, cell in enumerate(header_row):
        if not cell:
            continue
        c_lower = str(cell).lower().replace('\n', ' ')
        if 'name' in c_lower or 'student' in c_lower:
            col_map['name'] = i
        elif 'roll' in c_lower or 'reg' in c_lower or 'id' in c_lower:
            col_map['roll'] = i
        elif 'room' in c_lower:
            col_map['room'] = i
        elif 'branch' in c_lower or 'dept' in c_lower or 'department' in c_lower:
            col_map['dept'] = i
        elif 'email' in c_lower:
            col_map['email'] = i
    return col_map


def extract_students_from_pdf(file_stream_or_bytes):
    """
    Extracts student records from a PDF file in-memory.
    Returns a list of extracted student dictionaries.
    Raises ValueError if PDF is invalid or contains no readable text.
    """
    if isinstance(file_stream_or_bytes, bytes):
        pdf_bytes = file_stream_or_bytes
    else:
        pdf_bytes = file_stream_or_bytes.read()

    if not pdf_bytes:
        raise ValueError("Uploaded file is empty.")

    students = []
    has_text = False

    # Attempt 1: pdfplumber (table + text extraction)
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    has_text = True

                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if not table:
                            continue

                        # Check if first row is a header
                        header_row = table[0]
                        col_map = find_column_indices(header_row)

                        start_idx = 1 if ('name' in col_map or 'roll' in col_map) else 0

                        for row in table[start_idx:]:
                            if not row:
                                continue

                            if col_map and ('name' in col_map or 'roll' in col_map):
                                name = str(row[col_map['name']]).strip() if 'name' in col_map and col_map['name'] < len(row) and row[col_map['name']] else ""
                                roll = str(row[col_map['roll']]).strip().upper() if 'roll' in col_map and col_map['roll'] < len(row) and row[col_map['roll']] else ""
                                room = str(row[col_map['room']]).strip() if 'room' in col_map and col_map['room'] < len(row) and row[col_map['room']] else "101"
                                dept_raw = str(row[col_map['dept']]).strip() if 'dept' in col_map and col_map['dept'] < len(row) and row[col_map['dept']] else "CSE"
                                email_raw = str(row[col_map['email']]).strip().lower() if 'email' in col_map and col_map['email'] < len(row) and row[col_map['email']] else ""

                                # Clean name (remove newlines, extra spaces)
                                name = re.sub(r'\s+', ' ', name).strip()
                                dept = dept_raw.upper().replace('\n', '') if dept_raw else "CSE"

                                # Extract branch if dept contains multi-word text
                                for k_dept in KNOWN_DEPARTMENTS:
                                    if k_dept in dept:
                                        dept = k_dept
                                        break

                                # Skip headers repeating inside table
                                if name.lower() in ['name of the student', 'student name', 'full name', 'name'] or roll.lower() in ['roll no.', 'roll no', 'roll number']:
                                    continue

                                if name or roll:
                                    # Standardize roll number if empty or short
                                    if not roll and name:
                                        roll = re.sub(r'[^A-Za-z0-9]', '', name).upper()[:10]
                                    
                                    clean_email = email_raw if '@' in email_raw else f"{roll.lower().replace('-', '')}@srivasaviengg.ac.in"

                                    students.append({
                                        'roll_number': roll,
                                        'full_name': name,
                                        'email': clean_email,
                                        'department': dept or 'CSE',
                                        'semester': '5',
                                        'room_number': room or '101'
                                    })
                            else:
                                # Fallback row parsing
                                s_dict = parse_student_row(row)
                                if s_dict and (s_dict.get('roll_number') or s_dict.get('full_name')):
                                    students.append(s_dict)

                # Attempt 1b: Fallback to text line extraction if no table rows found
                if not students and text.strip():
                    lines = text.splitlines()
                    for line in lines:
                        s_dict = parse_student_row(line)
                        if s_dict and (s_dict.get('roll_number') or s_dict.get('full_name')):
                            students.append(s_dict)
    except Exception:
        pass

    # Fallback to pypdf if no students found yet
    if not students:
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    has_text = True
                    lines = text.splitlines()
                    for line in lines:
                        s_dict = parse_student_row(line)
                        if s_dict and (s_dict.get('roll_number') or s_dict.get('full_name')):
                            students.append(s_dict)
        except Exception as ex:
            raise ValueError(f"Unable to process PDF: {str(ex)}")

    if not has_text:
        raise ValueError("The PDF does not contain readable text. Please upload a text-based PDF.")

    # Deduplicate students in the same PDF by roll_number or full_name
    unique_students = []
    seen_keys = set()
    for s in students:
        r_num = s.get('roll_number')
        f_name = s.get('full_name')
        key = r_num or f_name
        if key and key not in seen_keys:
            seen_keys.add(key)
            unique_students.append(s)

    return unique_students
