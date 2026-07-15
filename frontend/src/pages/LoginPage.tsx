import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { InstallHint } from "@/components/shell/InstallHint";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";

export function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from =
    (location.state as { from?: string } | null)?.from &&
    (location.state as { from?: string }).from !== "/login"
      ? (location.state as { from: string }).from
      : "/create";

  const [itcode, setItcode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") {
    return <Navigate to={from} replace />;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const value = itcode.trim();
    if (!value) {
      setError("请输入 ITCode");
      return;
    }
    setSubmitting(true);
    try {
      await login(value);
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("登录失败，请检查网络或后端服务");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-background text-foreground">
      <div
        className="pointer-events-none absolute inset-0 opacity-80"
        style={{
          background:
            "radial-gradient(120% 80% at 50% -10%, color-mix(in oklch, var(--primary) 28%, transparent), transparent 60%), linear-gradient(180deg, color-mix(in oklch, var(--secondary) 55%, transparent), transparent 45%)",
        }}
      />

      <main className="relative z-10 flex min-h-0 flex-1 flex-col justify-center px-5 pb-28 pt-8">
        <div className="mx-auto w-full max-w-sm space-y-8">
          <div className="space-y-3 text-center">
            <img
              src="/pwa-192.png?v=20260715"
              alt="FlashApp"
              className="mx-auto size-16 rounded-2xl shadow-sm"
              width={64}
              height={64}
            />
            <h1 className="text-3xl font-semibold tracking-tight">FlashApp</h1>
            <p className="text-sm leading-relaxed text-muted-foreground">
              使用公司 ITCode 登录，口述需求即可部署可分享的内网应用。
            </p>
          </div>

          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="itcode">ITCode</Label>
              <Input
                id="itcode"
                name="itcode"
                autoComplete="username"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                placeholder="例如 zhangle"
                value={itcode}
                onChange={(e) => setItcode(e.target.value)}
                disabled={submitting || status === "loading"}
              />
            </div>

            {error ? (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}

            <Button className="w-full" size="lg" type="submit" disabled={submitting}>
              {submitting ? "登录中…" : "进入 FlashApp"}
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground">
            白名单用户见 docs/auth_users.md，无需密码。
          </p>
        </div>
      </main>

      <InstallHint />
    </div>
  );
}
