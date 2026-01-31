from __future__ import annotations
from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from hurag.schemas import Knowledge
    from openai import AsyncOpenAI

from ..events import (
    Copy_response_clicked,
    Regenerate_response_clicked,
    Like_response_clicked,
    Dislike_response_clicked,
    Download_response_clicked,
    Show_message_citations_clicked,
)
from .. import logger, conf, oa_client_name, oa_model_name
from hurag.llm import with_oa_client, chat, extract_chunk

from nicegui import ui
from datetime import datetime

_CTX_SIZE_MAP = {
    "tiny": (4, -2),  # 4 docs, 1 history round
    "medium": (5, -10),  # 5 docs, 5 history rounds
    "large": (None, None),  # unlimited
}


async def display_user_message(
    message: str,
    username: str,
    timestamp: datetime = datetime.now(),
) -> ui.chat_message:
    """Display a user message in the chat viewer."""
    return ui.chat_message(
        message, name=username, stamp=timestamp.strftime("%Y-%m-%d %H:%M"), sent=True
    )


async def display_bot_message(content) -> ui.markdown:
    """Display a bot message in the chat viewer."""
    import mdformat
    return ui.markdown(
        mdformat.text(content) if content else "",
        # content if content else "",
        extras=["fenced-code-blocks", "tables", "latex", "mermaid"],
    ).classes("w-full max-w-full text-gray-800")


async def display_message_footer(
    message_id: str | None,
    pair_id: str | None,
    timestamp: datetime = datetime.now(),
    likes: int = 0,
    dislikes: int = 0,
) -> ui.column:
    """Display a footer for a message with actions like 'like' and 'dislike'."""
    footer_col = ui.column().classes("w-full self-stretch items-stretch gap-0")
    with footer_col:
        ui.markdown(
            f"---\n*以上内容为人工智能生成，仅供参考。*"
            f" {timestamp.strftime('%Y-%m-%d %H:%M')}",
        ).classes("text-caption text-gray-500 mb-0")
        if message_id:
            with ui.row().classes("justify-left py-0 my-0"):
                with ui.button(
                    on_click=lambda e, i=message_id: Copy_response_clicked.emit(i),
                    icon="sym_r_content_copy",
                ).props("round dense flat size=sm color=gray-500 my-0 py-0"):
                    ui.tooltip("Copy").classes("text-caption")

                with ui.button(
                    on_click=lambda e, i=pair_id: Regenerate_response_clicked.emit(i),
                    icon="sym_r_refresh",
                ).props("round dense flat size=sm color=gray-500 my-0 py-0"):
                    ui.tooltip("Regenerate").classes("text-caption")

                with ui.button(
                    on_click=lambda e, i=message_id: Like_response_clicked.emit(e, i),
                    icon="sym_r_thumb_up",
                ).props(
                    "round dense flat size=sm color=gray-500 my-0 py-0"
                    if not likes
                    else "round dense flat size=sm color=amber-600 my-0 py-0"
                ):
                    ui.tooltip("Like").classes("text-caption")

                with ui.button(
                    on_click=lambda e, i=message_id: Dislike_response_clicked.emit(
                        e, i
                    ),
                    icon="sym_r_thumb_down",
                ).props(
                    "round dense flat size=sm color=gray-500 my-0 py-0"
                    if not dislikes
                    else "round dense flat size=sm color=amber-600 my-0 py-0"
                ):
                    ui.tooltip("Dislike").classes("text-caption")

                with ui.button(
                    on_click=lambda e, i=message_id: Download_response_clicked.emit(i),
                    icon="sym_r_download",
                ).props("round dense flat size=sm color=gray-500 my-0 py-0"):
                    ui.tooltip("Download").classes("text-caption")

                with ui.button(
                    on_click=lambda e,
                    i=message_id: Show_message_citations_clicked.emit(i),
                    icon="sym_r_auto_stories",
                ).props("round dense flat size=sm color=gray-500 my-0 py-0"):
                    ui.tooltip("Citations").classes("text-caption")

    return footer_col


async def scroll_to_bottom(c):
    ui.run_javascript(
        f"getElement({c.id}).scrollTop = getElement({c.id}).scrollHeight;"
    )


@with_oa_client(client_name=oa_client_name)
async def chat_with_backend(
    container: ui.column,
    mode: Literal["naive", "mix", "community", "global"] | None,
    message: str,
    knowledge_list: list[tuple[Knowledge, float]],
    system_prompt: str | None = None,
    history: list | None = None,
    temperature: float | None = 0,
    timeout: int = 180,
    oaclient: AsyncOpenAI | None = None,
) -> tuple[str, datetime]:
    """
    Chat with the backend LLM service and display the response.

    Arguments:
        container: The UI container to display the chat messages.
        mode: The chat mode.
        message: The user message used to create the prompt.
        knowledge_list: The list of knowledge items to use.
        system_prompt: The system prompt.
        history: The chat history.
        temperature: The temperature for the LLM.
        timeout: The timeout for the backend request.
        oaclient: Placeholder for injecting an OpenAI client.

    Returns:
        A tuple containing:
            - The message of the bot response.
            - The timestamp of the bot response.
    """
    from httpx import RemoteProtocolError
    import mdformat

    content = ""
    if mode:
        from ..prompts import create_rag_prompt

        prompt = create_rag_prompt(
            query=message,
            knowledge_list=knowledge_list,
            kn_limit=_CTX_SIZE_MAP[conf.services.ctx_size][0],
        )
    else:
        prompt = message

    hist_limit = _CTX_SIZE_MAP[conf.services.ctx_size][1]
    with container:
        bot_msg_md = await display_bot_message("")
        try:
            response = await chat(
                model=oa_model_name,
                prompt=prompt,
                system_prompt=system_prompt,
                history_messages=history[hist_limit:] if hist_limit else history,
                client=oaclient,
                temperature=temperature,
                stream=True,
                timeout=timeout,
            )
            async for chunk in response:
                content += extract_chunk(chunk)
                # bot_msg_md.set_content(content)
                bot_msg_md.set_content(mdformat.text(content) if content else "")
                await scroll_to_bottom(container)
        except RemoteProtocolError:
            logger.error(f"Context window overflow")
            ui.notify("上下文超长", type="negative")
            content += "\n\n> **[系统错误]** 上下文超长，模型崩溃😵💫🤯😇"
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            ui.notify(f"模型连接中断: {str(e)}", type="negative")
            content += "\n\n> **[系统错误]** 模型连接中断🤕🤕🤕"

        # bot_msg_md.set_content(mdformat.text(content))
    return content, datetime.now()
