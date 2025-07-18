from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = '7518919599:AAFs5Za1EwvBt_AIN5QXZ3tCbmnttVPHfDU'  # <-- Твой токен бота
ADMIN_ID = 876997540          # <-- Твой user_id (куда слать уведомления)

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

    # Новое бизнес-сообщение
    if 'business_message' in data:
        pass  # Можно логировать новые сообщения, если нужно

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

    # Сообщение удалено
    if 'deleted_business_messages' in data:
        try:
            deleted_data = data['deleted_business_messages']
            
            # Проверяем разные возможные структуры данных
            messages = []
            if isinstance(deleted_data, dict) and 'messages' in deleted_data:
                messages = deleted_data['messages']
            elif isinstance(deleted_data, list):
                messages = deleted_data
            else:
                # Если структура неизвестна, пробуем обработать как есть
                messages = [deleted_data] if deleted_data else []
            
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                    
                chat = msg.get('chat', {}).get('title', 'Unknown')
                msg_type = msg.get('type', 'unknown')
                user = msg.get('from', {}).get('username') or msg.get('from', {}).get('first_name', 'Unknown')
                
                caption = (
                    f"<b>Сообщение удалено</b>\n"
                    f"<b>Тип:</b> {msg_type}\n"
                    f"<b>Чат:</b> {chat}\n"
                    f"<b>Пользователь:</b> @{user if user else 'Без username'}\n"
                )
                
                # Текстовые сообщения
                if msg_type == 'text':
                    text = msg.get('text', '[нет текста]')
                    send_to_admin(caption + f"<b>Текст:</b> {text}")
                # Фото
                elif msg_type == 'photo' and 'photo' in msg:
                    file_id = msg['photo']['file_id']
                    send_media_to_admin('Photo', file_id, caption + '[фото]')
                # Документ (файл)
                elif msg_type == 'document' and 'document' in msg:
                    file_id = msg['document']['file_id']
                    send_media_to_admin('Document', file_id, caption + '[документ]')
                # Голосовое сообщение
                elif msg_type == 'voice' and 'voice' in msg:
                    file_id = msg['voice']['file_id']
                    send_media_to_admin('Voice', file_id, caption + '[голосовое сообщение]')
                # Кружок (video_note)
                elif msg_type == 'video_note' and 'video_note' in msg:
                    file_id = msg['video_note']['file_id']
                    send_media_to_admin('VideoNote', file_id, caption + '[кружок]')
                # Видео
                elif msg_type == 'video' and 'video' in msg:
                    file_id = msg['video']['file_id']
                    send_media_to_admin('Video', file_id, caption + '[видео]')
                else:
                    send_to_admin(caption + '[неизвестный тип медиа или нет данных]')
                    
        except Exception as e:
            send_to_admin(f"Ошибка при обработке удалённого сообщения: {str(e)}")

    return 'ok'

if __name__ == '__main__':
    # Исправлено для работы на Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 