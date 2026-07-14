import { Check, Copy, ExternalLink, Share2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

type Props = {
  title: string;
  url: string;
  stageLabel: string;
};

export function ShareCard({ title, url, stageLabel }: Props) {
  const [copied, setCopied] = useState(false);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      // fallback
      window.prompt("复制内网链接", url);
    }
  }

  async function share() {
    const payload = {
      title: `FlashApp · ${title}`,
      text: `【${stageLabel}】${title}\n内网体验：${url}`,
      url,
    };
    if (navigator.share) {
      try {
        await navigator.share(payload);
        return;
      } catch {
        // user cancel or unsupported — fall through to copy
      }
    }
    await copyLink();
  }

  return (
    <div className="space-y-3 rounded-2xl bg-secondary/50 px-4 py-4">
      <div className="space-y-1">
        <p className="text-xs font-medium text-primary">一键分享卡片</p>
        <p className="text-sm font-medium leading-snug">{title}</p>
        <p className="break-all text-xs text-muted-foreground">{url}</p>
      </div>
      <div className="flex gap-2">
        <Button type="button" className="flex-1" variant="default" onClick={() => void share()}>
          <Share2 className="size-4" />
          分享到 IM
        </Button>
        <Button type="button" variant="outline" onClick={() => void copyLink()} aria-label="复制链接">
          {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
        </Button>
        <Button type="button" variant="outline" asChild>
          <a href={url} target="_blank" rel="noreferrer" aria-label="打开应用">
            <ExternalLink className="size-4" />
          </a>
        </Button>
      </div>
    </div>
  );
}
