import { LayoutGrid, Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { StageBadge } from "@/components/apps/StageBadge";
import { Button } from "@/components/ui/button";
import { ApiError, listTasks, type TaskSummary } from "@/lib/api";
import { formatTime, isActiveStage, taskTitle } from "@/lib/task-utils";
import { cn } from "@/lib/utils";

export function AppsPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const highlight = params.get("highlight");

  const [items, setItems] = useState<TaskSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const data = await listTasks({ limit: 50 });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "加载失败");
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // 有进行中任务时轮询列表
  useEffect(() => {
    const hasActive = items.some((item) => isActiveStage(item.current_stage));
    if (!hasActive) return;
    const timer = window.setInterval(() => {
      void load(true);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [items, load]);

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 px-4 py-6">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">我的应用</h2>
          <p className="text-sm text-muted-foreground">
            {total > 0 ? `共 ${total} 个任务` : "口述部署后的应用会出现在这里"}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="刷新"
          onClick={() => void load()}
          disabled={loading}
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
        </Button>
      </div>

      {highlight ? (
        <div className="rounded-2xl bg-secondary/60 px-4 py-3 text-sm">
          已提交任务，正在编排…
          <button
            type="button"
            className="mt-1 block text-primary"
            onClick={() => navigate(`/apps/${highlight}`)}
          >
            查看进度 →
          </button>
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      {loading && items.length === 0 ? (
        <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          加载中…
        </div>
      ) : null}

      {!loading && items.length === 0 && !error ? (
        <div className="flex flex-col items-center justify-center gap-3 px-4 py-16 text-center">
          <LayoutGrid className="size-10 text-primary" />
          <p className="text-sm text-muted-foreground">还没有应用</p>
          <Button type="button" onClick={() => navigate("/create")}>
            去创建
          </Button>
        </div>
      ) : null}

      <ul className="space-y-2">
        {items.map((item) => {
          const active = highlight === item.id;
          return (
            <li key={item.id}>
              <Link
                to={`/apps/${item.id}`}
                className={cn(
                  "block rounded-2xl border border-transparent px-4 py-3 transition-colors",
                  "bg-muted/50 hover:bg-muted",
                  active && "border-primary/40 bg-secondary/50",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 space-y-1">
                    <p className="truncate text-sm font-medium">
                      {taskTitle(item.raw_voice_text, item.id)}
                    </p>
                    <p className="text-xs text-muted-foreground">{formatTime(item.updated_at)}</p>
                  </div>
                  <StageBadge stage={item.current_stage} />
                </div>
                {item.exposed_url ? (
                  <p className="mt-2 truncate text-xs text-primary">{item.exposed_url}</p>
                ) : null}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
