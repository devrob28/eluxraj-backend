from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.models.signal import Signal, SignalDelivery

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created!")
