import { useState } from "react";

import { sendChat, type DocumentResponse, type SourceChunk } from "@/lib/api";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  usedRag?: boolean;
  sources?: SourceChunk[];
};

export function useChat(pdfDoc: DocumentResponse | null, blocked = false) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processing = pdfDoc?.status === "processing";
  const canAsk = question.trim().length > 0 && !asking && !blocked && !processing;
  const historyItems = messages.filter((message) => message.role === "user");

  function ask(text: string): boolean {
    const cleaned = text.trim();
    if (!cleaned || asking || blocked || processing) {
      return false;
    }

    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: cleaned },
    ]);
    setQuestion("");
    setError(null);
    setAsking(true);
    void send(cleaned);
    return true;
  }

  async function send(cleaned: string) {
    try {
      const documentId = pdfDoc?.status === "ready" ? pdfDoc.document_id : undefined;
      const result = await sendChat(cleaned, documentId);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          usedRag: result.used_rag,
          sources: result.sources,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The request failed.");
    } finally {
      setAsking(false);
    }
  }

  return {
    question,
    setQuestion,
    messages,
    historyItems,
    asking,
    error,
    canAsk,
    ask,
  };
}
