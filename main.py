import uuid, logging
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
logger = logging.getLogger(__name__)

@register("smart_reply","Dubnium-105","LLM 自主判断是否回复群聊消息","2.1.0")
class SmartReplyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}

    @filter.on_llm_request()
    async def on_llm_request(self, event, req):
        """在 LLM 收到请求时判断是否回复群聊"""
        if not self.config.get("enable", True): return
        if event.get_message_type() != "GROUP_MESSAGE": return
        if event.is_at_or_wake_command: return
        
        msg_text = event.message_str or ""
        sender = event.message_obj.sender.nickname if event.message_obj.sender else "unknown"
        group_name = getattr(event.message_obj, 'group_name', '') or ''
        
        # 把判断附加到 system prompt
        dp = self.config.get("prompt","如果这条消息不需要回复，请只回复一个空格。")
        req.system_prompt = (req.system_prompt or "") + f"\n\n[群聊: {group_name} 发言人: {sender}] {dp}"
        logger.info(f"[SmartReply] inline check for {sender}:{msg_text[:30]}")
