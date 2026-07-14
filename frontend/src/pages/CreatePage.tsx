import { ImagePlus, Loader2, Mic, Square, X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ApiError, createTask, uploadImage } from "@/lib/api";
import { FunAsrSession, type FunAsrStatus } from "@/lib/funasr";
import { cn } from "@/lib/utils";

type LocalImage = {
  id: string;
  file: File;
  previewUrl: string;
};

export function CreatePage() {
  const navigate = useNavigate();
  const fileInputId = useId();
  const fileRef = useRef<HTMLInputElement>(null);
  const sessionRef = useRef<FunAsrSession | null>(null);

  const [text, setText] = useState("");
  const [images, setImages] = useState<LocalImage[]>([]);
  const [asrStatus, setAsrStatus] = useState<FunAsrStatus>("idle");
  const [asrError, setAsrError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const listening = asrStatus === "listening" || asrStatus === "connecting";

  const imagesRef = useRef<LocalImage[]>([]);
  imagesRef.current = images;

  useEffect(() => {
    return () => {
      void sessionRef.current?.stop();
      imagesRef.current.forEach((img) => URL.revokeObjectURL(img.previewUrl));
    };
  }, []);

  async function toggleListening() {
    setAsrError(null);
    if (listening) {
      await sessionRef.current?.stop();
      sessionRef.current = null;
      return;
    }

    const session = new FunAsrSession({
      onPartial: (chunk) => {
        setText((prev) => {
          const next = chunk.trim();
          if (!next) return prev;
          if (!prev.trim()) return next;
          // FunASR 常返回累计或片段；若为扩展则替换，否则追加
          if (next.startsWith(prev.trim()) || prev.trim().startsWith(next)) {
            return next.length >= prev.trim().length ? next : prev;
          }
          return `${prev.trim()} ${next}`.trim();
        });
      },
      onStatus: setAsrStatus,
      onError: (message) => {
        setAsrError(message);
        setAsrStatus("error");
      },
    });
    sessionRef.current = session;
    try {
      await session.start();
    } catch (error) {
      setAsrStatus("error");
      setAsrError(error instanceof Error ? error.message : "无法开始录音");
      sessionRef.current = null;
    }
  }

  function onPickImages(fileList: FileList | null) {
    if (!fileList?.length) return;
    const next: LocalImage[] = [];
    for (const file of Array.from(fileList)) {
      if (!file.type.startsWith("image/")) continue;
      next.push({
        id: `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`,
        file,
        previewUrl: URL.createObjectURL(file),
      });
    }
    setImages((prev) => [...prev, ...next].slice(0, 6));
  }

  function removeImage(id: string) {
    setImages((prev) => {
      const target = prev.find((item) => item.id === id);
      if (target) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((item) => item.id !== id);
    });
  }

  async function onSubmit() {
    setSubmitError(null);
    const raw = text.trim();
    if (!raw && images.length === 0) {
      setSubmitError("请先语音/输入需求，或上传示意图");
      return;
    }

    if (listening) {
      await sessionRef.current?.stop();
      sessionRef.current = null;
    }

    setSubmitting(true);
    try {
      const imagePaths: string[] = [];
      for (const item of images) {
        const uploaded = await uploadImage(item.file);
        imagePaths.push(uploaded.path);
      }
      const task = await createTask({
        raw_voice_text: raw || null,
        image_paths: imagePaths,
        images_content: images.map((item) => item.file.name),
      });
      navigate(`/apps?highlight=${task.id}`, { replace: false });
    } catch (error) {
      if (error instanceof ApiError) {
        setSubmitError(error.message);
      } else {
        setSubmitError("提交失败，请稍后重试");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-5 px-4 py-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold tracking-tight">创建应用</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          按住思路口述需求，可附带 UI 草图；提交后进入异步编排流水线。
        </p>
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="requirement">需求描述</Label>
          <span className="text-xs text-muted-foreground">
            {asrStatus === "listening"
              ? "识别中…"
              : asrStatus === "connecting"
                ? "连接 FunASR…"
                : "可手动编辑"}
          </span>
        </div>
        <textarea
          id="requirement"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          placeholder="例如：做一个请假审批小应用，员工提交申请，主管审批…"
          className="w-full resize-none rounded-2xl border border-input bg-background px-4 py-3 text-sm leading-relaxed outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30"
          disabled={submitting}
        />

        <div className="flex items-center gap-3">
          <Button
            type="button"
            size="lg"
            variant={listening ? "secondary" : "default"}
            className={cn("flex-1", listening && "animate-pulse")}
            onClick={() => void toggleListening()}
            disabled={submitting}
          >
            {listening ? (
              <>
                <Square className="size-4" />
                停止录音
              </>
            ) : (
              <>
                <Mic className="size-4" />
                语音输入
              </>
            )}
          </Button>
        </div>
        {asrError ? (
          <p className="text-xs text-destructive" role="alert">
            {asrError}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            语音走内网 FunASR；连不上时可直接打字。
          </p>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>辅助图片</Label>
          <button
            type="button"
            className="inline-flex items-center gap-1 text-sm font-medium text-primary"
            onClick={() => fileRef.current?.click()}
            disabled={submitting || images.length >= 6}
          >
            <ImagePlus className="size-4" />
            添加
          </button>
          <input
            id={fileInputId}
            ref={fileRef}
            type="file"
            accept="image/*"
            capture="environment"
            multiple
            className="hidden"
            onChange={(e) => {
              onPickImages(e.target.files);
              e.target.value = "";
            }}
          />
        </div>

        {images.length === 0 ? (
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="flex w-full flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-border bg-muted/40 px-4 py-10 text-sm text-muted-foreground"
            disabled={submitting}
          >
            <ImagePlus className="size-6 text-primary" />
            拍照或从相册选择草图
          </button>
        ) : (
          <div className="grid grid-cols-3 gap-2">
            {images.map((img) => (
              <div key={img.id} className="relative aspect-square overflow-hidden rounded-xl bg-muted">
                <img
                  src={img.previewUrl}
                  alt={img.file.name}
                  className="size-full object-cover"
                />
                <button
                  type="button"
                  aria-label="移除图片"
                  className="absolute right-1 top-1 rounded-full bg-background/90 p-1 text-foreground shadow"
                  onClick={() => removeImage(img.id)}
                  disabled={submitting}
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {submitError ? (
        <p className="text-sm text-destructive" role="alert">
          {submitError}
        </p>
      ) : null}

      <Button
        type="button"
        size="lg"
        className="w-full"
        disabled={submitting}
        onClick={() => void onSubmit()}
      >
        {submitting ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            提交中…
          </>
        ) : (
          "提交并开始部署"
        )}
      </Button>
    </div>
  );
}
