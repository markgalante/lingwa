import {createContext, useEffect, useState} from 'react';
import {api} from '../../api/client';

interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  is_verified: boolean;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({children}: {children: React.ReactNode}) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(() => !!localStorage.getItem('token'));

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    api
      .get<User>('/auth/me')
      .then(setUser)
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(token: string) {
    localStorage.setItem('token', token);
    const userData = await api.get<User>('/auth/me');
    setUser(userData);
  }

  function logout() {
    localStorage.removeItem('token');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{user, isLoading, login, logout}}>{children}</AuthContext.Provider>
  );
}

export {AuthContext};
export type {AuthContextValue, User};
