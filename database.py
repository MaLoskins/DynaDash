import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, Text, LargeBinary, Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import enum 


Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uploads = relationship("CsvUpload", back_populates="user")

    def __repr__(self):
       return f"<User(id={self.user_id}, username='{self.username}')>"



class ProcessingStatus(enum.Enum):
    uploaded = 'uploaded'
    queued = 'queued'
    processing = 'processing'
    cleaning = 'cleaning'
    visualizing = 'visualizing'
    completed = 'completed'
    failed = 'failed'


class CsvUpload(Base):
    __tablename__ = 'csv_uploads'

    upload_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, index=True) # 添加 ForeignKey 和 index
    original_filename = Column(String, nullable=False)

  
    original_file_content = Column(LargeBinary, nullable=False) 


    file_size = Column(BigInteger) 
    upload_timestamp = Column(DateTime, default=datetime.utcnow)

    # Use SQLAlchemy  Enum to match Python Enum
    status = Column(SQLAlchemyEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.uploaded)

    processing_start_time = Column(DateTime, nullable=True)
    processing_end_time = Column(DateTime, nullable=True)

    # column to store cleaned data  

    cleaned_file_content = Column(LargeBinary, nullable=True) 
 

    visualization_info = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

  
    user = relationship("User", back_populates="uploads")

    def __repr__(self):
       return f"<CsvUpload(id={self.upload_id}, filename='{self.original_filename}', status='{self.status.value}')>"

