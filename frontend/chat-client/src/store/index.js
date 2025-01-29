import { createStore } from 'vuex';

export default createStore({
  state: {
    token: localStorage.getItem('access_token') || null,
    isAuthenticated: !!localStorage.getItem('access_token'),
    username: localStorage.getItem('username') || null // 추가
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      state.isAuthenticated = !!token;
      if (token) {
        localStorage.setItem('access_token', token);
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
      }
    },
    SET_USERNAME(state, username) { // 추가
      state.username = username;
      if (username) {
        localStorage.setItem('username', username);
      } else {
        localStorage.removeItem('username');
      }
    }
  },
  actions: {
    setToken({ commit }, token) {
      commit('SET_TOKEN', token);
    },
    setUsername({ commit }, username) { // 추가
      commit('SET_USERNAME', username);
    },
    logout({ commit }) {
      commit('SET_TOKEN', null);
      commit('SET_USERNAME', null); // 추가
    }
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    getToken: state => state.token,
    getUsername: state => state.username // 추가
  }
});
