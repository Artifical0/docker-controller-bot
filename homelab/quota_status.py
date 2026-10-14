"""Telegram /quota：发送 account_watch.py 每 5 分钟写好的账号与额度汇总（机器人不保存任何密钥）。"""
import json,pathlib,time,logging
from homelab import paths as homelab_paths
def install(bot,menu):
    @bot.message_handler(commands=['quota'])
    def quota(message):
        if not menu.allowed(message,message.from_user.id):return
        try:
            data=json.loads(homelab_paths.data_file('account-watch/status.json').read_text())
            text=data['report']
            age=time.time()-data['generated_at']
            if age>1200:text+=f'\n\n⚠️ 数据已 {int(age//60)} 分钟没更新，巡检脚本可能没在运行。'
        except Exception as ex:
            logging.warning('quota status read failed: %s',type(ex).__name__)
            menu.send(message,'⚠️ 暂时读不到账号汇总，请稍后重试。');return
        kwargs={}
        if getattr(message.chat,'is_forum',False):kwargs['message_thread_id']=message.message_thread_id
        bot.send_message(message.chat.id,text[:4000],**kwargs)
    return quota
