<template>
  <div class="chat-container">
    <!-- 채팅방 목록 -->
    <div class="chat-rooms">
      <div class="rooms-header">
        <h2>채팅방 목록</h2>
        <button @click="showCreateRoomModal = true" class="create-room-btn">
          <span class="material-icons">add</span>
          새 채팅방
        </button>
      </div>

      <!-- 로딩 상태 -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>채팅방을 불러오는 중...</p>
      </div>

      <!-- 채팅방 리스트 -->
      <div class="rooms-list" v-else-if="chatRooms.length > 0">
        <div 
          v-for="room in chatRooms" 
          :key="room.id"
          :class="['room-item', { active: currentRoom && currentRoom.id === room.id }]"
          @click="selectRoom(room)"
        >
          <div class="room-info">
            <h3>{{ room.name }}</h3>
            <p class="last-message">{{ room.last_message || '새로운 채팅방' }}</p>
          </div>
          <span class="room-date">{{ formatDate(room.created_at) }}</span>
        </div>
      </div>

      <!-- 빈 채팅방 상태 -->
      <div v-else class="empty-state">
        <span class="material-icons">chat_bubble_outline</span>
        <h3>채팅방이 없습니다</h3>
        <p>새로운 채팅방을 만들어 대화를 시작해보세요!</p>
        <button @click="showCreateRoomModal = true" class="create-first-room-btn">첫 채팅방 만들기</button>
      </div>
    </div>

    <!-- 채팅방 메시지 영역 -->
    <div class="chat-area" v-if="currentRoom">
      <div class="chat-header">
        <h2>{{ currentRoom.name }}</h2>
        <div class="chat-actions">
          <button class="invite-btn">
            <span class="material-icons">person_add</span>
            초대하기
          </button>
        </div>
      </div>

      <div class="messages" ref="messageContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="message.id || index"
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
        <button @click="sendMessage" :disabled="!wsConnected || !newMessage.trim()">
          <span class="material-icons">send</span>
        </button>
      </div>
    </div>

    <!-- 채팅방 생성 모달 -->
    <div v-if="showCreateRoomModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h3>새 채팅방 만들기</h3>
          <button @click="showCreateRoomModal = false" class="close-btn">
            <span class="material-icons">close</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="roomName">채팅방 이름</label>
            <input 
              v-model="newRoomName"
              id="roomName"
              type="text"
              placeholder="채팅방 이름을 입력하세요"
              @keyup.enter="createRoom"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showCreateRoomModal = false" class="cancel-btn">취소</button>
          <button @click="createRoom" class="create-btn" :disabled="!newRoomName?.trim()">만들기</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { mapGetters } from "vuex";

