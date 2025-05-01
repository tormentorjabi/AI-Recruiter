import logging

from datetime import datetime, timezone

from src.database.session import Session
from src.database.models import Resume


logger = logging.getLogger(__name__)


async def update_candidate_entry_resume_score(resume_id: int, score: int) -> None:
    '''Добавить оценку по скринингу резюме в сущность кандидата'''
    try:
        with Session() as db:
            resume = db.query(Resume).get(resume_id)
            if resume:
                resume.gigachat_score = score
                resume.analysis_status = 'completed'
                resume.update_at = datetime.now(timezone.utc)
                db.commit()
                return
            return
    except Exception as e:
        logger.error(f'Failed to update resume score for resume_id: {resume_id}. {str(e)}')
        return