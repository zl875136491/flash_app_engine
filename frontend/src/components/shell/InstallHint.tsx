import { Download, Share, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DISMISS_KEY = "flashapp.installHint.dismissed";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  const mq = window.matchMedia("(display-mode: standalone)").matches;
  const ios = "standalone" in navigator && Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
  return mq || ios;
}

function isIosSafari(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent;
  const iOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const webkit = /WebKit/.test(ua);
  const notChrome = !/CriOS|FxiOS|EdgiOS/.test(ua);
  return iOS && webkit && notChrome;
}

export function InstallHint({ className }: { className?: string }) {
  const [visible, setVisible] = useState(false);
  const [ios, setIos] = useState(false);
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    if (isStandalone()) return;
    try {
      if (localStorage.getItem(DISMISS_KEY) === "1") return;
    } catch {
      // ignore
    }

    setIos(isIosSafari());
    setVisible(true);

    const onBip = (event: Event) => {
      event.preventDefault();
      setDeferred(event as BeforeInstallPromptEvent);
      setVisible(true);
    };
    window.addEventListener("beforeinstallprompt", onBip);
    return () => window.removeEventListener("beforeinstallprompt", onBip);
  }, []);

  function dismiss() {
    setVisible(false);
    try {
      localStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // ignore
    }
  }

  async function onInstall() {
    if (!deferred) return;
    await deferred.prompt();
    try {
      await deferred.userChoice;
    } catch {
      // ignore
    }
    setDeferred(null);
    dismiss();
  }

  if (!visible) return null;

  return (
    <div
      className={cn(
        "pointer-events-auto fixed inset-x-4 z-40 mx-auto max-w-sm",
        "bottom-[max(1.25rem,env(safe-area-inset-bottom))]",
        className,
      )}
      role="status"
    >
      <div className="relative overflow-hidden rounded-2xl border border-border/60 bg-background/95 p-4 shadow-lg backdrop-blur-md">
        <div
          className="pointer-events-none absolute -right-8 -top-10 size-28 rounded-full opacity-40"
          style={{
            background:
              "radial-gradient(circle, color-mix(in oklch, var(--primary) 55%, transparent), transparent 70%)",
          }}
        />
        <button
          type="button"
          aria-label="关闭"
          className="absolute right-2 top-2 rounded-full p-1.5 text-muted-foreground hover:bg-muted"
          onClick={dismiss}
        >
          <X className="size-4" />
        </button>

        <div className="flex gap-3 pr-6">
          <img
            src="/pwa-192.png?v=20260715"
            alt=""
            className="size-11 shrink-0 rounded-xl shadow-sm"
            width={44}
            height={44}
          />
          <div className="min-w-0 space-y-1.5">
            <p className="text-sm font-semibold tracking-tight">安装 FlashApp</p>
            {ios ? (
              <p className="text-xs leading-relaxed text-muted-foreground">
                点击底部分享
                <Share className="mx-0.5 inline size-3 align-text-bottom" />
                ，选择「添加到主屏幕」，获得接近原生 App 的体验。
              </p>
            ) : deferred ? (
              <p className="text-xs leading-relaxed text-muted-foreground">
                安装到主屏幕后可全屏使用、更快打开，体验更完整。
              </p>
            ) : (
              <p className="text-xs leading-relaxed text-muted-foreground">
                用浏览器菜单将本站「添加到主屏幕 / 安装应用」，获得更完整的 PWA 体验。
              </p>
            )}
          </div>
        </div>

        {deferred ? (
          <Button type="button" className="mt-3 w-full" size="sm" onClick={() => void onInstall()}>
            <Download className="size-3.5" />
            安装到主屏幕
          </Button>
        ) : null}
      </div>
    </div>
  );
}
