import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { UserRole } from '@/types'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/user',
    redirect: '/user/dashboard',
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/dashboard',
    name: 'UserDashboard',
    component: () => import('@/views/user/Dashboard.vue'),
    meta: { requiresAuth: false, role: UserRole.USER },
  },
  {
    path: '/user/transfer',
    name: 'TransferMoney',
    component: () => import('@/views/user/TransferMoney.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/transactions',
    name: 'Transactions',
    component: () => import('@/views/user/Transactions.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/cards',
    name: 'Cards',
    component: () => import('@/views/user/Cards.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/cards/request',
    name: 'RequestCard',
    component: () => import('@/views/user/RequestCard.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/loans',
    name: 'Loans',
    component: () => import('@/views/user/Loans.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/savings',
    name: 'SavingsPlans',
    component: () => import('@/views/user/SavingsPlans.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/requests',
    name: 'Requests',
    component: () => import('@/views/user/Requests.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/user/account',
    name: 'Account',
    component: () => import('@/views/user/Account.vue'),
    meta: { requiresAuth: true, role: UserRole.USER },
  },
  {
    path: '/banker',
    redirect: '/banker/dashboard',
    meta: { requiresAuth: true, role: UserRole.BANKER },
  },
  {
    path: '/banker/dashboard',
    name: 'BankerDashboard',
    component: () => import('@/views/banker/Dashboard.vue'),
    meta: { requiresAuth: true, role: UserRole.BANKER },
  },
  {
    path: '/banker/requests',
    name: 'BankerRequests',
    component: () => import('@/views/banker/Requests.vue'),
    meta: { requiresAuth: true, role: UserRole.BANKER },
  },
  {
    path: '/banker/cards',
    name: 'BankerCardManagement',
    component: () => import('@/views/banker/CardManagement.vue'),
    meta: { requiresAuth: true, role: UserRole.BANKER },
  },
  {
    path: '/admin',
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true, role: UserRole.ADMIN },
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, role: UserRole.ADMIN },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/admin/Users.vue'),
    meta: { requiresAuth: true, role: UserRole.ADMIN },
  },
  {
    path: '/admin/logs',
    name: 'AdminLogs',
    component: () => import('@/views/admin/Logs.vue'),
    meta: { requiresAuth: true, role: UserRole.ADMIN },
  },
  {
    path: '/admin/capital',
    name: 'AdminCapital',
    component: () => import('@/views/admin/Capital.vue'),
    meta: { requiresAuth: true, role: UserRole.ADMIN },
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('@/views/admin/Settings.vue'),
    meta: { requiresAuth: true, role: UserRole.ADMIN },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function checkRoleAccess(userRole: UserRole, requiredRole: UserRole): boolean {
  if (userRole === requiredRole) return true
  
  if (userRole === UserRole.ADMIN) {
    return true
  }
  
  if (userRole === UserRole.BANKER) {
    return requiredRole === UserRole.USER
  }
  
  return false
}

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  const profileStr = localStorage.getItem('profile')
  
  let user = null
  if (profileStr) {
    try {
      const profile = JSON.parse(profileStr)
      user = profile.user
    } catch (e) {
      console.error('Failed to parse profile from localStorage:', e)
      localStorage.removeItem('profile')
    }
  }

  const requiresAuth = to.meta.requiresAuth
  const requiredRole = to.meta.role as UserRole | undefined

  if (requiresAuth && !token) {
    next('/login')
    return
  }

  if (requiredRole && user?.role) {
    const hasAccess = checkRoleAccess(user.role, requiredRole)
    
    if (!hasAccess) {
      if (user.role === UserRole.USER) {
        next('/user/dashboard')
      } else if (user.role === UserRole.BANKER) {
        next('/banker/dashboard')
      } else if (user.role === UserRole.ADMIN) {
        next('/admin/dashboard')
      } else {
        next('/login')
      }
      return
    }
  }

  if (!requiresAuth && token && user) {
    if (user.role === UserRole.USER) {
      next('/user/dashboard')
    } else if (user.role === UserRole.BANKER) {
      next('/banker/dashboard')
    } else if (user.role === UserRole.ADMIN) {
      next('/admin/dashboard')
    } else {
      next()
    }
    return
  }

  next()
})

export default router

