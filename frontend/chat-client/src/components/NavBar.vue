<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/" class="nav-logo">
        ChatApp
      </router-link>
      <div class="nav-links">
        <template v-if="isLoggedIn">
          <router-link to="/chat" class="nav-link">채팅</router-link>
          <button @click="logout" class="nav-link logout-btn">로그아웃</button>
        </template>
        <template v-else>
          <router-link to="/" class="nav-link">로그인</router-link>
          <router-link to="/signup" class="nav-link">회원가입</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'NavBar',
  data() {
    return {
      isLoggedIn: false // 나중에 Vuex로 관리할 예정
    }
  },
  methods: {
    logout() {
      this.isLoggedIn = false;
      this.$router.push('/');
    }
  }
}
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