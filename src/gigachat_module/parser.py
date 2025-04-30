import os
import re
import logging
import asyncio
import aiohttp

from datetime import date
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, List, Union, Tuple


logger = logging.getLogger(__name__)
load_dotenv()


'''
    TODO:
        - Данные об образовании (см. models/Education);
        - Данные об уровне владения навыком (см models/CandidateSkill.proficiency)
'''



HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}

COOKIES = {
    "hhuid": os.getenv("HH_UID"),
    "hhtoken": os.getenv("HH_TOKEN")
}


@dataclass
class EmploymentInfo:
    employment_type: Optional[str]
    work_schedule: Optional[str]

@dataclass
class WorkExperienceInfo:
    company: str
    position: str
    # Период работы хранится в формате: 
    # 1) Tuple['YYYY-MM', 'YYYY-MM'] - если дата окончания имеется
    # 2) Tuple['YYYY-MM', None] - если работа по настоящее время
    period: Tuple[Optional[str], Optional[str]]
    description: str

@dataclass
class ResumeData:
    link: str
    vacancy_id: int
    name: Optional[str]
    age: Optional[int]
    birthdate: Optional[date]
    address: Optional[str]
    citizenship: Optional[str]
    ready_to_relocate: Optional[bool]
    job_search_status: Optional[str]
    salary: Optional[int]
    position: Optional[str]
    skills: Optional[List[str]]
    experiences: Optional[List[WorkExperienceInfo]]
    employment: Optional[EmploymentInfo]
    
    def to_list(self) -> list:
        experience_summary = None
        skills_summary = None
        employment_summary = None
        
        if not self.experiences is None:
            experience_summary = "\n".join(
                f"Компания: {exp.company}; Должность: {exp.position}; "
                f"Период: {exp.period}; Описание: {exp.description}"
                for exp in self.experiences
            )
            
        if not self.skills is None:
            skills_summary = ", ".join(self.skills)
            
        if not self.employment is None:
            employment_summary = f"Занятость: {self.employment.employment_type}; График работы: {self.employment.work_schedule}"
            
        return [
            self.link,
            self.name,
            self.age,
            self.birthdate,
            self.address,
            self.citizenship,
            self.ready_to_relocate,
            self.job_search_status,
            self.salary,
            self.position,
            skills_summary,
            experience_summary,
            employment_summary,
        ]
    

async def _fetch_html(
    url: str,
    session: aiohttp.ClientSession
) -> Optional[str]:
    try:
        async with session.get(
            url=url, 
            headers=HEADERS,
            cookies=COOKIES
        ) as response:
            response.raise_for_status()
            return await response.text()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f'Error fetching resume from {url}. Message: {e}')
        return None


def _parse_russian_date(date_str: str) -> Optional[date]:
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    try:
        parts = date_str.strip().split()
        day = int(parts[0])
        month = months[parts[1]]
        year = int(parts[2])
        return date(year, month, day)
    except (ValueError, IndexError, KeyError) as e:
        logger.error(f'Error while parse_russian_date: {str(e)}')
        return None


def _extract_text(
    soup: BeautifulSoup, 
    selector: str, 
    default: str = "Не указано"
) -> Union[str, None]:
    try:
        element = soup.select_one(selector)
        return element.text.strip() if element else default
    except Exception as e:
        logger.error(f"Error in _extract_text: {str(e)}")
        return None


def _extract_citizenship(soup: BeautifulSoup) -> Union[str, None]:
    try:
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text.startswith("Гражданство"):
                return text.replace("Гражданство:", "").strip()
        return None
    except Exception as e:
        logger.error(f'Error in _extract_citizenship: {str(e)}')
        return None
   

def _extract_relocation_info(soup: BeautifulSoup) -> Union[bool, None]:
    try:
        relocation_info_p = soup.find('p', string=lambda text: text and 'переезду' in text)
        if relocation_info_p:
            relocation_text = relocation_info_p.get_text(strip=True).lower()
            return True if ["готов к переезду", "готова к переезду"] in relocation_text else False
        return None
    except Exception as e:
        logger.error(f'Error in _extract_relocation_info: {str(e)}')
        return None


def _extract_age(soup: BeautifulSoup) -> Union[int, None]:
    try:
        age_element = soup.find("span", {"data-qa": "resume-personal-age"}).text.strip()
        if age_element:
            match = re.search(r'(\d+)', age_element)
            return int(match.group(1)) if match else None
        return None
    except Exception as e:
        logger.error(f'Error in _extract_age: {str(e)}')
        return None
    

def _extract_salary(soup: BeautifulSoup) -> Union[int, None]:
    try:
        salary_element = soup.find("span", {"data-qa": "resume-block-salary"}) 
        if salary_element:
            digits = re.sub(r"[^\d]", "", salary_element.text.strip())
            return int(digits) if digits else None
    except Exception as e:
        logger.error(f'Error in _extract_salary: {str(e)}')
        return None
    

def _parse_month_year(month_year_str: str) -> Optional[str]:
    month_map = {
        'январь': '01', 'января': '01',
        'февраль': '02', 'февраля': '02',
        'март': '03', 'марта': '03',
        'апрель': '04', 'апреля': '04',
        'май': '05', 'мая': '05',
        'июнь': '06', 'июня': '06',
        'июль': '07', 'июля': '07',
        'август': '08', 'августа': '08',
        'сентябрь': '09', 'сентября': '09',
        'октябрь': '10', 'октября': '10',
        'ноябрь': '11', 'ноября': '11',
        'декабрь': '12', 'декабря': '12'
    }
    
    try:
        parts = month_year_str.split()
        if len(parts) < 2:
            return None
        
        month_part = parts[0].lower()
        year = parts[1]
        
        if len(year) > 4:
            year = year[:4]
        
        month = month_map.get(month_part)
        if not month:
            return None
        
        return f'{year}-{month}'
        
    except Exception as e:
        logger.error(f'Error while trying to _parse_month_year: {month_year_str}.\nError:{str(e)}')
        return None


