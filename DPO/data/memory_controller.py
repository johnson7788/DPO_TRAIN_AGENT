#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/12/9 17:50
# @File  : memory_controller.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  : 记忆控制,从metadata的history中获取记忆

import logging
import uuid
from typing import List, Dict, Any
from google.genai import types
from google.adk.runners import Runner
from google.adk.events import Event

logger = logging.getLogger(__name__)


class MemoryController:
    def __init__(self, runner: Runner):
        self.runner = runner
        self.app_name = runner.app_name

    async def inject_history_from_metadata(self, session_obj, metadata: Dict[str, Any]):
        """
        从 metadata 中读取 history 字段，并将其注入到当前 session 的 events 中。
        注意：这里直接操作 Session 对象。
        """
        if not metadata:
            return

        history_data = metadata.get("history")

        # 校验数据有效性
        if not history_data or not isinstance(history_data, list):
            return

        logger.info(f"Session {session_obj.id}: 检测到 metadata 历史记录，准备注入 {len(history_data)} 条数据")

        # 【关键步骤 1】: 如果 metadata 里传了 history，通常意味着用户希望以这份历史为准。
        # 因此我们需要清空 Session 中已有的 events，否则会变成 历史+历史+新问题。
        # 如果你想做“追加”模式，请注释掉下面这行。
        session_obj.events.clear()

        # 获取 Session Service
        session_service = self.runner.session_service

        for turn in history_data:
            role = turn.get("role")  # expecting "user" or "model"
            content_text = turn.get("content")

            if role and content_text:
                # 1. 转换 Role 和 Author
                # ADK 中 Content.role 只能是 "user" 或 "model"
                # ADK 中 Event.author 应该是 "user" 或者 Agent 的名字 (例如 "Navi_Agent")

                genai_role = "user"
                event_author = "user"

                if role == "model" or role == "assistant":
                    genai_role = "model"
                    # 这里最好填入你的 Agent 名称，或者保持 "model"
                    # 如果你的 Agent 有名字 (self.runner.agent.name)，最好用那个
                    event_author = self.runner.agent.name

                    # 2. 构建 Content 对象
                new_message = types.Content(
                    role=genai_role,
                    parts=[types.Part(text=content_text)]
                )

                # 3. 构建 Event 对象
                # Event 需要一个 invocation_id，我们这里生成一个假的 UUID 即可
                dummy_invocation_id = str(uuid.uuid4())

                event = Event(
                    invocation_id=dummy_invocation_id,
                    author=event_author,
                    content=new_message
                )

                # 4. 插入到 Session 中
                # 使用 session_service 的 append_event 方法
                await session_service.append_event(
                    session=session_obj,
                    event=event
                )

        logger.info(f"历史记录注入完成，当前 Session 共有 {len(session_obj.events)} 个事件")