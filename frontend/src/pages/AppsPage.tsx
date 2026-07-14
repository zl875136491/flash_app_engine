import { LayoutGrid } from "lucide-react";
import { useSearchParams } from "react-router-dom";

/** 任务点 12 将接入完整任务列表、阶段日志与分享入口。 */
export function AppsPage() {
  const [params] = useSearchParams();
  const highlight = params.get("highlight");

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 px-4 py-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold tracking-tight">我的应用</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          已部署应用、阶段进度与内网 URL 将在任务点 12 展示。
        </p>
      </div>

      {highlight ? (
        <div className="rounded-2xl bg-secondary/60 px-4 py-3 text-sm text-secondary-foreground">
          任务已提交：<span className="font-medium">{highlight}</span>
          <p className="mt-1 text-xs text-muted-foreground">编排进行中，完整看板即将接入。</p>
        </div>
      ) : null}

      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl bg-muted/60 px-4 py-12 text-center">
        <LayoutGrid className="size-10 text-primary" />
        <p className="text-sm text-muted-foreground">暂无应用列表</p>
      </div>
    </div>
  );
}
