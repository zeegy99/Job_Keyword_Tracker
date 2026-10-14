#For now I will just hard-code what skills I have
from pathlib import Path
import json 

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PATH_TO_MYSKILLS = PROJECT_ROOT / "nlp_sifting" / "my_skills.json"

def matches_my_skills(category, keyword):
    with open(PATH_TO_MYSKILLS, 'r', encoding='utf-8') as f:
        file_content = json.load(f)
        for keyword_i_know in file_content[category]:
            # print("In resume", keyword_i_know)
            if keyword_i_know == keyword:
                return 1
        return 0
        

