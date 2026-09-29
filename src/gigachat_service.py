# src/gigachat_service.py

from gigachat import GigaChat
from config import GIGACHAT_KEY, test_query


def format_faq() -> str:
    """Формирует текстовый контекст из словаря test_query"""
    context = ""
    # Читаем вопросы и ответы из заглушки
    for item in test_query:
        context += f"Вопрос: {item['question']}\nОтвет: {item['answer']}\n\n"
    return context


def get_faq_answer(user_message: str) -> str | None:
    """
    Отправляет вопрос в GigaChat вместе с базой знаний.
    Возвращает готовый ответ, либо None, если ответа в базе нет.
    """
    system_prompt = (
        "Ты — виртуальный помощник деканата. Твоя задача — отвечать на вопросы "
        "строго на основе предоставленной базы знаний.\n"
        "Если вопрос пользователя совпадает по смыслу с одним из вопросов в базе, "
        "выведи ТОЛЬКО готовый ответ из базы. Ничего не придумывай.\n"
        "Если в базе нет подходящего ответа, верни ровно одно слово: NOT_FOUND.\n\n"
        f"База знаний:\n{format_faq()}"
    )

    with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
        response = giga.chat({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            # Температура 0.1 делает ответы менее креативными и более точными для FAQ
            "temperature": 0.1
        })

        ai_response = response.choices[0].message.content.strip()

        # Если модель не нашла ответ в FAQ, она вернет флаг NOT_FOUND
        if "NOT_FOUND" in ai_response.upper():
            return None

        return ai_response