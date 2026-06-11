import { useEffect, useState, useCallback } from "react";
import type { Meeting, MeetingBriefStatus } from "../types";

const WS_URL = "ws://localhost:8080/ws/meetings";
const API_URL = "http://localhost:8080";

export function useLiveMeetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const fetchInitialMeetings = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/meetings`);
      if (!response.ok) return;
      const data: Meeting[] = await response.json();

      // For each done meeting, fetch its brief and attach it
      const enriched = await Promise.all(
        data.map(async (meeting) => {
          if (meeting.brief_status === "done") {
            try {
              const briefRes = await fetch(`${API_URL}/meetings/${meeting.id}/brief`);
              if (briefRes.ok) {
                const briefData = await briefRes.json();
                return { ...meeting, brief: briefData.data };
              }
            } catch {
              // brief fetch failed, return meeting without brief
            }
          }
          return meeting;
        })
      );

      setMeetings(enriched);
    } catch (error) {
      console.error("Failed to fetch initial meetings:", error);
    }
  }, []);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const update: MeetingBriefStatus = JSON.parse(event.data);
      setMeetings((prev) =>
        prev.map((meeting) => {
          if (meeting.id === update.meeting_id) {
            return {
              ...meeting,
              brief_status: update.status,
              ...(update.brief && { brief: update.brief }),
            };
          }
          return meeting;
        })
      );
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }, []);

  const connect = useCallback(() => {
    const websocket = new WebSocket(WS_URL);
    websocket.onopen = () => {
      setIsConnected(true);
      fetchInitialMeetings();
    };
    websocket.onmessage = handleMessage;
    websocket.onclose = () => {
      setIsConnected(false);
      setTimeout(connect, 3000);
    };
    websocket.onerror = () => {
      setIsConnected(false);
    };
    setWs(websocket);
  }, [fetchInitialMeetings, handleMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (ws) ws.close();
    };
  }, [connect]);

  return { meetings, isConnected };
}