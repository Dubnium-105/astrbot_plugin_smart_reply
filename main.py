import uuid
import logging
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig

logger = logging.getLogger(__name__)

@register("smart_reply","Dubnium-105","LLM 自主判断是否回复群聊消息，支持独立判断或合并到主提示词","1.1.0")
class SmartReplyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context, config)

    @filter.on_llm_request
    async def on_llm_request(self, event, req):
        if not self.config.get("enable", True): return
        if not self.config.get("inline_mode", False): return
        if event.get_message_type() != "GROUP_MESSAGE": return
        if event.is_at_or_wake_command: return
        p = self.config.get("prompt","如果不需要回复，只回复一个空格。")
        req.system_prompt = (req.system_prompt or "") + "\n\n[系统规则] " + p

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        if not self.config.get("enable", True): return
        if self.config.get("inline_mode", False): return
        if event.is_at_or_wake_command: return
        wl = self.config.get("whitelist", [])
        if wl:
            g = event.get_group_id()
            if g not in wl and event.unified_msg_origin not in wl:
                event.stop_event(); return
        try:
            from astrbot.builtin_stars.astrbot.long_term_memory import LongTermMemory
            ltm = LongTermMemory(self.context)
            chats = getattr(ltm,'session_chats',{}).get(event.unified_msg_origin,[])
        except: return
        if not chats: return
        n = self.config.get("history_count", 12)
        h = "\n".join(chats[-n:])
        dp = self.config.get("prompt","你是一个群聊中的 AI 助手。请判断是否应该回复这条消息。只回复 YES 或 NO。")
        prompt = f"群聊记录:\n{h}\n\n{dp}\n只回复 YES 或 NO。"
        try:
            pid = self.config.get("provider_id","")
            provider = self.context.get_provider_by_id(pid) if pid else self.context.get_using_provider(event.unified_msg_origin)
            if not provider: return
            resp = await provider.text_chat(prompt=prompt, session_id=uuid.uuid4().hex, persist=False)
            r = resp.completion_text.strip().upper()
            if "YES" in r and "NO" not in r:
                logger.info("SmartReply: YES")
            else:
                event.stop_event()
        except Exception as e:
            logger.error(f"SmartReply error: {e}")
