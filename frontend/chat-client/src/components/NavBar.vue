<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/" class="nav-logo">
        ChatApp
      </router-link>
      <div class="nav-links">
        <template v-if="isAuthenticated">
          <span class="welcome-message">{{ username }}님 반갑습니다</span>
          <router-link to="/chat" class="nav-link">채팅</router-link>
          <button @click="handleLogout" class="nav-link logout-btn">로그아웃</button>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link">로그인</router-link>
          <router-link to="/signup" class="nav-link">회원가입</router-link>
        </template>
      </div>
    </div> 
  </nav>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'NavBar',
  computed: {
    ...mapGetters(['isAuthenticated']),
    username() {
      return localStorage.getItem('username') || '사용자';
    }
  },
  methods: {
    handleLogout() {
      this.$store.dispatch('logout');
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      this.$router.push('/login');
    }
  },
  created() {
    // 컴포넌트가 생성될 때 로그인 상태 체크
    const token = localStorage.getItem('access_token');
    if (token) {
      this.$store.dispatch('setToken', token);
    }
  }
};
</script>

<style scoped>
.navbar {
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-logo {
  font-size: 20px;
  font-weight: bold;
  color: #742DDD;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}

.nav-link {
  color: #333;
  text-decoration: none;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-link:hover {
  background-color: #f5f5f5;
}

.logout-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  padding: 8px 12px;
}

.logout-btn:hover {
  color: #742DDD;
  background-color: #f5f5f5;
  border-radius: 4px;
}
</style>