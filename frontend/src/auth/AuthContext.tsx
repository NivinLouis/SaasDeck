import { createContext, useCallback, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { TokenPair, User } from "../api/types";

interface LoginPayload {
  email: string;
  password: string;
}

interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);

  const login = useCallback(async ({ email, password }: LoginPayload) => {
    const tokens = await api.post<TokenPair>("/auth/login", { email, password });
    const currentUser = await api.get<User>("/me", tokens.access);
    setAccessToken(tokens.access);
    setRefreshToken(tokens.refresh);
    setUser(currentUser);
    return currentUser;
  }, []);

  const logout = useCallback(async () => {
    if (accessToken && refreshToken) {
      try {
        await api.post<void>("/auth/logout", { refresh: refreshToken }, accessToken);
      } catch {
        // Local session must still end even when the server token has expired.
      }
    }
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
  }, [accessToken, refreshToken]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, accessToken, isAuthenticated: Boolean(user && accessToken), login, logout }),
    [accessToken, login, logout, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
