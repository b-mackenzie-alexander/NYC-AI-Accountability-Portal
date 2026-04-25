"use client";

import React, { useState } from "react";
import { uploadDisclosure } from "@/lib/api";

export default function UploadDemoClient() {
  const [agencyName, setAgencyName] = useState("Administration for Children's Services");
  const [adminToken, setAdminToken] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) {
      setError("Choose a PDF before uploading.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const uploadResult = await uploadDisclosure(file, agencyName, adminToken);
      setResult(uploadResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-2xl rounded-xl bg-white p-6 shadow">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-orange-600">
          Local demo tooling
        </p>
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Admin PDF Upload</h1>
        <p className="mb-6 text-sm text-gray-600">
          This page is hidden, unlinked, and disabled unless the local demo flag is enabled.
          Paste the backend admin token for this session only; it is never stored.
        </p>

        <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
          <label className="flex flex-col">
            <span className="mb-1 font-medium text-gray-800">Agency name</span>
            <input
              value={agencyName}
              onChange={(e) => setAgencyName(e.target.value)}
              className="rounded-lg border px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              required
            />
          </label>

          <label className="flex flex-col">
            <span className="mb-1 font-medium text-gray-800">Admin token</span>
            <input
              type="password"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              className="rounded-lg border px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              required
            />
          </label>

          <label className="flex flex-col">
            <span className="mb-1 font-medium text-gray-800">Disclosure PDF</span>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="rounded-lg border px-3 py-2 text-gray-900"
              required
            />
          </label>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-6 py-2.5 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Uploading..." : "Upload PDF"}
          </button>
        </form>

        {result && (
          <pre className="mt-6 max-h-80 overflow-auto rounded-lg bg-gray-950 p-4 text-xs text-green-100">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </main>
  );
}
