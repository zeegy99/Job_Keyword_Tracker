import re

SWE_PATTERNS = [
    re.compile(r'\bsoftware\s+engineer', re.IGNORECASE),
    re.compile(r'\bswe\b', re.IGNORECASE),
    re.compile(r'\bsoftware\s+developer', re.IGNORECASE),
    re.compile(r'\bfull[\s-]?stack\s+engineer', re.IGNORECASE),
    re.compile(r'\bbackend\s+engineer', re.IGNORECASE),
    re.compile(r'\bfrontend\s+engineer', re.IGNORECASE),
]

def is_swe_title(title: str) -> bool:
    return any(pattern.search(title) for pattern in SWE_PATTERNS)

test_titles = [
    "Software Engineer, Frontend",
    "Software Engineer II - Backend",
    "Senior Software Engineer",
    "SWE Intern - Summer 2027",
    "Full-Stack Software Engineer",
    "Software Engineering Manager",  
    "Field Engineer",                  
    "Sales Engineer",                 
]
for t in test_titles:
    print(f"{is_swe_title(t)!s:5} | {t}")

