import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import Signup from '../components/signup.vue'
import ChatRooms from '../components/ChatRooms.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: Login
  },
  {
    path: '/signup',
    name: 'signup',
    component: Signup
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatRooms,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 네비게이션 가드
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
