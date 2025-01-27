<template>
  <div class="chat-container">
    <div class="chat-rooms">
      <div class="rooms-header">
        <h2>채팅방 목록</h2>
        <button @click="createRoom" class="create-room-btn">
          <i class="fas fa-plus"></i> 새 채팅방
        </button>
      </div>
      
      <div class="rooms-list">
        <div 
          v-for="room in chatRooms" 
          :key="room.id"
          :class="['room-item', { active: currentRoom?.id === room.id }]"
          @click="selectRoom(room)"
        >
          <div class="room-info">
            <h3>{{ room.name }}</h3>
            <p class="last-message">{{ room.last_message || '새로운 채팅방' }}</p>
          </div>
          <span class="room-date">{{ formatDate(room.created_at) }}</span>
        </div>
      </div>
    </div>

    <div class="chat-area" v-if="currentRoom">
      <div class="chat-header">
        <h2>{{ currentRoom.name }}</h2>
        <div class="chat-actions">
          <button class="invite-btn">초대하기</button>
        </div>
      </div>

      <div class="messages" ref="messageContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', { 'my-message': message.username === username }]"
        >
          <div class="message-info">
            <span class="message-username">{{ message.username }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-content">{{ message.content }}</div>
        </div>
      </div>

      <div class="chat-input">
        <input 
          v-model="newMessage" 
          @keyup.enter="sendMessage"
          placeholder="메시지를 입력하세요..."
          :disabled="!wsConnected"
        />
        <button @click="sendMessage" :disabled="!wsConnected">
          <i class="fas fa-paper-plane"></i>
        </button>
      </div>
    </div>

    <div class="no-room-selected" v-else>
      <div class="no-room-message">
        <i class="fas fa-comments"></i>
        <p>채팅방을 선택해주세요</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

export default {
  name: 'ChatRooms',
  setup() {
    const chatRooms = ref([]);
    const currentRoom = ref(null);
    const messages = ref([]);
    const newMessage = ref('');
    const wsConnected = ref(false);
    const ws = ref(null);
    const username = ref(localStorage.getItem('username'));
    const messageContainer = ref(null);

    const loadChatRooms = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await axios.get('http://localhost:8002/chat/rooms', {
          headers: { Authorization: `Bearer ${token}` }
        });
        chatRooms.value = response.data;
      } catch (error) {
        console.error('채팅방 목록 로딩 실패:', error);
      }
    };

    const connectWebSocket = (roomId) => {
      const token = localStorage.getItem('access_token');
      ws.value = new WebSocket(`ws://localhost:8002/chat/ws/${roomId}?token=${token}`);

      ws.value.onopen = () => {
        wsConnected.value = true;
        console.log('WebSocket 연결됨');
      };

      ws.value.onmessage = (event) => {
        const message = JSON.parse(event.data);
        messages.value.push(message);
        scrollToBottom();
      };

      ws.value.onclose = () => {
        wsConnected.value = false;
        console.log('WebSocket 연결 끊김');
      };
    };

    const selectRoom = (room) => {
      if (ws.value) {
        ws.value.close();
      }
      currentRoom.value = room;
      messages.value = [];
      connectWebSocket(room.id);
    };

    const sendMessage = () => {
      if (newMessage.value.trim() && ws.value && wsConnected.value) {
        ws.value.send(JSON.stringify({
          message: newMessage.value
        }));
        newMessage.value = '';
      }
    };

    const scrollToBottom = () => {
      if (messageContainer.value) {
        setTimeout(() => {
          messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
        }, 50);
      }
    };

    const formatDate = (date) => {
      return new Date(date).toLocaleDateString();
    };

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    };

    onMounted(() => {
      loadChatRooms();
    });

    onUnmounted(() => {
      if (ws.value) {
        ws.value.close();
      }
    });

    return {
      chatRooms,
      currentRoom,
      messages,
      newMessage,
      wsConnected,
      username,
      messageContainer,
      selectRoom,
      sendMessage,
      formatDate,
      formatTime
    };
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
  margin-top: 60px;
  background-color: #f5f5f5;
}

.chat-rooms {
  width: 300px;
  background: white;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
}

.rooms-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.create-room-btn {
  padding: 8px 12px;
  background: #742DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.rooms-list {
  flex: 1;
  overflow-y: auto;
}

.room-item {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.room-item:hover {
  background-color: #f8f9fa;
}

.room-item.active {
  background-color: #f0f2ff;
}

.room-info h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.last-message {
  margin: 5px 0 0;
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.room-date {
  font-size: 12px;
  color: #999;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-actions button {
  padding: 8px 12px;
  background: #742DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f8f9fa;
}

.message {
  margin-bottom: 20px;
  max-width: 70%;
}

.message.my-message {
  margin-left: auto;
}

.message-info {
  margin-bottom: 5px;
  font-size: 12px;
}

.message-username {
  font-weight: 600;
  color: #333;
}

.message-time {
  color: #999;
  margin-left: 8px;
}

.message-content {
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.my-message .message-content {
  background: #742DDD;
  color: white;
}

.chat-input {
  padding: 20px;
  background: white;
  border-top: 1px solid #eee;
  display: flex;
  gap: 10px;
}

.chat-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.chat-input button {
  padding: 10px 20px;
  background: #742DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.no-room-selected {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8f9fa;
}

.no-room-message {
  text-align: center;
  color: #666;
}

.no-room-message i {
  font-size: 48px;
  margin-bottom: 10px;
  color: #742DDD;
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }

  .chat-rooms {
    width: 100%;
    height: 50%;
  }

  .chat-area {
    height: 50%;
  }
}
</style> 