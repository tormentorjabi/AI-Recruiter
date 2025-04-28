import requests
from bs4 import BeautifulSoup
import re
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()


def parse_russian_date(date_str: str) -> date:
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    parts = date_str.strip().split()
    day = int(parts[0])
    month = months[parts[1]]
    year = int(parts[2])
    return date(year, month, day)

def get_resume(url):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    cookies = {
    "hhuid": os.getenv("HH_UID"),
    "hhtoken": os.getenv("HH_TOKEN"),
    }
    response = requests.get(url, headers=headers, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Дата рождения
        try:
            birthday_tag = soup.find('span', {'data-qa': 'resume-personal-birthday'})
            birthdate = parse_russian_date(birthday_tag.text) if birthday_tag else None
        except Exception as e:
            birthdate = None

        # Имя
        h2 = soup.find("h2", {"data-qa": "resume-personal-name"})
        if h2:
            name = h2.text.strip()
        else:
            name = "ФИО не указанно"
        # Сколько лет

        # Адрес (город проживания)
        try:
            address_tag = soup.find('span', {'data-qa': 'resume-personal-address'})
            address = address_tag.text.strip() if address_tag else "Адрес не указан"
        except:
            address = "Адрес не указан"

        # Гражданство
        try:
            citizenship = "Гражданство не указано"
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text.startswith("Гражданство"):
                    citizenship = text.replace("Гражданство:", "").strip()
                    break
        except:
            citizenship = "Гражданство не указано"

        # Готовность к переезду (bool)
        try:
            relocation_info_p = soup.find('p', string=lambda text: text and 'переезду' in text)
            if relocation_info_p:
                relocation_text = relocation_info_p.get_text(strip=True).lower()
                ready_to_relocate = "готов к переезду" in relocation_text or "готова к переезду" in relocation_text
            else:
                ready_to_relocate = False
        except:
            ready_to_relocate = False

        # Статус поиска работы
        try:
            status_span = soup.find("span", {"data-qa": "job-search-status"})
            job_search_status = status_span.get_text(strip=True) if status_span else "Статус не указан"
        except:
            job_search_status = "Статус не указан"

        # Возраст
        try:
            age = soup.find("span", {"data-qa": "resume-personal-age"}).text.strip()
            match = re.search(r'(\d+)', age) 
            if match:
                    age = int(match.group(1))
            else:
                    age = "Возраст отсутствует"
        except:
            age = "Возраст отсутствует"
        # Должность
        try:
            position = soup.find("span", {"data-qa": "resume-block-title-position"}).text.strip()
        except:
            position = "Должность не найдена"

        # Зарплата
        salary_elem = soup.find("span", {"data-qa": "resume-block-salary"}) 
        if salary_elem:
            salary = salary_elem.text.strip()
            digits = re.sub(r"[^\d]", "", salary)
            salary = int(digits)
        else:
            salary = "Зараплата не указанна"

        # Опыт работы
        experience_section = soup.find("div", {"data-qa": "resume-block-experience"})
        experience_blocks = experience_section.find_all("div", class_="resume-block-item-gap")
        experience_list = []

        for block in experience_blocks:
        # Ищем нужные подблоки
            company_elem = block.find("div", {"class": "bloko-text bloko-text_strong"})
            position_elem = block.find("div", {"data-qa": "resume-block-experience-position"})
            period_elem = block.find("div", {"class": "bloko-column bloko-column_xs-4 bloko-column_s-2 bloko-column_m-2 bloko-column_l-2"})    
            description_elem = block.find("div", {"data-qa": "resume-block-experience-description"})

            # Получаем текст, если блок найден
            company = company_elem.text.strip() if company_elem else ""
            position = position_elem.text.strip() if position_elem else ""
            period = period_elem.text.strip() if period_elem else ""
            description = description_elem.text.strip() if description_elem else ""

            # Собираем в словарь
            experience = {
                "Компания": company,
                "Должность": position,
                "Период": period,
                "Описание": description
            }

            # Проверка на дубли (можно по компании + должности)
            if experience not in experience_list:
                experience_list.append(experience)
                
        # Очистка
        cleaned_experience = []
        for exp in experience_list:
            cleaned_exp = {key: value.replace('\xa0', ' ').replace('\n', ' ') for key, value in exp.items()}
            cleaned_experience.append(cleaned_exp)

        experience_summary = ""
        for exp in cleaned_experience:
            exp_str = f"Компания: {exp['Компания']}; Должность: {exp['Должность']}; Период: {exp['Период']}; Описание: {exp['Описание']}"
            experience_summary += exp_str + "\n"

        # Навыки
        skills_section = soup.find("div", {"data-qa": "skills-table"})
        skills_list = []

        if skills_section:
            spans = skills_section.find_all("span")
            for span in spans:
                skill = span.get_text(strip=True)
                if skill:  # Проверим, чтобы не было пустых значений
                    skills_list.append(skill)
        else:
            skills_list = "Навыки отсутствуют"

        skills_summary = ", ".join(skills_list) if isinstance(skills_list, list) and skills_list else "Навыки отсутствуют"
        # Занятость и График работы
        containers = soup.find_all("div", class_="resume-block-container")

        employment_info = {}

        for container in containers:
            paragraphs = container.find_all("p")
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:  # Пропускаем пустые строки
                    if "Занятость" in text:
                        employment_info["Занятость"] = text.replace("Занятость:", "")
                    elif "График работы" in text:
                        employment_info["График работы"] = text.replace("График работы:", "")
        if employment_info["Занятость"] == False:
            employment_info["Занятость"] = " Занятость не указанна"
        if employment_info["График работы"] == False:
            employment_info["График работы"] = "График работы не указан"

        employment = {
            "Занятость": employment_info.get("Занятость", "Занятость не указана"),
            "График работы": employment_info.get("График работы", "График работы не указан")
        }

        # Преобразуем в строку
        employment_summary = f"Занятость: {employment['Занятость']}; График работы: {employment['График работы']}"


        all_data= [name, age, position, salary, experience_summary, skills_summary, employment_summary, birthdate, address, citizenship, ready_to_relocate, job_search_status]
        return all_data
    else:
        print(f"Ошибка: статус код {response.status_code}")
