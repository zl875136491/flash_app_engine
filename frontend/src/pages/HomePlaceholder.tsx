import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

/** 任务点 9 占位首页：验证主题、移动端壳与 shadcn 基础组件。 */
export function HomePlaceholder() {
  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <header
        className="flex shrink-0 items-center justify-between border-b border-border px-4"
        style={{ height: "var(--mobile-header-height)" }}
      >
        <div className="flex items-center gap-2">
          <span className="inline-flex size-7 items-center justify-center rounded-lg bg-primary text-xs font-bold text-primary-foreground">
            F
          </span>
          <span className="font-semibold tracking-tight">FlashApp</span>
        </div>
        <span className="text-xs text-muted-foreground">PWA</span>
      </header>

      <main className="docs-scroll min-h-0 flex-1 overflow-y-auto px-4 py-8">
        <div className="mx-auto flex max-w-md flex-col gap-6">
          <div className="space-y-2">
            <p className="text-sm font-medium text-primary">FlashApp Engine</p>
            <h1 className="text-3xl font-semibold tracking-tight">口述即部署</h1>
            <p className="text-sm leading-relaxed text-muted-foreground">
              前端脚手架已就绪：React 19、Vite、PWA、shadcn/ui，主题取自
              <code className="mx-1 rounded bg-muted px-1 py-0.5 text-xs">src/index.css</code>
              。登录与任务流将在后续任务点接入。
            </p>
          </div>

          <div className="rounded-2xl bg-secondary/60 p-4 text-sm text-secondary-foreground">
            <div className="mb-2 flex items-center gap-2 font-medium">
              <Sparkles className="size-4 text-primary" />
              移动端优先
            </div>
            <p className="leading-relaxed text-muted-foreground">
              禁用缩放、全屏壳层、底部安全区预留。可「添加到主屏幕」作为独立应用启动。
            </p>
          </div>

          <Button className="w-full" size="lg" type="button" disabled>
            下一步：登录（任务点 10）
          </Button>
        </div>
      </main>

      <footer
        className="flex shrink-0 items-center justify-center border-t border-border text-xs text-muted-foreground"
        style={{
          height: "calc(var(--mobile-tabbar-height) + env(safe-area-inset-bottom, 0px))",
          paddingBottom: "env(safe-area-inset-bottom, 0px)",
        }}
      >
        脚手架就绪
      </footer>
    </div>
  );
}
