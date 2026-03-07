import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE users ADD COLUMN referral_code VARCHAR(20) UNIQUE'))
        print('Added referral_code column')
    except Exception as e:
        print(f'referral_code: {e}')
    
    try:
        conn.execute(text('ALTER TABLE users ADD COLUMN referred_by INTEGER'))
        print('Added referred_by column')
    except Exception as e:
        print(f'referred_by: {e}')
    
    conn.commit()
    print('Migration complete!')
