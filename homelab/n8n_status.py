"""Forward authenticated Telegram /status commands to the n8n report workflow."""
import json,pathlib,time,threading,urllib.request,logging
from homelab import paths as homelab_paths
def install(bot,menu):
    lock=threading.Lock();last={};busy=set()
    @bot.message_handler(commands=['status'])
    def status(message):
        uid=message.from_user.id
        if not menu.allowed(message,uid):return
        with lock:
            if uid in busy or time.monotonic()-last.get(uid,0)<20:
                menu.send(message,'正在获取或刚刚获取过状态，请稍后再试。');return
            busy.add(uid);last[uid]=time.monotonic()
        try:
            cfg=json.loads(homelab_paths.data_file('n8n-status.json').read_text())
            req=urllib.request.Request(cfg['url'],data=b'{}',headers={'X-HomeLab-Key':cfg['token'],'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=95) as f:report=json.load(f)
            text=report.get('text')
            if not isinstance(text,str) or not text or len(text)>4000:raise ValueError('Invalid report')
            kwargs={}
            if getattr(message.chat,'is_forum',False):kwargs['message_thread_id']=message.message_thread_id
            bot.send_message(message.chat.id,text,**kwargs)
        except Exception as ex:
            logging.warning('n8n status query failed: %s',type(ex).__name__)
            menu.send(message,'⚠️ 暂时无法获取 Home Lab 状态，请稍后重试。')
        finally:
            with lock:busy.discard(uid)
    return status
