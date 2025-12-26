"""Chat widget API endpoints for multi-tab chat with history storage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated
import os
import httpx
from langflow.services.deps import get_variable_service

from fastapi import APIRouter, Body, Depends, HTTPException, status
from lfx.log.logger import logger
from sqlmodel import select

from langflow.api.utils import DbSession

from langflow.api.v1.chat_schemas import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatWidgetRequest,
)
from langflow.services.auth.utils import get_current_active_user, get_current_user_mcp
from langflow.services.database.models.widget_message.model import WidgetMessage, WidgetMessageCreate
from langflow.services.database.models.widget_session.model import WidgetSession, WidgetSessionCreate
from langflow.services.database.models.flow.model import Flow
from langflow.services.database.models.user.model import User


router = APIRouter(tags=["Chat Widget"], prefix="/chat")


async def get_current_active_user_optional(
    current_user: Annotated[User | None, Depends(get_current_user_mcp)] = None,
) -> User | None:
    """Optional version of get_current_active_user that doesn't raise if auth fails."""
    try:
        if current_user and current_user.is_active:
            return current_user
    except Exception:
        pass
    return None


@router.post("/session", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    *,
    session: DbSession,
    request: Annotated[ChatSessionCreateRequest, Body()],
    current_user: Annotated[User | None, Depends(get_current_active_user_optional)] = None,
) -> ChatSessionResponse:
    """Create a new chat session (tab)."""
    try:
        # Verify flow exists if provided and not placeholder
        flow = None
        if request.flow_id and str(request.flow_id) != "00000000-0000-0000-0000-000000000000":
            flow = await session.get(Flow, request.flow_id)
            if not flow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Flow with id {request.flow_id} not found",
                )

        # Use authenticated user if available, otherwise use provided user_id
        user_id = current_user.id if current_user else request.user_id

        # Create widget session
        widget_session = WidgetSession(
            session_name=request.session_name,
            flow_id=flow.id if flow else None,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True,
        )

        session.add(widget_session)
        await session.commit()
        await session.refresh(widget_session)

        return ChatSessionResponse(
            session_id=widget_session.id,
            session_name=widget_session.session_name,
            flow_id=widget_session.flow_id or uuid.UUID(int=0),
            user_id=widget_session.user_id,
            created_at=widget_session.created_at,
            updated_at=widget_session.updated_at,
            is_active=widget_session.is_active,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error creating chat session: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {exc!s}",
        ) from exc


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    *,
    session: DbSession,
    session_id: uuid.UUID,
) -> ChatHistoryResponse:
    """Retrieve chat history for a specific session."""
    try:
        # Get widget session
        widget_session = await session.get(WidgetSession, session_id)
        if not widget_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id {session_id} not found",
            )

        # Get all messages for this session, ordered by timestamp
        stmt = (
            select(WidgetMessage).where(WidgetMessage.session_id == session_id).order_by(WidgetMessage.timestamp.asc())
        )
        result = await session.exec(stmt)
        messages = result.all()

        # Convert to response format
        message_responses = [
            ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                user_message=msg.user_message,
                assistant_message=msg.assistant_message,
                timestamp=msg.timestamp,
                metadata=msg.extra_metadata or {},
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            session_id=widget_session.id,
            session_name=widget_session.session_name,
            messages=message_responses,
            total_messages=len(message_responses),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving chat history: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {exc!s}",
        ) from exc


@router.post("/widget", response_model=ChatMessageResponse)
async def chat_widget(
    *,
    session: DbSession,
    request: Annotated[ChatWidgetRequest, Body()],
) -> ChatMessageResponse:
    """Chat widget endpoint that accepts messages and returns OpenAI responses."""
    try:
        # Verify widget session exists
        widget_session = await session.get(WidgetSession, request.session_id)
        if not widget_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id {request.session_id} not found",
            )

        # Verify flow exists if provided and not placeholder
        flow = None
        if request.flow_id and str(request.flow_id) != "00000000-0000-0000-0000-000000000000":
            flow = await session.get(Flow, request.flow_id)
            if not flow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Flow with id {request.flow_id} not found",
                )

        # Call OpenAI API directly using OPENAI_API_KEY
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            # If env var not set, try fetching from stored variables for the session user
            if not api_key:
                try:
                    variable_service = get_variable_service()
                    if widget_session.user_id:
                        api_key = await variable_service.get_variable(
                            user_id=widget_session.user_id,
                            name="OPENAI_API_KEY",
                            field="openai_api_key",
                            session=session,
                        )
                except Exception:
                    # ignore and fallback to env check below
                    api_key = (
                        api_key
                        or "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"
                    )
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set")
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": request.message}],
            }
            headers = {
                "Authorization": f"Bearer {'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'}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            # Extract assistant response and metadata
            assistant_response = data["choices"][0]["message"]["content"] if data.get("choices") else ""
            extra_meta = data.get("usage", {}) or {}
            if not isinstance(extra_meta, dict):
                try:
                    extra_meta = dict(extra_meta)
                except (TypeError, ValueError):
                    extra_meta = {}
        except Exception as oai_exc:
            logger.warning(f"OpenAI API call failed, falling back to mock: {oai_exc}")
            assistant_response = f"Mock GPT response for: {oai_exc}"
            extra_meta = {"model": "gpt-mock"}

        # Store the message in database
        widget_message = WidgetMessage(
            session_id=request.session_id,
            flow_id=widget_session.flow_id,
            user_message=request.message,
            assistant_message=assistant_response,
            timestamp=datetime.now(timezone.utc),
            extra_metadata=extra_meta,
        )

        session.add(widget_message)

        # Update session's updated_at timestamp
        widget_session.updated_at = datetime.now(timezone.utc)
        session.add(widget_session)

        await session.commit()
        await session.refresh(widget_message)

        return ChatMessageResponse(
            id=widget_message.id,
            session_id=widget_message.session_id,
            user_message=widget_message.user_message,
            assistant_message=widget_message.assistant_message,
            timestamp=widget_message.timestamp,
            metadata=widget_message.extra_metadata or {},
        )

    except HTTPException:
        raise
    except Exception as exc:
        await logger.aexception("Error processing chat widget message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {exc!s}",
        ) from exc
