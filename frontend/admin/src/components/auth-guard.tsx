import { Navigate } from '@tanstack/react-router';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const token = localStorage.getItem('token');

  if (!token) {
    // 将用户重定向到登录页面，并保存尝试访问的URL
    const redirect = window.location.pathname
    return <Navigate to="/sign-in" search={{ redirect }} />
  }

  return <>{children}</>;
}