import sys,types,importlib.util,tempfile
from types import SimpleNamespace as NS
uno=types.ModuleType('uno');uno.createUnoStruct=lambda n:NS();sys.modules['uno']=uno
uh=types.ModuleType('unohelper');uh.Base=type('Base',(),{});sys.modules['unohelper']=uh
awt=types.ModuleType('com.sun.star.awt')
for n in ['XActionListener','XItemListener','XMouseListener','XTopWindowListener']: setattr(awt,n,type(n,(),{}))
sys.modules['com.sun.star.awt']=awt
class Model:
 def __init__(self): self.children={};self.StringItemList=();self.Enabled=True;self.Text=''
 def createInstance(self,n):return Model()
 def insertByName(self,n,item):self.children[n]=item
class Control:
 def __init__(self,m):self.m=m;self.SelectedItemPos=-1;self.visible=True
 def getModel(self):return self.m
 @property
 def Text(self):return self.m.Text
 @Text.setter
 def Text(self,v):self.m.Text=v
 @property
 def ItemCount(self):return len(self.m.StringItemList)
 def addItem(self,v,p):self.m.StringItemList=(*self.m.StringItemList[:p],v,*self.m.StringItemList[p:])
 def removeItems(self,p,n):self.m.StringItemList=self.m.StringItemList[:p]+self.m.StringItemList[p+n:]
 def selectItemPos(self,p,v):self.SelectedItemPos=p
 def setText(self,v):self.Text=v
 def getText(self):return self.Text
 def setVisible(self,v):self.visible=v
 def setActionCommand(self,v):pass
 def addActionListener(self,v):pass
 def addItemListener(self,v):pass
class Dialog:
 def setModel(self,m):self.m=m;self.controls={n:Control(c) for n,c in m.children.items()}
 def createPeer(self,*a):pass
 def getControl(self,n):return self.controls[n]
 def addTopWindowListener(self,v):pass
 def removeTopWindowListener(self,v):pass
 def setVisible(self,v):self.visible=v
 def dispose(self):self.disposed=True
 def toFront(self):pass
class SM:
 def createInstanceWithContext(self,n,ctx):
  return Dialog() if n.endswith('UnoControlDialog') else Model()
from pathlib import Path
p=str(Path(__file__).resolve().parents[1] / 'extension/Scripts/python/lexique_forensique.py')
spec=importlib.util.spec_from_file_location('lex',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m._ctx=lambda:NS(ServiceManager=SM());m._desktop=lambda:NS(getCurrentComponent=lambda:None)
user_profile = tempfile.TemporaryDirectory()
m._user_data_dir=lambda:user_profile.name
m.open_lexicon();w=m._OPEN_LEXICON_WINDOWS[0];d=w['dialog'];l=w['listener'];nav=w['navigation']
assert len(l.matches)>50
for name,c in d.m.children.items():
 assert c.PositionX>=0 and c.PositionY>=0 and c.PositionX+c.Width<=420 and c.PositionY+c.Height<=334,(name,vars(c))
data=m._load_data();family,sub=m._category_parts(next(e for e in data if e['id']=='acquisition-forensique'))
d.getControl('cmbCategory').setText(family);l.itemStateChanged(NS(Source=d.getControl('cmbCategory')))
assert all(m._category_parts(e)[0]==family for e in l.matches)
d.getControl('cmbSubcategory').setText(sub);l.itemStateChanged(NS(Source=d.getControl('cmbSubcategory')))
assert all(m._category_parts(e)[1]==sub for e in l.matches)
assert l.formulation_text.Text and 'FORMULATIONS POUR RAPPORT' not in l.detail_box.Text
saved=l.current
for module in ['verify','scenarios','lexicon']:
 nav.select(module)
 assert all(d.getControl(n).visible==(key==module) for key,names in nav.groups.items() for n in names)
assert l.current==saved
m.open_scenarios();assert len(m._OPEN_LEXICON_WINDOWS)==1
l.search_box.Text='ZZZZ-no-result';l.refresh();assert not l.matches and not l.insert_button.getModel().Enabled and not l.formulation_text.Text
m._close_module_window(d);assert not any([m._OPEN_LEXICON_WINDOWS,m._OPEN_VERIFY_WINDOWS,m._OPEN_SCENARIO_WINDOWS])
print('OK: construction, geometry, cascading filters, formulations, module state, window reuse, empty results, cleanup')
