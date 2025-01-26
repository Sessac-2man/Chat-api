import { createStore } from 'vuex';

export default createStore({
  state: {
    token: localStorage.getItem('access_token') || null,
    isAuthenticated: !!localStorage.getItem('access_token')
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
    }
  },
  actions: {
    setToken({ commit }, token) {
      commit('SET_TOKEN', token);
    },
    logout({ commit }) {
      commit('SET_TOKEN', null);
    }
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    getToken: state => state.token
  }
}); 