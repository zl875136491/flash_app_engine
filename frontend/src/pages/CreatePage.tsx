import { Mic2 } from "lucide-react";

/** 任务点 11 将接入语音 / 图片创建任务。 */
export function CreatePage() {
  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 px-4 py-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold tracking-tight">创建应用</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          以语音为主、图片为辅描述需求。完整录入与提交将在任务点 11 实现。
        </p>
      </div>
      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl bg-secondary/50 px-4 py-12 text-center">
        <Mic2 className="size-10 text-primary" />
        <p className="text-sm text-muted-foreground">语音输入占位</p>
      </div>
    </div>
  );
}
