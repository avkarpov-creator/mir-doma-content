#!/usr/bin/env python3
"""Дымовой тест JS-калькуляторов в статьях.

Для каждого блока <!-- wp:html --> со <script> строит заглушку DOM со значениями
полей по умолчанию, исполняет скрипт в node, вызывает обработчики input/change
и проверяет, что вывод не пустой и без NaN/undefined.

    python3 scripts/calc-smoke.py              # все статьи
    python3 scripts/calc-smoke.py <slug> ...   # выбранные

Нужен node: в PATH или в переменной MD_NODE. Если node нет, официальный
бинарник с nodejs.org можно распаковать во временную папку и указать в MD_NODE.
Виджеты, которые строят разметку через appendChild (карты, списки), дают
ложное «empty output» — смотрите их глазами.
"""
import re,sys,json,glob,os,subprocess,tempfile,shutil
node=os.environ.get('MD_NODE') or shutil.which('node')
if not node: sys.exit('node не найден: установите или задайте MD_NODE')
S=tempfile.mkdtemp()
only=set(sys.argv[1:])
bad=0; total=0
for f in sorted(glob.glob('articles/*.md')):
    if only and os.path.basename(f)[:-3] not in only: continue
    t=open(f,encoding='utf-8').read()
    blocks=re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->',t,re.S)
    for bi,b in enumerate(blocks):
        scripts=re.findall(r'<script>(.*?)</script>',b,re.S)
        if not scripts: continue
        total+=1
        vals={}
        for m in re.finditer(r'<(input|textarea)([^>]*)>',b):
            a=m.group(2); i=re.search(r'id="([^"]+)"',a)
            if not i: continue
            v=re.search(r'value="([^"]*)"',a); typ=re.search(r'type="([^"]+)"',a)
            vals[i.group(1)]={'value':v.group(1) if v else '','checked':' checked' in a,'type':typ.group(1) if typ else ''}
        for sid,body in re.findall(r'<select[^>]*id="([^"]+)"[^>]*>(.*?)</select>',b,re.S):
            m=re.search(r'value="([^"]*)"[^>]*selected',body) or re.search(r'value="([^"]*)"',body)
            vals[sid]={'value':m.group(1) if m else '','checked':False,'type':'select'}
        ids=re.findall(r'id="([^"]+)"',b)
        js='''
var V=%s, IDS=%s, els={};
function mk(id){var v=V[id]||{value:'',checked:false};return {id:id,value:v.value,checked:v.checked,type:v.type,textContent:'',innerHTML:'',className:'',style:{},dataset:{},
 classList:{add(){},remove(){},toggle(){},contains(){return false}},_h:[],addEventListener(t,f){if(t==='input'||t==='change')this._h.push(f)},click(){},setAttribute(){},getAttribute(){return null},appendChild(){},querySelector(){return mk('_q')},querySelectorAll(){return []},closest(){return null},focus(){},select(){},remove(){}};}
IDS.forEach(function(i){els[i]=mk(i)});
var document={getElementById:function(i){return els[i]||null},getElementsByName:function(n){return IDS.filter(function(i){return i.indexOf(n)>=0}).map(function(i){return els[i]})},querySelector:function(){return null},querySelectorAll:function(){return []},createElement:function(){return mk('_c')},addEventListener(){},body:mk('_b')};
var window={print(){},addEventListener(){},location:{href:''},navigator:{clipboard:{writeText(){return Promise.resolve()}}}}; var navigator=window.navigator; var location=window.location; var alert=function(){}; var localStorage={getItem(){return null},setItem(){}};
try{ %s
 IDS.forEach(function(i){els[i]._h.forEach(function(f){try{f.call(els[i],{target:els[i],preventDefault(){}})}catch(e){throw e}})});
 var o=IDS.map(function(i){return els[i].textContent||els[i].innerHTML}).filter(Boolean);
 console.log(JSON.stringify({ok:true,out:o.join(' | ').slice(0,160)}));
}catch(e){console.log(JSON.stringify({ok:false,err:String(e)}))}
'''%(json.dumps(vals,ensure_ascii=False),json.dumps(ids),'\n'.join(scripts))
        p=os.path.join(S,'t.js'); open(p,'w',encoding='utf-8').write(js)
        r=subprocess.run([node,p],capture_output=True,text=True,timeout=20)
        res=(r.stdout.strip().splitlines() or ['{}'])[-1]
        try: d=json.loads(res)
        except Exception: d={'ok':False,'err':(r.stderr or res)[:200]}
        empty=d.get('ok') and not d.get('out')
        if not d.get('ok') or empty or 'NaN' in d.get('out','') or 'undefined' in d.get('out',''):
            bad+=1; print('PROBLEM',os.path.basename(f),bi,d.get('err') or d.get('out') or 'empty output')
print('проверено',total,'проблем',bad)
sys.exit(1 if bad else 0)
