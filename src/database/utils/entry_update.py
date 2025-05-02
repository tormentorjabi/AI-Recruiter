import logging

from typing import Optional
from datetime import datetime, timezone

from src.database.session import Session
from src.database.models import Resume


logger = logging.getLogger(__name__)


async def update_candidate_entry_resume_score(resume_id: int, score: int) -> Optional[None]:
    '''Добавить оценку по скринингу резюме в сущность кандидата'''
    try:
        with Session() as db:
            resume = db.query(Resume).get(resume_id)
            
            if not resume:
                logger.warning(f'No resume with ID: {resume_id}')
                return
            
            resume.gigachat_score = score
            resume.analysis_status = 'completed'
            resume.update_at = datetime.now(timezone.utc)
            
            db.commit()

    except Exception as e:
        logger.error(f'Failed to update resume score for resume_id: {resume_id}. {str(e)}')
        return