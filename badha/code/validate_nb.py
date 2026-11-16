import json, os, re, random, tempfile, sys
nb=json.load(open(sys.argv[1]))
d=tempfile.mkdtemp(); os.chdir(d)
cells=[c["source"] for c in nb["cells"] if c["cell_type"]=="code"]
G={}
exec(cells[0],G); exec(cells[1],G)
def parse_prompt(u):
    msg = re.search(r"debtor country (\w+); currency (\w+)", u); c, cur = msg.group(1), msg.group(2); rules=[]
    for m in re.finditer(r"R\d+ \[(.*?); jurisdiction: (.*?); effective ([\d-]+)(?:; condition: currency is (\w+))?\] (.*?)Charge bearer must be (\w+)\.(.*)", u):
        rules.append(dict(tier={v:k for k,v in G['TIERS'].items()}[m.group(1)],scope=G['COUNTRIES'] if m.group(2)=="all countries" else m.group(2).split(", "),cond=("currency",m.group(4)) if m.group(4) else None,date=m.group(3),value=m.group(6),loud=bool(m.group(5).strip() or m.group(7).strip())))
    return {"country":c,"currency":cur}, rules
rr=random.Random(5)
def swayed(u):
    if "Say it." in u: return "ANSWER: SHAR"
    msg,rules=parse_prompt(u); a=G['oracle'](rules,msg)[0]; loud=[r for r in rules if r['loud']]
    return "ANSWER: "+(loud[0]['value'] if loud and rr.random()<0.2 else a)
G['MODELS']=[{"provider":"mock","model":"mock-a","fn":swayed},{"provider":"mockB","model":"mock-b","fn":swayed},{"provider":"openai","model":"x","key":""}]
G['MODELS'][1]["provider"]="mock"
for c in cells[2:]: exec(c,G)
print(sorted(os.listdir(d)), sorted(os.listdir(os.path.join(d,'badha_run'))))
