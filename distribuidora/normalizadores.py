import re
import unicodedata


def normalizar_cep(valor):
    numeros = re.sub(r'\D', '', valor)
    if not numeros or len(numeros) > 8:
        return None
    cep = numeros.zfill(8)
    return cep if cep != '00000000' else None


def chave_bairro(nome):
    texto = unicodedata.normalize('NFKD', (nome or '').casefold())
    sem_acentos = ''.join(letra for letra in texto if not unicodedata.combining(letra))
    return ' '.join(re.findall(r'[^\W_]+', sem_acentos))
