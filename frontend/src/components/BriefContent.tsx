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
            Tech Signals
          </h4>
          <div className="space-y-3 text-sm">
            {brief.tech_signals.frontend.length > 0 && (
              <div>
                <span className="font-medium">Frontend:</span>{" "}
                <span className="text-foreground">
                  {brief.tech_signals.frontend.join(", ")}
                </span>
              </div>
            )}
            {brief.tech_signals.backend.length > 0 && (
              <div>
                <span className="font-medium">Backend:</span>{" "}
                <span className="text-foreground">
                  {brief.tech_signals.backend.join(", ")}
                </span>
              </div>
            )}
            {brief.tech_signals.infra.length > 0 && (
              <div>
                <span className="font-medium">Infrastructure:</span>{" "}
                <span className="text-foreground">
                  {brief.tech_signals.infra.join(", ")}
                </span>
              </div>
            )}
            {brief.tech_signals.data_tools.length > 0 && (
              <div>
                <span className="font-medium">Data Tools:</span>{" "}
                <span className="text-foreground">
                  {brief.tech_signals.data_tools.join(", ")}
                </span>
              </div>
            )}
            {brief.tech_signals.oss_activity && (
              <div>
                <span className="font-medium">OSS Activity:</span>{" "}
                <span className="text-foreground">
                  {brief.tech_signals.oss_activity}
                </span>
              </div>
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