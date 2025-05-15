from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
import hashlib
from redis.asyncio import Redis as redis_async

from app.repositories.refresh_token_repository import refresh_token_repo # Import repo
from app.repositories.user_repository import user_repo
from app.core.security import create_access_token, create_refresh_token, revoke_token, decode_refresh_token
from app.models.refresh_token_model import RefreshToken


class AuthService:
    def __init__(self, user_repository=user_repo, refresh_token_repository=refresh_token_repo):
        self.user_repository = user_repository # User repo từ user_service.py có thể được inject
        self.refresh_token_repository = refresh_token_repository

    def _hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    async def store_refresh_token_in_db(
        self,
        db: Session,
        *,
        user_id: UUID,
        refresh_token_str: str, # Refresh token gốc
        # expires_in_minutes: int, # Sẽ lấy từ payload của refresh_token_str
        family_id: Optional[UUID] = None, # Cho rotation
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        redis_client: redis_async.Redis # Cần để decode token lấy exp và jti
    ):
        # Giải mã token để lấy thời gian hết hạn và jti (jti không lưu vào DB, chỉ để thu hồi ở Redis)
        # Hoặc bạn có thể tính expires_at dựa trên settings.REFRESH_TOKEN_EXPIRE_MINUTES
        # Nếu token_payload được truyền vào thì tốt hơn
        token_payload = await decode_refresh_token(token=refresh_token_str, redis_client=redis_client)
        if not token_payload or not token_payload.exp:
            # Không nên xảy ra nếu token vừa được tạo
            raise ValueError("Could not decode refresh token to get expiration for DB storage")

        hashed_token = self._hash_refresh_token(refresh_token_str)
        expires_at_dt = datetime.fromtimestamp(token_payload.exp, tz=timezone.utc)

        # Kiểm tra xem hash này đã tồn tại chưa (để tránh lỗi unique constraint)
        existing_token = self.refresh_token_repository.get_by_token_hash(db, token_hash=hashed_token)
        if existing_token:
            # Xử lý trường hợp hash đã tồn tại:
            # 1. Nếu là token cũ của cùng user, có thể là lỗi logic hoặc re-submission -> bỏ qua hoặc thu hồi token cũ này
            # 2. Nếu của user khác -> vấn đề hash collision (rất hiếm với SHA256) hoặc lỗi nghiêm trọng
            print(f"Warning: Refresh token hash {hashed_token} already exists in DB.")
            # Có thể chọn cách cập nhật token hiện có thay vì tạo mới, hoặc ném lỗi.
            # Để đơn giản, nếu đã tồn tại và chưa bị thu hồi, có thể không làm gì cả hoặc cập nhật expires_at.
            if existing_token.user_id == user_id and not existing_token.is_revoked:
                print(f"Updating existing refresh token {existing_token.id} for user {user_id}")
                existing_token.expires_at = expires_at_dt
                existing_token.updated_at = datetime.now(timezone.utc)
                # Cập nhật các thông tin khác nếu cần
                self.refresh_token_repository.update(db, db_obj=existing_token, obj_in={"expires_at": expires_at_dt})
                return existing_token # Trả về token đã cập nhật
            else: # Hash tồn tại nhưng của user khác hoặc đã bị thu hồi -> có thể là lỗi
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Refresh token hash conflict")


        # Tạo đối tượng RefreshToken model để lưu
        # RefreshTokenCreateSchema có thể là RefreshTokenBase
        db_refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=hashed_token,
            expires_at=expires_at_dt,
            family=family_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=False
            # id, created_at, updated_at sẽ được BaseModel xử lý
        )
        # Sử dụng create của repository
        created_token = self.refresh_token_repository.create(db, obj_in=db_refresh_token)
        print(f"Refresh token for user {user_id} (ID: {created_token.id}) stored in DB.")
        return created_token


    async def validate_and_process_refresh_token(
        self,
        db: Session,
        *,
        received_refresh_token: str,
        redis_client: redis_async.Redis,
        ip_address: Optional[str] = None, # Để lưu cho token mới nếu rotation
        user_agent: Optional[str] = None  # Để lưu cho token mới nếu rotation
    ) -> dict:
        # 1. Giải mã refresh token và kiểm tra blacklist Redis
        old_token_payload = await decode_refresh_token(token=received_refresh_token, redis_client=redis_client)
        if not old_token_payload or not old_token_payload.sub or not old_token_payload.jti or not old_token_payload.exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token (payload error or blacklisted in Redis)",
            )

        # 2. Hash refresh token nhận được để kiểm tra với DB
        received_token_hash = self._hash_refresh_token(received_refresh_token)

        # 3. Kiểm tra với Database
        db_refresh_token_info = self.refresh_token_repository.get_active_by_token_hash_and_user(
            db, token_hash=received_token_hash, user_id=UUID(old_token_payload.sub) # Giả sử sub là user_id (UUID)
        )

        if not db_refresh_token_info:
            # Token không tìm thấy trong DB, hoặc đã bị thu hồi, hoặc đã hết hạn theo DB
            # Đây là dấu hiệu nghi ngờ token bị đánh cắp nếu nó vẫn còn hợp lệ theo payload (chưa vào blacklist Redis)
            # -> Thu hồi tất cả token trong cùng family (nếu có family_id trong payload hoặc db_refresh_token_info (nếu tìm thấy nhưng is_revoked))
            # hoặc thu hồi tất cả token của user đó.
            user_to_check = self.user_repository.get(db, id=UUID(old_token_payload.sub)) # Lấy user để lấy family hoặc user_id
            if user_to_check:
                print(f"Potential misuse: Refresh token (hash: {received_token_hash}) not valid in DB for user {user_to_check.id}. Revoking family/all tokens.")
                # Lấy family_id từ token cũ (nếu có) hoặc thu hồi tất cả
                family_to_revoke = db_refresh_token_info.family if db_refresh_token_info else None # Hoặc từ payload nếu có
                if family_to_revoke:
                    self.refresh_token_repository.revoke_family(db, user_id=user_to_check.id, family_id=family_to_revoke)
                else:
                    self.refresh_token_repository.revoke_all_for_user(db, user_id=user_to_check.id)

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not valid, revoked in DB, or family compromised.")

        # 4. Lấy thông tin user
        user = self.user_repository.get(db, id=db_refresh_token_info.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        # 5. Tạo Access Token mới
        new_access_token = create_access_token(subject=str(user.id)) # Sử dụng user.id (UUID) làm subject

        # 6. Refresh Token Rotation
        #    a. Thu hồi refresh token cũ trong Redis
        await revoke_token(
            jti=old_token_payload.jti,
            expires_at_timestamp=old_token_payload.exp,
            redis_client=redis_client
        )
        #    b. Thu hồi refresh token cũ trong Database
        self.refresh_token_repository.mark_as_revoked(db, token_id=db_refresh_token_info.id)

        #    c. Tạo Refresh Token mới (cùng family với token cũ)
        new_refresh_token_family = db_refresh_token_info.family or uuid4() # Tạo family mới nếu token cũ không có
        new_refresh_token_str = create_refresh_token(subject=str(user.id))

        #    d. Lưu Refresh Token mới vào Database
        await self.store_refresh_token_in_db(
            db,
            user_id=user.id,
            refresh_token_str=new_refresh_token_str,
            family_id=new_refresh_token_family,
            ip_address=ip_address,
            user_agent=user_agent,
            redis_client=redis_client # Cần để decode token mới lấy exp
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
        }

    async def revoke_all_tokens_for_user_on_logout(
        self,
        db: Session,
        *,
        user_id: UUID,
        current_access_token_jti: Optional[str], # JTI của access token đang dùng để logout
        current_access_token_exp: Optional[int], # EXP của access token đang dùng
        current_refresh_token_str: Optional[str], # Refresh token đang dùng (nếu client gửi)
        redis_client: redis_async.Redis
    ):
        """Thu hồi tất cả refresh token của user trong DB và blacklist token hiện tại."""
        print(f"Revoking all DB refresh tokens for user {user_id}")
        self.refresh_token_repository.revoke_all_for_user(db, user_id=user_id)

        # Blacklist access token hiện tại
        if current_access_token_jti and current_access_token_exp:
            await revoke_token(
                jti=current_access_token_jti,
                expires_at_timestamp=current_access_token_exp,
                redis_client=redis_client
            )

        # Blacklist refresh token hiện tại nếu được cung cấp
        if current_refresh_token_str:
            rt_payload = await decode_refresh_token(token=current_refresh_token_str, redis_client=redis_client) # Kiểm tra lại xem nó có đang bị blacklist không
            if rt_payload and rt_payload.jti and rt_payload.exp: # Chỉ thu hồi ở Redis nếu nó chưa bị blacklist
                 await revoke_token(
                    jti=rt_payload.jti,
                    expires_at_timestamp=rt_payload.exp,
                    redis_client=redis_client
                )
        return True

# Tạo instance
auth_service = AuthService()