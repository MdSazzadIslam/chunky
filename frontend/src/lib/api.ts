import { getUserId } from "./user";

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export type DocumentStatus = "processing" | "ready" | "error";

export type DocumentResponse = {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  duplicate: boolean;
  error_message: string | null;
};

export type SourceChunk = {
  chunk_index: number;
  page: number | null;
  text: string;
  score: number | null;
};

export type ChatResponse = {
  answer: string;
  used_rag: boolean;
  sources: SourceChunk[];
};

function headers(json = false): HeadersInit {
  const value: Record<string, string> = {
    "X-User-Id": getUserId(),
  };
  if (json) {
    value["Content-Type"] = "application/json";
  }
  return value;
}

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | { msg: string }[] };
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg;
    }
  } catch {
    /* fall through */
  }
  return `Request failed (${response.status})`;
}

export function validatePdf(file: File): string | null {
  if (!file) {
    return "Choose a PDF file first.";
  }
  if (file.type !== "application/pdf") {
    return "File type must be application/pdf.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return `PDF must be ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB or smaller.`;
  }
  return null;
}

export async function uploadDocument(file: File): Promise<DocumentResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch("/backend/api/v1/documents/upload", {
    method: "POST",
    headers: headers(),
    body: form,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as DocumentResponse;
}

export async function getDocument(documentId: string): Promise<DocumentResponse> {
  const response = await fetch(`/backend/api/v1/documents/${documentId}`, {
    headers: headers(),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as DocumentResponse;
}

export async function sendChat(question: string, documentId?: string): Promise<ChatResponse> {
  const response = await fetch("/backend/api/v1/chat", {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({
      question,
      document_id: documentId || null,
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as ChatResponse;
}
