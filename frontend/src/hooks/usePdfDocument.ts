import { useEffect, useState } from "react";

import { getDocument, uploadDocument, validatePdf, type DocumentResponse } from "@/lib/api";

export function usePdfDocument() {
  const [pdfDoc, setPdfDoc] = useState<DocumentResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const documentId = pdfDoc?.document_id;
  const status = pdfDoc?.status;

  useEffect(() => {
    if (!documentId || status !== "processing") {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const latest = await getDocument(documentId);
        setPdfDoc(latest);
        if (latest.status === "error") {
          setError(latest.error_message || "PDF processing failed.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not check document status.");
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [documentId, status]);

  async function uploadPdf(file: File): Promise<void> {
    const validationError = validatePdf(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setUploading(true);
    try {
      const uploaded = await uploadDocument(file);
      setPdfDoc(uploaded);
      if (uploaded.status === "error") {
        setError(uploaded.error_message || "PDF processing failed.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setPdfDoc(null);
    } finally {
      setUploading(false);
    }
  }

  function clearPdf() {
    setPdfDoc(null);
    setError(null);
  }

  function clearError() {
    setError(null);
  }

  return { pdfDoc, uploading, error, uploadPdf, clearPdf, clearError };
}
