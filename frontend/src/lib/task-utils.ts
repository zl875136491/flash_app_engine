import type { Stage } from "@/lib/api";

export const STAGE_LABEL: Record<Stage, string> = {
  Received: "已接收",
  Analyzing: "架构解析",
  Coding: "编码中",
  Building: "构建中",
  Verifying: "验证中",
  Success: "已部署",
  Failed: "失败",
  Stopped: "已停止",
};

export const ACTIVE_STAGES: Stage[] = [
  "Received",
  "Analyzing",
  "Coding",
  "Building",
  "Verifying",
];

export function isActiveStage(stage: Stage): boolean {
  return ACTIVE_STAGES.includes(stage);
}

export function formatTime(iso: string): string {
  const normalized = normalizeApiDate(iso);
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/** 兼容历史无时区后缀的 UTC 字符串，避免被当成本地时间解析。 */
function normalizeApiDate(iso: string): string {
  const raw = (iso || "").trim();
  if (!raw) return raw;
  if (/[zZ]$|[+-]\d{2}:\d{2}$/.test(raw)) return raw;
  return `${raw}Z`;
}

export function taskTitle(raw: string | null | undefined, id: string): string {
  const text = (raw || "").trim();
  if (!text) return `任务 ${id.slice(-6)}`;
  return text.length > 36 ? `${text.slice(0, 36)}…` : text;
}

export function formatQuota(used: number, limit: number): string {
  return `运行中 ${used}/${limit}`;
}
