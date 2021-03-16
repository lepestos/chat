import json
from django.contrib.auth import get_user_model
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Message, ChatRoom

User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def fetch_messages(self, data):
        """
        Loads first 10 messages
        """
        messages = Message.last_10_messages(self.chat, 0)
        content = {
            'command': 'fetch_messages',
            'messages': self.messages_to_json(messages)
        }
        self.send_message(content)

    def new_message(self, data):
        """
        Adds new message to database
        """
        author = data['from']
        if self.chat_type == 0:
            is_read = True
        else:
            is_read = False
        author_user = User.objects.filter(username=author)[0]
        message = Message.objects.create(author=author_user,
                                         content=data['message'],
                                         chat_room=self.chat,
                                         is_read=is_read)
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message),
        }
        return self.send_chat_message(content)

    def add_messages(self, data):
        """
        Fetches 10 additional messages when the chat window
        is being scrolled up
        """
        order = data['order']
        messages = Message.last_10_messages(self.chat, order)
        content = {
            'command': 'add_messages',
            'messages': self.messages_to_json(messages)
        }
        self.send_message(content)

    def delete_message(self, data):
        """
        Deletes the message from database
        """
        message_id = data['id']
        initiator_name = data['initiator']
        try:
            message = Message.objects.get(id=message_id)
            initiator = User.objects.get(username=initiator_name)
        except Message.DoesNotExist:
            return
        except User.DoesNotExist:
            return
        if (initiator_name == message.author.username or
            initiator_name == self.chat.owner.username or
            initiator in self.chat.moderators.all()) and \
                initiator not in self.chat.black_list.all():
            message.delete()

    def edit_message(self, data):
        """
        Edits the message
        """
        message_id = data['id']
        message_content = data['message_content']
        initiator_name = data['initiator']
        try:
            message = Message.objects.get(id=message_id)
            initiator = User.objects.get(username=initiator_name)
        except Message.DoesNotExist:
            return
        except User.DoesNotExist:
            return

        if (initiator_name == message.author.username or
            initiator_name == self.chat.owner.username or
            initiator in self.chat.moderators.all()) and \
                initiator not in self.chat.black_list.all():
            message.content = message_content
            message.save()

    def read_message(self, data):
        message_id = data['id']
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return
        message.read()


    def messages_to_json(self, messages):
        json_messages = []
        for message in messages:
            json_messages.append(self.message_to_json(message))
        return json_messages

    def message_to_json(self, message):
        """
        Converts message to json format
        """
        st = str(message.timestamp)
        st = st[:st.find('.')]
        return {
            'author': message.author.username,
            'content': message.content,
            'timestamp': st,
            'id': message.id,
            'is_read': message.is_read
        }

    # dictionary of commands sent by websocket
    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message,
        'add_messages': add_messages,
        'delete_message': delete_message,
        'edit_message': edit_message,
        'read_message': read_message,
    }

    def connect(self):
        # accept connection
        self.user = self.scope['user']
        self.chat_name = self.scope['url_route']['kwargs']['chat_name']
        self.chat = ChatRoom.objects.get(slug=self.chat_name)
        self.room_group_name = 'chat_%s' % self.chat_name
        self.chat_type = self.chat.chat_type
        # join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )
        self.accept()

    def disconnect(self, close_code):
        # leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # send command to the corresponding method
        self.commands[text_data_json['command']](self, text_data_json)

    def send_chat_message(self, message):
        now = timezone.now()
        # send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.username,
                'datetime': now.isoformat(),
            }
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    def chat_message(self, event):
        text_data = json.dumps(event['message'])
        self.send(text_data=text_data)
