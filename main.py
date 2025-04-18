import os

from dotenv import load_dotenv
from gigachat_module.client import get_gigachat_client
from langchain_core.messages import HumanMessage, SystemMessage
from gigachat_module.resume_screening import ResumeScreening
from gigachat_module.parser import get_resume

load_dotenv()

screener = ResumeScreening()
resume_data = get_resume("https://ekaterinburg.hh.ru/resume/0343600aff0c1b1b130039ed1f4a7a6e7a494c")

try:
    if (resume_data[1] >= 24 and resume_data[1] <= 35):
        age_point = 20
    elif (resume_data[1] >= 36 and resume_data[1] <= 42):
        age_point = 10
    elif (resume_data[1] >= 18 and resume_data[1] <= 23):
        age_point = 5
    else:
        age_point = 0
except:
    age_point = 0
try:
    if(resume_data[3] > 60000):
        salary_point = 0
    elif(resume_data[3] >= 30000 and resume_data[3] <= 60000):
        salary_point= 10
    else:
        salary_point = 5
except:
    salary_point = 0
itog = screener.screen_resume(resume_data)
for item in itog:
    print(item)
    