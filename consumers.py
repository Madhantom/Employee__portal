import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message
from .utils import send_push_notification


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.receiver_id = self.scope["url_route"]["kwargs"]["receiver_id"]

        if self.scope["user"].is_anonymous:
            await self.close()
            return

        user1 = self.scope["user"].id
        user2 = int(self.receiver_id)

        self.room_name = f"chat_{min(user1, user2)}_{max(user1, user2)}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        sender = self.scope["user"]
        receiver = await self.get_receiver()

        saved_msg = await self.save_message(sender, receiver, message) 

        await self.channel_layer.group_send(
            self.room_name, 
            {
                "type": "chat_message",
                "message": message,
                "sender": sender.username,
                "sender_id": sender.id,
                "created_at": saved_msg["created_at"],
            }
        )

        # 🔔 send browser push to receiver
        await self.send_push(receiver, sender, message)

    @database_sync_to_async
    def send_push(self, receiver, sender, message):
        send_push_notification(
            user=receiver,
            title=f"New message from {sender.username}",
            body=message[:100],
            url=f"/chat/{sender.id}/"
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event.get("message", ""),
            "sender": event["sender"],
            "sender_id": event["sender_id"],
            "created_at": event["created_at"],
            "attachment_url": event.get("attachment_url"),
            "attachment_type": event.get("attachment_type"),
            "attachment_name": event.get("attachment_name"),
        }))

    @database_sync_to_async
    def get_receiver(self):
        return User.objects.get(id=self.receiver_id)

    @database_sync_to_async
    def save_message(self, sender, receiver, message):
        msg = Message.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            is_read=False,
        )
        return {"created_at": msg.created_at.strftime("%H:%M")}