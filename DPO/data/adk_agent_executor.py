#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/10/29
# @File  : adk_agent_executor.py
# @Contact : github: johnson7788
# @Desc  : 基于Google ADK的Agent执行器（thought + tool支持）

import asyncio
import logging
from collections.abc import AsyncGenerator
import os

from google.adk import Runner
from google.adk.events import Event
from google.genai import types

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCard,
    Artifact,
    FilePart,
    FileWithBytes,
    FileWithUri,
    GetTaskRequest,
    GetTaskSuccessResponse,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageSuccessResponse,
    Task,
    TaskQueryParams,
    TaskState,
    TaskStatus,
    TextPart,
    DataPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from a2a.utils.message import new_agent_text_message
from memory_controller import MemoryController
import contextvars
from agent import current_model_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ADKAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent."""

    def __init__(self, runner: Runner, card: AgentCard, run_config):
        self.runner = runner
        self._card = card
        self._running_sessions = {}
        self.run_config = run_config
        # 支持记忆注入
        self.memory_controller = MemoryController(runner)

    def _run_agent(
        self,
        session_id: str,
        new_message: types.Content
    ) -> AsyncGenerator[Event, None]:
        """运行ADK Agent"""
        return self.runner.run_async(
            session_id=session_id,
            user_id="self",
            new_message=new_message,
            run_config=self.run_config,
        )

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
        metadata: dict | None = None,
    ) -> None:
        """处理请求"""
        if metadata is None:
            metadata = {}

        # --- 解析 metadata 中的模型指令 ---
        model_info = None
        if "model" in metadata:
            model_info = {
                "model": metadata["model"],
                "provider": metadata.get("provider", os.environ.get("MODEL_PROVIDER", "google"))
            }

        # 使用 current_model_config.set 设置当前协程的上下文
        # 这样 root_agent.canonical_model 在读取时就能拿到正确的值
        token = current_model_config.set(model_info)

        try:
            # 获取或创建会话（合并metadata）
            session_obj = await self._upsert_session(session_id, metadata)
            logger.info(f"处理请求，会话ID: {session_id}")
            logger.info(f"收到请求信息: {new_message}")

            # 更新会话ID以用于agent运行
            session_id = session_obj.id

            # 在 agent 运行之前，将 metadata 中的 history 写入 memory service
            if metadata:
                try:
                    await self.memory_controller.inject_history_from_metadata(
                        session_obj, metadata
                    )
                except Exception as e:
                    logger.exception(f"注入历史到 memory_controller 时出错: {e}")

            async for event in self._run_agent(session_id, new_message):
                agent_author = event.author

                # 没有内容的事件直接跳过（例如纯流事件）
                if not event.content or not event.content.parts:
                    logger.info(f"event.content没有结果，跳过, Agent是: {agent_author}, event是: {event}")
                    continue

                # ---------------------
                # 1. 最终响应
                # ---------------------
                if event.is_final_response():
                    try:
                        final_session = await self.runner.session_service.get_session(
                            app_name=self.runner.app_name,
                            user_id="self",
                            session_id=session_id,
                        )
                    except Exception:
                        final_session = None

                    # 把 session.state.metadata 作为 artifact metadata 返回
                    final_metadata = {}
                    if final_session is not None and getattr(final_session, "state", None):
                        final_metadata = final_session.state.get("metadata", {}) or {}

                    parts = convert_genai_parts_to_a2a(event.content.parts)
                    logger.debug("Yielding final response: %s", parts)
                    await task_updater.add_artifact(parts=parts, metadata=final_metadata)
                    await task_updater.complete()
                    break

                # ---------------------
                # 2. 工具调用（function_call）
                # ---------------------
                if event.get_function_calls():
                    logger.info(f"触发了工具调用... 返回DataPart数据, {event}")
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            convert_genai_parts_to_a2a(event.content.parts),
                        ),
                    )
                    # 小延迟，帮助前端更好区分消息
                    await asyncio.sleep(0.1)
                    continue

                # ---------------------
                # 3. 工具返回（function_response）
                # ---------------------
                if event.get_function_responses():
                    logger.info(f"工具返回了结果... 返回DataPart数据, {event}")
                    references = {}
                    try:
                        final_session = await self.runner.session_service.get_session(
                            app_name=self.runner.app_name,
                            user_id="self",
                            session_id=session_id,
                        )
                        if final_session is not None and getattr(final_session, "state", None):
                            search_dbs = final_session.state.get("search_dbs", [])
                            references = {"search_dbs": search_dbs}
                    except Exception as e:
                        logger.exception(f"获取工具引用信息失败: {e}")

                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            convert_genai_parts_to_a2a(event.content.parts),
                            metadata=references or None,
                        ),
                    )
                    continue

                # ---------------------
                # 4. 普通中间回复（含 text / thought / file）
                # ---------------------
                logger.debug(f"中间回复事件: {event}")
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        convert_genai_parts_to_a2a(event.content.parts),
                    ),
                )
        finally:
            # --- 关键：请求结束时必须重置上下文变量，防止污染后续请求 ---
            current_model_config.reset(token)
            logger.debug(f"会话 {session_id} 执行完毕，模型上下文已重置")
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """执行请求"""
        logger.info(f"开始执行请求: {context.context_id}")

        # 创建任务更新器
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        # 立即通知任务已提交
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        # 处理请求
        await self._process_request(
            types.UserContent(
                parts=convert_a2a_parts_to_genai(context.message.parts),
            ),
            context.context_id,
            updater,
            metadata=context.message.metadata,
        )
        logger.debug("[adk agent] 执行完成，退出")

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """取消请求"""
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str, metadata: dict | None = None) -> any:
        """
        获取或创建会话，并合并 metadata（采用版本2逻辑）
        """
        if metadata is None:
            metadata = {}

        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name,
            user_id="self",
            session_id=session_id,
        )

        if session is None:
            logger.info(f"创建新会话: {session_id}")
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id="self",
                session_id=session_id,
                state={"metadata": metadata},
            )
        else:
            logger.info(f"使用现有会话: {session_id}")
            # 更新metadata
            current_metadata = session.state.get("metadata", {}) or {}
            current_metadata.update(metadata)
            session.state["metadata"] = current_metadata

        if session is None:
            logger.error(f"关键错误: 会话创建失败 {session_id}")
            raise RuntimeError(f"获取或创建会话失败: {session_id}")

        return session


# =====================================================================
# 转换工具：A2A <-> GenAI Part
# =====================================================================

def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """将A2A Part类型转换为Google Gen AI Part类型"""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """将单个A2A Part类型转换为Google Gen AI Part类型"""
    part = part.root
    if isinstance(part, TextPart):
        return types.Part(text=part.text)
    if isinstance(part, FilePart):
        if isinstance(part.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=part.file.uri,
                    mime_type=part.file.mime_type,
                )
            )
        if isinstance(part.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=part.file.bytes,
                    mime_type=part.file.mime_type,
                )
            )
        raise ValueError(f"不支持的文件类型: {type(part.file)}")
    raise ValueError(f"不支持的Part类型: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """
    将Google Gen AI Part类型转换为A2A Part类型

    合并逻辑：
    - 普通 text / file / inline_data --> TextPart / FilePart（支持 thought 元数据）
    - function_call / function_response --> DataPart(data=[{...}, {...}])
    """
    converted = []
    tool_res = []

    for part in parts:
        # tool / function 系列
        if part.function_call or part.function_response:
            tool_res.append(extract_function_info_to_datapart(part))
            continue

        # 普通内容（text / file / inline_data）
        if part.text or part.file_data or part.inline_data:
            converted.append(convert_genai_part_to_a2a(part))

    # 如果有tool相关内容，统一包成一个 DataPart 返回（保持与版本2行为一致）
    if tool_res:
        return [DataPart(data={"data": tool_res})]

    return converted


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """
    将单个Google Gen AI Part类型转换为A2A Part类型

    合并逻辑：
    - 来自版本1：支持 thought 标记，通过 metadata={"thought": True} 传给 TextPart
    """
    # text / thought
    if part.text:
        # Gemini 的 thought 内容也是放在 text 字段里的，额外有 thought 属性
        is_thought = getattr(part, "thought", False)
        metadata = {"thought": True} if is_thought else {}
        # 假设 TextPart 支持 metadata 参数
        return TextPart(text=part.text, metadata=metadata)

    # 文件（URI）
    if part.file_data:
        return FilePart(
            file=FileWithUri(
                uri=part.file_data.file_uri,
                mime_type=part.file_data.mime_type,
            )
        )

    # 文件（二进制）
    if part.inline_data:
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data,
                    mime_type=part.inline_data.mime_type,
                )
            )
        )

    raise ValueError(f"Unsupported part type: {part}")


def extract_function_info_to_datapart(part: types.Part) -> dict:
    """
    从单个GenAI Part对象中提取 function_call 或 function_response 信息，
    用于后面封装到 DataPart 中。

    返回格式示例：
    {
        "type": "function_call",
        "id": "...",
        "name": "...",
        "args": {...}
    }
    或
    {
        "type": "function_response",
        "id": "...",
        "name": "...",
        "response": {...}
    }
    """
    if part.function_call:
        return {
            "type": "function_call",
            "id": part.function_call.id,
            "name": part.function_call.name,
            "args": part.function_call.args,
        }

    if part.function_response:
        return {
            "type": "function_response",
            "id": part.function_response.id,
            "name": part.function_response.name,
            "response": part.function_response.response,
        }

    raise ValueError(f"Part不包含function_call或function_response: {part}")
