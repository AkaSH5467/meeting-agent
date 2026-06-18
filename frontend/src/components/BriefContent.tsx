import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { BriefOutput } from "../types";
import { clsx } from "clsx";

const confidenceColors = {
  high: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-red-100 text-red-800",
};

export function BriefContent({ brief }: { brief: BriefOutput }) {
  // Safe defaults — older briefs saved before the schema change may be
  // missing these fields entirely, which would otherwise crash the render.
  const techSignals = brief.tech_signals ?? { domain_tags: [], notable_tools: [], summary: "" };
  const domainTags = techSignals.domain_tags ?? [];
  const notableTools = techSignals.notable_tools ?? [];
  const techSummary = techSignals.summary ?? "";

  return (
    <Card className="mt-3">
      <CardContent className="pt-3 space-y-4">
        <div>
          <h4 className="font-medium text-sm text-muted-foreground mb-1">
            What they do
          </h4>
          <p className="text-sm text-foreground">{brief.what_they_do}</p>
        </div>

        {brief.recent_news.length > 0 && (
          <div>
            <h4 className="font-medium text-sm text-muted-foreground mb-2">
              Recent News
            </h4>
            <ul className="space-y-2 text-sm">
              {brief.recent_news.map((news, i) => (
                <li key={i} className="flex flex-col gap-0.5">
                  <span className="font-medium">{news.headline}</span>
                  <span className="text-xs text-muted-foreground">
                    {news.date && `${news.date} `}{news.source && `— ${news.source}`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <Separator />

        <div>
          <h4 className="font-medium text-sm text-muted-foreground mb-2">
            Domain & Tech Signals
          </h4>
          <div className="space-y-3 text-sm">
            {techSummary && (
              <p className="text-foreground">{techSummary}</p>
            )}
            {domainTags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {domainTags.map((tag, i) => (
                  <Badge key={i} variant="outline" className="text-xs font-normal">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
            {notableTools.length > 0 && (
              <div>
                <span className="font-medium">Notable tools:</span>{" "}
                <span className="text-foreground">
                  {notableTools.join(", ")}
                </span>
              </div>
            )}
            {domainTags.length === 0 &&
              !techSummary && (
                <p className="text-xs text-muted-foreground italic">
                  No domain signals found for this company.
                </p>
              )}
          </div>
        </div>

        {brief.pain_points.length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-2">
                Pain Points
              </h4>
              <ul className="space-y-1 text-sm">
                {brief.pain_points.map((point, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-muted-foreground">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {brief.talking_points.length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-2">
                Talking Points
              </h4>
              <ol className="space-y-2 text-sm list-decimal list-inside">
                {brief.talking_points.map((tp, i) => (
                  <li key={i} className="space-y-1">
                    <span className="font-medium">{tp.point}</span>
                    {tp.rationale && (
                      <span className="text-xs text-muted-foreground ml-4 block">
                        {tp.rationale}
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          </>
        )}

        <Separator />

        <div className="flex items-center justify-between">
          <Badge
            className={clsx(confidenceColors[brief.confidence], "text-xs")}
          >
            Confidence: {brief.confidence}
          </Badge>
          {brief.data_gaps.length > 0 && (
            <span className="text-xs text-muted-foreground">
              Gaps: {brief.data_gaps.join(", ")}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}