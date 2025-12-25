"""Chat widget API endpoints for multi-tab chat with history storage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from lfx.log.logger import logger
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.chat_schemas import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatWidgetRequest,
)
from langflow.services.auth.utils import get_current_active_user
from langflow.services.database.models.chat_message.model import ChatMessage, ChatMessageCreate
from langflow.services.database.models.chat_session.model import ChatSession, ChatSessionCreate
from langflow.services.database.models.flow.model import Flow

router = APIRouter(tags=["Chat Widget"], prefix="/chat")


@router.post("/session", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    *,
    session: DbSession,
    request: Annotated[ChatSessionCreateRequest, Body()],
    current_user: CurrentActiveUser | None = Depends(get_current_active_user),
) -> ChatSessionResponse:
    """Create a new chat session (tab).

    Args:
        session: Database session
        request: Chat session creation request
        current_user: Current authenticated user (optional)

    Returns:
        ChatSessionResponse: Created chat session details

    Raises:
        HTTPException: If flow not found or creation fails
    """
    try:
        # Verify flow exists
        flow = await session.get(Flow, request.flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow with id {request.flow_id} not found",
            )

        # Use authenticated user if available, otherwise use provided user_id
        user_id = current_user.id if current_user else request.user_id

        # Create chat session
        chat_session = ChatSession(
            session_name=request.session_name,
            flow_id=request.flow_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True,
        )

        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)

        return ChatSessionResponse(
            session_id=chat_session.id,
            session_name=chat_session.session_name,
            flow_id=chat_session.flow_id,
            user_id=chat_session.user_id,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
            is_active=chat_session.is_active,
        )

    except HTTPException:
        raise
    except Exception as exc:
        await logger.aexception("Error creating chat session")
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
    """Retrieve chat history for a specific session.

    Args:
        session: Database session
        session_id: Chat session ID

    Returns:
        ChatHistoryResponse: Chat history with all messages

    Raises:
        HTTPException: If session not found
    """
    try:
        # Get chat session
        chat_session = await session.get(ChatSession, session_id)
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id {session_id} not found",
            )

        # Get all messages for this session, ordered by timestamp
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
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
                metadata=msg.metadata,
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            session_id=chat_session.id,
            session_name=chat_session.session_name,
            messages=message_responses,
            total_messages=len(message_responses),
        )

    except HTTPException:
        raise
    except Exception as exc:
        await logger.aexception("Error retrieving chat history")
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
    """Chat widget endpoint that accepts messages and returns GPT responses.

    This endpoint:
    1. Accepts a user message
    2. Processes it through the specified Langflow flow
    3. Stores both user message and assistant response in the database
    4. Returns the assistant's response

    Args:
        session: Database session
        request: Chat widget request with message and session info

    Returns:
        ChatMessageResponse: The chat message with assistant response

    Raises:
        HTTPException: If session/flow not found or processing fails
    """
    try:
        # Verify chat session exists
        chat_session = await session.get(ChatSession, request.session_id)
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id {request.session_id} not found",
            )

        # Verify flow exists
        flow = await session.get(Flow, request.flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow with id {request.flow_id} not found",
            )

        # TODO: Integrate Langflow's OpenAI component programmatically
        # For now, using a placeholder response
        # In production, you would:
        # 1. Load the flow
        # 2. Execute it with the user's message
        # 3. Get the response from the OpenAI component
        assistant_response = f"This is a placeholder response. In production, this would be processed by flow {request.flow_id}. User said: {request.message}"

        # Store the message in database
        chat_message = ChatMessage(
            session_id=request.session_id,
            flow_id=request.flow_id,
            user_message=request.message,
            assistant_message=assistant_response,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "model": "gpt-5.2",  # This would come from the actual flow execution
                "tokens": 0,  # This would be calculated from the actual response
            },
        )

        session.add(chat_message)

        # Update session's updated_at timestamp
        chat_session.updated_at = datetime.now(timezone.utc)
        session.add(chat_session)

        await session.commit()
        await session.refresh(chat_message)

        return ChatMessageResponse(
            id=chat_message.id,
            session_id=chat_message.session_id,
            user_message=chat_message.user_message,
            assistant_message=chat_message.assistant_message,
            timestamp=chat_message.timestamp,
            metadata=chat_message.metadata,
        )

    except HTTPException:
        raise
    except Exception as exc:
        await logger.aexception("Error processing chat widget message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {exc!s}",
        ) from exc
