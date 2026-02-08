"""Edit session service for timeline editor."""
from __future__ import annotations

from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.edit_session import EditSession, EditAction
from app.schemas.editor import EditActionInput


class EditSessionService:
    """Service for managing edit sessions and actions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session(self, job_id: str) -> EditSession | None:
        return (
            self.db.query(EditSession)
            .filter(EditSession.job_id == job_id)
            .first()
        )

    def get_or_create_session(self, job_id: str) -> EditSession:
        session = self.get_session(job_id)
        if session:
            return session

        session = EditSession(job_id=job_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session(
        self,
        job_id: str,
        actions: Iterable[EditActionInput],
    ) -> EditSession:
        session = self.get_or_create_session(job_id)

        existing_actions = {action.id: action for action in session.actions}
        keep_action_ids: set[UUID] = set()

        for action_input in actions:
            if action_input.id and action_input.id in existing_actions:
                action = existing_actions[action_input.id]
                self._apply_action_update(action, action_input)
                keep_action_ids.add(action.id)
            elif action_input.id:
                raise ValueError("指定されたアクションが編集セッションに存在しません")
            else:
                action = self._create_action(session.id, action_input)
                self.db.add(action)
                keep_action_ids.add(action.id)

        for action in list(session.actions):
            if action.id not in keep_action_ids:
                self.db.delete(action)

        self.db.commit()
        self.db.refresh(session)
        return session

    def _create_action(self, session_id: UUID, action_input: EditActionInput) -> EditAction:
        return EditAction(
            session_id=session_id,
            risk_item_id=action_input.risk_item_id,
            type=action_input.type,
            start_time=action_input.start_time,
            end_time=action_input.end_time,
            options=self._serialize_options(action_input),
        )

    def _apply_action_update(
        self,
        action: EditAction,
        action_input: EditActionInput,
    ) -> None:
        action.risk_item_id = action_input.risk_item_id
        action.type = action_input.type
        action.start_time = action_input.start_time
        action.end_time = action_input.end_time
        action.options = self._serialize_options(action_input)

    @staticmethod
    def _serialize_options(action_input: EditActionInput) -> dict | None:
        if action_input.options is None:
            return None
        return action_input.options.model_dump()
