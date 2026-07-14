import { ArrowLeft, Loader2, Play, RotateCcw, Square, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ShareCard } from "@/components/apps/ShareCard";
import { StageBadge } from "@/components/apps/StageBadge";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  getTask,
  removeTask,
  retryTask,
  startTask,
  stopTask,
  type TaskDetail,
} from "@/lib/api";
import { formatTime, isActiveStage, STAGE_LABEL, taskTitle } from "@/lib/task-utils";

export function TaskDetailPage() {
  const navigate = useNavigate();
  const { taskId = "" } = useParams();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

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

  async function runAction(action: "stop" | "start" | "retry" | "remove") {
    if (!taskId) return;
    setActing(true);
    setActionError(null);
    try {
      if (action === "remove") {
        if (!window.confirm("确定移除该应用？容器与任务记录将被删除且不可恢复。")) {
          return;
        }
        await removeTask(taskId);
        navigate("/apps", { replace: true });
        return;
      }
      if (action === "stop") {
        setTask(await stopTask(taskId));
      } else if (action === "start") {
        setTask(await startTask(taskId));
      } else {
        setTask(await retryTask(taskId));
      }
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "操作失败");
    } finally {
      setActing(false);
    }
  }

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

      {task.exposed_url && task.current_stage === "Success" ? (
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
              : task.current_stage === "Stopped"
                ? "应用已停止，启动后可重新访问。"
                : "暂无对外链接。"}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {task.current_stage === "Success" ? (
          <Button
            type="button"
            variant="secondary"
            disabled={acting}
            onClick={() => void runAction("stop")}
          >
            {acting ? <Loader2 className="size-4 animate-spin" /> : <Square className="size-4" />}
            停止
          </Button>
        ) : null}
        {task.current_stage === "Stopped" ? (
          <Button type="button" disabled={acting} onClick={() => void runAction("start")}>
            {acting ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            启动
          </Button>
        ) : null}
        {task.current_stage === "Failed" ? (
          <Button type="button" disabled={acting} onClick={() => void runAction("retry")}>
            {acting ? <Loader2 className="size-4 animate-spin" /> : <RotateCcw className="size-4" />}
            重试
          </Button>
        ) : null}
        {!isActiveStage(task.current_stage) ? (
          <Button
            type="button"
            variant="outline"
            disabled={acting}
            onClick={() => void runAction("remove")}
          >
            {acting ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
            移除
          </Button>
        ) : null}
      </div>
      {actionError ? (
        <p className="text-sm text-destructive" role="alert">
          {actionError}
        </p>
      ) : null}

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
