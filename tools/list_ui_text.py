"""Developer inventory of strings for explicit localization review."""
from pathlib import Path
import ast
import json
ROOT=Path(__file__).resolve().parents[1]
def template(node):
    if isinstance(node,ast.Constant) and isinstance(node.value,str):return node.value
    if not isinstance(node,ast.JoinedStr):return None
    chunks=[];count=0
    for value in node.values:
        if isinstance(value,ast.Constant):chunks.append(value.value.replace('{','{{').replace('}','}}'))
        else:
            spec=''
            if value.format_spec:spec=':'+''.join(v.value for v in value.format_spec.values if isinstance(v,ast.Constant))
            conv='!'+chr(value.conversion) if value.conversion!=-1 else ''
            chunks.append('{p'+str(count)+conv+spec+'}');count+=1
    return ''.join(chunks)
def main():
    found={}
    for path in (ROOT/'qnmr').glob('*.py'):
        if path.stem in ('i18n','_catalog'):continue
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        parents={child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            if not isinstance(node,(ast.Constant,ast.JoinedStr)):continue
            parent=parents.get(node)
            if isinstance(parent,(ast.JoinedStr,ast.FormattedValue)):continue
            if isinstance(node,ast.Constant) and node.lineno==1:continue
            value=template(node)
            if not value or len(value)<3 or not any(c.isalpha() for c in value):continue
            if isinstance(parent,ast.Expr):continue
            # Keep full messages, labels and titles; omit identifiers, filenames,
            # styles, Python expressions and machine protocol field names.
            if value.startswith('#') or 'QWidget {' in value or value.startswith('<') and '>' not in value:continue
            if len(value)>3000:continue
            if not (' ' in value or value[0].isupper() or any(ord(c)>127 for c in value)):continue
            found.setdefault(value,[]).append(f'{path.name}:{node.lineno}')
    (ROOT/'outputs/ui_text_inventory.json').write_text(json.dumps(found,indent=2,ensure_ascii=False),encoding='utf-8')
    for value,locations in sorted(found.items()):print(json.dumps(value,ensure_ascii=False),','.join(locations))
if __name__=='__main__':main()
