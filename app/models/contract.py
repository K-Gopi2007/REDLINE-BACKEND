from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", backref="contracts")
    risk_reports = relationship("RiskReport", back_populates="contract")
    negotiation_reports = relationship("NegotiationReport", back_populates="contract")

class RiskReport(Base):
    __tablename__ = "risk_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    risk_score = Column(Integer)
    risk_level = Column(String) # LOW, MEDIUM, HIGH
    issues = Column(Text) # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    contract = relationship("Contract", back_populates="risk_reports")

class NegotiationReport(Base):
    __tablename__ = "negotiation_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    suggestions = Column(Text) # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    contract = relationship("Contract", back_populates="negotiation_reports")
