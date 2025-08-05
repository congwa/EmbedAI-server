import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface AuthUser {
  id: number
  email: string
  is_admin: boolean
  created_at: string
}

interface AuthState {
  user: AuthUser | null
  accessToken: string
  setUser: (user: AuthUser | null) => void
  setAccessToken: (accessToken: string) => void
  resetAccessToken: () => void
  reset: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: '',
      setUser: (user) => set({ user }),
      setAccessToken: (accessToken) => {
        set({ accessToken })
        localStorage.setItem('token', accessToken)
      },
      resetAccessToken: () => {
        set({ accessToken: '', user: null })
        localStorage.removeItem('token')
      },
      reset: () => {
        set({ user: null, accessToken: '' })
        localStorage.removeItem('token')
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
      }),
    }
  )
)

// 选择器函数
const selectUser = (state: AuthState) => state.user
const selectAccessToken = (state: AuthState) => state.accessToken
const selectIsAdmin = (state: AuthState) => state.user?.is_admin ?? false

// 导出 hooks
export const useAuth = () => {
  const user = useAuthStore(selectUser)
  const accessToken = useAuthStore(selectAccessToken)
  const isAdmin = useAuthStore(selectIsAdmin)
  const { setUser, setAccessToken, resetAccessToken, reset } = useAuthStore()

  return {
    user,
    accessToken,
    isAdmin,
    setUser,
    setAccessToken,
    resetAccessToken,
    reset,
  }
}