export default {
  name: "ChatRooms",
  data() {
    return {
      chatRooms: [],
      currentRoom: null,
      showCreateRoomModal: false,
      newRoomName: "",
      newMessage: "",
      messages: [],
      ws: null,
      wsConnected: false,
      isLoading: false,
    };
  },
  computed: {
    ...mapGetters(["getToken", "getUsername"]),
    username() {
      return this.getUsername; // 컴포넌트 내에서 더 쉽게 접근하기 위해 추가
    },
  },
  methods: {
    formatDate(dateString) {
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    async loadChatRooms() {
      this.isLoading = true;
      console.log("채팅방 로드 시작");
      try {
        const response = await axios.get("http://localhost:8008/chat/rooms", {
          headers: { Authorization: `Bearer ${this.getToken}` },
        });
        this.chatRooms = response.data;
        console.log("채팅방 로드 성공:", this.chatRooms);
      } catch (error) {
        console.error("채팅방 로드 실패:", error);
        alert("채팅방을 불러오는 데 실패했습니다.");
      } finally {
        this.isLoading = false;
      }
    },
    async createRoom() {
      if (!this.newRoomName.trim()) return;
      try {
        const response = await axios.post(
          "http://localhost:8008/chat/rooms",
          { room_name: this.newRoomName }, // 'room_name'으로 수정
          {
            headers: {
              Authorization: `Bearer ${this.getToken}`,
              "Content-Type": "application/json",
            },
          }
        );
        const newRoom = response.data;
        this.chatRooms.push(newRoom);
        this.showCreateRoomModal = false;
        this.newRoomName = "";
        this.selectRoom(newRoom);

        alert("채팅방이 성공적으로 생성되었습니다.");
      } catch (error) {
        console.error("채팅방 생성 실패:", error);
        alert("채팅방 생성에 실패했습니다.");
      }
    },
    selectRoom(room) {
      this.currentRoom = room;
      this.messages = [];
      this.loadMessages(room.id); // 메시지 로드 추가
      this.connectWebSocket(room.id);
    },
    async loadMessages(roomId) {
      try {
        const response = await axios.get(`http://localhost:8008/chat/rooms/${roomId}/messages`, {
          headers: { Authorization: `Bearer ${this.getToken}` },
        });
        this.messages = response.data;
        this.scrollToBottom();
      } catch (error) {
        console.error("메시지 로드 실패:", error);
        alert("메시지를 불러오는 데 실패했습니다.");
      }
    },
    connectWebSocket(roomId) {
      if (this.ws) this.ws.close(); // 기존 연결 종료

      const wsUrl = `ws://localhost:8008/chat/ws/${roomId}?token=${this.getToken}`; // '/chat' 프리픽스 추가
      console.log('WebSocket 연결 시도:', wsUrl); // 디버깅용 로그 추가
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.wsConnected = true;
        console.log('WebSocket 연결됨:', wsUrl);
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.error) {
          console.error("서버 오류:", message.error);
          alert(`오류: ${message.error}`);
          return;
        }
        this.messages.push(message);
        this.scrollToBottom();
      };

      this.ws.onclose = (event) => {
        this.wsConnected = false;
        console.log('WebSocket 연결 종료:', event.code, event.reason);
        if (event.code !== 1000) { // 정상 종료가 아닐 경우 재연결 시도
          setTimeout(() => {
            this.connectWebSocket(roomId);
          }, 3000);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 에러:', error);
      };
    },
    sendMessage() {
      if (this.wsConnected && this.newMessage.trim()) {
        const messagePayload = {
          message: this.newMessage, // 서버에서 'message' 키를 기대
          username: this.username,
        };
        this.ws.send(JSON.stringify(messagePayload));
        this.messages.push({
          ...messagePayload,
          timestamp: new Date().toISOString(),
        });
        this.newMessage = "";
        this.scrollToBottom();
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messageContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },
  },
  async mounted() {
    await this.loadChatRooms();
  },
  beforeUnmount() {
    if (this.ws) this.ws.close();
  },
};
</script>

<style scoped>

/* 로딩 상태 스타일 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.loading-spinner {
  border: 4px solid #f3f3f3; /* 배경 */
  border-top: 4px solid #2D8DDD; /* 로딩 바 색상 */
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 2s linear infinite; /* 회전 애니메이션 */
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-state p {
  font-size: 16px;
  margin-top: 10px;
  font-weight: bold;
}
/* 스타일은 제공해주신 대로 유지합니다. 필요 시 추가 수정 */
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
  background: #f5f7fb;
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

.rooms-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.create-room-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: #2D8DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.create-room-btn .material-icons {
  font-size: 20px;
}

.rooms-list {
  flex: 1;
  overflow-y: auto;
}

.room-item {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.room-item:hover {
  background: #f8f9fa;
}

.room-item.active {
  background: #e3f2fd;
}

.room-info h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.last-message {
  margin: 5px 0 0;
  font-size: 14px;
  color: #666;
}

.room-date {
  font-size: 12px;
  color: #999;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  height: calc(100vh - 200px);
}

.empty-state .material-icons {
  font-size: 64px;
  color: #2D8DDD;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  color: #333;
  margin: 0 0 8px 0;
}

.empty-state p {
  color: #666;
  margin: 0 0 24px 0;
}

.create-first-room-btn {
  padding: 12px 24px;
  background: #2D8DDD;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.create-first-room-btn:hover {
  background: #2477c0;
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

.chat-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.invite-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: #2D8DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.invite-btn:hover {
  background: #2477c0;
}

.messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 70%;
}

.my-message {
  align-self: flex-end;
}

.message-info {
  margin-bottom: 4px;
  font-size: 14px;
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
  background: #2D8DDD;
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
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input input:focus {
  border-color: #2D8DDD;
}

.chat-input button {
  padding: 8px;
  background: #2D8DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.chat-input button:hover {
  background: #2477c0;
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

.no-room-message .material-icons {
  font-size: 48px;
  margin-bottom: 10px;
  color: #2D8DDD;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #666;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: #2D8DDD;
}

.modal-footer {
  padding: 16px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.cancel-btn {
  padding: 8px 16px;
  background: #f5f5f5;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
  transition: background-color 0.2s;
}

.cancel-btn:hover {
  background: #e5e5e5;
}

.create-btn {
  padding: 8px 16px;
  background: #2D8DDD;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.create-btn:hover {
  background: #2477c0;
}

.create-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
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
