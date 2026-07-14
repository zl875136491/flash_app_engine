import { LayoutGrid, Loader2, Play, RefreshCw, RotateCcw, Square, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { StageBadge } from "@/components/apps/StageBadge";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  listTasks,
  removeTask,
  retryTask,
  startTask,
  stopTask,
  type QuotaInfo,
  type TaskSummary,
} from "@/lib/api";
import { formatQuota, formatTime, isActiveStage, taskTitle } from "@/lib/task-utils";
import { cn } from "@/lib/utils";

export function AppsPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const highlight = params.get("highlight");

  const [items, setItems] = useState<TaskSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const data = await listTasks({ limit: 50 });
      setItems(data.items);
      setTotal(data.total);
      if (data.quota) setQuota(data.quota);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "加载失败");
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const hasActive = items.some((item) => isActiveStage(item.current_stage));
    if (!hasActive) return;
    const timer = window.setInterval(() => {
      void load(true);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [items, load]);

  async function runAction(
    taskId: string,
    action: "stop" | "start" | "retry" | "remove",
  ) {
    setActionId(taskId);
    setError(null);
    try {
      if (action === "remove") {
        if (!window.confirm("确定移除该应用？容器与任务记录将被删除且不可恢复。")) {
          return;
        }
        await removeTask(taskId);
      } else if (action === "stop") {
        await stopTask(taskId);
      } else if (action === "start") {
        await startTask(taskId);
      } else {
        await retryTask(taskId);
      }
      await load(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "操作失败");
    } finally {
      setActionId(null);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 px-4 py-6">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">我的应用</h2>
          <p className="text-sm text-muted-foreground">
            {quota
              ? formatQuota(quota.used, quota.limit)
              : total > 0
                ? `共 ${total} 个任务`
                : "口述部署后的应用会出现在这里"}
            {quota && total > 0 ? ` · 共 ${total} 个任务` : null}
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
          const busy = actionId === item.id;
          return (
            <li key={item.id}>
              <div
                className={cn(
                  "rounded-2xl border border-transparent px-4 py-3",
                  "bg-muted/50",
                  active && "border-primary/40 bg-secondary/50",
                )}
              >
                <Link to={`/apps/${item.id}`} className="block">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <p className="truncate text-sm font-medium">
                        {taskTitle(item.raw_voice_text, item.id)}
                      </p>
                      <p className="text-xs text-muted-foreground">{formatTime(item.updated_at)}</p>
                    </div>
                    <StageBadge stage={item.current_stage} />
                  </div>
                  {item.exposed_url && item.current_stage === "Success" ? (
                    <p className="mt-2 truncate text-xs text-primary">{item.exposed_url}</p>
                  ) : null}
                </Link>

                <div className="mt-3 flex flex-wrap gap-2">
                  {item.current_stage === "Success" ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      disabled={busy}
                      onClick={() => void runAction(item.id, "stop")}
                    >
                      {busy ? <Loader2 className="size-3.5 animate-spin" /> : <Square className="size-3.5" />}
                      停止
                    </Button>
                  ) : null}
                  {item.current_stage === "Stopped" ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={busy}
                      onClick={() => void runAction(item.id, "start")}
                    >
                      {busy ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
                      启动
                    </Button>
                  ) : null}
                  {item.current_stage === "Failed" ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={busy}
                      onClick={() => void runAction(item.id, "retry")}
                    >
                      {busy ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : (
                        <RotateCcw className="size-3.5" />
                      )}
                      重试
                    </Button>
                  ) : null}
                  {!isActiveStage(item.current_stage) ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={busy}
                      onClick={() => void runAction(item.id, "remove")}
                    >
                      {busy ? <Loader2 className="size-3.5 animate-spin" /> : <Trash2 className="size-3.5" />}
                      移除
                    </Button>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
