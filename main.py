import uuid
import logging
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig

logger = logging.getLogger(__name__)

@register(
    "smart_reply",
    "Dubnium-105",
    "LLM 自主判断是否回复群聊消息",
    "1.0.0"
)
class SmartReplyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context, config)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        if not self.config.get("enable", True):
            return
        if event.is_at_or_wake_command:
            return
        whitelist = self.config.get("whitelist", [])
        if whitelist:
            gid = event.get_group_id()
            sid = event.unified_msg_origin
            if gid not in whitelist and sid not in whitelist:
                event.stop_event()
                return
        try:
            from astrbot.builtin_stars.astrbot.long_term_memory import LongTermMemory
            ltm = LongTermMemory(self.context)
            cfg = ltm.cfg(event)
            session_chats = getattr(ltm, 'session_chats', {})
            chats = session_chats.get(event.unified_msg_origin, [])
        except Exception:
            return
        if not chats:
            return
        n = self.config.get("history_count", 12)
        recent = chats[-n:]
        history = "\n".join(recent)
        decide_prompt = self.config.get("prompt",
            "你是一个群聊中的 AI 助手。请判断是否应该回复这条消息。考虑因素：消息是否明确提到你、向你提问、或需要帮助；回复是否自然不突兀；如果只是群友闲聊不需要回复。只回复 YES 或 NO。")
        prompt = f"群聊记录:\n{history}\n\n{decide_prompt}\n只回复 YES 或 NO。"
        try:
            provider_id = self.config.get("provider_id", "")
            if provider_id:
                provider = self.context.get_provider_by_id(provider_id)
            else:
                provider = self.context.get_using_provider(event.unified_msg_origin)
            if not provider:
                return
            response = await provider.text_chat(
                prompt=prompt, session_id=uuid.uuid4().hex, persist=False)
            result = response.completion_text.strip().upper()
            if "YES" in result and "NO" not in result:
                logger.info(f"SmartReply: YES")
            else:
                logger.debug(f"SmartReply: NO")
                event.stop_event()
        except Exception as e:
            logger.error(f"SmartReply error: {e}")
