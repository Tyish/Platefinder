from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    database_url: str = "sqlite:///./numberplates.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Optional YOLO plate detector (.pt weights). Leave empty to use OpenCV contours only.
    yolo_model_path: str = ""
    yolo_confidence: float = 0.35

    # RTSP capture timeout (seconds)
    rtsp_timeout_seconds: int = 12

    # Email (SMTP)
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    notify_email_to: str = ""

    # SMS (Twilio-compatible REST API)
    sms_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    notify_sms_to: str = ""


settings = Settings()
