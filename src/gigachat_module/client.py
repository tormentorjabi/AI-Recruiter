import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat


load_dotenv()


SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
MODEL = os.getenv("GIGACHAT_MODEL")
CERTIFICATE_BUNDLE_FILE = os.getenv("CA_BUNDLE_FILE")


def get_gigachat_client() -> GigaChat:
    try:
        if not AUTH_KEY:
            raise ValueError("GigaChat credentials not found in environmental variables.")
        
        giga =  GigaChat(
            credentials=AUTH_KEY,
            model=MODEL,
            scope=SCOPE,
            verify_ssl_certs=False,
            # ca_bundle_file="russian_trusted_root_ca.cer",
        )
        
        return giga
    
    except Exception as e:
        print(f'Error initializing GigaChat client: {e}')
        raise
    