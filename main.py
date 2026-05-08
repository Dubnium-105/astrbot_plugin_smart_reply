import uuid, logging
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
logger = logging.getLogger(__name__)

@register("smart_reply","Dubnium-105","LLM 自主判断是否回复群聊消息","2.0.0")
class SmartReplyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}

    @filter.on_decorating_result()
    async def on_message(self, event: AstrMessageEvent):
        logger.info(f"[SmartReply] FIRED!")
        if not self.config.get("enable", True): return
        if event.get_message_type() != "GROUP_MESSAGE": return
        if self.config.get("inline_mode", False): return
        if event.is_at_or_wake_command: return
        
        msg_text = event.message_str or ""
        sender = event.message_obj.sender.nickname if event.message_obj.sender else "unknown"
        group_name = getattr(event.message_obj, 'group_name', '') or ''
        
        dp = self.config.get("prompt","只回复 YES 或 NO。")
        prompt = f"群聊: {group_name}\n发言人: {sender}\n消息: {msg_text}\n\n{dp}"
        
        try:
            pid = self.config.get("provider_id","")
            provider = self.context.get_provider_by_id(pid) if pid else self.context.get_using_provider(event.unified_msg_origin)
            if not provider: return
            resp = await provider.text_chat(prompt=prompt, session_id=uuid.uuid4().hex, persist=False)
            r = resp.completion_text.strip().upper()
            if "YES" in r and "NO" not in r:
                logger.info(f"[SmartReply] YES {sender}:{msg_text[:30]}")
            else:
                logger.info(f"[SmartReply] NO  {sender}:{msg_text[:30]}")
                event.stop_event()
        except Exception as e:
            logger.error(f"[SmartReply] err: {e}")
