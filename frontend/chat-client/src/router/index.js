import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import Signup from '../components/signup.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 네비게이션 가드 추가
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token')
  
  // 로그인이 필요한 페이지 목록
  const authRequired = ['/chat']
  
  if (authRequired.includes(to.path) && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
