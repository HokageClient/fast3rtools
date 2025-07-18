from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

BOT_TOKEN = '7518919599:AAFs5Za1EwvBt_AIN5QXZ3tCbmnttVPHfDU'  # <-- Твой токен бота
ADMIN_ID = 876997540          # <-- Твой user_id (куда слать уведомления)

# Хранилище сообщений: message_id -> message_data
messages_store = {}

# Функция для отправки текстовых уведомлений админу
def send_to_admin(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": ADMIN_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

# Функция для пересылки медиа админу
def send_media_to_admin(file_type, file_id, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/send{file_type}"
    data = {
        "chat_id": ADMIN_ID,
        file_type.lower(): file_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if not data:
        return 'ok'

    # Новое бизнес-сообщение - СОХРАНЯЕМ БЕЗ УВЕДОМЛЕНИЙ
    if 'business_message' in data:
        msg = data['business_message']
        message_id = msg.get('message_id')
        if message_id:
            messages_store[message_id] = msg
            # НЕ отправляем отладочную информацию - только сохраняем

    # Сообщение отредактировано
    if 'edited_business_message' in data:
        try:
            old = data['edited_business_message'].get('old_message', {})
            new = data['edited_business_message'].get('new_message', {})
            chat = data['edited_business_message'].get('chat', {}).get('title', 'Unknown')
            user = new.get('from', {}).get('username') or new.get('from', {}).get('first_name', 'Unknown')
            send_to_admin(
                f"<b>Сообщение отредактировано</b>\n"
                f"<b>Пользователь:</b> @{user if user else 'Без username'}\n"
                f"<b>Чат:</b> {chat}\n"
                f"<b>Старое:</b> {old.get('text', '[медиа]')}\n"
                f"<b>Новое:</b> {new.get('text', '[медиа]')}"
            )
        except Exception as e:
            send_to_admin(f"Ошибка при обработке отредактированного сообщения: {str(e)}")

    # Сообщение удалено - ИСПРАВЛЕНО
    if 'deleted_business_messages' in data:
        try:
            deleted_data = data['deleted_business_messages']
            chat = deleted_data.get('chat', {})
            chat_title = chat.get('first_name', 'Unknown')
            if chat.get('username'):
                chat_title = f"@{chat['username']}"
            
            # Получаем ID удалённых сообщений
            message_ids = deleted_data.get('message_ids', [])
            
            for message_id in message_ids:
                # Ищем сохранённое сообщение
                if message_id in messages_store:
                    msg = messages_store[message_id]
                    
                    # Получаем информацию о пользователе
                    user_info = msg.get('from', {})
                    user_name = user_info.get('username') or user_info.get('first_name', 'Unknown')
                    if user_info.get('username'):
                        user_name = f"@{user_info['username']}"
                    
                    # Определяем тип сообщения
                    msg_type = 'text'
                    if 'photo' in msg:
                        msg_type = 'photo'
                    elif 'document' in msg:
                        msg_type = 'document'
                    elif 'voice' in msg:
                        msg_type = 'voice'
                    elif 'video_note' in msg:
                        msg_type = 'video_note'
                    elif 'video' in msg:
                        msg_type = 'video'
                    
                    caption = (
                        f"<b>Сообщение удалено</b>\n"
                        f"<b>Тип:</b> {msg_type}\n"
                        f"<b>Чат:</b> {chat_title}\n"
                        f"<b>Пользователь:</b> {user_name}\n"
                    )
                    
                    # Обрабатываем по типу
                    if msg_type == 'text':
                        text = msg.get('text', '[нет текста]')
                        send_to_admin(caption + f"<b>Текст:</b> {text}")
                    elif msg_type == 'photo':
                        file_id = msg['photo']['file_id']
                        send_media_to_admin('Photo', file_id, caption + '[фото]')
                    elif msg_type == 'document':
                        file_id = msg['document']['file_id']
                        send_media_to_admin('Document', file_id, caption + '[документ]')
                    elif msg_type == 'voice':
                        file_id = msg['voice']['file_id']
                        send_media_to_admin('Voice', file_id, caption + '[голосовое сообщение]')
                    elif msg_type == 'video_note':
                        # ИСПРАВЛЕНО: правильно извлекаем file_id для кружка
                        file_id = msg['video_note']['file_id']
                        send_media_to_admin('VideoNote', file_id, caption + '[кружок]')
                    elif msg_type == 'video':
                        file_id = msg['video']['file_id']
                        send_media_to_admin('Video', file_id, caption + '[видео]')
                    else:
                        send_to_admin(caption + '[неизвестный тип медиа]')
                    
                    # Удаляем из хранилища
                    del messages_store[message_id]
                else:
                    send_to_admin(f"<b>Сообщение удалено</b>\n<b>ID:</b> {message_id}\n<b>Чат:</b> {chat_title}\n[сообщение не найдено в кэше]")
                    
        except Exception as e:
            send_to_admin(f"Ошибка при обработке удалённого сообщения: {str(e)}")

    return 'ok'

if __name__ == '__main__':
    # Исправлено для работы на Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 