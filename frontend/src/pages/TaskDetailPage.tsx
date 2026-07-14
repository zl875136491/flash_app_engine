import { ArrowLeft, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ShareCard } from "@/components/apps/ShareCard";
import { StageBadge } from "@/components/apps/StageBadge";
import { Button } from "@/components/ui/button";
import { ApiError, getTask, type TaskDetail } from "@/lib/api";
import { formatTime, isActiveStage, STAGE_LABEL, taskTitle } from "@/lib/task-utils";

export function TaskDetailPage() {
  const { taskId = "" } = useParams();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (silent = false) => {
      if (!taskId) return;
      if (!silent) setLoading(true);
      setError(null);
      try {
        const data = await getTask(taskId);
        setTask(data);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "加载失败");
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [taskId],
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!task || !isActiveStage(task.current_stage)) return;
    const timer = window.setInterval(() => {
      void load(true);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [task, load]);

  if (loading && !task) {
    return (
      <div className="flex h-full items-center justify-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        加载任务…
      </div>
    );
  }

  if (error && !task) {
    return (
      <div className="mx-auto max-w-md space-y-4 px-4 py-6">
        <p className="text-sm text-destructive">{error}</p>
        <Button asChild variant="outline">
          <Link to="/apps">返回列表</Link>
        </Button>
      </div>
    );
  }

  if (!task) return null;

  const title = taskTitle(task.raw_voice_text, task.id);
  const logs = [...task.logs].reverse();

  return (
    <div className="mx-auto flex max-w-md flex-col gap-5 px-4 py-6">
      <div className="flex items-center gap-2">
        <Button asChild variant="ghost" size="icon" aria-label="返回">
          <Link to="/apps">
            <ArrowLeft className="size-5" />
          </Link>
        </Button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-semibold tracking-tight">{title}</h2>
          <p className="text-xs text-muted-foreground">更新于 {formatTime(task.updated_at)}</p>
        </div>
        <StageBadge stage={task.current_stage} />
      </div>

      {task.raw_voice_text ? (
        <section className="space-y-1">
          <h3 className="text-sm font-medium">需求原文</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">{task.raw_voice_text}</p>
        </section>
      ) : null}

      {task.exposed_url ? (
        <ShareCard
          title={title}
          url={task.exposed_url}
          stageLabel={STAGE_LABEL[task.current_stage]}
        />
      ) : (
        <div className="rounded-2xl bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
          {isActiveStage(task.current_stage)
            ? "部署完成后将在此显示内网访问链接与分享卡片。"
            : task.current_stage === "Failed"
              ? "任务失败，暂无对外链接。"
              : "暂无对外链接。"}
        </div>
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">阶段日志</h3>
          {isActiveStage(task.current_stage) ? (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Loader2 className="size-3 animate-spin" />
              自动刷新
            </span>
          ) : null}
        </div>

        {logs.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无日志</p>
        ) : (
          <ol className="space-y-3 border-l border-border pl-4">
            {logs.map((log, index) => (
              <li key={`${log.created_at}-${index}`} className="relative space-y-1">
                <span className="absolute -left-[1.35rem] top-1.5 size-2.5 rounded-full bg-primary" />
                <div className="flex flex-wrap items-center gap-2">
                  <StageBadge stage={log.stage} />
                  <span className="text-xs text-muted-foreground">{formatTime(log.created_at)}</span>
                </div>
                <p className="text-sm font-medium">{log.message}</p>
                {log.detail ? (
                  <p className="whitespace-pre-wrap break-words text-xs leading-relaxed text-muted-foreground">
                    {log.detail.length > 500 ? `${log.detail.slice(0, 500)}…` : log.detail}
                  </p>
                ) : null}
              </li>
            ))}
          </ol>
        )}
      </section>

      {error ? (
        <p className="text-xs text-destructive" role="alert">
          刷新失败：{error}
        </p>
      ) : null}
    </div>
  );
}
