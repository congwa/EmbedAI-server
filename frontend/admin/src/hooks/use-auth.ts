import { useMutation } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { adminService } from '@/services/admin'
import { useAuthStore } from '@/stores/authStore'
import { AdminLoginRequest, AdminRegisterRequest } from '@/services/types'

export function useLogin() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async (data: AdminLoginRequest) => {
      const response = await adminService.login(data)
      return response
    },
    onSuccess: (response) => {
      if (response.success) {
        const { access_token, user } = response.data
        useAuthStore.getState().setAccessToken(access_token)
        useAuthStore.getState().setUser(user)
        localStorage.setItem('token', access_token)
        navigate({ to: '/' })
      }
    },
  })
}

export function useRegister() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async (data: AdminRegisterRequest) => {
      const response = await adminService.register(data)
      return response
    },
    onSuccess: (response) => {
      if (response.success) {
        navigate({ to: '/sign-in' })
      }
    },
  })
}