def _parse_date_entry(entry: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        lines = entry.split('\n')
        if len(lines) < 1:
            return None, None
        
        date_range = lines[0].strip()
        
        if "по настоящее время" in date_range:
            start_part = date_range.split("—")[0].strip()
            start_date = _parse_month_year(start_part)
            return start_date, None
        
        if "—" in date_range:
            start_part, end_part = date_range.split("—")
            start_date = _parse_month_year(start_part.strip())
            end_date = _parse_month_year(end_part.strip())
            return start_date, end_date
        
        return None, None
            
    except Exception as e:
        logger.error(f'Error while trying to parse date entry: {entry}.\nError:{str(e)}')
        return None, None
    

def _extract_experiences(soup: BeautifulSoup) -> List[WorkExperienceInfo]:
    try:
        experiences = []
        experience_section = soup.find("div", {"data-qa": "resume-block-experience"})
        
        if not experience_section:
            return experiences
        
        for block in experience_section.find_all("div", class_="resume-block-item-gap"):
            # Ищем нужные подблоки
            company = block.find("div", {"class": "bloko-text bloko-text_strong"})
            position = block.find("div", {"data-qa": "resume-block-experience-position"})
            period = block.find("div", {"class": "bloko-column bloko-column_xs-4 bloko-column_s-2 bloko-column_m-2 bloko-column_l-2"})
            description = block.find("div", {"data-qa": "resume-block-experience-description"})
            # Очищаем данные, собираем опыт вместе
            experience = WorkExperienceInfo(
                company=company.text.strip().replace('\xa0', ' ').replace('\n', ' ') if company else "",
                position=position.text.strip().replace('\xa0', ' ').replace('\n', ' ') if position else "",
                period=_parse_date_entry(period.text.strip().replace('\xa0', ' ')) if period else "",
                description=description.text.strip().replace('\xa0', ' ').replace('\n', ' ') if description else ""
            )
            # Проверка на дубли
            if experience not in experiences:
                experiences.append(experience)
                
        return experiences
    
    except Exception as e:
        logger.error(f'Error in _extract_experiences: {str(e)}')
        return None


def _extract_skills(soup: BeautifulSoup) -> List[str]:
    try:
        skills_section = soup.find("div", {"data-qa": "skills-table"})
        if not skills_section:
            return []
        
        return [
            span.get_text(strip=True) 
            for span in skills_section.find_all("span") 
            if span.get_text(strip=True)
        ]
    except Exception as e:
        logger.error(f'Error in _extract_skills: {str(e)}')
        return None
    

def _extract_employment_info(soup: BeautifulSoup) -> Optional[EmploymentInfo]:
    try:
        employment_type = None
        work_schedule = None
        
        containers = soup.find_all("div", class_="resume-block-container")
        for container in containers:
            paragraphs = container.find_all("p")
            for p in paragraphs:
                text = p.get_text(strip=True)
                if "Занятость" in text:
                        employment_type = text.replace("Занятость:", "").strip()
                elif "График работы" in text:
                        work_schedule = text.replace("График работы:", "").strip()
        
        if employment_type is None or work_schedule is None:
            return None
        
        return EmploymentInfo(
            employment_type=employment_type,
            work_schedule=work_schedule
        )
        
    except Exception as e:
        logger.error(f'Error in _extract_employment_info: {str(e)}')
        return None
    

async def parse_resume(
    url: str,
    vacancy_id: int,
    session: Optional[aiohttp.ClientSession] = None
) -> Optional[ResumeData]:
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
        
    try:
        html = await _fetch_html(url, session)
        if not html:
            logger.error(f'Error: Content was None after HTML fetch from {url}')
            return None
        soup = BeautifulSoup(html, "html.parser")

        link = url
        birthday_tag = soup.find('span', {'data-qa': 'resume-personal-birthday'})
        birthdate = _parse_russian_date(birthday_tag.text) if birthday_tag else None
        name = _extract_text(soup, "h2[data-qa='resume-personal-name']", "ФИО не указано")
        address = _extract_text(soup, "span[data-qa='resume-personal-address']", "Адрес не указан")
        citizenship = _extract_citizenship(soup)
        ready_to_relocate = _extract_relocation_info(soup)
        job_search_status_text = _extract_text(soup, "span[data-qa='job-search-status']", "Статус не указан")
        job_search_status = job_search_status_text.replace('\xa0', ' ') if job_search_status_text else None
        age = _extract_age(soup)
        position = _extract_text(soup, "span[data-qa='resume-block-title-position']", "Должность не указана")
        salary = _extract_salary(soup)
        experiences = _extract_experiences(soup)
        skills = _extract_skills(soup)
        employment = _extract_employment_info(soup)
        
        return ResumeData(
            link=link,
            vacancy_id=vacancy_id,
            name=name,
            age=age,
            birthdate=birthdate,
            address=address,
            citizenship=citizenship,
            ready_to_relocate=ready_to_relocate,
            job_search_status=job_search_status,
            position=position,
            salary=salary,
            experiences=experiences,
            skills=skills,
            employment=employment
        )
        
    except Exception as e:
        logger.error(f'Error in get_resume: {str(e)}')
        return None

    finally:
        if close_session and not session.closed:
            await session.close()
            
            
async def parse_multiple_resumes(resumes_data: List[Tuple[str, int]]) -> List[Optional[ResumeData]]:
    async with aiohttp.ClientSession() as session:
        tasks = [
            parse_resume(url, vacancy_id, session) 
            for url, vacancy_id in resumes_data
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)