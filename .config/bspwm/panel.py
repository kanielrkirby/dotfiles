#!/usr/bin/env -S nix run nixpkgs#python312 --
import json, selectors, subprocess, time
from pathlib import Path
S=selectors.DefaultSelector(); D={}; DIR=Path('/tmp'); datef=DIR/'panel_date_format'; vpnf=DIR/'panel_vpn'; netf=DIR/'panel_network'; workf=DIR/'bspwm_current_workspace'; tsf=DIR/'panel_tailscale'

def cmd(*x, timeout=1):
 try: return subprocess.run(x,capture_output=True,text=True,timeout=timeout).stdout.strip()
 except (OSError,subprocess.SubprocessError): return ''
def watch(*x, data=None):
 try:
  p=subprocess.Popen(x,stdout=subprocess.PIPE,text=True,bufsize=1); S.register(p.stdout,selectors.EVENT_READ,data or x[0])
 except OSError: pass
def val(p,default):
 try: return p.read_text().strip() or default
 except OSError: return default

def desktops():
 try:
  d=json.loads(cmd('bspc','wm','-d')); w=int(val(workf,'1')); off=(w-1)*9; fm=d['focusedMonitorId']; cur=''; occ=set()
  for m in d['monitors']:
   for x in m['desktops']:
    if x.get('root'): occ.add(x['name'])
    if m['id']==fm and x['id']==m['focusedDesktopId']: cur=x['name']
  n=int(cur)-off
  out=''.join(f"%{{A:/home/mx/.config/bspwm/bspwm-workspace-helper.sh focus {i}:}}%{{F#{'FFFFFF' if i==n else '888888' if str(off+i) in occ else '444444'}}}{'['+str(i)+']' if i==n else ' '+str(i)+' '}%{{F-}}%{{A}}" for i in range(1,10))
  D['desk']=out+f" %{{A:/home/mx/.config/bspwm/bspwm-workspace-helper.sh cycle:}}[{('W','P','O')[w-1]}]%{{A}}"
 except (ValueError,KeyError,TypeError,json.JSONDecodeError): D['desk']=''
def audio():
 v=cmd('wpctl','get-volume','@DEFAULT_AUDIO_SINK@'); p=v.split(); D['vol']=f'{int(float(p[1])*100)}%' if len(p)>1 else 'N/A'; D['muted']='M' if 'MUTED' in v else ''; D['mic']='X' if 'yes' in cmd('pactl','get-source-mute','@DEFAULT_SOURCE@') else ''
def brightness():
 b=cmd('brightnessctl','-m').split(','); D['bright']=b[3].rstrip('%') if len(b)>3 else 'N/A'
def date():
 D['date']=cmd('date','+%A, %B %d, %Y %I:%M %p' if val(datef,'compact')=='verbose' else '+%a %Y-%m-%d %H:%M')
def battery():
 try: D['bat']=('C' if Path('/sys/class/power_supply/BAT0/status').read_text().strip()=='Charging' else 'D')+' '+Path('/sys/class/power_supply/BAT0/capacity').read_text().strip()+'%'
 except OSError: D['bat']='N/A'
def files():
 try:
  t=json.loads(cmd('tailscale','status','--json')); suffix='.'+t.get('MagicDNSSuffix','').rstrip('.')
  online=t.get('Self',{}).get('Online') is True and t.get('BackendState')=='Running'; name=t.get('Self',{}).get('DNSName','').rstrip('.')
  if suffix and name.endswith(suffix): name=name[:-len(suffix)].rstrip('.')
  exit_id=t.get('ExitNodeStatus',{}).get('ID'); peers=t.get('Peer',{}); exit_name=next((p.get('DNSName','').rstrip('.').removesuffix(suffix).rstrip('.') for p in peers.values() if p.get('ID')==exit_id), '')
  D['ts']=f'[TS:{name}{">"+exit_name if exit_name else ""}]' if online and name else '[TS:off]'
 except (json.JSONDecodeError,AttributeError): D['ts']='[TS:off]'
 try:
  m=json.loads(cmd('mullvad','status','--json')); s=m.get('state','').lower(); host=m.get('details',{}).get('location',{}).get('hostname','')
  D['vpn']=f'[M:{host}]' if s=='connected' and host else f'[M:{s or "off"}]'
 except (json.JSONDecodeError,AttributeError): D['vpn']='[M:unknown]'
 active=cmd('nmcli','-t','-f','type,state,name','connection','show','--active').splitlines()
 name=next((x.split(':',2)[2] for x in active if x.startswith('802-11-wireless:')), 'Wired' if any(x.startswith('802-3-ethernet:') for x in active) else 'off')
 D['net']=f'[W:{name}]'
