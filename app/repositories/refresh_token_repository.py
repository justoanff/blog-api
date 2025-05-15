from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select
from datetime import datetime, timezone

from app.models.refresh_token_model import RefreshToken
# RefreshTokenCreate có thể là RefreshTokenBase hoặc một schema Pydantic riêng nếu cần
from app.models.refresh_token_model import RefreshTokenBase as RefreshTokenCreateSchema
from app.repositories.base_repository import BaseRepository

class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenCreateSchema, RefreshTokenCreateSchema]):
    # Lưu ý: UpdateSchemaType ở đây có thể giống CreateSchemaType nếu bạn không có schema update riêng

    def get_by_token_hash(self, db: Session, *, token_hash: str) -> Optional[RefreshToken]:
        """
        Lấy RefreshToken dựa trên hash của nó.
        """
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return db.exec(statement).first()

    def get_active_by_token_hash_and_user(
        self, db: Session, *, token_hash: str, user_id: UUID
    ) -> Optional[RefreshToken]:
        """
        Lấy RefreshToken đang hoạt động (chưa bị thu hồi, chưa hết hạn)
        dựa trên hash và user_id.
        """
        statement = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked == False)
            .where(RefreshToken.expires_at > datetime.now(timezone.utc))
        )
        return db.exec(statement).first()

    def mark_as_revoked(self, db: Session, *, token_id: Optional[UUID] = None, token_hash: Optional[str] = None) -> Optional[RefreshToken]:
        """
        Đánh dấu một RefreshToken là đã bị thu hồi, dựa trên ID hoặc hash.
        """
        if not token_id and not token_hash:
            return None # Cần ít nhất một định danh

        token_to_revoke: Optional[RefreshToken] = None
        if token_id:
            token_to_revoke = self.get(db, id=token_id)
        elif token_hash:
            token_to_revoke = self.get_by_token_hash(db, token_hash=token_hash)

        if token_to_revoke and not token_to_revoke.is_revoked:
            token_to_revoke.is_revoked = True
            token_to_revoke.updated_at = datetime.now(timezone.utc) # Cập nhật thủ công nếu onupdate không áp dụng cho is_revoked
            db.add(token_to_revoke)
            db.commit()
            db.refresh(token_to_revoke)
        return token_to_revoke

    def revoke_all_for_user(self, db: Session, *, user_id: UUID, except_token_hash: Optional[str] = None) -> int:
        """
        Thu hồi tất cả RefreshTokens cho một user_id cụ thể,
        ngoại trừ một token_hash nhất định (nếu được cung cấp, ví dụ token hiện tại).
        Trả về số lượng token đã bị thu hồi.
        """
        query = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked == False)
            .where(RefreshToken.expires_at > datetime.now(timezone.utc))
        )
        if except_token_hash:
            query = query.where(RefreshToken.token_hash != except_token_hash)

        tokens_to_revoke = db.exec(query).all()
        count = 0
        for token in tokens_to_revoke:
            token.is_revoked = True
            token.updated_at = datetime.now(timezone.utc)
            db.add(token)
            count += 1

        if count > 0:
            db.commit()
            # Không cần refresh từng cái, chỉ cần commit là đủ
        return count

    def revoke_family(self, db: Session, *, user_id: UUID, family_id: UUID, except_token_hash: Optional[str] = None) -> int:
        """
        Thu hồi tất cả RefreshTokens trong cùng một "family" cho một user,
        thường được dùng trong kịch bản phát hiện lạm dụng token rotation.
        """
        if not family_id:
            return 0

        query = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.family == family_id)
            .where(RefreshToken.is_revoked == False)
            # .where(RefreshToken.expires_at > datetime.now(timezone.utc)) # Có thể thu hồi cả token đã hết hạn trong family
        )
        if except_token_hash: # Nếu đang tạo token mới trong family này, không thu hồi nó
             query = query.where(RefreshToken.token_hash != except_token_hash)

        tokens_to_revoke = db.exec(query).all()
        count = 0
        for token in tokens_to_revoke:
            token.is_revoked = True
            token.updated_at = datetime.now(timezone.utc)
            db.add(token)
            count += 1

        if count > 0:
            db.commit()
        return count


    def delete_expired_tokens(self, db: Session) -> int:
        """
        Xóa các RefreshToken đã hết hạn hoặc đã bị thu hồi quá lâu.
        Hàm này có thể được gọi bởi một cron job.
        """
        # Ví dụ: Xóa các token đã hết hạn
        expired_tokens_query = select(RefreshToken).where(RefreshToken.expires_at <= datetime.now(timezone.utc))
        expired_tokens = db.exec(expired_tokens_query).all()

        # Hoặc xóa các token đã bị thu hồi và đã cũ (ví dụ: thu hồi hơn 30 ngày trước)
        # old_revoked_tokens_query = select(RefreshToken).where(RefreshToken.is_revoked == True).where(RefreshToken.updated_at < some_past_date)
        # old_revoked_tokens = db.exec(old_revoked_tokens_query).all()

        count = 0
        for token in expired_tokens: # Thay bằng list token bạn muốn xóa
            db.delete(token)
            count += 1

        if count > 0:
            db.commit()
        return count

# Tạo instance của repository
refresh_token_repo = RefreshTokenRepository(RefreshToken)