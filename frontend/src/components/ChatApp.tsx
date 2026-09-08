"use client";

import { FormEvent, type ReactNode, useRef, useState } from "react";

import { type ChatMessage, useChat } from "@/hooks/useChat";
import { usePdfDocument } from "@/hooks/usePdfDocument";
import { useTheme } from "@/hooks/useTheme";
import {
  ArrowUpIcon,
  BoltIcon,
  ChatIcon,
  ChevronIcon,
  CloseIcon,
  FileIcon,
  HistoryIcon,
  MoonIcon,
  PaperclipIcon,
  SunIcon,
} from "@/components/icons";

type View = "chat" | "history" | "documents";

const SUGGESTIONS = [
  "Summarize this document",
  "What are the main findings?",
  "Extract key points",
  "Explain in simple terms",
];

export default function ChatApp() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [view, setView] = useState<View>("chat");
  const { dark, toggleTheme } = useTheme();
  const { pdfDoc, uploading, error: documentError, uploadPdf, clearPdf, clearError: clearDocumentError } =
    usePdfDocument();
  const {
    question,
    setQuestion,
    messages,
    historyItems,
    asking,
    error: chatError,
    canAsk,
    ask,
  } = useChat(pdfDoc, uploading);

  const error = chatError ?? documentError;
  const busy = uploading || asking;

  async function onPickPdf(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file) {
      return;
    }
    await uploadPdf(file);
    if (fileRef.current) {
      fileRef.current.value = "";
    }
  }

  function submitAsk(text: string) {
    if (!ask(text)) {
      return;
    }
    clearDocumentError();
    setView("chat");
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submitAsk(question);
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between px-5 py-4 sm:px-8">
        <button type="button" onClick={() => setView("chat")} className="flex items-center gap-2.5">
          <Logo />
          <span className="text-[18px] font-semibold tracking-tight">Chunky</span>
        </button>

        <div className="flex items-center gap-1 sm:gap-2">
          <NavButton active={view === "history"} onClick={() => setView("history")} icon={<HistoryIcon />} label="History" />
          <NavButton active={view === "documents"} onClick={() => setView("documents")} icon={<FileIcon />} label="Documents" />
          <span className="mx-2 hidden h-5 w-px bg-[var(--line)] sm:block" />
          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--ink)] hover:bg-[var(--chip)]"
            aria-label="Toggle theme"
          >
            {dark ? <MoonIcon /> : <SunIcon />}
          </button>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--chip)] text-[13px] font-medium">
            N
          </div>
        </div>
      </header>

      <main className="flex min-h-0 flex-1 flex-col px-5 pb-5 sm:px-8">
        {view === "chat" && messages.length === 0 ? (
          <EmptyState onSuggestion={submitAsk} />
        ) : null}

        {view === "chat" && messages.length > 0 ? (
          <MessageList messages={messages} thinking={asking} />
        ) : null}

        {view === "history" ? (
          <Panel title="History">
            {historyItems.length === 0 ? (
              <p className="text-[15px] text-[var(--muted)]">No questions yet.</p>
            ) : (
              <ul className="space-y-2">
                {historyItems.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setQuestion(item.content);
                        setView("chat");
                      }}
                      className="w-full rounded-2xl bg-[var(--chip)] px-4 py-3 text-left text-[14px]"
                    >
                      {item.content}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        ) : null}

        {view === "documents" ? (
          <Panel title="Documents">
            {pdfDoc ? (
              <p className="text-[15px] text-[var(--muted)]">
                {pdfDoc.filename} · {pdfDoc.status}
              </p>
            ) : (
              <p className="text-[15px] text-[var(--muted)]">No PDF uploaded yet. Attach one in the chat box.</p>
            )}
          </Panel>
        ) : null}

        {error ? (
          <p className="mx-auto mb-3 w-full max-w-[760px] rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <form onSubmit={onSubmit} className="mx-auto w-full max-w-[760px]">
          {pdfDoc ? (
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[var(--chip)] px-3 py-1 text-[13px]">
              <FileIcon width={14} height={14} />
              <span>{uploading ? "Uploading…" : pdfDoc.filename}</span>
              <button type="button" onClick={clearPdf} aria-label="Remove PDF">
                <CloseIcon />
              </button>
            </div>
          ) : null}

          <div className="flex items-center gap-1 rounded-[28px] bg-[var(--input)] px-2 py-2 sm:px-3">
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              disabled={busy}
              onChange={(event) => onPickPdf(event.target.files)}
            />
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="flex h-10 w-10 items-center justify-center rounded-full text-[var(--muted)] hover:text-[var(--ink)]"
              aria-label="Upload PDF"
              disabled={busy}
            >
              <PaperclipIcon />
            </button>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask anything or upload a PDF..."
              className="h-11 flex-1 bg-transparent text-[15px] outline-none placeholder:text-[var(--muted)]"
            />
            <span className="hidden items-center gap-0.5 pr-1 text-[13px] font-medium sm:flex">
              GPT-4o
              <ChevronIcon className="text-[var(--muted)]" />
            </span>
            <button
              type="submit"
              disabled={!canAsk}
              className="ml-1 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--send)] text-[var(--send-fg)] disabled:opacity-30"
              aria-label="Send"
            >
              <ArrowUpIcon />
            </button>
          </div>
          <p className="mt-3 text-center text-[11px] leading-5 text-[var(--muted)]">
            By using Chunky, you agree that answers may be generated by AI and should be verified for accuracy.
          </p>
        </form>
      </main>
    </div>
  );
}

function Logo() {
  return (
    <span className="relative h-7 w-7 shrink-0">
      <span className="absolute left-1.5 top-0 h-[13px] w-[13px] rotate-45 rounded-[3px] bg-[#d0d0d4]" />
      <span className="absolute left-0.5 top-1.5 h-[13px] w-[13px] rotate-45 rounded-[3px] bg-[#b8b8be]" />
      <span className="absolute left-0 top-3 h-[13px] w-[13px] rotate-45 rounded-[3px] bg-[var(--ink)]" />
    </span>
  );
}

function NavButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 rounded-full px-3 py-2 text-[14px] ${
        active ? "bg-[var(--chip)] font-medium" : "text-[var(--ink)] hover:bg-[var(--chip)]"
      }`}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
}

function EmptyState({ onSuggestion }: { onSuggestion: (prompt: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-[760px] flex-1 flex-col items-center justify-center pb-6 text-center">
      <p className="text-[12px] font-medium tracking-[0.18em] text-[var(--muted)]">YOUR DOCUMENTS, ANSWERED</p>
      <h1 className="mt-4 text-[40px] font-semibold leading-none tracking-tight sm:text-[56px]">
        Ask. Upload. <span className="text-[var(--accent)]">Understand.</span>
      </h1>
      <p className="mt-5 max-w-md text-[16px] leading-7 text-[var(--muted)]">
        Chat with your documents or just ask anything.
        <br />
        Get clear, accurate answers in seconds.
      </p>

      <div className="mt-14 grid w-full gap-8 sm:grid-cols-3">
        <Feature
          icon={<FileIcon width={18} height={18} />}
          title="Use your PDFs"
          text="Upload a PDF in the chat and get grounded answers."
        />
        <Feature
          icon={<ChatIcon width={18} height={18} />}
          title="Ask anything"
          text="Summarize, find details, compare, or explain."
        />
        <Feature
          icon={<BoltIcon width={18} height={18} />}
          title="Fast and reliable"
          text="Powered by state-of-the-art AI with source-backed answers."
        />
      </div>

      <div className="mt-12 flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSuggestion(prompt)}
            className="rounded-full bg-[var(--chip)] px-4 py-2.5 text-[13px]"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}

function Feature({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="flex flex-col items-center">
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-[var(--icon-bg)]">{icon}</div>
      <p className="text-[15px] font-medium">{title}</p>
      <p className="mt-1.5 max-w-[210px] text-[13px] leading-5 text-[var(--muted)]">{text}</p>
    </div>
  );
}

function MessageList({ messages, thinking }: { messages: ChatMessage[]; thinking: boolean }) {
  return (
    <ul className="mx-auto flex w-full max-w-[760px] flex-1 flex-col gap-4 overflow-y-auto pb-6">
      {messages.map((message) => (
        <li
          key={message.id}
          className={message.role === "user" ? "ml-12 rounded-2xl bg-[var(--chip)] px-4 py-3" : "mr-12 py-3"}
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
            {message.role === "user" ? "You" : message.usedRag ? "Chunky · RAG" : "Chunky"}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-[15px] leading-7">{message.content}</p>
          {message.sources && message.sources.length > 0 ? (
            <details className="mt-3 rounded-xl bg-[var(--chip)] px-3 py-2">
              <summary className="cursor-pointer text-sm text-[var(--muted)]">
                {message.sources.length} retrieved chunk{message.sources.length === 1 ? "" : "s"}
              </summary>
              <div className="mt-3 space-y-3">
                {message.sources.map((source) => (
                  <div key={`${message.id}-${source.chunk_index}`} className="text-sm leading-6">
                    <p className="text-xs text-[var(--muted)]">
                      Chunk {source.chunk_index}
                      {source.page ? ` · page ${source.page}` : ""}
                    </p>
                    <p className="mt-1">{source.text}</p>
                  </div>
                ))}
              </div>
            </details>
          ) : null}
        </li>
      ))}
      {thinking ? <li className="text-sm text-[var(--muted)]">Thinking…</li> : null}
    </ul>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-[760px] flex-1 flex-col pt-8">
      <h1 className="text-3xl font-semibold">{title}</h1>
      <div className="mt-5">{children}</div>
    </div>
  );
}