def click(t,l='',r='',up='',down=''):
 a=[x for x in (f'%{{A:{l}:}}' if l else '',f'%{{A3:{r}:}}' if r else '',f'%{{A4:{up}:}}' if up else '',f'%{{A5:{down}:}}' if down else '') if x]
 return ''.join(a)+t+'%{A}'*len(a)
def render():
 brightness=f"%{{A4:brightnessctl set +5%:}}%{{A5:brightnessctl set 5%-:}}{D['bright']}%%{{A}}%{{A}}"
 right='   '.join((click(D['ts'],'/home/mx/.config/bspwm/panel-toggle-tailscale.sh'),click(D['vpn'],'/home/mx/.config/bspwm/panel-toggle-vpn.sh','mullvad reconnect'),click(D['net'],'/home/mx/.config/bspwm/panel-toggle-wifi.sh','ghostty -e nmtui'),click('[B]','', 'ghostty -e bluetoothctl'),brightness,click(D['mic']+D['muted']+(' ' if D['mic'] or D['muted'] else '')+D['vol'],'wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle','pactl set-source-mute @DEFAULT_SOURCE@ toggle','wpctl set-volume -l 1.2 @DEFAULT_AUDIO_SINK@ 5%+','wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-'),click(D['date'],'/home/mx/.config/bspwm/panel-toggle-date.sh','ghostty -e sh -c "cal -y; read"'),click(D['bat'],'',"ghostty -e sh -c 'SUDO_ASKPASS=/home/mx/.local/bin/sudo-askpass sudo -A -Es btop'")))
 print('%{B#1a1a1a}%{F#CCCCCC}%{l} '+D['desk']+'%{r}'+right+' ',flush=True)
for p,v in ((datef,'compact'),(workf,'1'),(tsf,'')):
 if not p.exists(): p.write_text(v)
for x in (('bspc','subscribe','desktop_focus','node_transfer'),('nmcli','monitor'),('mullvad','status','listen'),('pw-mon','-N')): watch(*x)
watch('udevadm','monitor','--kernel','--subsystem-match=backlight',data='bright')
watch('udevadm','monitor','--kernel','--subsystem-match=power_supply',data='battery')
watch('curl','-sN','--unix-socket','/run/tailscale/tailscaled.sock','http://local-tailscaled/localapi/v0/watch-ipn-bus',data='tailscale')
watch('inotifywait','-m','-q','-e','close_write',str(datef),data='date')
watch('inotifywait','-m','-q','-e','close_write,modify',str(workf),data='desk')
watch('inotifywait','-m','-q','-e','close_write,modify,attrib',str(tsf),data='tailscale')
desktops(); audio(); brightness(); date(); battery(); files(); render(); dirty={'desk','audio','bright','date','battery','files'}; next_poll=time.monotonic()+10
while True:
 for k,_ in S.select(max(0,next_poll-time.monotonic())):
  if not k.fileobj.readline():
   S.unregister(k.fileobj); k.fileobj.close(); continue
  dirty.add({'bspc':'desk','pw-mon':'audio','nmcli':'files','mullvad':'files','tailscale':'files','date':'date','bright':'bright','battery':'battery'}.get(k.data,'files'))
 if time.monotonic()>=next_poll:
  dirty.update(('bright','date','battery')); next_poll=time.monotonic()+10
 if dirty:
  if 'desk' in dirty: desktops()
  if 'audio' in dirty: audio()
  if 'bright' in dirty: brightness()
  if 'date' in dirty: date()
  if 'battery' in dirty: battery()
  if 'files' in dirty: files()
  render(); dirty.clear()
