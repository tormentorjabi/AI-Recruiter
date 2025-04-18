'''
    - Date of removal from database schema: 
        //  17-04-2025
    
    - Reason for removal:
        //  As of right now it's certain that separate model representing
        //  candidate's answers from Telegram bot's interactions is meaningless,
        //  since it's much easier and logically correct to capture answers within
        //  the BotInteraction instance itself.

        //  The schema for CandidateAnswer had a fundamental flaw which is a column
        //  to store GigaChat response (gigachat_response field), but the answer instance
        //  itself doesn't serve a purpose outside of BotInteraction.

        //  The solution would be to interpret CandidateAnswer as a collection of all the
        //  answers provided by the candidate and store big string of combined answers in 
        //  the answer_text field.

        //  But the more I think about it, less sense it all makes. Current implementation
        //  of candidate-side logic of our Telegram bot completely ignores CandidateAnswer model
        //  and instead encapsulates answers as JSON values, that can be easily tied out to the 
        //  between instances of [BotQuestions - BotInteractions - Applications - Candidates]
        
    - Related Alembic migration code:
        //  d54d626526f3
'''
# from sqlalchemy import (
#     Column,
#     ForeignKey,
#     Integer, 
#     Text,
#     DateTime
# )
# from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.orm import relationship
# from src.database.session import Base
# from datetime import datetime


# class CandidateAnswer(Base):
#     """
#     Модель ответов кандидата в Telegram боте
    
#     Fields:
#         candidate_id (int): FK на соискателя по вакансии
#         question_id (int): FK на текущий вопрос из банка вопросов
#         application_id (int): FK на отклик
#         answer_text (text): Подготовленные и обобщенные ответы кандидата, для их отправки в GigaChat
#         gigachat_response (JSONB): Последний результат GigaChat по ответам из Telegram бота
#         created_at (datetime): Дата создания записи
#         updated_at (datetime): Время обновления записи
#     """
#     __tablename__ = 'candidate_answers'
    
#     id = Column(Integer, primary_key=True)
#     candidate_id = Column(Integer, ForeignKey('candidates.id'))
#     question_id = Column(Integer, ForeignKey('bot_questions.id'))
#     application_id = Column(Integer, ForeignKey('applications.id'))
#     # Аналогично с resumes.parsed_text предлагаю сохранять здесь итоговую строку,
#     # сконструированную из ответов кандидата, которую будем отправлять на обработку
#     # в GigaChat
#     # Открыто для обсуждения.
#     answer_text = Column(Text)
#     gigachat_response = Column(JSONB)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime)
    
#     candidate = relationship("Candidate", back_populates="answers")
#     question = relationship("BotQuestion", back_populates="answers")
#     application = relationship("Application", back_populates="answers")
    