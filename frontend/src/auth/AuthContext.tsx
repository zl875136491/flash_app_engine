import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ApiError, fetchMe, loginWithItcode } from "@/lib/api";
import {
  clearSession,
  getStoredToken,
  getStoredUser,
  persistSession,
  type AuthUser,
} from "@/lib/auth-storage";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: AuthStatus;
  user: AuthUser | null;
  login: (itcode: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = getStoredToken();
      const cached = getStoredUser();
      if (!token) {
        if (!cancelled) {
          setUser(null);
          setStatus("anonymous");
        }
        return;
      }

      try {
        const me = await fetchMe();
        if (cancelled) return;
        const next = { itcode: me.itcode, name: me.name };
        persistSession(token, next);
        setUser(next);
        setStatus("authenticated");
      } catch (error) {
        if (cancelled) return;
        clearSession();
        // 后端不可达时，若本地仍有缓存，开发期可短暂保留；正式鉴权失败则匿名
        if (error instanceof ApiError && error.status === 401) {
          setUser(null);
          setStatus("anonymous");
          return;
        }
        if (cached) {
          setUser(cached);
          setStatus("authenticated");
          return;
        }
        setUser(null);
        setStatus("anonymous");
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (itcode: string) => {
    const tokenRes = await loginWithItcode(itcode.trim().toLowerCase());
    let nextUser: AuthUser = { itcode: tokenRes.itcode, name: tokenRes.itcode };
    persistSession(tokenRes.access_token, nextUser);
    try {
      const me = await fetchMe();
      nextUser = { itcode: me.itcode, name: me.name };
      persistSession(tokenRes.access_token, nextUser);
    } catch {
      // /me 失败时仍可用登录返回的 itcode
    }
    setUser(nextUser);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
    setStatus("anonymous");
  }, []);

  const value = useMemo(
    () => ({ status, user, login, logout }),
    [status, user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
