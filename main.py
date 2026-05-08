import uuid, logging
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
logger = logging.getLogger(__name__)

@register("smart_reply","Dubnium-105","LLM 自主判断是否回复群聊消息","1.4.0")
class SmartReplyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        logger.info(f"[SmartReply] handler called, msg={event.message_str[:50] if event.message_str else 'EMPTY'}")
        if not self.config.get("enable", True): return
        if self.config.get("inline_mode", False): return
        if event.is_at_or_wake_command: return
        wl = self.config.get("whitelist", [])
        if wl:
            g = event.get_group_id()
            if g not in wl and event.unified_msg_origin not in wl:
                event.stop_event(); return
        msg_text = event.message_str or ""
        sender = event.message_obj.sender.nickname if event.message_obj.sender else "unknown"
        group_name = getattr(event.message_obj, 'group_name', '') or ''
        dp = self.config.get("prompt","你是一个群聊中的 AI 助手。只回复 YES 或 NO。")
        prompt = f"群聊: {group_name}\n发言人: {sender}\n消息: {msg_text}\n\n{dp}\n只回复 YES 或 NO。"
        try:
            pid = self.config.get("provider_id","")
            provider = self.context.get_provider_by_id(pid) if pid else self.context.get_using_provider(event.unified_msg_origin)
            if not provider: return
            resp = await provider.text_chat(prompt=prompt, session_id=uuid.uuid4().hex, persist=False)
            r = resp.completion_text.strip().upper()
            if "YES" in r and "NO" not in r:
                logger.info(f"[SmartReply] YES {group_name} {sender}: {msg_text[:30]}")
            else:
                logger.info(f"[SmartReply] NO  {group_name} {sender}: {msg_text[:30]}")
                event.stop_event()
        except Exception as e:
            logger.error(f"[SmartReply] err: {e}")
